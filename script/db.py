from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    # Поля из первого задания
    userid = Column(Integer, primary_key=True)
    username = Column(String)
    role = Column(String)  # 'teacher' или 'student'
    tutorcode = Column(String, nullable=True, unique=True) # Уникальный код для преподавателя
    subscribe = Column(String, nullable=True) # Имя пользователя преподавателя, на которого подписан студент
    extra = Column(String, nullable=True)
    
    # Поля из второго задания
    vm_host = Column(String, nullable=True)
    vm_port = Column(Integer, nullable=True)
    vm_username = Column(String, nullable=True)
    vm_password = Column(String, nullable=True)

engine = None
async_session = None

def initialize_db(database_url: str):
    global engine, async_session
    if engine is None:
        engine = create_async_engine(database_url, echo=False) # Отключаем echo для чистоты логов
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, async_session

async def init_db():
    if not engine:
        raise RuntimeError("Database not initialized. Call initialize_db() first.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session() -> AsyncSession:
    async with async_session() as session:
        yield session 