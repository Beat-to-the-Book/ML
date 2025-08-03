import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

# TF-IDF - 추천 연산 소요 시간: 0.02s
class HybridRecommender:
    def __init__(self, book_repository, alpha=0.5):
        self.book_repository = book_repository
        self.alpha = alpha

    def get_hybrid_recommendations(self, read_books, user_behavior):
        if self.book_repository is None:
            logger.warning("[HybridRecommender] book_repository 없음")
            return []

        book_pool = self.book_repository.get_book_pool()
        if not book_pool:
            logger.warning("[HybridRecommender] 도서 풀이 비어 있음")
            return []

        pool_df = pd.DataFrame(book_pool)
        pool_df['text'] = pool_df['author'].fillna('') + " " + pool_df['genre'].fillna('')

        read_ids = {entry.get("bookId") for entry in (read_books or [])}
        pool_df = pool_df[~pool_df["id"].isin(read_ids)]
        logger.info(f"[HybridRecommender] 읽은 책 제외 후 {len(pool_df)}권 남음")

        if pool_df.empty:
            logger.warning("[HybridRecommender] 추천할 책이 없음")
            return []

        vectorizer = TfidfVectorizer()
        pool_vectors = vectorizer.fit_transform(pool_df['text'])

        # 콘텐츠 기반 유사도
        content_similarities = np.zeros(pool_vectors.shape[0])
        if read_books:
            content_texts = [
                f"{book.get('author', '')} {book.get('genre', '')}" for book in read_books
            ]
            content_vectors = vectorizer.transform(content_texts)
            content_mean_vector = np.asarray(content_vectors.mean(axis=0)).reshape(1, -1)
            content_similarities = cosine_similarity(content_mean_vector, pool_vectors).flatten()
            logger.info(f"[HybridRecommender] 콘텐츠 유사도 계산 완료")
        else:
            logger.info("[HybridRecommender] 콘텐츠 유사도 미사용")

        # 행동 기반 유사도
        behavior_similarities = np.zeros(pool_vectors.shape[0])
        if user_behavior:
            input_texts, weights = [], []
            read_books_dict = {b["bookId"]: b for b in read_books or []}
            for entry in user_behavior:
                book_id = entry.get("bookId")
                book = read_books_dict.get(book_id, {"author": "", "genre": ""})
                text = f"{book.get('author', '')} {book.get('genre', '')}"
                input_texts.append(text)
                weights.append(entry.get("clickCount", 0) + entry.get("stayTime", 0) / 30)

            if input_texts:
                behavior_vectors = vectorizer.transform(input_texts)
                weights = np.array(weights) / np.sum(weights)
                weighted_vector = np.average(behavior_vectors.toarray(), axis=0, weights=weights)
                behavior_similarities = cosine_similarity([weighted_vector], pool_vectors).flatten()
                logger.info(f"[HybridRecommender] 행동 유사도 계산 완료")
        else:
            logger.info("[HybridRecommender] 행동 유사도 미사용")

        # 유사도 결합 또는 랜덤 추천
        if not read_books and not user_behavior:
            top_books = pool_df.sample(n=min(5, len(pool_df)))
        else:
            combined = self.alpha * content_similarities + (1 - self.alpha) * behavior_similarities
            top_indices = combined.argsort()[-5:][::-1]
            top_books = pool_df.iloc[top_indices]

        results = [{
            "bookId": row["id"],
            "title": row["title"],
            "author": row["author"],
            "coverImageUrl": row["frontCoverImageUrl"]
        } for _, row in top_books.iterrows()]

        logger.info(f"[HybridRecommender] 최종 추천 결과: {results}")
        return results
