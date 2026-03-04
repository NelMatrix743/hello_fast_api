from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

import uuid
import datetime
from collections.abc import AsyncGenerator



DATABASE_URL = "sqlite+aiosqlite:///./test.db"


class Post(DeclarativeBase):

    __tablename__ : str = "posts"

    id: Column = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption: Column = Column(Text)
    url: Column = Column(String, nullable=False)
    file_type: Column = Column(String, nullable=False)
    file_name: Column = Column(String, nullable=False)
    created_at: Column = Column(DateTime, default=datetime.utcnow)

