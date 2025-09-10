# run_demo.py
import json
import argparse
import pandas as pd
from rich.console import Console
from rich.table import Table
from inference import load_xgb_model, predict_from_free_text_LLM

console = Console()

# DEFAULT_QAS = [
#     {"text": "After a sincere apology, we usually regain our footing.", "value": 1},     # apology works (aligned)
#     {"text": "Apologies rarely change the trajectory of a disagreement.", "value": 3},  # opposite of apology-helps
#     {"text": "Finding couple-only time at home is uncommon for us.", "value": 3},       # time scarcity
#     {"text": "Traveling together tends to be a bright spot for us.", "value": 1},       # enjoy travel
#     {"text": "We’re largely on the same page about what marriage should be.", "value": 1},  # marriage ideas
#     {"text": "In heated exchanges, I sometimes take cheap shots.", "value": 3},         # insulting/negative language
#     {"text": "I’m aware of the main things weighing on her lately.", "value": 1},       # knows concerns/stress
#     {"text": "Disagreements often build rather than stay level.", "value": 3},          # not calm / escalation
#     {"text": "In conflict, I sometimes focus on her shortcomings.", "value": 3},        # blame/remind inadequacies
#     {"text": "Our views on independence and boundaries mostly align.", "value": 1},     # personal freedom values
#     {"text": "The way issues get raised often rubs me the wrong way.", "value": 3},     # hate approach
#     {"text": "Arguments can ignite before either of us notices.", "value": 4},          # fights sudden
#     {"text": "Our long-term plans mostly pull in the same direction.", "value": 1},     # common goals
#     {"text": "Stepping away for a bit is sometimes the only way I cool down.", "value": 2},  # leave home / withdrawal
#     {"text": "I may shut down to avoid losing my temper.", "value": 2},                 # go silent to control anger
#     {"text": "At home we can feel like we’re living side by side, not together.", "value": 3}, # strangers at home
#     {"text": "I can usually name the things she really enjoys.", "value": 1},           # know likes
#     {"text": "Time off together is generally enjoyable for both of us.", "value": 1},   # enjoy holidays
#     {"text": "Phrases like 'you always' or 'you never' creep into our fights.", "value": 3},  # always/never
#     {"text": "We define what happiness means in similar terms.", "value": 1},           # same happiness views
# ]


# DEFAULT_QAS = [
#     {"text": "A small repair phrase tends to steady the ship for us.", "value": 1},  # apology works (aligned)
#     {"text": "Our apologies often feel cosmetic rather than course-correcting.", "value": 3},  # opposite of apology-helps
#     {"text": "Carving out couple-only pockets at home is a rarity.", "value": 3},  # time scarcity
#     {"text": "Trips together are usually a bright patch for us.", "value": 1},  # enjoy travel
#     {"text": "Our picture of marriage mostly overlaps.", "value": 1},  # marriage ideas
#     {"text": "In the heat of it, I sometimes slip into jabs.", "value": 3},  # insulting/negative language
#     {"text": "I keep up with what's been weighing on her lately.", "value": 1},  # knows concerns/stress
#     {"text": "Tensions tend to climb instead of settling.", "value": 3},  # not calm / escalation
#     {"text": "In conflict, I catch myself zeroing in on her flaws.", "value": 3},  # blame/remind inadequacies
#     {"text": "We read personal freedom and boundaries in similar ways.", "value": 1},  # personal freedom values
#     {"text": "The way topics get raised often grates on me.", "value": 3},  # hate approach
#     {"text": "Arguments can spark out of the blue.", "value": 4},  # fights sudden
#     {"text": "Our long-term tracks largely run in parallel.", "value": 1},  # common goals
#     {"text": "Stepping away for a spell is sometimes how I cool down.", "value": 2},  # leave home / withdrawal
#     {"text": "I go quiet to keep a lid on my temper.", "value": 2},  # go silent to control anger
#     {"text": "Home can feel side-by-side rather than together.", "value": 3},  # strangers at home
#     {"text": "I could name the little things that light her up.", "value": 1},  # know likes
#     {"text": "Time off together is generally easy between us.", "value": 1},  # enjoy holidays
#     {"text": "Those 'always/never' lines still slip into our quarrels.", "value": 3},  # always/never
#     {"text": "We mean similar things when we say 'happy'.", "value": 1},  # same happiness views
# ]



