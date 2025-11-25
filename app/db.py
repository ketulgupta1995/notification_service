import os

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, nullable=True)
    email = Column(String, unique=True, nullable=True)
    name = Column(String)
    slack_webhook = Column(String, nullable=True)
    preferences = Column(JSON, default={})


class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    channel = Column(String)  # 'email', 'slack', 'in_app', 'multi'
    subject_template = Column(String, nullable=True)
    body_template = Column(Text)
    is_default = Column(Boolean, default=False)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True)
    channel = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    subject = Column(String, default={})
    message = Column(String, default={})
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    template = relationship("Template")


async def init_db():
    # 1. Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Insert dummy data
    async with AsyncSessionLocal() as session:
        # Check if we already seeded
        result = await session.execute(select(User).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            print("✔ Dummy data already exists, skipping seed.")
            return

        print("🌱 Seeding initial dummy data...")

        # Dummy users
        users = [
            User(
                group_id=1,
                email="alice@example.com",
                name="Alice",
                slack_webhook=None,
                preferences={"email": True, "slack": False},
            ),
            User(
                group_id=2,
                email="bob@example.com",
                name="Bob",
                slack_webhook="https://hooks.slack.com/services/xxxx",
                preferences={"email": True, "slack": True},
            ),
            User(
                group_id=None,
                email="charlie@example.com",
                name="Charlie",
                slack_webhook=None,
                preferences={"email": False, "slack": False},
            ),
            User(
                group_id=4,
                email="ketulgupta1995@gmail.com",
                name="Ketul",
                slack_webhook=None,
                preferences={"email": True, "slack": True},
            ),
            User(
                group_id=4,
                email="kruti@example.com",
                name="Kruti",
                slack_webhook=None,
                preferences={"email": True, "slack": False},
            ),
        ]

        session.add_all(users)
        await session.commit()

        # add few templates
        templates = [
            Template(   
                name="Welcome Email",
                channel="email",
                subject_template="Welcome, {name}!",
                body_template="Hello {name}, welcome to our platform.",
                is_default=True,
            ),
            Template(
                name="Slack Alert",
                channel="slack",
                subject_template=None,
                body_template="Alert: {alert_message}",
                is_default=False,
            ),  
        ]
        session.add_all(templates)
        await session.commit()  

        print("✔ Dummy data inserted successfully!")


async def get_db() ->  AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def validate_user_or_group(notification, db : AsyncSession):
    if notification.user_id is not None:
        stmt = select(User).where(User.id == notification.user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        return user , None
    else:
        stmt = select(User).where(User.group_id == notification.user_group)
        result = await db.execute(stmt)
        # get all users in the group
        users =  result.scalars().all()
        return None , users