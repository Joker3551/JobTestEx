from typing import Annotated
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    # echo=True,
    )

session_factory = sessionmaker(engine)

def get_session():
    with session_factory() as s:
        yield s

sessionDep = Annotated[Session, Depends(get_session)]


class Base(DeclarativeBase):
    pass