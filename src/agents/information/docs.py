from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableMap
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from src.utils import State, get_prompts, get_agent

AGENT_KEY = "information_docs"

class DocsAgent:
    def __init__(self):
        self.llm = get_agent(AGENT_KEY)
        self.prompt = get_prompts(AGENT_KEY)
        self.tavily = TavilySearchResults()
        self.graph = self._build_graph()

    def _run_tavily_search(self, query: str, domain: str = "https://www.keycloak.org/documentation"):
        results = self.tavily.invoke({
            "query": query,
            "include_raw_content": True,
            "include_domains": [domain],
            "search_depth": "advanced",
            "num_results": 5
        })

        if not results:
            return "Unable to find relevant content."

        return "\n\n".join([r["content"] for r in results if "content" in r])

    def _build_query_gen(self):
        return (
            RunnableMap({
                "docs_query": lambda s: s["docs_query"],
                "context": lambda s: s.get("context", []),
                "docs": lambda s: s["docs"]
            })
            | self.prompt
            | self.llm
        )

    def _query_gen_node(self, state: dict):
        result = self.query_gen.invoke(state)
        state["docs_summary"] = result.content if hasattr(result, "content") else str(result)
        return state

    def _tavily_search_node(self, state: dict):
        query_msg = state["docs_query"][-1] if isinstance(state["docs_query"], list) else state["docs_query"]
        doc_source = state["docs_source"][-1] if isinstance(state["docs_source"], list) else state["docs_source"]
        
        query_str = query_msg.content if isinstance(query_msg, HumanMessage) else str(query_msg)

        try:
            result = self._run_tavily_search(query_str,doc_source)
            state["docs"] = [HumanMessage(content=result)]
        except Exception as e:
            state["docs"] = [HumanMessage(content=f"Failed to fetch documents: {str(e)}")]
        return state

    def _extract_final(self, state: dict):
        content = state.get("docs_summary") or "No summary available."
        state["final_result"] = content
        return state

    def _build_graph(self):
        self.query_gen = self._build_query_gen()

        sg = StateGraph(dict)
        sg.add_node("load_docs", self._tavily_search_node)
        sg.add_node("query_docs", self._query_gen_node)
        sg.add_node("final", self._extract_final)

        sg.add_edge(START, "load_docs")
        sg.add_edge("load_docs", "query_docs")
        sg.add_edge("query_docs", "final")
        sg.add_edge("final", END)
        return sg.compile()

def information_docs_node(state: State) -> State:
    query = state.get("docs_query", [])

    if isinstance(query, list) or not state.get("docs_source",''):
        if not query:
            state["docs_response"] = [AIMessage(content="PASS")]
            return state
        query = query[-1]
    elif query == "PASS":
        state["docs_response"] = [AIMessage(content="PASS")]
        return state
    agent = DocsAgent()
    result = agent.graph.invoke({
        "docs_query": state["docs_query"],
        "docs_source": state["docs_source"],
        "context": state.get("context", [])
    })
    state["docs_response"] = [AIMessage(content=result["final_result"])]
    return state
