from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///oreacle.db")

SessionLocal = sessionmaker(bind=engine)
