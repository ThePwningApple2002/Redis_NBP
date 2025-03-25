import os
import yaml


def load_config(config_path: str = "schema.yaml") -> dict:
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def get_openai_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("Please set your OPEN_AI_KEY environment variable.")
    return key