DEFAULT_QAS = [
    {"text": "A small repair phrase tends to steady the ship for us.", "value": 0},  # apology works (aligned)
    {"text": "Our apologies often feel cosmetic rather than course-correcting.", "value": 1},  # opposite of apology-helps
    {"text": "Carving out couple-only pockets at home is a rarity.", "value": 1},  # time scarcity
    {"text": "Trips together are usually a bright patch for us.", "value": 1},  # enjoy travel
    {"text": "Our picture of marriage mostly overlaps.", "value": 1},  # marriage ideas
    {"text": "In the heat of it, I sometimes slip into jabs.", "value": 2},  # insulting/negative language
    {"text": "I keep up with what's been weighing on her lately.", "value": 1},  # knows concerns/stress
    {"text": "Tensions tend to climb instead of settling.", "value": 1},  # not calm / escalation
    {"text": "In conflict, I catch myself zeroing in on her flaws.", "value": 0},  # blame/remind inadequacies
    {"text": "We read personal freedom and boundaries in similar ways.", "value": 1},  # personal freedom values
    {"text": "The way topics get raised often grates on me.", "value": 0},  # hate approach
    {"text": "Arguments can spark out of the blue.", "value": 1},  # fights sudden
    {"text": "Our long-term tracks largely run in parallel.", "value": 1},  # common goals
    {"text": "Stepping away for a spell is sometimes how I cool down.", "value": 2},  # leave home / withdrawal
    {"text": "I go quiet to keep a lid on my temper.", "value": 2},  # go silent to control anger
    {"text": "Home can feel side-by-side rather than together.", "value": 0},  # strangers at home
    {"text": "I could name the little things that light her up.", "value": 1},  # know likes
    {"text": "Time off together is generally easy between us.", "value": 1},  # enjoy holidays
    {"text": "Those 'always/never' lines still slip into our quarrels.", "value": 1},  # always/never
    {"text": "We mean similar things when we say 'happy'.", "value": 1},  # same happiness views
]

def pretty_print_audit(audit_df: pd.DataFrame):
    table = Table(show_lines=True)
    cols = [
        "feature", "feature_text", "user_text", "raw_value",
        "normalized_value", "relation", "relation_conf", "flip", "status"
    ]
    for c in cols:
        table.add_column(c)

    for _, row in audit_df[cols].fillna("").iterrows():
        table.add_row(*(str(row[c]) for c in cols))
    console.print(table)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str,
                        help="Path to a JSON file with a list of {text, value} items. Defaults to built-in 20 items.")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Decision threshold for Class=1 (divorce). Default 0.5")
    args = parser.parse_args()

    qas = DEFAULT_QAS
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            qas = json.load(f)

    model = load_xgb_model()
    proba, pred, filled_vec, audit = predict_from_free_text_LLM(
        qas, model, nli_thr=0.65, dedup="best", decision_thr=args.threshold
    )

    console.rule("[bold]Prediction")
    console.print(f"[bold yellow]p(Divorce) = {proba:.2f} -> Class = {pred}[/bold yellow]")

    console.rule("[bold]Audit log (first 20)")
    pretty_print_audit(audit.head(20))

    console.rule("[bold]Filled feature vector (non-NaN)")
    nonnull = pd.DataFrame({"Feature": filled_vec.index, "Value": filled_vec.values}).dropna()
    console.print(nonnull.to_string(index=False))

if __name__ == "__main__":
    main()
