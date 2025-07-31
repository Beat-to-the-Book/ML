from app.core.extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password  # 보통 해싱된 비밀번호 저장

    def to_dict(self):
        """ JSON 직렬화용 딕셔너리 변환 함수 """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }
