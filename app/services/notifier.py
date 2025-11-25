# simeple fast api app that gets requests to send or schedule notifications vai email, Slack, and in-app notifications.

import time
import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Notification, Template, User, get_db, init_db, validate_user_or_group
from app.logger import get_logger
from app.services.api_models import NotificationRequest, render_template
from app.services.scheduler import (
    scheduler,
    send_scheduled_notification,
    send_to_topics,
)

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    time.sleep(10)
    await init_db()
    scheduler.start()


logger = get_logger()


@app.post("/notify/")
async def notify(notification: NotificationRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received notification request: {notification}")

    logger.info("Validating user/group in the database")
    user, users = await validate_user_or_group(notification, db)

    if not user and not users:
        raise HTTPException(status_code=404, detail="User / Group not found")

    if user:
        logger.info(f"User validated: {user}")
        users = [user]  # wrap single user in a list for uniform processing
    if users:
        logger.info(f"User group validated with {len(users)} users")

    await process_template(notification, db)

    logger.info(datetime.now())
    scheduled_date = (
        datetime.strptime(notification.scheduled_time, "%Y-%m-%dT%H:%M:%S")
        if notification.scheduled_time
        else None
    )
    ids = []
    if users:
        for user in users:
            str_id = str(uuid.uuid4())
            notification_id = str_id.encode("utf-8")
            if notification.scheduled_time:
                if scheduled_date > datetime.now():
                    logger.info(
                        f"Scheduling notification for {notification.scheduled_time}"
                    )
                    scheduler.add_job(
                        send_scheduled_notification,
                        trigger="date",
                        run_date=scheduled_date,
                        args=[notification_id, notification.model_dump(), user],
                        id=str_id,
                        replace_existing=True,
                    )
                    return {"status": "scheduled", "notification_id": str_id}
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="date should be after current time in utc",
                    )

            else:
                logger.info("Sending notification immediately")
                for channel in notification.channels:
                    logger.info(f"Sending via channel: {channel}")
                    await send_to_topics(
                        notification_id, notification.model_dump(), user, channel
                    )
                    logger.info(f"Notification added to send queue: {notification}")
            ids.append(str_id)

        return {"status": "sent", "notification_ids": ids}


async def process_template(notification, db):
    if notification.template and notification.template.template_str:
        logger.info("Using template for notification")
        # Here you would typically fetch and render the template with data
        rendered_message = render_template(
            notification.template.template_str, notification.template.data
        )
        notification.message = rendered_message
        logger.info(f"Rendered message: {rendered_message}")

    elif notification.template and notification.template.template_id:
        logger.info("Fetching template from database")
        result = await db.execute(
            select(Template).where(Template.id == notification.template.template_id)
        )
        template = result.scalars().first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        rendered_message = render_template(
            template.body_template, notification.template.data
        )
        notification.message = rendered_message
        logger.info(f"Rendered message from DB template: {rendered_message}")


# create a dummy slack webhook endpoint for testing
@app.post("/slack/webhook/")
async def slack_webhook(payload: dict):
    logger.info(f"Received Slack webhook payload: {payload}")
    return {"status": "received", "payload": payload}


# endpoint to get all templates
@app.get("/templates/")
async def get_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template))
    templates = result.scalars().all()
    return {"templates": [template.__dict__ for template in templates]}


# get all users
@app.get("/users/")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {"users": [user.__dict__ for user in users]}


# get all notifications
@app.get("/notifications/")
async def get_notifications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification))
    notifications = result.scalars().all()
    return {"notifications": [notification.__dict__ for notification in notifications]}


