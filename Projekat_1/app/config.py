import os
import yaml
from dotenv import load_dotenv 


def load_config(config_path: str = "schema.yaml") -> dict:
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def get_openai_api_key() -> str:
    load_dotenv()

    api_key = os.getenv("OPEN_AI_KEY")
    os.environ["OPENAI_API_KEY"] = api_key
    if not api_key:
        raise ValueError("Please set your OPEN_AI_KEY environment variable.")
    return api_key
