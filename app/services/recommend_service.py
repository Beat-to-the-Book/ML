import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

def get_combined_recommendations(read_books, user_behavior, book_pool_cache, alpha=0.5):
    if not read_books or book_pool_cache is None:
        logger.warning("입력 데이터 없음 (read_books 또는 book_pool_cache)")
        return []

    book_pool = book_pool_cache.get_book_pool()
    if not book_pool:
        logger.warning("DB에 도서가 없음")
        return []

    logger.info(f"가져온 book_pool 개수: {len(book_pool)}")

    pool_df = pd.DataFrame(book_pool)
    pool_df['text'] = pool_df['author'].fillna('') + " " + pool_df['genre'].fillna('')

    # 읽은 책 제외
    read_ids = {entry.get("bookId") for entry in read_books}
    logger.info(f"제외할 책 id 목록 (읽은 책 id 전부): {read_ids}")

    pool_df = pool_df[~pool_df["id"].isin(read_ids)]
    logger.info(f"읽은 책 제외 후 남은 pool_df 크기: {len(pool_df)}")

    if pool_df.empty:
        logger.warning("읽은 책 제외하고 남은 책이 없음")
        return []

    # TF-IDF 벡터화
    vectorizer = TfidfVectorizer()
    pool_vectors = vectorizer.fit_transform(pool_df['text'])

    # 콘텐츠 기반 유사도
    content_texts = [
        f"{book.get('author', '')} {book.get('genre', '')}" for book in read_books
    ]
    if not content_texts:
        logger.warning("content_texts 비어 있음")
        return []

    content_vectors = vectorizer.transform(content_texts)
    content_mean_vector = np.asarray(content_vectors.mean(axis=0)).reshape(1, -1)
    content_similarities = cosine_similarity(content_mean_vector, pool_vectors).flatten()

    logger.info(f"content_similarities 통계 - min: {content_similarities.min()}, max: {content_similarities.max()}, mean: {content_similarities.mean()}")

    # 행동 기반 유사도
    input_texts = []
    weights = []

    # read_books를 bookId로 빠르게 조회할 수 있도록 변환
    read_books_dict = {book['bookId']: book for book in read_books}

    for entry in user_behavior:
        book_id = entry.get("bookId")
        click = entry.get("clickCount", 0)
        stay = entry.get("stayTime", 0)

        book = read_books_dict.get(book_id)
        if not book:
            logger.warning(f"행동 데이터에 있지만 읽은 책 목록에 없는 bookId={book_id}")
            continue

        text = f"{book.get('author', '')} {book.get('genre', '')}"
        input_texts.append(text)
        weights.append(click + stay / 30)

    if not input_texts:
        logger.warning("input_texts 비어 있음 (행동 기반 추천 불가)")
        behavior_similarities = np.zeros_like(content_similarities)
    else:
        behavior_vectors = vectorizer.transform(input_texts)
        weights = np.array(weights)
        weights = weights / weights.sum()
        weighted_behavior_vector = np.average(behavior_vectors.toarray(), axis=0, weights=weights)
        behavior_similarities = cosine_similarity([weighted_behavior_vector], pool_vectors).flatten()

    logger.info(f"behavior_similarities 통계 - min: {behavior_similarities.min()}, max: {behavior_similarities.max()}, mean: {behavior_similarities.mean()}")

    # 최종 결합
    combined_similarities = alpha * content_similarities + (1 - alpha) * behavior_similarities
    top_indices = combined_similarities.argsort()[-5:][::-1]

    logger.info(f"최종 combined_similarities 상위 5개 점수: {combined_similarities[top_indices]}")

    if len(top_indices) == 0:
        logger.warning("추천 결과 없음 - top_indices 비어 있음")
        return []

    top_books = pool_df.iloc[top_indices][['id', 'title', 'author', 'frontCoverImageUrl']]
    logger.info(f"추천된 top_books: {top_books.to_dict(orient='records')}")

    # bookId를 다시 맞춰주기
    results = []
    for _, row in top_books.iterrows():
        results.append({
            "bookId": row['id'],
            "title": row['title'],
            "author": row['author'],
            "coverImageUrl": row['frontCoverImageUrl']
        })

    return results
