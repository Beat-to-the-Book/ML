import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

# NLP - 추천 연산 소요 시간: 1.89s
# SentenceTransformer(BERT) 기반으로 콘텐츠와 행동 정보를 벡터화해서 추천하는 의미 기반(semantic) 하이브리드 추천 시스템
class SemanticHybridRecommender:
    def __init__(self, book_repository, alpha=0.5):
        self.book_repository = book_repository
        self.alpha = alpha
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    def get_semantic_hybrid_recommendations(self, read_books, user_behavior):
        if self.book_repository is None:
            logger.warning("[SemanticHybridRecommender] book_repository 없음")
            return []

        book_pool = self.book_repository.get_book_pool()
        if not book_pool:
            logger.warning("[SemanticHybridRecommender] 도서 풀이 비어 있음")
            return []

        pool_df = pd.DataFrame(book_pool)
        pool_df['text'] = pool_df['author'].fillna('') + " " + pool_df['genre'].fillna('')

        read_ids = {entry.get("bookId") for entry in (read_books or [])}
        pool_df = pool_df[~pool_df["id"].isin(read_ids)]
        logger.info(f"[SemanticHybridRecommender] 읽은 책 제외 후 {len(pool_df)}권 남음")

        if pool_df.empty:
            logger.warning("[SemanticHybridRecommender] 추천할 책이 없음")
            return []

        # 도서 풀 임베딩
        pool_texts = pool_df["text"].tolist()
        pool_embeddings = self.embedding_model.encode(pool_texts, convert_to_tensor=True)

        # 콘텐츠 기반 유사도
        content_similarities = np.zeros(len(pool_df))
        if read_books:
            read_texts = [
                f"{book.get('author', '')} {book.get('genre', '')}" for book in read_books
            ]
            read_embeddings = self.embedding_model.encode(read_texts, convert_to_tensor=True)
            content_mean_embedding = read_embeddings.mean(dim=0, keepdim=True)
            content_similarities = cosine_similarity(
                content_mean_embedding.cpu().numpy(), pool_embeddings.cpu().numpy()
            ).flatten()
            logger.info(f"[SemanticHybridRecommender] 콘텐츠 유사도 계산 완료")

        # 행동 기반 유사도
        behavior_similarities = np.zeros(len(pool_df))
        if user_behavior:
            read_books_dict = {b["bookId"]: b for b in read_books or []}
            input_texts, weights = [], []

            for entry in user_behavior:
                book_id = entry.get("bookId")
                book = read_books_dict.get(book_id, {"author": "", "genre": ""})
                text = f"{book.get('author', '')} {book.get('genre', '')}"
                input_texts.append(text)
                weights.append(entry.get("clickCount", 0) + entry.get("stayTime", 0) / 30)

            if input_texts:
                behavior_embeddings = self.embedding_model.encode(input_texts, convert_to_tensor=True)
                weights = np.array(weights)
                weights = weights / weights.sum()
                weighted_vector = np.average(behavior_embeddings.cpu().numpy(), axis=0, weights=weights)
                behavior_similarities = cosine_similarity([weighted_vector], pool_embeddings.cpu().numpy()).flatten()
                logger.info(f"[SemanticHybridRecommender] 행동 유사도 계산 완료")

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

        logger.info(f"[SemanticHybridRecommender] 최종 추천 결과: {results}")
        return results
