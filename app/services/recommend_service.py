from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def get_similar_books_from_multiple(book_list, book_pool_cache):
    if not book_list or book_pool_cache is None:
        logger.warning("book_list 또는 book_pool_cache 없음")
        return []

    book_pool = book_pool_cache.get_book_pool()
    logger.info(f"책 Pool 로드 완료 - 총 책 수: {len(book_pool)}")

    if not book_pool:
        logger.warning("책 Pool 비어 있음")
        return []

    if not book_list:
        logger.warning("입력 도서 목록 비어 있음")
        return []

    try:
        # 책 리스트를 데이터프레임으로 변환
        pool_df = pd.DataFrame(book_pool)

        if pool_df.empty or 'author' not in pool_df or 'genre' not in pool_df:
            logger.warning(f"pool_df 이상 - 컬럼들: {pool_df.columns}")
            return []

        # TF-IDF 벡터화 기준 텍스트 구성
        pool_texts = pool_df['author'] + " " + pool_df['genre']
        input_texts = [f"{book['author']} {book['genre']}" for book in book_list]

        logger.debug(f"TF-IDF input_texts: {input_texts}")
        logger.debug(f"TF-IDF pool_texts 예시: {pool_texts[:5].tolist()}")

        # 벡터화
        vectorizer = TfidfVectorizer()
        pool_vectors = vectorizer.fit_transform(pool_texts)
        input_vectors = vectorizer.transform(input_texts)

        # 입력 벡터 평균
        mean_vector = input_vectors.mean(axis=0)

        # 코사인 유사도 계산
        similarities = cosine_similarity(mean_vector, pool_vectors).flatten()
        top_indices = similarities.argsort()[-5:][::-1]

        top_books = pool_df.iloc[top_indices].to_dict(orient='records')
        logger.info(f"유사도 top 5 책: {[book['title'] for book in top_books]}")

        return top_books
    except Exception as e:
        logger.error(f"[추천 계산 오류] {e}", exc_info=True)
        return []
