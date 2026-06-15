from pydantic import BaseModel
from typing import Optional

class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: Optional[str] = None
    store_id: int
    re_sphere: Optional[float] = None
    re_cylinder: Optional[float] = None
    re_axis: Optional[int] = None
    re_add: Optional[float] = None
    le_sphere: Optional[float] = None
    le_cylinder: Optional[float] = None
    le_axis: Optional[int] = None
    le_add: Optional[float] = None
    lens_type_id: int
    lens_index: Optional[float] = None
    coating: Optional[str] = None
    frame_details: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None
    changed_by: str = "Human"