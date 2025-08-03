from kafka import KafkaProducer
import json
from app.core.config import Config
import logging

logger = logging.getLogger(__name__)

# Flask → Spring으로 보내는 Kafka Producer
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
        producer.flush() # 버퍼에 남아 있는 모든 메시지를 브로커에 즉시 전송 (동기)
        logger.info(f"Kafka 전송 완료: userId={user_id}, 추천 책 수={len(recommendations)}권")
    except Exception as e:
        logger.error(f"Kafka 전송 실패: {e}")
