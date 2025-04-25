from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def normalize_book(book):
    """비교를 위한 전처리 함수"""
    return (
        str(book.get('title', '')).strip().lower(),
        str(book.get('author', '')).strip().lower(),
        str(book.get('genre', '')).strip().lower()
    )

def get_similar_books_from_multiple(book_list, book_pool_cache):
    # 입력 도서 없으면 바로 종료
    if not book_list:
        logger.warning("입력 도서 목록이 비어 있어 추천을 건너뜀")
        return []

    # 캐시 객체 없거나 pool 비어있으면 강제 로드
    if book_pool_cache is None:
        logger.warning("book_pool_cache가 None이라 강제 종료")
        return []

    book_pool = book_pool_cache.get_book_pool()
    if not book_pool:
        logger.warning("책 Pool 비어 있음. 강제 재로드 시도")
        try:
            book_pool_cache.last_updated = datetime.min  # 강제 만료
            book_pool = book_pool_cache.get_book_pool()
            logger.info(f"강제 재로딩 결과 책 수: {len(book_pool)}")
        except Exception as e:
            logger.error(f"[강제 재로딩 실패] {e}", exc_info=True)
            return []

    try:
        # 사용자가 읽은 책 전처리 후 Set 구성
        read_set = {
            normalize_book(book) for book in book_list
        }

        # 읽지 않은 책만 필터링
        filtered_books = [
            book for book in book_pool
            if normalize_book(book) not in read_set
        ]

        if not filtered_books:
            logger.warning("필터링 후 남은 추천 후보가 없음")
            return []

        # 추천 대상 책 DataFrame 구성
        pool_df = pd.DataFrame(filtered_books)
        if pool_df.empty or 'author' not in pool_df or 'genre' not in pool_df:
            logger.warning(f"pool_df 이상 - 컬럼들: {pool_df.columns}")
            return []

        # TF-IDF용 텍스트 구성
        pool_texts = pool_df['author'] + " " + pool_df['genre']
        input_texts = [
            f"{book.get('author', '')} {book.get('genre', '')}" for book in book_list
        ]

        logger.debug(f"TF-IDF input_texts: {input_texts}")

        # TF-IDF 벡터화
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
