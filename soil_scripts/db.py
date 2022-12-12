from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from . import config


DATABASE_USERNAME = config.DATABASE_USERNAME
DATABASE_PASSWORD = config.DATABASE_PASSWORD
DATABASE_HOST = config.DATABASE_HOST
DATABASE_NAME = config.DATABASE_NAME
DATABASE_PORT = config.DATABASE_PORT

sqlalchemy_uri = (
    f"postgresql+asyncpg://{DATABASE_USERNAME}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

engine = create_async_engine(sqlalchemy_uri)

DbSession = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


class DbConnectionError(Exception):
    ...


@contextmanager
def sync_session() -> Session:
    sync_sqlalchemy_uri = (
        f"postgresql+psycopg2://{DATABASE_USERNAME}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )
    sync_engine = sa.create_engine(sync_sqlalchemy_uri)
    Session = sessionmaker(bind=sync_engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise DbConnectionError(f"Cannot connect to db: {e}")
    finally:
        session.close()
