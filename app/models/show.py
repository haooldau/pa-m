from sqlalchemy import Column, Integer, String, Date, DateTime
from ..config.database import Base
from datetime import datetime

class Show(Base):
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    artist = Column(String(255))
    tag = Column(String(50))
    city = Column(String(50))
    venue = Column(String(255))
    lineup = Column(String(255))
    date = Column(Date)
    price = Column(String(255))
    status = Column(String(50))
    detail_url = Column(String(255))
    poster = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow) 