from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, connect_args={"check_same_thread": False})


def init_db(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session
