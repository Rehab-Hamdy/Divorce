# Divorce Risk Prediction with LLM and XGBoost

This project predicts divorce likelihood based on relationship-related free-text answers using a **Gemini-powered LLM** (LLM routes) and **XGBoost classifier**.

---

## 🔑 Key Features
- **Free-text to structured data:** Maps user inputs to a fixed set of 54 canonical questions.
- **Polarity adjustment:** Detects contradictions (opposite meanings) and flips values.
- **Prediction:** Uses **XGBoost** to predict divorce likelihood.
- **Auditability:** Provides logs showing which canonical item was matched, stance, confidence, and adjusted values.

---

## 📁 Project Structure
.
├── canonical.py # Canonical items (Atr1..Atr54)
├── config.py # Configuration for environment variables
├── gemini_router.py # Routes user input to canonical items (Gemini LLM)
├── inference.py # Normalizes user input and predicts with XGBoost
├── train_xgb.py # Trains XGBoost model
├── run_demo.py # Runs the demo with free-text input
├── .env.example # Example environment file
└── README.md # Project documentation



---

## ⚙️ Setup

### 1. Install Dependencies
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```


▶️ Run Demo

To run the demo with free-text inputs, use:
```bash
python run_demo.py
```

The output includes:
p(Divorce) = 0.96 -> Class = 1
And an audit log showing mappings and results for each input.

🧠 How It Works
- LLM Routing: Routes the free-text input to the most relevant canonical question using Gemini API.
- Polarity Fixing: Checks if the user input contradicts the canonical question (using NLI). If the contradiction is detected, the answer scale (0–4) is flipped.
- Deduplication: Handles cases where multiple inputs map to the same canonical item.
- Prediction: Uses the XGBoost classifier to predict the divorce likelihood, which outputs a probability and class.
