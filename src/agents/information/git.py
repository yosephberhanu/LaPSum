import os
import shlex
import subprocess
from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableMap

from src.utils import State, get_prompts, get_agent

AGENT_KEY = "information_git"

class GitAgent:
    """
    An agent that answers questions about Git history by generating and executing Git commands.
    """

    class GitCommand(BaseModel):
        command: str = Field(..., description="The git command to run (excluding 'git')")

    def __init__(self):
        self.llm = get_agent(AGENT_KEY)
        self.prompt = get_prompts(AGENT_KEY)
        self.run_git_tool = self._make_git_tool()
        self.graph = self._build_graph()

    def _make_git_tool(self):
        @tool
        def run_git_command(repository_path, command: str) -> str:
            """Run a git command in the given repository path."""
            if isinstance(repository_path, list):
                repository_path = repository_path[-1]
            if not os.path.exists(os.path.join(repository_path, ".git")):
                return f"Error: {repository_path} is not a valid Git repository."
            try:
                print(f"git {command}")
                result = subprocess.run(
                    ["git"] + shlex.split(command.strip()),
                    cwd=repository_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                return f"Error running git command: {e.stderr.strip()}"

        return run_git_command

    def _build_query_gen(self):
        return (
            RunnableMap({
                "git_query": lambda s: s["git_query"],
                "repository_path": lambda s: s["repository_path"],
                "context": lambda s: s.get("context", [])
            }) 
            | self.prompt 
            | self.llm.bind_tools([self.GitCommand])
        )

    def _query_gen_node(self, state: dict):
        message = self.query_gen.invoke(state)
        tool_call = next((tc for tc in message.tool_calls if tc["name"] == "GitCommand"), None)
        state["command"] = tool_call["args"]["command"] if tool_call else "log -1"
        return state    

    def _run_git_node(self, state: dict):
        result = self.run_git_tool.invoke({
            "repository_path": state["repository_path"],
            "command": state["command"]
        })
        state["result"] = result
        return state

    def _check_result_node(self, state: dict) -> Literal["final", "fix_command"]:
        return "fix_command" if state["result"].startswith("Error:") else "final"

    def _fix_command_node(self, state: dict):
        fix_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Git expert. Fix the git command below based on the error message."),
            ("human", "Repository: {repository_path}\n\nOriginal command:\n{command}\n\nError:\n{result}")
        ])
        fixer = (
            RunnableMap({
                "repository_path": lambda s: s["repository_path"],
                "command": lambda s: s["command"],
                "result": lambda s: s["result"]
            }) 
            | fix_prompt 
            | self.llm.bind_tools([self.GitCommand])
        )
        message = fixer.invoke(state)
        tool_call = next((tc for tc in message.tool_calls if tc["name"] == "GitCommand"), None)
        state["command"] = tool_call["args"]["command"] if tool_call else "log -1"
        return state

    def _extract_final(self, state: dict) -> dict:
        state["final_result"] = state["result"]
        return state

    def _build_graph(self):
        self.query_gen = self._build_query_gen()
        sg = StateGraph(dict)

        sg.add_node("generate_command", self._query_gen_node)
        sg.add_node("run_command", self._run_git_node)
        sg.add_node("fix_command", self._fix_command_node)
        sg.add_node("final", self._extract_final)

        sg.add_edge(START, "generate_command")
        sg.add_edge("generate_command", "run_command")
        sg.add_conditional_edges("run_command", self._check_result_node)
        sg.add_edge("fix_command", "run_command")
        sg.add_edge("final", END)

        return sg.compile()

def information_git_node(state: State) -> State:
    query = state.get("git_query", [])
    if not state.get("run_git", False):
        state["git_response"] = [AIMessage(content="PASS")]
        return state

    if isinstance(query, list):
        if not query:  # If it's an empty list
            print("Git query skipped: empty list.")
            state["git_response"] = [AIMessage(content="PASS")]
            return state
        query = query[-1]  # Otherwise, use the last HumanMessage
    elif query == "PASS":
        state["git_response"] = [AIMessage(content="PASS")]
        return state

    agent = GitAgent()
    result = agent.graph.invoke({
        "git_query": state["git_query"],
        "repository_path": (
            state["repository_path"] if isinstance(state["repository_path"], list)
            else [state["repository_path"]]
        ),
        "context": []
    })
    state["git_response"] = [AIMessage(content=result["result"])]
    return state