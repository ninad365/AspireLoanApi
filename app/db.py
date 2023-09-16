from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "mysql+mysqlconnector://root:ninad1234@localhost/mydatabase"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)