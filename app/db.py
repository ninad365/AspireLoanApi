import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "mysql+mysqlconnector://root:ninad1234@localhost/mydatabase"

engine = create_engine(
    DATABASE_URL,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
Base.metadata.create_all(bind=engine)