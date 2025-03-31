from kafka import KafkaProducer
import json
from app.config import Config
import logging

logger = logging.getLogger(__name__)

# Flask -> Spring
# Kafka Producer: Flask에서 추천 도서를 다시 Spring으로 전달
producer = KafkaProducer(
    bootstrap_servers=[Config.KAFKA_SERVER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_recommendations_to_kafka(user_id, recommendations):
    message = {
        "userId": user_id,
        "books": recommendations
    }

    try:
        producer.send("recommendation_topic", message)
        logger.info(f"Kafka 전송 완료: userId={user_id}, books={len(recommendations)}권")
    except Exception as e:
        logger.error(f"Kafka 전송 실패: {e}")
