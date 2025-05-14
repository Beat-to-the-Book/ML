import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

def get_combined_recommendations(read_books, user_behavior, book_pool_cache, alpha=0.5):
    # 캐시 객체가 없으면 종료
    if book_pool_cache is None:
        logger.warning("book_pool_cache 없음")
        return []

    # DB에서 도서 풀 가져오기
    book_pool = book_pool_cache.get_book_pool()
    if not book_pool:
        logger.warning("DB에 도서가 없음")
        return []

    logger.info(f"가져온 book_pool 개수: {len(book_pool)}")

    # 도서 목록을 DataFrame으로 변환
    pool_df = pd.DataFrame(book_pool)
    pool_df['text'] = pool_df['author'].fillna('') + " " + pool_df['genre'].fillna('')

    # 이미 읽은 책은 제외
    read_ids = {entry.get("bookId") for entry in (read_books or [])}
    pool_df = pool_df[~pool_df["id"].isin(read_ids)]
    logger.info(f"읽은 책 제외 후 남은 pool_df 크기: {len(pool_df)}")

    if pool_df.empty:
        logger.warning("읽은 책 제외 후 남은 책이 없음")
        return []

    # 전체 도서에 대해 TF-IDF 벡터 생성
    vectorizer = TfidfVectorizer()
    pool_vectors = vectorizer.fit_transform(pool_df['text'])

    # 콘텐츠 기반 유사도 계산
    content_similarities = np.zeros(pool_vectors.shape[0])
    if read_books:
        content_texts = [
            f"{book.get('author', '')} {book.get('genre', '')}" for book in read_books
        ]
        content_vectors = vectorizer.transform(content_texts)
        content_mean_vector = np.asarray(content_vectors.mean(axis=0)).reshape(1, -1)
        content_similarities = cosine_similarity(content_mean_vector, pool_vectors).flatten()
        logger.info(f"content_similarities 통계 - min: {content_similarities.min()}, max: {content_similarities.max()}, mean: {content_similarities.mean()}")
    else:
        logger.info("read_books 비어 있음 - 콘텐츠 기반 유사도 미사용")

    # 행동 기반 유사도 계산
    behavior_similarities = np.zeros(pool_vectors.shape[0])
    if user_behavior:
        input_texts = []
        weights = []

        # 행동 데이터에 있는 bookId에 대한 정보 가져오기
        read_books_dict = {book['bookId']: book for book in read_books or []}

        for entry in user_behavior:
            book_id = entry.get("bookId")
            click = entry.get("clickCount", 0)
            stay = entry.get("stayTime", 0)

            # 행동 데이터 기반 텍스트 생성 (없으면 공백)
            book = read_books_dict.get(book_id, {"author": "", "genre": ""})
            text = f"{book.get('author', '')} {book.get('genre', '')}"
            input_texts.append(text)
            weights.append(click + stay / 30)

        # 행동 기반 유사도 벡터 계산
        if input_texts:
            behavior_vectors = vectorizer.transform(input_texts)
            weights = np.array(weights)
            weights = weights / weights.sum()
            weighted_behavior_vector = np.average(behavior_vectors.toarray(), axis=0, weights=weights)
            behavior_similarities = cosine_similarity([weighted_behavior_vector], pool_vectors).flatten()
            logger.info(f"behavior_similarities 통계 - min: {behavior_similarities.min()}, max: {behavior_similarities.max()}, mean: {behavior_similarities.mean()}")
        else:
            logger.info("user_behavior 있음. 그러나 input_texts 없음")

    # 추천 결과 추출 방식 선택
    if not read_books and not user_behavior:
        # 아무 정보도 없으면 랜덤 추천
        logger.info("read_books와 user_behavior 모두 없음 - 랜덤 추천")
        top_books = pool_df.sample(n=min(5, len(pool_df)))
    else:
        # 콘텐츠/행동 기반 유사도 결합
        combined_similarities = alpha * content_similarities + (1 - alpha) * behavior_similarities
        top_indices = combined_similarities.argsort()[-5:][::-1]
        logger.info(f"최종 combined_similarities 상위 5개 점수: {combined_similarities[top_indices]}")
        top_books = pool_df.iloc[top_indices]

    # 추천 결과 포맷 구성
    results = []
    for _, row in top_books.iterrows():
        results.append({
            "bookId": row['id'],
            "title": row['title'],
            "author": row['author'],
            "coverImageUrl": row['frontCoverImageUrl']
        })

    logger.info(f"추천된 top_books: {results}")
    return results
