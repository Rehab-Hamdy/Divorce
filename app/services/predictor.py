# app/services/predictor.py
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from inference import load_xgb_model, predict_from_free_text_LLM
from canonical import FEATURES
from app.models import Answer, Prediction, Assessment

# Load XGB once (process-wide)
_xgb_model = None
def get_model():
    global _xgb_model
    if _xgb_model is None:
        _xgb_model = load_xgb_model()
    return _xgb_model

def _qas_from_answers(answers: List[Answer]) -> List[Dict[str, Any]]:
    """Turn DB answers into the qas format the inference expects."""
    qas = []
    for a in answers:
        qas.append({"text": a.user_text, "value": a.value})
    return qas

def _avg_vectors(x_a: pd.Series, x_b: pd.Series) -> pd.Series:
    """Element-wise average ignoring NaNs."""
    arr = np.vstack([x_a.values, x_b.values])
    avg = np.nanmean(arr, axis=0)
    return pd.Series(avg, index=FEATURES, dtype=float)

def predict_for_assessment(db: Session, assessment_id: int, decision_thr: float = 0.5) -> Tuple[float, int, Dict[str, float], List[Dict[str, Any]]]:
    """
    - Pull all answers for assessment.
    - Split by partner A/B.
    - Map/normalize each side via LLM.
    - Average A & B per canonical feature.
    - Run XGB on the averaged vector.
    - Save Prediction row; return results.
    """
    answers_all = db.query(Answer).filter(Answer.assessment_id == assessment_id).all()
    a_answers = [a for a in answers_all if a.partner.value == "A"]
    b_answers = [a for a in answers_all if a.partner.value == "B"]

    model = get_model()

    # Build qas lists
    qas_a = _qas_from_answers(a_answers)
    qas_b = _qas_from_answers(b_answers)

    # If one side is missing, we still proceed with the other
    proba_a, pred_a, x_a, audit_a = predict_from_free_text_LLM(qas_a, model, nli_thr=0.65, dedup="best", decision_thr=decision_thr) if qas_a else (0.0, 0, pd.Series(np.nan, index=FEATURES), pd.DataFrame([]))
    proba_b, pred_b, x_b, audit_b = predict_from_free_text_LLM(qas_b, model, nli_thr=0.65, dedup="best", decision_thr=decision_thr) if qas_b else (0.0, 0, pd.Series(np.nan, index=FEATURES), pd.DataFrame([]))

    # Average vectors
    x_avg = _avg_vectors(x_a.reindex(FEATURES), x_b.reindex(FEATURES))

    # Final prediction on averaged vector
    X_row = pd.DataFrame([x_avg.values], columns=FEATURES)
    proba = float(model.predict_proba(X_row)[0, 1])
    pred_class = int(proba >= decision_thr)

    # Merge audits and tag partner
    audit_a = audit_a.copy()
    audit_b = audit_b.copy()
    if not audit_a.empty:
        audit_a["partner"] = "A"
    if not audit_b.empty:
        audit_b["partner"] = "B"
    audit_combined = pd.concat([audit_a, audit_b], ignore_index=True) if not (audit_a.empty and audit_b.empty) else pd.DataFrame([])

    # Persist prediction
    pred_row = Prediction(
        assessment_id=assessment_id,
        proba=proba,
        pred_class=pred_class,
        vector_json={feat: (None if pd.isna(v) else float(v)) for feat, v in x_avg.items()},
        audit_json=(audit_combined.fillna("").to_dict(orient="records") if not audit_combined.empty else []),
    )
    db.add(pred_row)
    db.commit()
    db.refresh(pred_row)

    return proba, pred_class, pred_row.vector_json, pred_row.audit_json
