import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# На Railway берётся из переменной DATABASE_URL, локально остаётся ваша база
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/glas")

# Railway иногда отдаёт postgres://, а SQLAlchemy ждёт postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()