import os
from dotenv import load_dotenv, find_dotenv
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv(find_dotenv())
set_tracing_disabled(True)

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

client_provider = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",  # Gemini
)

MODEL = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client_provider,
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "data.json")
OUTPUT_PATH = os.path.join("data", "profiles_datas.json")