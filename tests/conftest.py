import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import sessionmaker
from main import app
from src.database import Base, get_db
