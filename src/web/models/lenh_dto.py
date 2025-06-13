# ========================
# src/models/lenh_dto.py
# ========================
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class LenhDTO(BaseModel):
    ten: str
    moTa: Optional[str] = None
    giaTren: float
    giaDuoi: float
    chotLoi: List[float]
    kichThuocLo: float
    catLo: List[float]
    hanhDong: bool  # True = Mua, False = Bán
    symbol: str
    ngayHetHan: datetime