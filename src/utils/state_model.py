from typing import Annotated, List, Optional, Set, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from .data_models import UMLClassDiagram

def identity(a, b):
    return b

class State(TypedDict):
    # User input
    user_query: Annotated[list[HumanMessage], add_messages]

    # Project config
    source_db: Annotated[Optional[HumanMessage], identity]
    repository_path: Annotated[Optional[HumanMessage], identity]
    github_url: Annotated[Optional[HumanMessage], identity]
    docs_source: Annotated[Optional[HumanMessage], identity]
    docs_source_type: Annotated[Optional[HumanMessage], identity]

    # Agent input queries
    source_query: Annotated[list[HumanMessage], add_messages]
    git_query: Annotated[list[HumanMessage], add_messages]
    github_query: Annotated[list[HumanMessage], add_messages]
    docs_query: Annotated[list[HumanMessage], add_messages]

    # Agent outputs
    supervisor_response: Annotated[Optional[list[BaseMessage]], add_messages]
    source_response: Annotated[Optional[list[BaseMessage]], add_messages]
    git_response: Annotated[Optional[list[BaseMessage]], add_messages]
    github_response: Annotated[Optional[list[BaseMessage]], add_messages]
    docs_response: Annotated[Optional[list[BaseMessage]], add_messages]

    # Final output
    final_response: Annotated[Optional[HumanMessage], identity]
    
    information_round: Annotated[int, identity]
    information_done: Annotated[Set[str], identity]
    run_git: Annotated[Optional[bool], identity]
    run_github: Annotated[Optional[bool], identity]
    run_docs: Annotated[Optional[bool], identity]
    run_code: Annotated[Optional[bool], identity]