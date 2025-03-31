import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


# 도서 데이터 로드
books_data = pd.read_csv("data/books.csv") # title, author, genre 컬럼이 포함된 CSV 파일

# TF-IDF 벡터화
vectorizer = TfidfVectorizer()
book_features = vectorizer.fit_transform(books_data['author'] + " " + books_data['genre'])

def get_similar_books(title, author, genre):
    # 입력 도서의 특징 벡터 생성
    input_text = f"{author} {genre}"
    input_vector = vectorizer.transform([input_text])

    # 코사인 유사도 계산
    similarities = cosine_similarity(input_vector, book_features).flatten()
    similar_indices = similarities.argsort()[-5:][::-1]  # 가장 유사한 5개

    return books_data.iloc[similar_indices].to_dict(orient='records')
