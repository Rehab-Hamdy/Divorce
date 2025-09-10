# gemini_router.py
import json
import time
import random
from typing import Dict, Any, List, Union
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, DeadlineExceeded
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME
from canonical import canonical_items

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) not set. Put it in .env.")

genai.configure(api_key=GEMINI_API_KEY)

ROUTER_SYSTEM = (
    "You are a semantic router for a fixed bank of 54 survey items (Atr1..Atr54). "
    "For each USER sentence, select EXACTLY ONE canonical item that best matches the MEANING, not just keywords. "
    "Also classify the stance of the USER sentence relative to the chosen canonical text:\n"
    "- 'entails'  = user expresses essentially the SAME claim\n"
    "- 'contradicts' = user expresses the OPPOSITE claim\n"
    "- 'neutral'  = you cannot reasonably tell either way\n\n"
    "CRITICAL RULES:\n"
    "1) Prefer 'entails' or 'contradicts' when the meaning is clear. Use 'neutral' only when truly unsure.\n"
    "2) Do not guess below the confidence threshold supplied in the prompt; if nothing is above threshold, return 'no_match'.\n\n"
    "Output JSON ONLY, as:\n"
    "{\n"
    "  \"results\": [\n"
    "    {\n"
    "      \"target_id\": \"Atr##\" | \"no_match\",\n"
    "      \"relation\": \"entails\" | \"contradicts\" | \"neutral\",\n"
    "      \"confidence\": 0.0..1.0,\n"
    "      \"alternates\": [ {\"id\": \"Atr##\", \"confidence\": 0.0..1.0} ]\n"
    "    }, ...\n"
    "  ]\n"
    "}\n\n"
)


gemini_model = genai.GenerativeModel(
    model_name=GEMINI_MODEL_NAME,
    system_instruction=ROUTER_SYSTEM,
    generation_config={
        "temperature": 0.0,
        "response_mime_type": "application/json",
    },
)

def _generate_json(prompt_obj: dict, max_retries: int = 4) -> Union[dict, None]:
    """
    Calls Gemini and returns parsed JSON. Retries on transient errors with backoff.
    """
    delay = 2.0  # start with small delay; quota errors return suggested retry windows
    for attempt in range(1, max_retries + 1):
        try:
            resp = gemini_model.generate_content(json.dumps(prompt_obj))
            text = getattr(resp, "text", "") or (
                resp.candidates[0].content.parts[0].text
                if getattr(resp, "candidates", None) and resp.candidates[0].content.parts else ""
            )
            return json.loads(text)
        except (ResourceExhausted, ServiceUnavailable, DeadlineExceeded) as e:
            # Backoff with jitter
            sleep_s = delay + random.uniform(0, 1.0)
            time.sleep(sleep_s)
            delay = min(delay * 2, 16.0)
            if attempt == max_retries:
                return {"error": f"{e.__class__.__name__}: {e}"}
        except Exception as e:
            # JSON parse or other errors
            if attempt == max_retries:
                return {"error": f"JSON/Other error: {e}"}
            time.sleep(1.0 + random.uniform(0, 0.5))
    return {"error": "Unknown error after retries"}

def gemini_route_and_relation_batch(user_texts: List[str], topk: int = 1, min_conf_allow: float = 0.0) -> Dict[str, Any]:
    canon_list = [{"id": c["id"], "text": c["text"]} for c in canonical_items]
    prompt = {
        "task": "route_and_relation_batch",
        "instructions": {
            "choose_one": True,
            "return_topk": int(topk),
            "no_guess_below_conf": float(min_conf_allow)
        },
        "user_texts": user_texts,
        "canonical_items": canon_list,
        "schema_hint": {
            "results": [{
                "target_id": "Atr##",
                "relation": "entails|contradicts|neutral",
                "confidence": "float 0..1",
                "alternates": [{"id": "Atr##", "confidence": "float 0..1"}]
            }]
        }
    }
    out = _generate_json(prompt)
    if not isinstance(out, dict):
        return {"error": "Non-dict response from model"}
    if "error" in out:
        return out
    if "results" not in out or not isinstance(out["results"], list):
        return {"error": "Missing 'results' list in model output", "raw": out}
    return out

# Optional: single-item helper using the batch path
def gemini_route_and_relation(user_text: str, topk: int = 1, min_conf_allow: float = 0.0) -> Dict[str, Any]:
    out = gemini_route_and_relation_batch([user_text], topk=topk, min_conf_allow=min_conf_allow)
    if "error" in out:
        return out
    results = out.get("results", [])
    return results[0] if results else {"error": "Empty results"}
