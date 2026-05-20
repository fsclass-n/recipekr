"""
predict.py - Spring Boot에서 호출하는 AI 추천 스크립트
---------------------------------------------------------
[사용 방법]
  Spring Boot의 ProcessBuilder가 아래와 같이 실행합니다:
    python predict.py --ingredients "계란,양파,감자" --health_type "다이어트" --top_n 3

[출력]
  JSON 배열 형태로 표준 출력(stdout)으로 반환합니다.
  Spring Boot는 이 JSON을 파싱하여 화면에 렌더링합니다.

[에러 처리]
  오류 발생 시 {"error": "메시지"} 형태의 JSON을 출력합니다.
"""

import sys
import json
import pickle
import argparse
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ----------------------------------------------------------------
# 경로 설정
# ----------------------------------------------------------------
BASE_DIR        = Path(__file__).resolve().parent
MODEL_DIR       = BASE_DIR / "models"
VECTORIZER_PATH   = MODEL_DIR / "vectorizer.pkl"
TFIDF_MATRIX_PATH = MODEL_DIR / "tfidf_matrix.pkl"   # [수정] cosine_matrix → tfidf_matrix
RECIPE_IDS_PATH   = MODEL_DIR / "recipe_ids.pkl"

# ----------------------------------------------------------------
# 건강 유형 한글 → 내부 키 매핑
# ----------------------------------------------------------------
HEALTH_TYPE_MAP = {
    "다이어트":  "diet",
    "당뇨":      "diabetes",
    "저염식":    "low_sodium",
    "일반":      "normal",
    "diet":      "diet",
    "diabetes":  "diabetes",
    "low_sodium":"low_sodium",
    "normal":    "normal",
}

def load_models():
    """학습된 모델 파일(.pkl)을 로드합니다."""
    if not VECTORIZER_PATH.exists():
        raise FileNotFoundError(
            "모델 파일이 없습니다. python train.py를 먼저 실행해 주세요."
        )
    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer: TfidfVectorizer = pickle.load(f)
    with open(TFIDF_MATRIX_PATH, "rb") as f:   # [수정] tfidf_matrix 로드
        tfidf_matrix: np.ndarray = pickle.load(f)
    with open(RECIPE_IDS_PATH, "rb") as f:
        recipes: list = pickle.load(f)
    return vectorizer, tfidf_matrix, recipes

def recommend(ingredients: str, health_type: str, top_n: int) -> list:
    """
    사용자 입력(재료 + 건강유형)을 기반으로 추천 레시피를 반환합니다.

    Args:
        ingredients: 쉼표로 구분된 재료 문자열 (예: "계란,양파,감자")
        health_type: 건강 유형 (예: "다이어트", "당롼")
        top_n: 반환할 추천 결과 개수

    Returns:
        추천 레시피 딕셔너리 리스트
    """
    vectorizer, tfidf_matrix, recipes = load_models()  # [수정]

    # 1) 건강유형 정규화 + 가중치 반영
    mapped_type = HEALTH_TYPE_MAP.get(health_type.strip(), "normal")
    query_text  = f"{ingredients} {mapped_type} {mapped_type} {mapped_type}"

    # 2) 사용자 입력을 TF-IDF 벡터로 변환
    query_vec = vectorizer.transform([query_text])

    # 3) [수정] query_vec(1xF) vs tfidf_matrix(NxF) 코사인 유사도 계산
    #    차원이 일치하므로 에러 없음
    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    # 4) 건강 유형 필터: mapped_type 이 일치하거나 "normal"인 레시피만 우선 대상
    filtered_indices = [
        i for i, r in enumerate(recipes)
        if HEALTH_TYPE_MAP.get(str(r.get("health_type", "normal")).strip(), "normal")
        in (mapped_type, "normal")
    ]

    if not filtered_indices:
        # 필터 결과가 없으면 전체 대상으로 재시도
        filtered_indices = list(range(len(recipes)))

    # 5) 유사도 기준 내림차순 정렬 후 상위 top_n 선택
    filtered_scores   = [(i, sim_scores[i]) for i in filtered_indices]
    sorted_scores     = sorted(filtered_scores, key=lambda x: x[1], reverse=True)
    top_indices       = [idx for idx, _ in sorted_scores[:top_n]]

    # 6) 결과 조립
    result = []
    for rank, idx in enumerate(top_indices, start=1):
        r = recipes[idx]
        result.append({
            "rank":        rank,
            "id":          r.get("id"),
            "title":       r.get("title"),
            "ingredients": r.get("ingredients"),
            "calories":    r.get("calories"),
            "health_type": r.get("health_type"),
            "recipe_text": r.get("recipe_text"),
            "score":       round(float(sim_scores[idx]), 4),
        })
    return result

def main():
    parser = argparse.ArgumentParser(description="레시피 AI 추천 엔진")
    parser.add_argument("--ingredients",  type=str, required=True,
                        help="쉼표로 구분된 재료 (예: 계란,양파,감자)")
    parser.add_argument("--health_type",  type=str, default="일반",
                        help="건강 유형 (다이어트|당뇨|저염식|일반)")
    parser.add_argument("--top_n",        type=int, default=3,
                        help="추천 결과 개수 (기본값: 3)")
    args = parser.parse_args()

    results = recommend(
        ingredients=args.ingredients,
        health_type=args.health_type,
        top_n=args.top_n,
    )
    # ✅ Spring Boot가 읽을 수 있도록 JSON 형태로 stdout 출력
    print(json.dumps(results, ensure_ascii=False))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # ❌ 에러 발생 시에도 JSON 형태로 출력 (Spring Boot 파싱 에러 방지)
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)
