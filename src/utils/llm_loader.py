import os
import yaml
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.tools import Tool

def load_llm(agent_config):
    """
    Loads an LLM instance based on the configuration for a specific agent.

    Parameters:
    - agent_config (dict): Configuration dictionary with keys:
        - 'provider' (str): LLM provider name ('openai', 'anthropic', 'ollama', 'groq').
        - 'model' (str): Model name (e.g. 'gpt-4', 'claude-3-sonnet-20240229').
        - 'temperature' (float, optional): Sampling temperature (default is 0.7).

    Returns:
    - LLM instance from the appropriate LangChain chat module.
    """
    provider = agent_config["provider"]
    model = agent_config["model"]
    temperature = agent_config.get("temperature", 0.7)

    if provider == "openai":
        return ChatOpenAI(model=model, temperature=temperature)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, temperature=temperature)
    elif provider == "ollama":
        return ChatOllama(model=model, temperature=temperature)
    elif provider == "groq":
        return ChatGroq(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

# Load the YAML config file that defines LLM configurations for multiple agents
config_path = os.path.join(os.path.dirname(__file__), "../..",os.getenv("CONFIG_FILE"))

with open(os.path.abspath(config_path), "r") as f:
    config = yaml.safe_load(f)

# Dictionary to store initialized LLMs per agent
agents = {}

# Loop through each defined agent in the config and load its corresponding LLM
for agent_name in config["llms"].keys():
    agents[agent_name] = load_llm(config["llms"][agent_name])


def get_agent(agent_name: str):
    """
    Retrieves a previously loaded LLM instance by its agent name.

    Parameters:
    - agent_name (str): The name of the agent as defined in the config.

    Returns:
    - The LLM instance associated with the given agent name.

    Raises:
    - ValueError if the agent name is not found.
    """
    if agent_name not in agents:
        raise ValueError(f"Agent {agent_name} not found.")
    return agents[agent_name]