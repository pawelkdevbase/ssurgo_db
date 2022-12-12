import os
from pathlib import Path

BASEDIR = Path(__file__).parent.parent.resolve().absolute()
TMPDIR = BASEDIR.joinpath("tmp")

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "soil_data")
