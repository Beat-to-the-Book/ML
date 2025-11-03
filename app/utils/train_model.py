import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier
import joblib
import os

def train_model_from_csv(
        csv_path=os.path.join(os.path.dirname(__file__), "../data/training_data.csv"),
        model_path=os.path.join(os.path.dirname(__file__), "../data/xgb_model.pkl")
):
    print(f"CSV 로딩 중: {csv_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV 파일이 존재하지 않습니다: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError("CSV 파일이 비어 있습니다.")

    # 필수 컬럼 확인
    required_cols = ["author", "genre", "stay_time", "scroll_depth", "label"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"필수 컬럼 누락: {col}")

    # 텍스트 생성
    df["text"] = df["author"].fillna('') + " " + df["genre"].fillna('')
    if df["text"].isnull().all():
        raise ValueError("모든 텍스트가 비어 있어 임베딩 불가능")

    print("문장 임베딩 시작")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embed_model.encode(df["text"].tolist(), show_progress_bar=True)

    # 임베딩 유효성 검사
    embeddings_array = np.array(embeddings)
    if embeddings_array.ndim != 2:
        raise ValueError(f"임베딩 결과의 차원이 이상함: {embeddings_array.shape}")

    embed_df = pd.DataFrame(embeddings_array, columns=[f"emb_{i}" for i in range(embeddings_array.shape[1])])
    df = pd.concat([df.reset_index(drop=True), embed_df], axis=1)

    # 학습 데이터 구성
    feature_cols = ["stay_time", "scroll_depth"] + list(embed_df.columns)
    X = df[feature_cols]
    y = df["label"]

    df["label"] = df["label"].astype(int)
    print("라벨 분포:\n", df["label"].value_counts())

    if X.isnull().any().any():
        raise ValueError("X 데이터에 결측치가 존재합니다.")
    if y.isnull().any():
        raise ValueError("y(label) 컬럼에 결측치가 존재합니다.")

    # 데이터 분할
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

    print("모델 학습 시작 (XGBoost)")
    model = XGBClassifier(use_label_encoder=False, eval_metric="logloss")
    model.fit(X_train, y_train)

    # 평가
    y_pred = model.predict(X_test)
    print("평가 결과:")
    print(classification_report(y_test, y_pred))

    # 모델 저장
    joblib.dump(model, model_path)
    print(f"모델 저장 완료: {model_path}")

# 직접 실행
if __name__ == "__main__":
    train_model_from_csv()