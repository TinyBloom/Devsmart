"""
DevSmart Database Connection
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import types
from datetime import datetime
import uuid

from config.settings import settings


class GUID(types.TypeDecorator):
    """通用 UUID 类型，兼容 PostgreSQL 和 SQLite"""
    impl = types.String(36)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value)
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


# 创建异步引擎（根据数据库类型配置）
connect_args = {}
if 'sqlite' in settings.database_url:
    connect_args['check_same_thread'] = False

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args=connect_args,
)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""
    pass


async def get_db_session() -> AsyncSession:
    """获取数据库会话（依赖注入）"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_database():
    """初始化数据库（创建表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)