from typing import Literal
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph,  START, END
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableMap
from langchain_community.utilities import SQLDatabase

from src.utils import State, get_prompts, get_agent

AGENT_KEY = "source_code"
class SourceAgent:
    """
    An agent that uses a large language model to generate, execute, and optionally fix
    SQL queries based on user questions and UML diagram context stored in a SQLite database.

    The agent is designed to:
    - Interpret a user question (source_query) in the context of a UML-based schema.
    - Use an LLM to generate a SQL query.
    - Execute the query on the database.
    - If an error occurs, ask the LLM to fix the query and retry.
    - Return the final query result.

    Attributes:
        db (SQLDatabase): The SQLDatabase object connected to the provided database URI.
        llm (BaseLanguageModel): The initialized LLM used for query generation and correction.
        prompt (ChatPromptTemplate): The prompt used to instruct the LLM.
        execute_sql_tool (Tool): A LangChain tool that executes SQL queries.
        graph (Graph): The compiled LangGraph execution graph.
    """

    class GeneratedQuery(BaseModel):
        """
        Schema for the tool output from the LLM, containing the SQL query to be executed.
        """
        sql: str = Field(..., description="The SQL query to execute.")

    def __init__(self, db_uri: str = "sqlite:///uml-data.db"):
        """
        Initializes the SourceAgent with a database connection and LLM tools.

        Args:
            db_uri (str): URI to the SQLite database containing UML schema data.
        """
        self.db = SQLDatabase.from_uri(db_uri)
        self.llm = get_agent(AGENT_KEY)
        self.prompt = get_prompts(AGENT_KEY)
        self.execute_sql_tool = self._make_execute_sql_tool()
        self.graph = self._build_graph()

    def _make_execute_sql_tool(self):
        """
        Creates a LangChain tool that executes SQL queries on the configured database.

        Returns:
            Tool: A callable LangChain tool for executing SQL.
        """
        db = self.db
        @tool
        def execute_sql(query: str) -> str:
            """Executes a SQL query against the UML database and returns the result."""
            result = db.run_no_throw(query)
            return result or "Error: Query failed."
        
        return execute_sql

    def _build_query_gen(self):
        """
        Builds a runnable chain that generates SQL queries from user input using the LLM.

        Returns:
            Runnable: A LangChain runnable pipeline for query generation.
        """
        return (
            RunnableMap({
                "context": lambda s: s["context"],
                "source_query": lambda s: s["source_query"],
                "history": lambda s: s.get("history", [])
            })
            | self.prompt
            | self.llm.bind_tools([self.GeneratedQuery])
        )

    def _query_gen_node(self, state: dict):
        """
        LangGraph node that invokes the query generation chain and returns SQL.

        Args:
            state (dict): The graph state containing 'source_query' and 'context'.

        Returns:
            dict: A dictionary containing the generated SQL as 'sql'.
        """
        message = self.query_gen.invoke(state)
        tool_call = next((tc for tc in message.tool_calls if tc["name"] == "GeneratedQuery"), None)
        if tool_call:
            sql = tool_call["args"]["sql"]
            return {"sql": sql}
        return {"sql": "SELECT 1"}  # fallback

    def _run_sql_node(self, state: dict):
        """
        LangGraph node that executes the generated SQL query and stores the result.

        Args:
            state (dict): The graph state containing 'sql'.

        Returns:
            dict: The updated state with the execution result in 'result'.
        """
        result = self.execute_sql_tool.invoke({"query": state["sql"]})
        state["result"] = result
        return state

    def _check_result_node(self, state: dict) -> Literal["final", "fix_query"]:
        """
        Determines whether the query result is valid or needs to be fixed.

        Args:
            state (dict): The graph state containing the SQL execution result.

        Returns:
            Literal["final", "fix_query"]: The next node to execute based on result status.
        """
        if state["result"].startswith("Error:"):
            return "fix_query"
        return "final"

    def _fix_query_node(self, state: dict):
        """
        LangGraph node that uses the LLM to fix an invalid SQL query based on the error message.

        Args:
            state (dict): The graph state containing the original SQL and error message.

        Returns:
            dict: A dictionary with a revised SQL query as 'sql'.
        """
        fix_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a SQL expert. Fix the SQL query below based on the error message."),
            ("human", "Original query:\n{sql}\n\nError:\n{result}"),
        ])
        fixer = (
            RunnableMap({
                "sql": lambda s: s["sql"],
                "result": lambda s: s["result"]
            })
            | fix_prompt
            | self.llm.bind_tools([self.GeneratedQuery])
        )
        message = fixer.invoke(state)
        tool_call = next((tc for tc in message.tool_calls if tc["name"] == "GeneratedQuery"), None)
        if tool_call:
            return {"sql": tool_call["args"]["sql"]}
        return {"sql": "SELECT 1"}

    def _extract_final(self, state: dict) -> dict:
        """
        Final LangGraph node that saves the final query result to 'final_result'.

        Args:
            state (dict): The graph state with the SQL execution result.

        Returns:
            dict: The updated state with 'final_result'.
        """
        state["final_result"] = state["result"]
        return state

    def _build_graph(self):
        """
        Constructs the LangGraph pipeline for query generation, execution, and fixing.

        Returns:
            Graph: The compiled LangGraph execution graph.
        """
        self.query_gen = self._build_query_gen()

        sg = StateGraph(dict)
        sg.add_node("generate_query", self._query_gen_node)
        sg.add_node("run_query", self._run_sql_node)
        sg.add_node("fix_query", self._fix_query_node)
        sg.add_node("final", self._extract_final)

        sg.add_edge(START, "generate_query")
        sg.add_edge("generate_query", "run_query")
        sg.add_conditional_edges("run_query", self._check_result_node)
        sg.add_edge("fix_query", "run_query")
        sg.add_edge("final", END)

        return sg.compile()
def information_source_code_node(state: State) -> State:
    """
    Handles LLM-based SQL query generation and execution for source code context.

    This function extracts the latest source query from the state, uses a SourceAgent 
    to generate and execute a SQL query based on the UML diagram in the specified 
    SQLite database, and stores the result in `state["source_response"]`.

    If the source query is "PASS", the function skips processing and returns the 
    state unchanged.

    Args:
        state (State): The current LangGraph state containing the source query and 
                       the name of the source database (as 'source_db').

    Returns:
        State: The updated state with the SQL query result stored in 'source_response'.
    """
    query = state["source_query"][-1] if isinstance(state["source_query"], list) and state["source_query"] else state["source_query"]
    if not state.get("run_code", False):
        state["source_response"] = [AIMessage(content="PASS")]
        return state
    if query == "PASS":
        state["source_response"] = ""
        return state
    agent = SourceAgent(db_uri=f"sqlite:///{state['source_db']}")
    result = agent.graph.invoke({
            "source_query": state["source_query"],
            "context": []
        })
    state["source_response"] = AIMessage(result["final_result"])
    return state
