from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from src.web.models.positions import Position

class SuccessResponse(BaseModel):
    status: str = Field("success", description="Response status")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

class ErrorResponse(BaseModel):
    status: str = Field("error", description="Response status")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")

class PositionsResponse(BaseModel):
    status: str = Field("success", description="Response status")
    message: Optional[str] = Field(None, description="Success message")
    positions: List[Position] = Field(..., description="List of active positions") 

__all__ = ["SuccessResponse", "ErrorResponse", "PositionsResponse"]