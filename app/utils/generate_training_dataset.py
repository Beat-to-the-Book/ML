import csv
import os

CSV_PATH = "app/data/training_data.csv"
FIELDNAMES = [
    "user_id", "book_id", "stay_time", "scroll_depth", "timestamp",
    "purchased", "rented", "label", "title", "author", "genre", "price"
]

# 디렉토리 자동 생성
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

# 초기 파일 없으면 헤더 생성
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

def append_training_row(user_id, behavior, read_books):
    """
    behavior: {"bookId", "stayTime", "scrollDepth", "timestamp"}
    read_books: [{bookId, title, author, genre, price, purchased, rented}]
    """
    book_id = behavior["bookId"]
    matching_book = next((book for book in read_books if str(book["bookId"]) == str(book_id)), None)

    if not matching_book:
        return  # 도서 메타데이터 없음

    purchased = matching_book.get("purchased", False)
    rented = matching_book.get("rented", False)
    label = 1 if purchased or rented else 0

    row = {
        "user_id": user_id,
        "book_id": book_id,
        "stay_time": behavior.get("stayTime", 0),
        "scroll_depth": behavior.get("scrollDepth", 0),
        "timestamp": behavior.get("timestamp"),
        "purchased": int(purchased),
        "rented": int(rented),
        "label": label,
        "title": matching_book.get("title", ""),
        "author": matching_book.get("author", ""),
        "genre": matching_book.get("genre", ""),
        "price": matching_book.get("price", 0)
    }

    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)

# 직접 실행
if __name__ == "__main__":
    append_training_row()