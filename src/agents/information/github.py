from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableMap
from github import Github, GithubException
import os, json

from src.utils import State, get_prompts, get_agent

AGENT_KEY = "information_github"

class GitHubAgent:
    class GitHubQuery(BaseModel):
        query: str = Field(..., description="A GitHub metadata question turned into a structured query.")

    def __init__(self):
        self.llm = get_agent(AGENT_KEY)
        self.prompt = get_prompts(AGENT_KEY)
        self.github = Github(os.getenv("GITHUB_TOKEN"))
        self.graph = self._build_graph()

    def _run_github_query(self, repo_name: str, query: str):
        try:
            repo = self.github.get_repo(repo_name)
            if "issue" in query.lower():
                search = self.github.search_issues(f"repo:{repo_name} {query}")
                return json.dumps([{
                    "number": i.number,
                    "title": i.title,
                    "state": i.state,
                    "url": i.html_url
                } for i in search[:5]], indent=2)
            elif "pull" in query.lower():
                prs = repo.get_pulls(state="all")
                return json.dumps([{
                    "number": pr.number,
                    "title": pr.title,
                    "user": pr.user.login,
                    "url": pr.html_url
                } for pr in prs[:5]], indent=2)
            return "Query type not supported."
        except GithubException as e:
            return f"GitHub error: {str(e)}"

    def _build_query_gen(self):
        return (
            RunnableMap({
                "github_query": lambda s: s["github_query"],
                "github_url": lambda s: s["github_url"],
                "context": lambda s: s.get("context", [])
            })
            | self.prompt
            | self.llm.bind_tools([self.GitHubQuery])
        )

    def _query_gen_node(self, state: dict):
        message = self.query_gen.invoke(state)
        tool_call = next((tc for tc in message.tool_calls if tc["name"] == "GitHubQuery"), None)
        state["query"] = tool_call["args"]["query"] if tool_call else "issue"
        return state

    def _run_query_node(self, state: dict):
        result = self._run_github_query(state["github_url"][-1], state["query"])
        state["result"] = result
        return state

    def _extract_final(self, state: dict):
        state["final_result"] = state["result"]
        return state

    def _build_graph(self):
        self.query_gen = self._build_query_gen()
        sg = StateGraph(dict)
        sg.add_node("generate_query", self._query_gen_node)
        sg.add_node("run_query", self._run_query_node)
        sg.add_node("final", self._extract_final)

        sg.add_edge(START, "generate_query")
        sg.add_edge("generate_query", "run_query")
        sg.add_edge("run_query", "final")
        sg.add_edge("final", END)
        return sg.compile()

def information_github_node(state: State) -> State:
    query = state["github_query"][-1] if isinstance(state["github_query"], list) else state["github_query"]
    if not state.get("run_github", False):
        state["github_response"] = [AIMessage(content="PASS")]
        return state
    if query == "PASS":
        state["github_response"] = ""
        return state

    agent = GitHubAgent()
    result = agent.graph.invoke({
        "github_query": state["github_query"],
        "github_url": [state["github_url"]],
        "context": []
    })
    state["github_response"] = AIMessage(content=result["final_result"])
    return state