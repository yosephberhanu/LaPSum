from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

@tool
def parse_code(code):
    """
    Parses the code and provides a syntax tree
    :param code: string form of the code
    :return: string version of the SyntaxTree
    """
    import ast
    tree = ast.dump(ast.parse(code))
    return tree

if __name__ == "__main__":
    code_example = """
    def greet(name):
        return f"Hello, {name}!"
    """

    memory = MemorySaver()

    llm = ChatOllama(
        model="mistral",
        temperature=0.5
    ).bind_tools([parse_code])

    tools = [parse_code]

    agent_executor = create_react_agent(llm, tools, checkpointer=memory)

    # Use the agent
    config = {"configurable": {"thread_id": "abc123"}}
    for step in agent_executor.stream(
            {"messages": [HumanMessage(content=f"Please parse this code and briefly summarize\n{code_example}")]},
            config,
            stream_mode="values",
    ):
        step["messages"][-1].pretty_print()

    for step in agent_executor.stream(
            {"messages": [HumanMessage(content=f"Give me similar code to the provided code")]},
            config,
            stream_mode="values",
    ):
        step["messages"][-1].pretty_print()
