from kafka import KafkaConsumer
import json
from app.services.recommend_service import get_similar_books
from app.services.recommend_cache_service import cache_recommendations
from app.config import Config
from app.logger_config import setup_logger

consumer = KafkaConsumer(
    'recommendation_topic',
    bootstrap_servers=[Config.KAFKA_SERVER],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for message in consumer:
    data = message.value
    user_id = data['userId']
    title, author, genre = data['title'], data['author'], data['genre']

    recommended_books = get_similar_books(title, author, genre)
    cache_recommendations(user_id, recommended_books)
