from pydantic import BaseModel
from typing import List, Optional
from langgraph.graph import StateGraph, END
from utils.enum import ENUM
from text_to_sql.text_to_sql import TextToSQL
from text_to_sql.common import (
    Config,
    LLMConfig,
    SLConfig,
    ContextConfig,
    QueryConfig,
)


class AgentState(BaseModel):
    query: str
    model: str
    provider: str
    history: Optional[List[dict]] = []
    DetectIntent: Optional[str] = None
    CheckDetails: Optional[str] = None
    GenerateSQL: Optional[str] = None
    Summary: Optional[str] = None


# Format conversation history for context
def format_history(history, max_turns=5):
    if not history:
        return ""
    recent_history = history[-max_turns:]
    return "\n".join(
        [f"User: {turn['user']}\nAgent: {turn['agent']}" for turn in recent_history]
    )


# Tool: Detect if query is data-retrieval related (for text-to-SQL use case)
def detect_intent_tool(state: AgentState, llm_agent) -> dict:
    query = state.query

    """
    Detect whether the query is about retrieving data from a database (for SQL generation).
    Return 'data' if it is, otherwise 'other'.
    """

    system_prompt = f"""
    You are an expert assistant that decides if a user query is asking to retrieve data from a database.
    Return ONLY one of the following labels:

    - data: if the query is asking about facts, entities, statistics, filters, aggregations, rankings, or structured info.
    - other: if the query is not about retrieving data (e.g., definitions, instructions, or general advice).

    Here are some EXAMPLES:

    Query: Which actors have the first name 'Scarlett'?  
    → data

    Query: How many distinct actor last names are there?  
    → data

    Query: What is SQL?  
    → other

    Query: What does SELECT do in SQL?  
    → other

    Query: Which customers rented more than 3 categories?  
    → data

    Now, based on the query below, return only `data` or `other` (lowercase only — no explanation).

    Query:
    \"\"\"{query}\"\"\"
    """

    result = llm_agent.generate(system_prompt=system_prompt.strip(), user_prompt="")
    final = result.strip().lower()

    if final not in ["data", "other"]:
        final = "other"

    return {"DetectIntent": final}


# Tool: Check if the query is specific enough for SQL generation
def is_question_detailed_enough(state: AgentState, llm_agent) -> dict:
    """Check if the query is specific enough for SQL generation."""
    query = state.query
    history = state.history or []
    history_text = format_history(history, max_turns=3)

    system_prompt = f"""
    You are an AI that checks if the user input is specific enough for SQL generation.
    Recent conversation:
    {history_text}

    Is the following query detailed enough to generate a specific SQL query? Return only 'yes' or 'no'.
    """

    result = llm_agent.generate(system_prompt=system_prompt.strip(), user_prompt=query)
    final = result.strip().lower()

    if final not in ["yes", "no"]:
        final = "no"

    return {"CheckDetails": final}


# Tool: Generate SQL and update history
def generate_sql_tool(state: AgentState) -> dict:
    """Generate SQL query from user input and update conversation history."""
    query = state.query

    # Initialize text to sql model
    text_to_sql_config = Config(
        max_retry_attempt=5,
        rewriter_config=LLMConfig(
            type="api",
            model=state.model,
            provider=state.provider,
            api_key=ENUM.get(state.provider, ""),
        ),
        query_generator_config=LLMConfig(
            type="api",
            model=state.model,
            provider=state.provider,
            api_key=ENUM.get(state.provider, ""),
        ),
        schema_linker_config=SLConfig(
            type="api",
            model=state.model,
            provider=state.provider,
            api_key=ENUM.get(state.provider, ""),
            schema_path="./files/metadata/sakila.json",
        ),
        retrieve_context_config=ContextConfig(
            data_path="./files/dataset/dataset_sakila.csv"
        ),
        query_executor_config=QueryConfig(
            host=ENUM.get("DB_SOURCE_HOST", ""),
            database=ENUM.get("DB_SOURCE_DATABASE", ""),
            user=ENUM.get("DB_SOURCE_USER", ""),
            password=ENUM.get("DB_SOURCE_PASSWORD", ""),
            port=ENUM.get("DB_SOURCE_PORT", ""),
        ),
    )
    text_to_sql = TextToSQL(config=text_to_sql_config)

    # Generate SQL
    sql = text_to_sql.generate_v1(user_prompt=query, method="Multistage")
    result = text_to_sql.execute_query(sql)

    return {"GenerateSQL": result}


# Tool: Summarize SQL execution result
def summarize_data_tool(state: AgentState, llm_agent) -> dict:
    """Generate a natural language summary of the SQL result and update history."""
    query = state.query
    sql_output = state.GenerateSQL or {}
    history = state.history or []

    # Extract SQL result for natural language summary
    raw_data = sql_output.get("result", []) if isinstance(sql_output, dict) else []
    error_msg = sql_output.get("error") if isinstance(sql_output, dict) else None

    # Format the data (or error) for summarization
    data_str = str(raw_data[:10]) if raw_data else (error_msg or "No data returned.")

    system_prompt = f"""
    You are an AI assistant that helps users understand SQL results.
    
    The user asked: "{query}"
    The SQL result is:
    {data_str}
    
    Please summarize the result in natural language as if explaining to a non-technical user.
    """

    summary = llm_agent.generate(
        system_prompt=system_prompt.strip(), user_prompt=""
    ).strip()

    # Append to conversation history
    history.append(
        {
            "user": query,
            "agent": {
                "response": summary,
                "data": raw_data if raw_data else [error_msg] if error_msg else [],
            },
        }
    )

    return {"Summary": summary, "history": history}


# Build workflow graph
def build_graph(llm_agent):
    workflow = StateGraph(AgentState)

    workflow.add_node("DetectIntentTool", lambda state: detect_intent_tool(state, llm_agent))
    workflow.add_node("CheckDetailsTool", lambda state: is_question_detailed_enough(state, llm_agent))
    workflow.add_node("GenerateSQLTool", lambda state: generate_sql_tool(state))
    workflow.add_node("SummarizeDataTool", lambda state: summarize_data_tool(state, llm_agent))

    workflow.add_conditional_edges(
        "DetectIntentTool",
        lambda x: x.DetectIntent,
        {"data": "CheckDetailsTool", "other": END},
    )

    workflow.add_conditional_edges(
        "CheckDetailsTool",
        lambda x: x.CheckDetails,
        {"yes": "GenerateSQLTool", "no": END},
    )

    workflow.add_edge("GenerateSQLTool", "SummarizeDataTool")

    workflow.set_entry_point("DetectIntentTool")
    workflow.set_finish_point("SummarizeDataTool")

    # Compile graph
    return workflow.compile()
