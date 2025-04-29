from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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
    database: str
    history: Optional[List[dict]] = []
    Language: Optional[str] = None
    DetectIntent: Optional[str] = None
    CheckDetails: Optional[str] = None
    GenerateSQL: Optional[Dict[str, Any]] = None
    Summary: Optional[str] = None
    GeneratedQueryRaw: Optional[str] = None


# Format conversation history for context
def format_history(history, max_turns=5):
    if not history:
        return ""
    recent_history = history[-max_turns:]
    return "\n".join(
        [f"User: {turn['user']}\nAgent: {turn['agent']}" for turn in recent_history]
    )


# Tool: Detect language of query
def detect_language_tool(state: AgentState, llm_agent) -> dict:
    """Detect language (English or Indonesian) based on user query."""
    query = state.query

    system_prompt = """
    You are an AI assistant specialized in language detection.
    Your task is simple: Given a user query, return ONLY the detected language ISO code ('en' for English, 'id' for Indonesian).
    No explanation, no decoration. Just one word output.

    Examples:
    "How are you today?" -> en
    "Apa kabar hari ini?" -> id
    """

    result = llm_agent.generate(system_prompt=system_prompt.strip(), user_prompt=query)
    lang = result.strip().lower()

    if lang not in ["en", "id"]:
        lang = "en"  # Default to English

    return {"Language": lang}

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

    - data: if the query is asking about facts, entities, statistics, filters, aggregations, rankings, comparisons, counts, sums, averages, or any structured information that could be stored in tables
    - other: if the query is not about retrieving data (e.g., definitions, instructions, general advice, or how-to questions)

    THINK STEP BY STEP:
    1. Does the query ask for specific information that could be stored in database tables?
    2. Would answering this require looking up records or performing calculations on stored data?
    3. If yes to either, it's 'data'

    Here are some EXAMPLES:

    Query: Which actors have the first name 'Scarlett'?  
    → data (lookup in actor table)

    Query: How many distinct actor last names are there?  
    → data (count operation)

    Query: What is SQL?  
    → other (definition)

    Query: What does SELECT do in SQL?  
    → other (explanation)

    Query: Which customers rented more than 3 categories?  
    → data (filtering and counting)

    Query: Compare sales between 2022 and 2023  
    → data (comparison of stored data)

    Query: How do I write a JOIN query?  
    → other (instruction)

    Query: What's the average salary by department?  
    → data (aggregation)

    Now, based on the query below, return only `data` or `other` (lowercase only — no explanation).

    Query:
    \"\"\"{query}\"\"\"
    """

    result = llm_agent.generate(system_prompt=system_prompt.strip(), user_prompt="")
    final = result.strip().lower()

    if final not in ["data", "other"]:
        # Default to 'data' when unsure to allow for SQL attempt
        final = "data"

    return {"DetectIntent": final}


# Tool: Check if the query is specific enough for SQL generation
def is_question_detailed_enough(state: AgentState, llm_agent) -> dict:
    """Check if the query is specific enough for SQL generation."""
    query = state.query
    history = state.history or []
    history_text = format_history(history, max_turns=3)

    system_prompt = f"""
    You are an AI that checks if the user input is specific enough for SQL generation.
    Consider a question detailed enough if it:
    1. Specifies what data to retrieve (columns/fields)
    2. Includes relevant filters/conditions (WHERE clauses)
    3. Mentions any grouping/aggregation (GROUP BY)
    4. Or is a clear request that maps to database operations

    Recent conversation:
    {history_text}

    Return 'yes' if ANY of these are true:
    - The query contains specific entities/attributes to retrieve
    - It asks for filtered/aggregated/sorted data
    - It's a comparison between measurable quantities
    - The intent is clear enough to map to database tables/columns

    Return 'no' ONLY if:
    - The query is too vague to map to any database structure
    - It's missing critical details needed for SQL
    - It's a multi-part question needing clarification

    Return only 'yes' or 'no' based on the following query:
    """

    result = llm_agent.generate(system_prompt=system_prompt.strip(), user_prompt=query)
    final = result.strip().lower()

    if final not in ["yes", "no"]:
        # Default to 'yes' when unsure to allow for SQL attempt
        final = "yes"

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
        query_executor_config = QueryConfig(
            host=ENUM.get("database", {}).get(state.database, {}).get("DB_SOURCE_HOST", ""),
            database=ENUM.get("database", {}).get(state.database, {}).get("DB_SOURCE_DATABASE", ""),
            user=ENUM.get("database", {}).get(state.database, {}).get("DB_SOURCE_USER", ""),
            password=ENUM.get("database", {}).get(state.database, {}).get("DB_SOURCE_PASSWORD", ""),
            port=ENUM.get("database", {}).get(state.database, {}).get("DB_SOURCE_PORT", ""),
        )
    )
    text_to_sql = TextToSQL(config=text_to_sql_config)

    # Generate SQL
    sql = text_to_sql.generate_v1(user_prompt=query, method="Multistage")
    result = text_to_sql.execute_query(sql)

    return {"GenerateSQL": result, "GeneratedQueryRaw": sql}


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

    workflow.add_node("DetectLanguageTool", lambda state: detect_language_tool(state, llm_agent))
    workflow.add_node("DetectIntentTool", lambda state: detect_intent_tool(state, llm_agent))
    workflow.add_node("CheckDetailsTool", lambda state: is_question_detailed_enough(state, llm_agent))
    workflow.add_node("GenerateSQLTool", lambda state: generate_sql_tool(state))
    workflow.add_node("SummarizeDataTool", lambda state: summarize_data_tool(state, llm_agent))

    workflow.add_edge("DetectLanguageTool", "DetectIntentTool")
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

    workflow.set_entry_point("DetectLanguageTool")
    workflow.set_finish_point("SummarizeDataTool")

    # Compile graph
    return workflow.compile()
