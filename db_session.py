from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "sqlite:///./eSportsCalendar.db"

# PostgreSQL connection parameters
# DB_USER = "postgres"
# DB_PASSWORD = "admin"
# DB_HOST = "localhost"
# DB_PORT = "5432"
# DB_NAME = "esports"


# Construct the PostgreSQL database URL
# SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:NcZdQtivYG8VWFkOsb7S@containers-us-west-148.railway.app:6090/railway"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
