import asyncio
import json

from aiokafka import AIOKafkaConsumer
from logger import get_logger

from providers.email_provider import EmailProvider
from providers.inapp_provider import InAppProvider
from providers.slack_provider import SlackProvider
from db import Notification, get_db, init_db
KAFKA_BOOTSTRAP = "broker:29092"
logger = get_logger()
TOPICS = [
    "email",
    "slack",
    "inapp",
]

providers = {
    "email": EmailProvider(),
    "slack": SlackProvider(),
    "inapp": InAppProvider(),
}

GROUP_ID = "notification-service-group"


async def start_consumer(topic: str):
    """Start a Kafka consumer for a single topic."""
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=f"{GROUP_ID}-{topic}",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    logger.info(f"Starting consumer for topic: {topic}")
    await consumer.start()

    try:
        async for record in consumer:
            msg = _decode_value(record.value)
            logger.info(f"[{topic}] Received: {msg}")
            provider = providers.get(topic)
            if provider:
                result = await provider.send(
                    msg["user"],
                    msg["notification"]["subject"],
                    msg["notification"]["message"],
                )
                logger.info(f"[{topic}] Send result: {result}")
            # save the notification to db
            async for db in get_db() :
                notification_record = Notification(
                    id = msg["id"],
                    user_id=msg["user"]['id'],
                    channel=topic,
                    subject=msg["notification"]["subject"],
                    message=msg["notification"]["message"],
                    status="sent" if result else "failed",
                )
                db.add(notification_record)
                await db.commit()
                logger.info(f"[{topic}] Notification saved to DB with ID: {notification_record.id}")
    finally:
        await consumer.stop()
        print(f"Stopped consumer for topic: {topic}")

def _decode_value(value):
    if value is None:
        return None
    if isinstance(value, bytes):
        try:
            # Try JSON
            return json.loads(value.decode("utf-8"))
        except json.JSONDecodeError:
            # Fallback to plain text
            return value.decode("utf-8")
    return value


async def main():
    """Run all consumers as parallel tasks."""
    await asyncio.sleep(10)  # wait for other services to be up
    logger.info("Initializing database...")
    # await init_db()
    logger.info("Starting all consumers...")
    tasks = [asyncio.create_task(start_consumer(topic)) for topic in TOPICS]
    logger.info("All consumers started.")
    await asyncio.gather(*tasks)




if __name__ == "__main__":
    # once db is ready, run the main consumer loop
    asyncio.run(main())
