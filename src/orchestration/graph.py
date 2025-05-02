from langgraph.graph import StateGraph,  START, END
from langchain_core.messages import AIMessage, HumanMessage
# from langchain_ollama import ChatOllama
from langgraph.graph.message import add_messages
from src.utils import State
from src.agents.information import create_information_subgraph
from src.agents.response import response_node
from src.agents.supervisor import supervisor_node


workflow = StateGraph(State)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("information", create_information_subgraph())
workflow.add_node("response", response_node)

workflow.add_edge("supervisor", "information")
workflow.add_edge("information", "response")
workflow.add_edge("response", END)

workflow.add_edge(START,"supervisor")

graph = workflow.compile()