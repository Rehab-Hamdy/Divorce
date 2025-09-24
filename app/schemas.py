# app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class DoctorCreate(BaseModel):
    name: str
    email: str

class DoctorOut(BaseModel):
    id: int
    name: str
    email: str
    class Config: from_attributes = True

class CoupleCreate(BaseModel):
    doctor_id: int
    partner_a_name: str
    partner_b_name: str

class CoupleOut(BaseModel):
    id: int
    doctor_id: int
    partner_a_name: str
    partner_b_name: str
    class Config: from_attributes = True


class PredictionHistoryItem(BaseModel):
    id: int
    assessment_id: int
    proba: float
    pred_class: int
    created_at: str   # ISO timestamp
    title: Optional[str] = None

    class Config:
        from_attributes = True

class PredictionHistoryOut(BaseModel):
    couple_id: int
    items: List[PredictionHistoryItem]

class QuestionCreate(BaseModel):
    doctor_id: int
    text: str

class QuestionOut(BaseModel):
    id: int
    doctor_id: int
    text: str
    active: bool
    class Config: from_attributes = True

class AssessmentCreate(BaseModel):
    doctor_id: int
    couple_id: int
    title: Optional[str] = None

class AssessmentOut(BaseModel):
    id: int
    doctor_id: int
    couple_id: int
    title: Optional[str] = None
    class Config: from_attributes = True

class AnswerIn(BaseModel):
    question_id: Optional[int] = None
    partner: Literal["A","B"]
    value: int = Field(ge=0, le=4)
    text: str  # free-text (the asked question phrasing)

class AnswersBulkIn(BaseModel):
    items: List[AnswerIn]

class PredictionOut(BaseModel):
    id: int
    assessment_id: int
    proba: float
    pred_class: int
    vector_json: Dict[str, Optional[float]]
    audit_json: List[Dict[str, Any]]
    class Config: from_attributes = True

class DashboardCoupleRow(BaseModel):
    couple_id: int
    partner_a_name: str
    partner_b_name: str
    last_proba: Optional[float] = None
    last_class: Optional[int] = None

class DashboardOut(BaseModel):
    doctor_id: int
    couples: List[DashboardCoupleRow]
