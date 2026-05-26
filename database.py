from sqlalchemy import create_engine
from sqlalchemy import sessionmaker
from sqlalchemy.orm import DeclarativeBase
engine = create_engine("sqlite://", echo=True)


class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

