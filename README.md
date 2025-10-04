# Divorce Risk Prediction with LLM and XGBoost

- This project predicts divorce likelihood based on relationship-related answers. It combines:

  - Gemini-powered LLM for free-text to structured data mapping.
  - XGBoost classifier for prediction.
  - FastAPI backend for APIs.
  - HTML/CSS/JS UI for doctors to register, add couples, create assessments, enter answers, run predictions, and track couple history via timeline.

--------


## 🔑 Key Features

### 🔬 Core ML Pipeline

  - **Free-text → Structured data:** Maps user inputs to 54 canonical relationship questions.
  - **New Question Mapping:** If doctors add custom questions, the LLM automatically maps them to the most relevant canonical dimensions for consistency.
  - **Polarity adjustment:** Detects contradictions (opposite meanings) and flips values.
  - **Prediction:** Uses XGBoost to calculate divorce likelihood.
  - **Auditability:** Logs show which canonical item was matched, stance, confidence, and adjusted values.
  - **Recommendation Program Generation:** After prediction, an LLM generates tailored recommendations for couples based on assessment results.

### 🖥️ Web Application

  - **Doctor Login/Register**
  - **Dashboard:** Manage couples and start new assessments.
  - **Assessment Page:** Add structured answers for each partner.
  - **Prediction:** Run ML prediction and display results in the UI.
  - **Timeline View:** Each couple has a **history timeline** showing assessments, predictions, and progress over time.
  - **Recommendations:** For each assessment, the doctor can **generate AI-powered personalized recommendations** or view previously generated ones.

--------

## 📁 Project Structure
```bash
├── app/
│   ├── services/
│   │   ├── Predictor.py        # Runs predictions using the ML model
│   │   ├── Recommendation.py   # Creates recommendations using LLM
│   ├── db.py                   # Database connection setup
│   ├── main.py                 # FastAPI main app and routes
│   ├── models.py               # Database tables (SQLAlchemy models)
│   └── schemas.py              # Data formats (Pydantic schemas)
│
├── data/
│   ├── divorce_atr.csv         # Dataset for divorce attributes
│
├── frontend/                   # Website UI
│   ├── imgs/                   # Images
│   ├── app.js                  # Handles frontend API calls
│   ├── assessment-style.css    # Styles for assessment page
│   ├── assessment.html         # Page for adding answers
│   ├── dashboard.html          # Doctor’s main dashboard
│   ├── recommendation.html     # Shows generated recommendations
│   ├── style.css               # General styles
│   ├── timeline.html           # Timeline of couple’s history
│   └── welcome.html            # Welcome/Login page
│
├── models/
│   └── xgb_model.json          # Saved trained ML model
│
├── .gitignore                  # Files to ignore in Git
├── README.md                   # Project documentation
├── canonical.py                # Canonical 54 questions
├── config.py                   # Settings & environment variables
├── gemini_router.py            # Maps free-text → canonical questions with LLM
├── inference.py                # Preprocess + run prediction
├── model_train.py              # Script to train the XGBoost model
├── recommend_program.py        # Logic for full recommendation workflow
├── requirements.txt            # Needed Python packages
└── run_demo.py                 # Command-line demo for testing pipeline
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

## ▶️ Run Backend (FastAPI)

```bash
uvicorn backend.main:app --reload
```

Open Frontend

Just open frontend/index.html in your browser.

--------

## ▶️ Run CLI Demo

If you want to test the pipeline without UI:

```bash
python run_demo.py
```

The output includes:
p(Divorce) = 0.96 -> Class = 1
And an audit log showing mappings and results for each input.

--------

## 🧠 How It Works
- **LLM Routing:** Routes the free-text input to the most relevant canonical question using Gemini API.
- **Polarity Fixing:** Checks if the user input contradicts the canonical question (using NLI). If the contradiction is detected, the answer scale (0–4) is flipped.
- **Deduplication:** Handles cases where multiple inputs map to the same canonical item.
- **Prediction:** Uses the XGBoost classifier to predict the divorce likelihood, which outputs a probability and class.
- **Recommendations:** After prediction, the doctor can generate AI-powered recommendations for the couple.
- **UI Flow:** Doctor → enters answers → runs prediction → generates recommendations → views history in timeline.
