from sqlalchemy import Column, String, TIMESTAMP, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class FactEvent(Base):
    __tablename__ = "fact_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_time = Column(TIMESTAMP, nullable=False)
    user_id = Column(String)
    event_name = Column(String)
    platform = Column(String)
    list_name = Column(String)
    product_id = Column(String)
    product_name = Column(String)
    price = Column(Float)