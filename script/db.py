from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class VMConnection(Base):
    """
    Модель для хранения информации о SSH-подключениях к виртуальным машинам.
    """
    __tablename__ = 'vm_connections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.userid'))
    host = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    
    # Отношение к пользователю
    user = relationship("User", back_populates="vm_connections")
    
    def __repr__(self):
        return f"<VMConnection(user_id={self.user_id}, host={self.host}, username={self.username})>"

def init_db():
    """
    Инициализация базы данных.
    Создает все таблицы, если они не существуют.
    """
    database_url = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def get_db_session():
    """
    Получение сессии базы данных.
    
    Returns:
        Session: Сессия SQLAlchemy
    """
    database_url = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session() 