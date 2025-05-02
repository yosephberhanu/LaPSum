import re
from langchain_core.messages import BaseMessage, HumanMessage
def safe_get_content(value, label):
    if isinstance(value, list) and value:
        return value[-1].content
    if isinstance(value, BaseMessage):
        return value.content
    return f"{label}: PASS or not applicable"

def remove_think_block(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
