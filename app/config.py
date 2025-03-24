class Config:
    SPRING_BOOT_API = "http://beat_to_the_book_spring_boot:8080/api"
    KAFKA_SERVER = "beat_to_the_book_kafka:9092"
    REDIS_HOST = "redis"
    REDIS_PORT = 6379
    CACHE_EXPIRE = 600  # 10분

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://user:password@beat_to_the_book_mysql:3306/beat_to_the_book"
    SQLALCHEMY_TRACK_MODIFICATIONS = False # 객체 추적 X (성능 최적화)