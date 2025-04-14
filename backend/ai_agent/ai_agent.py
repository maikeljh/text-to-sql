import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import TypedDict, List, Optional
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from text_to_sql.text_to_sql import TextToSQL
from text_to_sql.core import GeneralLLM
from text_to_sql.common import (
    Config,
    LLMConfig,
    SLConfig,
    ContextConfig,
    QueryConfig,
)

# Load environment variables
load_dotenv()

# Configurations
text_to_sql_config = Config(
    max_retry_attempt=5,
    rewriter_config=LLMConfig(
        type="api",
        model="gemini-1.5-flash",
        provider="gemini",
        api_key=os.getenv("API_KEY"),
    ),
    query_generator_config=LLMConfig(
        type="api",
        model="gemini-1.5-flash",
        provider="gemini",
        api_key=os.getenv("API_KEY"),
    ),
    schema_linker_config=SLConfig(
        type="api",
        model="gemini-1.5-flash",
        provider="gemini",
        api_key=os.getenv("API_KEY"),
        schema_path="./files/metadata/sakila.json",
    ),
    retrieve_context_config=ContextConfig(data_path="./files/dataset/dataset_sakila.csv"),
    query_executor_config=QueryConfig(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_DATABASE"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
    ),
)

general_config = LLMConfig(
    type="api",
    model="gemini-1.5-flash",
    provider="gemini",
    api_key=os.getenv("API_KEY"),
)

# Initialize agents
text_to_sql = TextToSQL(config=text_to_sql_config)
llm_agent = GeneralLLM(config=general_config)

# Format conversation history for context
def format_history(history, max_turns=5):
    if not history:
        return ""
    recent_history = history[-max_turns:]
    return "\n".join(
        [f"User: {turn['user']}\nAgent: {turn['agent']}" for turn in recent_history]
    )

# Tool: Detect if query is SQL-related
@tool
def detect_intent_tool(state: dict) -> dict:
    """Detect whether a query is related to SQL or not."""
    query = state["query"]
    history = state.get("history", [])
    history_text = format_history(history, max_turns=3)

    system_prompt = f"""
    You are an AI assistant that determines if a query is related to SQL or not.
    Recent conversation:
    {history_text}

    Now, classify the following query into 'sql' or 'other'.
    """

    result = llm_agent.generate(
        system_prompt=system_prompt.strip(),
        user_prompt=query
    )
    return {"DetectIntent": result.strip().lower()}

# Tool: Check if the query is specific enough for SQL generation
@tool
def is_question_detailed_enough(state: dict) -> dict:
    """Check if the query is specific enough for SQL generation."""
    query = state["query"]
    history = state.get("history", [])
    history_text = format_history(history, max_turns=3)

    system_prompt = f"""
    You are an AI that checks if the user input is specific enough for SQL generation.
    Recent conversation:
    {history_text}

    Is the following query detailed enough to generate a specific SQL query? Return only 'yes' or 'no'.
    """

    result = llm_agent.generate(
        system_prompt=system_prompt.strip(),
        user_prompt=query
    )
    return {"CheckDetails": result.strip().lower()}

# Tool: Generate SQL and update history
@tool
def generate_sql_tool(state: dict) -> dict:
    """Generate SQL query from user input and update conversation history."""
    query = state["query"]
    sql = text_to_sql.generate_v1(user_prompt=query, method="Multistage")

    # Update history
    history = state.get("history", [])
    history.append({
        "user": query,
        "agent": sql
    })

    return {
        "GenerateSQL": sql,
        "history": history
    }

# Build workflow graph
class AgentState(TypedDict):
    query: str
    history: Optional[List[dict]]
    DetectIntent: Optional[str]
    CheckDetails: Optional[str]
    GenerateSQL: Optional[str]

workflow = StateGraph(AgentState)

workflow.add_node("DetectIntentTool", detect_intent_tool)
workflow.add_node("CheckDetailsTool", is_question_detailed_enough)
workflow.add_node("GenerateSQLTool", generate_sql_tool)

workflow.add_conditional_edges("DetectIntentTool", lambda x: x["DetectIntent"], {
    "sql": "CheckDetailsTool",
    "other": END
})

workflow.add_conditional_edges("CheckDetailsTool", lambda x: x["CheckDetails"], {
    "yes": "GenerateSQLTool",
    "no": END
})

workflow.set_entry_point("DetectIntentTool")
workflow.set_finish_point("GenerateSQLTool")


# Compile graph
graph = workflow.compile()