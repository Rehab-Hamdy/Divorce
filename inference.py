# inference.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from xgboost import XGBClassifier
from canonical import FEATURES, ID2TEXT
from gemini_router import gemini_route_and_relation_batch
from config import MODEL_PATH

def load_xgb_model() -> XGBClassifier:
    model = XGBClassifier()
    model.load_model(MODEL_PATH)  # native json
    return model

def _normalize_one_from_llm_route(route_obj: Dict[str, Any], user_val_0to4: int, nli_thr: float = 0.65) -> Tuple[Any, Any, Dict[str, Any]]:
    """
    Takes one route result item: {target_id, relation, confidence, alternates}
    Returns (feat_id, norm_value, meta) or (None, None, meta_on_error)
    """
    if "error" in route_obj:
        return None, None, {"status": "router_error", "raw": route_obj}

    fid = route_obj.get("target_id")
    conf = float(route_obj.get("confidence", 0.0))
    relation = route_obj.get("relation", "neutral")

    if not fid:
        return None, None, {"status": "router_missing_target", "raw": route_obj}

    v = float(np.clip(user_val_0to4, 0, 4))
    flip = (relation == "contradicts" and conf >= nli_thr)
    norm_v = 4.0 - v if flip else v

    meta = {
        "flip": flip,
        "relation": relation,
        "relation_conf": conf,
        "alternates": route_obj.get("alternates", []),
        "canon_text": ID2TEXT.get(fid, ""),
        "status": "ok"
    }
    return fid, norm_v, meta

def predict_from_free_text_LLM(qas: List[Dict[str, Any]], xgb_model: XGBClassifier, nli_thr: float = 0.65, dedup: str = "best", decision_thr: float = 0.5):
    """
    qas = [{"text": "...", "value": 0..4}, ...]
    Batch-calls Gemini to avoid rate-limit bursts.
    Returns: proba, pred, filled_vector(Series), audit_log(DataFrame)
    """
    # 1) Batch route all user texts
    texts = [qa.get("text", "") for qa in qas]
    routes = gemini_route_and_relation_batch(texts, topk=1, min_conf_allow=0.70)
    logs = []
    x = pd.Series(np.nan, index=FEATURES, dtype=float)
    taken: Dict[str, Tuple[float, float]] = {}

    if "error" in routes:
        # If the whole batch fails, record and return early with NaNs
        for qa in qas:
            logs.append({"user_text": qa.get("text", ""), "raw_value": qa.get("value", np.nan),
                        "status": "router_error", "error": routes["error"]})
        X_row = pd.DataFrame([x.values], columns=FEATURES)
        proba = float(xgb_model.predict_proba(X_row)[0, 1])
        pred = int(proba >= decision_thr)
        return proba, pred, x, pd.DataFrame(logs)

    results = routes.get("results", [])
    # 2) Normalize each mapped item
    for qa, route in zip(qas, results):
        fid, v, meta = _normalize_one_from_llm_route(route, qa.get("value", np.nan), nli_thr=nli_thr)
        if fid is None:
            logs.append({"user_text": qa.get("text", ""), "raw_value": qa.get("value", np.nan), **meta})
            continue

        conf = float(meta.get("relation_conf", 0.0))
        if (fid not in taken) or (dedup == "best" and conf > taken[fid][0]) or (dedup == "avg"):
            if dedup == "avg" and fid in taken and not np.isnan(x[fid]):
                x[fid] = np.nanmean([x[fid], v])
                taken[fid] = (max(taken[fid][0], conf), x[fid])
            else:
                x[fid] = v
                taken[fid] = (conf, v)

        logs.append({
            "feature": fid, "feature_text": ID2TEXT.get(fid, ""),
            "user_text": qa.get("text", ""), "raw_value": qa.get("value", np.nan),
            "normalized_value": v, **meta
        })

    # 3) Predict (XGBoost)
    X_row = pd.DataFrame([x.values], columns=FEATURES)
    proba = float(xgb_model.predict_proba(X_row)[0, 1])  # P(Class=1 Divorce)
    pred  = int(proba >= decision_thr)
    return proba, pred, x, pd.DataFrame(logs)
