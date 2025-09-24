# Divorce Risk Prediction with LLM and XGBoost

- This project predicts divorce likelihood based on relationship-related answers. It combines:

- Gemini-powered LLM for free-text to structured data mapping.
- XGBoost classifier for prediction.
- FastAPI backend for APIs.
- HTML/CSS/JS UI for doctors to register, add couples, create assessments, enter answers, and run predictions.

--------


## 🔑 Key Features

- **🔬 Core ML Pipeline**

- **Free-text → Structured data:** Maps user inputs to 54 canonical relationship questions.
- **Polarity adjustment:** Detects contradictions (opposite meanings) and flips values.
- **Prediction:** Uses XGBoost to calculate divorce likelihood.
- **Auditability:** Logs show which canonical item was matched, stance, confidence, and adjusted values.

- **🖥️ Web Application**

- **Doctor Login/Register**
- **Dashboard:** Manage couples and start new assessments.
- **Assessment Page:** Add structured answers for each partner.
- **Prediction:** Run ML prediction and display results in the UI.

--------

## 📁 Project Structure
```bash
.
├── canonical.py         # Canonical items (Attr1..Attr54)
├── config.py            # Configuration (env variables)
├── gemini_router.py     # Routes free-text → canonical items (Gemini LLM)
├── inference.py         # Normalization + XGBoost inference
├── train_xgb.py         # Training script for XGBoost
├── run_demo.py          # CLI demo for free-text inputs
├── backend/             # FastAPI backend (doctors, couples, assessments, answers, predict)
├── frontend/            # HTML/CSS/JS UI
│   ├── index.html       # Welcome + Login/Register
│   ├── register.html    # Doctor registration
│   ├── dashboard.html   # Couples dashboard
│   ├── assessment.html  # Create assessment, add answers, run prediction
│   ├── style.css        # UI styling
│   └── app.js           # Frontend API logic
├── .env.example         # Example environment file
└── README.md            # Project documentation
```


--------

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

--------

▶️ Run Backend (FastAPI)

```bash
uvicorn backend.main:app --reload
```

Open Frontend

Just open frontend/index.html in your browser.

--------

▶️ Run CLI Demo

If you want to test the pipeline without UI:

```bash
python run_demo.py
```

The output includes:
p(Divorce) = 0.96 -> Class = 1
And an audit log showing mappings and results for each input.

--------

🧠 How It Works
- LLM Routing: Routes the free-text input to the most relevant canonical question using Gemini API.
- Polarity Fixing: Checks if the user input contradicts the canonical question (using NLI). If the contradiction is detected, the answer scale (0–4) is flipped.
- Deduplication: Handles cases where multiple inputs map to the same canonical item.
- Prediction: Uses the XGBoost classifier to predict the divorce likelihood, which outputs a probability and class.
- UI → Doctor enters answers, runs predictions, and gets results in a web dashboard.
