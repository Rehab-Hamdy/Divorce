# model_train.py
import os, pandas as pd, numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from canonical import FEATURES
from config import DATA_PATH, MODEL_PATH, SEED

def main():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    X = df[FEATURES].astype(int).copy()
    y = df["Class"].astype(int).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )

    model = XGBClassifier(
        n_estimators=500,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        reg_alpha=0.0,
        random_state=SEED,
        n_jobs=-1,
        tree_method="hist",
        enable_categorical=False
    )

    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    print(f"Test accuracy: {acc:.3f}")

    # Save in native XGBoost json format
    model.save_model(MODEL_PATH)
    print(f"Saved model → {MODEL_PATH}")

if __name__ == "__main__":
    main()
