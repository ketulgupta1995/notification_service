# scheduler.py
import os

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.kafka import send_message
from app.logger import get_logger

DATABASE_URL = os.getenv("DATABASE_URL")  # from docker compose
DATABASE_URL = DATABASE_URL.replace("asyncpg", "psycopg2")

jobstores = {"default": SQLAlchemyJobStore(url=DATABASE_URL)}

scheduler = AsyncIOScheduler(jobstores=jobstores)
logger = get_logger()


async def send_to_topics(notification_id:bytes, notification, user , channel):
    kafka_event = {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "slack_webhook": user.slack_webhook,
            "preferences": user.preferences,
        },
        "notification": notification,
        "id": notification_id.decode('utf-8'),
    }
    logger.info(f"Producing event to Kafka: {kafka_event}")
    await send_message(notification_id, channel, kafka_event)


async def send_scheduled_notification(notification_id, notification, user):
    logger.info("Executing scheduled job:", notification)
    for channel in notification['channels']:
        logger.info(f"Sending Scheduled notifcation via channel: {channel}")
        # Here you would integrate with actual sending logic
        # create a event in kafka topic for processing
        await send_to_topics(notification_id, notification, user , channel) 
        logger.info(f"Scheduled Notification added to send queue: {notification}")
