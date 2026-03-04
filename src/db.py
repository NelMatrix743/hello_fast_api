from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

import uuid
from collections.abc import AsyncGenerator




DATABASE_URL = "sqlite+aiosqlite:///./test.db"

