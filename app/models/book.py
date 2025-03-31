from app import db

class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    bookDescription = db.Column(db.String(2000))
    price = db.Column(db.Float, nullable=False)
    publisher = db.Column(db.String(100))
    publishDate = db.Column(db.String(255))
    coverImageUrl = db.Column(db.String(500))

    def __init__(self, title, author, genre, bookDescription, price, publisher, publishDate, coverImageUrl):
        self.title = title
        self.author = author
        self.genre = genre
        self.bookDescription = bookDescription
        self.price = price
        self.publisher = publisher
        self.publishDate = publishDate
        self.coverImageUrl = coverImageUrl

    def to_dict(self):
        """ JSON 직렬화용 딕셔너리 변환 함수 """
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "genre": self.genre,
            "bookDescription": self.bookDescription,
            "price": self.price,
            "publisher": self.publisher,
            "publishDate": self.publishDate,
            "coverImageUrl": self.coverImageUrl,
        }
