# app/services/recommendation.py
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Assessment, Prediction, Recommendation
from recommend_program import call_gemini_recommend  # <-- LLM call

# ------------------------
# Positive / Negative sets
# ------------------------
POSITIVE_ITEMS = {
    "Atr1","Atr2","Atr3","Atr4","Atr5","Atr8","Atr9","Atr10","Atr11","Atr12",
    "Atr13","Atr14","Atr15","Atr16","Atr17","Atr18","Atr19","Atr20","Atr21",
    "Atr22","Atr23","Atr24","Atr25","Atr26","Atr27","Atr28","Atr29","Atr30"
}

NEGATIVE_ITEMS = {
    "Atr6","Atr7","Atr31","Atr32","Atr33","Atr34","Atr35","Atr36","Atr37","Atr38",
    "Atr39","Atr40","Atr41","Atr42","Atr43","Atr44","Atr45","Atr46","Atr47",
    "Atr48","Atr49","Atr50","Atr51","Atr52","Atr53","Atr54"
}


def risk_0_1(atr_id: str, value_0_4: Any) -> float:
    """Convert raw 0–4 answer into unified risk ∈ [0,1]."""
    try:
        v = float(value_0_4)
    except Exception:
        v = 0.0
    v = max(0.0, min(4.0, v))
    iv = int(round(v))

    if atr_id in POSITIVE_ITEMS:
        return round(1.0 - (iv / 4.0), 4)
    elif atr_id in NEGATIVE_ITEMS:
        return round(iv / 4.0, 4)
    else:
        return round(1.0 - (iv / 4.0), 4)


# ------------------------
# Domain Mapping
# ------------------------
DOMAIN_MAP = {
    "communication": list(range(1, 5)) + list(range(31, 38)),
    "affection": list(range(5, 10)),
    "values": list(range(10, 21)),
    "love_maps": list(range(21, 31)),
    "criticism": [32, 33, 34, 35, 36, 52, 53, 54],
    "volatility": list(range(37, 42)),
    "stonewalling": list(range(42, 48)),
    "defensiveness": list(range(48, 52)),
}


def calculate_domain_risks(vector_json: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Aggregate answers into risk bands per domain using risk_0_1 normalization."""
    domain_scores: Dict[str, Dict[str, Any]] = {}

    for domain, indices in DOMAIN_MAP.items():
        values: List[float] = []
        for i in indices:
            key = f"Atr{i}"
            if key in vector_json and vector_json[key] is not None:
                values.append(risk_0_1(key, vector_json[key]))

        avg_score = (sum(values) / len(values)) if values else 0.0

        if avg_score < 0.25:
            band = "Green"
        elif avg_score < 0.5:
            band = "Yellow"
        elif avg_score < 0.75:
            band = "Orange"
        else:
            band = "Red"

        domain_scores[domain] = {"risk": round(avg_score, 3), "band": band}

    return domain_scores


# ------------------------
# Recommendation Pipeline
# ------------------------
def generate_recommendation(db: Session, assessment_id: int):
    """Generate recommendations with LLM personalization."""
    # 1. get assessment
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        return {"error": "Assessment not found"}

    # 2. get latest prediction
    latest_pred = (
        db.query(Prediction)
        .filter(Prediction.assessment_id == assessment_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
    if not latest_pred:
        return {"error": "No prediction/vector data found. Run prediction first."}

    # 3. parse vector_json
    vector_raw = latest_pred.vector_json
    if isinstance(vector_raw, (str, bytes)):
        try:
            vector_json = json.loads(vector_raw)
        except Exception:
            return {"error": "Invalid vector_json format"}
    elif isinstance(vector_raw, dict):
        vector_json = vector_raw
    else:
        try:
            vector_json = json.loads(json.dumps(vector_raw))
        except Exception:
            return {"error": "Unrecognized vector_json type"}

    # 4. calculate risks
    domain_risks = calculate_domain_risks(vector_json)

    # 5. build modules (rules-based)
    modules: List[Dict[str, Any]] = []
    for domain, d in domain_risks.items():
        band = d.get("band", "Green")
        if domain == "communication" and band in ["Orange", "Red"]:
            modules.append({"domain": domain, "tasks": [
                "soft startup & XYZ feedback",
                "repair attempts & apology scripts",
                "timeouts & physiological self-soothing",
                "conflict debrief routine"
            ]})
        elif domain == "affection" and band != "Green":
            modules.append({"domain": domain, "tasks": [
                "Daily rituals of connection",
                "One weekly date",
                "One daily affection gesture"
            ]})
        elif domain == "values" and band != "Green":
            modules.append({"domain": domain, "tasks": [
                "Weekly 20-min talk on shared goals",
                "Define 3 family rituals around values",
                "Write a vision statement together"
            ]})
        elif domain == "love_maps" and band != "Green":
            modules.append({"domain": domain, "tasks": [
                "10 daily Love Map questions",
                "Weekly inner-world conversation (20 min)",
                "Stress check-in ritual"
            ]})
        elif domain == "criticism" and band in ["Orange", "Red"]:
            modules.append({"domain": domain, "tasks": [
                "Replace 'always/never' with specific complaints",
                "Practice the complaint formula (I feel... about... and need...)",
                "Create 1 repair cue (verbal or hand signal)"
            ]})
        elif domain == "volatility" and band in ["Orange", "Red"]:
            modules.append({"domain": domain, "tasks": [
                "Conflict timeout protocol (20 min breaks)",
                "Physiological self-soothing practice",
                "Conflict debrief checklist"
            ]})
        elif domain == "stonewalling" and band in ["Orange", "Red"]:
            modules.append({"domain": domain, "tasks": [
                "Flooding protocol (step back when overwhelmed)",
                "Use 're-entry' checklist after cooling down",
                "Daily body scan awareness exercise"
            ]})
        elif domain == "defensiveness" and band in ["Orange", "Red"]:
            modules.append({"domain": domain, "tasks": [
                "10% truth rule: find part you can own",
                "Daily ownership reflection",
                "Practice open-ended questions instead of rebuttals"
            ]})

    # 6. Call Gemini LLM to build the 4-week markdown table
    try:
        personalized_text = call_gemini_recommend(domain_risks, modules)
    except Exception as e:
        # fail-safe: if LLM call fails, produce a concise summary instead
        top_domains_sorted = sorted(domain_risks.items(), key=lambda kv: kv[1]["risk"], reverse=True)
        top_summary_lines = []
        for dom, info in top_domains_sorted[:3]:
            top_summary_lines.append(f"{dom.capitalize()}: {info['band']} (risk={info['risk']})")
        personalized_text = "Top concerns: " + "; ".join(top_summary_lines) if top_summary_lines else "No major concerns (all Green)."

    # 7. save in DB (create or update)
    existing = db.query(Recommendation).filter(Recommendation.assessment_id == assessment_id).first()
    if existing:
        existing.domains_json = domain_risks
        existing.modules_json = modules
        existing.personalized_text = personalized_text
        db.add(existing)
        db.commit()
        db.refresh(existing)
        rec = existing
    else:
        rec = Recommendation(
            assessment_id=assessment_id,
            domains_json=domain_risks,
            modules_json=modules,
            personalized_text=personalized_text
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

    return {
        "id": rec.id,
        "assessment_id": assessment_id,
        "domains": rec.domains_json,
        "modules": rec.modules_json,
        "text": rec.personalized_text  # markdown program
    }
