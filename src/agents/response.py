import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from src.utils import State, get_prompts, get_agent

AGENT_KEY = "response"
llm = get_agent(AGENT_KEY)
prompt = get_prompts(AGENT_KEY)

import ast

def clean_source_response(messages: list[BaseMessage]) -> list[BaseMessage]:
    if not messages:
        return []

    content = messages[0].content  # assume single message for now
    try:
        parsed = ast.literal_eval(content)  # safe parse string into Python list
        # Expecting list of tuples, extract first element of each
        class_names = sorted(set(item[0] for item in parsed if isinstance(item, tuple)))
        formatted = "The following classes or entities were found:\n" + "\n".join(f"- {name}" for name in class_names)
        return [AIMessage(content=formatted)]
    except Exception:
        return [AIMessage(content="(⚠️ Couldn't parse source response.)\n\n" + content)]
def ensure_list(value):
    # Ensure all values are lists of BaseMessages
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        return [HumanMessage(content=value)]
    elif isinstance(value, BaseMessage):
        return [value]
    else:
        return []

def response_node(state: State) -> State:
    input_data = {
        "user_query": ensure_list(state.get("user_query", [])),
        "source_response": clean_source_response(ensure_list(state.get("source_response", []))),
        "git_response": clean_source_response(ensure_list(state.get("git_response", []))),
        "github_response": clean_source_response(ensure_list(state.get("github_response", []))),
        "docs_response": clean_source_response(ensure_list(state.get("docs_response", []))),
        "context": ensure_list(state.get("context", [])),
    }
    # This chain already includes prompt -> LLM -> extract .content
    chain = prompt | llm | RunnableLambda(lambda msg: msg.content if isinstance(msg, BaseMessage) else msg)
    result = chain.invoke(input_data)
    state["final_response"] = AIMessage(content=result)
    return state