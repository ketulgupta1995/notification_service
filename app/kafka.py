# connect to kafka and send messages to topics
import json

from aiokafka import AIOKafkaProducer

bootstrap_servers = "broker:29092"

# The message should be json serialized
async def send_message(notification_id, topic: str, message: dict):
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    await producer.start()
    try:
        await producer.send_and_wait(topic, key = notification_id, value = json.dumps(message).encode("utf-8"))
    finally:
        await producer.stop()
