# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

DATA_PATH = os.getenv("DATA_PATH", "data/divorce_atr.csv")
MODEL_PATH = os.getenv("MODEL_PATH", "models/xgb_model.json")  # xgboost native format
SEED = int(os.getenv("SEED", "42"))
