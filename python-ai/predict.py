"""
predict.py - Spring Boot에서 호출하는 AI 추천 스크립트 (Gemini RAG 기반)
---------------------------------------------------------
[사용 방법]
  export GEMINI_API_KEY="your_api_key_here"
  python predict.py --ingredients "계란,양파,감자" --health_type "다이어트" --top_n 3

[출력]
  JSON 형태로 표준 출력(stdout)으로 반환합니다.
  {
    "recommendations": [...],  # 코사인 유사도 상위 레시피 (검색 결과)
    "ai_message": "..."        # 제미나이가 작성해준 맞춤형 챗봇 응답 (창의적 레시피 등)
  }
"""

import sys
import json
import pickle
import argparse
import os
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai

# ----------------------------------------------------------------
# 경로 설정
# ----------------------------------------------------------------
BASE_DIR          = Path(__file__).resolve().parent
MODEL_DIR         = BASE_DIR / "models"
EMBEDDINGS_PATH   = MODEL_DIR / "embeddings_matrix.pkl"
RECIPE_IDS_PATH   = MODEL_DIR / "recipe_ids.pkl"

def load_models():
    """저장된 제미나이 임베딩 행렬과 레시피 데이터를 로드합니다."""
    if not EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(
            "모델 임베딩 파일이 없습니다. python train.py를 먼저 실행해 주세요."
        )
    with open(EMBEDDINGS_PATH, "rb") as f:
        embeddings_matrix: np.ndarray = pickle.load(f)
    with open(RECIPE_IDS_PATH, "rb") as f:
        recipes: list = pickle.load(f)
    return embeddings_matrix, recipes

def generate_ai_response(ingredients: str, health_type: str, top_recipes: list) -> str:
    """
    제미나이 1.5 Flash 모델을 사용하여, 사용자 맞춤형 레시피 조언을 생성합니다.
    (RAG 방식: Retrieval-Augmented Generation)
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # 컨텍스트 조립
    context_text = "참고할 레시피 목록:\n"
    for r in top_recipes:
        context_text += f"- {r['title']} (칼로리: {r['calories']})\n  요리법: {r['recipe_text']}\n"
        
    prompt = f"""
당신은 친절하고 전문적인 요리사입니다. 사용자가 다음과 같은 재료와 건강 목적을 가지고 있습니다.
- 보유 재료: {ingredients}
- 건강 목적: {health_type}

위의 '참고할 레시피 목록'을 바탕으로, 사용자가 보유한 재료를 최대한 활용하면서 건강 목적에 부합하는 요리 팁이나 새롭고 창의적인 레시피 조합을 한 문단(300자 이내)으로 친절하게 제안해 주세요.
출력 형식은 마크다운을 사용하지 말고 평문으로 작성해 주세요.

{context_text}
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI 생성 중 오류가 발생했습니다: {str(e)}"

def recommend(ingredients: str, health_type: str, top_n: int) -> dict:
    """
    제미나이 임베딩을 이용한 문맥 검색 + 생성형 챗봇 응답 반환
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 없습니다.")
        
    genai.configure(api_key=api_key)
    embeddings_matrix, recipes = load_models()

    # 1) 검색어 텍스트 구성 및 임베딩 생성 (task_type="retrieval_query" 사용)
    query_text = f"요리명: \n재료: {ingredients}\n건강 유형: {health_type}식"
    
    query_result = genai.embed_content(
        model="models/text-embedding-004",
        content=query_text,
        task_type="retrieval_query"
    )
    query_vec = np.array(query_result['embedding']).reshape(1, -1)

    # 2) 코사인 유사도 계산
    sim_scores = cosine_similarity(query_vec, embeddings_matrix).flatten()

    # 3) 유사도 기준 내림차순 정렬 후 상위 top_n 선택 (단순화: 여기서는 건강유형을 의미론적으로 이미 내포함)
    sorted_indices = np.argsort(sim_scores)[::-1]
    top_indices    = sorted_indices[:top_n]

    # 4) 검색 결과 조립
    rec_results = []
    for rank, idx in enumerate(top_indices, start=1):
        r = recipes[idx]
        rec_results.append({
            "rank":        rank,
            "id":          r.get("id"),
            "title":       r.get("title"),
            "ingredients": r.get("ingredients"),
            "calories":    r.get("calories"),
            "health_type": r.get("health_type"),
            "recipe_text": r.get("recipe_text"),
            "score":       round(float(sim_scores[idx]), 4),
        })

    # 5) 생성형 AI를 이용해 검색 결과를 기반으로 새로운 맞춤형 조언 생성
    ai_message = generate_ai_response(ingredients, health_type, rec_results)

    return {
        "recommendations": rec_results,
        "ai_message": ai_message
    }

def main():
    parser = argparse.ArgumentParser(description="제미나이 RAG 레시피 추천 엔진")
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
