from app.core.extensions import db

class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    publisher = db.Column(db.String(100))
    publishDate = db.Column('publish_date', db.String(255))
    leftCoverImageUrl = db.Column('left_cover_image_url', db.String(500))
    frontCoverImageUrl = db.Column('front_cover_image_url', db.String(500))
    backCoverImageUrl = db.Column('back_cover_image_url', db.String(500))

    def __init__(self, title, author, genre, price, publisher=None, publishDate=None,
                 leftCoverImageUrl=None, frontCoverImageUrl=None, backCoverImageUrl=None):
        self.title = title
        self.author = author
        self.genre = genre
        self.price = price
        self.publisher = publisher
        self.publishDate = publishDate
        self.leftCoverImageUrl = leftCoverImageUrl
        self.frontCoverImageUrl = frontCoverImageUrl
        self.backCoverImageUrl = backCoverImageUrl

    def to_dict(self):
        """ JSON 직렬화용 딕셔너리 변환 함수 """
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "genre": self.genre,
            "price": self.price,
            "publisher": self.publisher,
            "publishDate": self.publishDate,
            "leftCoverImageUrl": self.leftCoverImageUrl,
            "frontCoverImageUrl": self.frontCoverImageUrl,
            "backCoverImageUrl": self.backCoverImageUrl,
        }
