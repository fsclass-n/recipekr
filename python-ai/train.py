"""
train.py - 레시피 추천 AI 모델 학습 스크립트
-------------------------------------------------
[MLOps 역할]
  - 레시피 데이터(data/recipes.csv)를 읽어 TF-IDF 벡터라이저와 TF-IDF 행렬을 생성합니다.
  - [수정] 코사인 유사도 행렬(NxN)이 아닌 TF-IDF 행렬(NxF)을 저장합니다.
  - predict.py에서 쿼리 벡터(1xF)와 실시간으로 유사도를 계산합니다.
  - 학습된 모델 파일(.pkl)을 models/ 폴더에 저장합니다.
  - GitHub Actions 크론잡을 통해 주기적으로 자동 실행됩니다.

[실행 방법]
  python train.py
"""

import os
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

# ----------------------------------------------------------------
# 경로 설정
# ----------------------------------------------------------------
BASE_DIR  = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "recipes.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

VECTORIZER_PATH = MODEL_DIR / "vectorizer.pkl"
TFIDF_MATRIX_PATH = MODEL_DIR / "tfidf_matrix.pkl"  # [수정] cosine_matrix → tfidf_matrix
RECIPE_IDS_PATH = MODEL_DIR / "recipe_ids.pkl"

def load_data() -> pd.DataFrame:
    """레시피 CSV 데이터를 읽어 반환합니다."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"레시피 데이터 파일이 없습니다: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH, encoding="utf-8")
    # 필수 컬럼 확인
    required = {"id", "title", "ingredients", "health_type"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV에 필수 컬럼이 없습니다. 필요: {required}")
    return df

def build_feature(row: pd.Series) -> str:
    """
    TF-IDF 입력 문자열 생성.
    재료와 건강유형을 조합하여 하나의 텍스트로 만듭니다.
    health_type에 가중치를 주기 위해 3회 반복합니다.
    """
    ingredients  = str(row["ingredients"]).strip()
    health_type  = str(row["health_type"]).strip() if pd.notna(row["health_type"]) else ""
    # 건강유형 가중치 부여 (동일 단어를 반복하면 TF-IDF 점수가 높아짐)
    return f"{ingredients} {health_type} {health_type} {health_type}"

def train():
    print("[train.py] 🍳 학습 시작...")
    df = load_data()
    print(f"[train.py] 레시피 데이터 로드 완료: {len(df)}개")

    # 1) 피처 컬럼 생성
    df["feature"] = df.apply(build_feature, axis=1)

    # 2) TF-IDF 벡터라이저 학습
    vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(df["feature"])
    print(f"[train.py] TF-IDF 행렬 생성 완료: shape={tfidf_matrix.shape}")

    # 3) [수정] 코사인 유사도 행렬 대신 TF-IDF 행렬 자체를 저장
    #    이유: predict.py에서 쿼리벡터(1xF)와 비교하려면 TF-IDF 행렬(NxF)이 필요
    #         코사인 유사도 행렬(NxN)은 차원이 맞지 않아 에러 발생
    print(f"[train.py] TF-IDF 행렬 저장 준비 완료: shape={tfidf_matrix.shape}")

    # 4) 모델 저장 (.pkl)
    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(TFIDF_MATRIX_PATH, "wb") as f:
        pickle.dump(tfidf_matrix, f)
    with open(RECIPE_IDS_PATH, "wb") as f:
        pickle.dump(df[["id", "title", "ingredients", "calories",
                         "health_type", "recipe_text"]].to_dict(orient="records"), f)

    print(f"[train.py] ✅ 모델 저장 완료: {MODEL_DIR}")

if __name__ == "__main__":
    train()
