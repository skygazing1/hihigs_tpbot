from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    userid = Column(Integer, primary_key=True)
    username = Column(String)
    role = Column(String)
    tutorcode = Column(String, nullable=True)
    subscribe = Column(String, nullable=True)
    extra = Column(String, nullable=True)

# Асинхронный движок для SQLite
engine = create_async_engine('sqlite+aiosqlite:///bot.db', echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 