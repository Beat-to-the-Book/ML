import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import joblib
import logging

logger = logging.getLogger(__name__)

class ModelBasedRecommender:
    def __init__(self, book_repository, model_path=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))  # /app/app/services
        model_path = os.path.abspath(os.path.join(base_dir, '..', '..', 'data', 'xgb_model.pkl'))
        self.book_repository = book_repository

        # 추천 모델 로드
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            logger.info(f"[ModelBasedRecommender] 모델 {model_path} 로드 완료")
        else:
            self.model = None
            logger.warning(f"[ModelBasedRecommender] 모델 파일 {model_path} 이 존재하지 않아, 추천 기능이 비활성화됩니다.")

        # SentenceTransformer 임베딩 모델 로드
        try:
            self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("[ModelBasedRecommender] 임베딩 모델 로드 완료")
        except Exception as e:
            self.embedding_model = None
            logger.error(f"[ModelBasedRecommender] 임베딩 모델 로드 실패: {e}")

    def get_model_based_recommendations(self, read_books, user_behavior):
        if self.model is None:
            logger.error("[ModelBasedRecommender] 모델이 로드되지 않았습니다. 추천을 수행할 수 없습니다.")
            return []

        if self.book_repository is None:
            logger.warning("[ModelBasedRecommender] book_repository 없음")
            return []

        # Redis 캐시된 book_pool 사용
        book_pool = self.book_repository.get_book_pool()
        if not book_pool:
            logger.warning("[ModelBasedRecommender] 도서 풀이 비어 있음")
            return []
        pool_df = pd.DataFrame(book_pool)

        # 읽은 책 제외
        read_ids = {book.get("bookId") for book in read_books}
        pool_df = pool_df[~pool_df["id"].isin(read_ids)]
        logger.info(f"[ModelBasedRecommender] 읽은 책 제외 후 {len(pool_df)}권 남음")

        if pool_df.empty:
            logger.warning("[ModelBasedRecommender] 추천할 책이 없음")
            return []

        # 임베딩/특징 계산은 매 요청 시 수행 (임베딩 캐시 없음)
        pool_df["text"] = (
                pool_df.get("title", "").fillna("") + " " +
                pool_df.get("author", "").fillna("") + " " +
                pool_df.get("genre", "").fillna("")
        ).str.strip()

        # pool_df에 대해 점수 예측
        pool_embeddings = self.embedding_model.encode(pool_df["text"].tolist())
        embed_df = pd.DataFrame(pool_embeddings, columns=[f"emb_{i}" for i in range(pool_embeddings.shape[1])])
        pool_df = pd.concat([pool_df.reset_index(drop=True), embed_df], axis=1)

        stay_time = np.mean([b.get("stayTime", 0) for b in user_behavior])
        scroll_depth = np.mean([b.get("scrollDepth", 0) for b in user_behavior])
        pool_df["stay_time"] = stay_time
        pool_df["scroll_depth"] = scroll_depth

        feature_cols = ["stay_time", "scroll_depth"] + [f"emb_{i}" for i in range(pool_embeddings.shape[1])]
        X_input = pool_df[feature_cols]
        scores = self.model.predict_proba(X_input)[:, 1]
        pool_df["score"] = scores

        top_books = pool_df.sort_values("score", ascending=False).head(5)

        results = [{
            "bookId": row["id"],
            "title": row["title"],
            "author": row["author"],
            "coverImageUrl": row["frontCoverImageUrl"],
            "score": round(row["score"], 4)
        } for _, row in top_books.iterrows()]

        logger.info(f"[ModelBasedRecommender] 최종 추천 결과: {results}")
        return results
