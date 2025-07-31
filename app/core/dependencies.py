from redis import Redis
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from app.core.config import Config

# Redis 클라이언트
redis_client = Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    decode_responses=True
)

# SQLAlchemy 세션
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
db_session = scoped_session(sessionmaker(bind=engine))
