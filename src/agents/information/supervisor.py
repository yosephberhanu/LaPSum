import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from src.utils import State, get_prompts, get_agent

AGENT_KEY = "information_supervisor"

llm = get_agent(AGENT_KEY)
prompt = get_prompts(AGENT_KEY)

def safe_parse_json(text: str):
    try:
        json_str = text[text.index("{"):]
        result = json.loads(json_str)

        if isinstance(result, list):
            print("Warning: LLM returned a list instead of a dict.")
            result = result[0] if result and isinstance(result[0], dict) else {}

        return result
    except Exception as e:
        return {}

def information_supervisor_node(state: State) -> State:
    input_vars = {
        "user_query": state.get("user_query", []),
        "context": state.get("context", []),
        "source_query": state.get("source_query", []),
        "git_query": state.get("git_query", []),
        "github_query": state.get("github_query", []),
        "docs_query": state.get("docs_query", []),
        "source_response": state.get("source_response", []),
        "git_response": state.get("git_response", []),
        "github_response": state.get("github_response", []),
        "docs_response": state.get("docs_response", [])
    }

    chain = prompt | llm | RunnableLambda(lambda msg: msg.content if isinstance(msg, BaseMessage) else msg)
    result = chain.invoke(input_vars)

    parsed = safe_parse_json(result)

    if isinstance(parsed, dict):
        if parsed.get("source_code", "PASS") != "PASS" and not state.get("source_response"):
            state["source_query"] = [HumanMessage(content=parsed["source_code"])]
        if parsed.get("git", "PASS") != "PASS" and not state.get("git_response"):
            state["git_query"] = [HumanMessage(content=parsed["git"])]
        if parsed.get("github", "PASS") != "PASS" and not state.get("github_response"):
            state["github_query"] = [HumanMessage(content=parsed["github"])]
        if parsed.get("docs", "PASS") != "PASS" and not state.get("docs_response"):
            state["docs_query"] = [HumanMessage(content=parsed["docs"])]

    # Add supervisor LLM output for debugging or transparency
    state["supervisor_response"] = [AIMessage(content=str(parsed))]
    return state