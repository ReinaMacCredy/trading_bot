from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from src.web.db.database import Base
from datetime import datetime

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    ten = Column(String)
    moTa = Column(String)
    giaTren = Column(Float)
    giaDuoi = Column(Float)
    chotLoi = Column(String)  # lưu JSON
    kichThuocLo = Column(Float)
    catLo = Column(String)
    hanhDong = Column(Boolean)
    symbol = Column(String)
    ngayHetHan = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
