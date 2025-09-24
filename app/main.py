# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from app.db import Base, engine, get_db
from app.models import Doctor, Couple, Question, Assessment, Answer, PartnerEnum, Prediction
from app.schemas import (
    DoctorCreate, DoctorOut,
    CoupleCreate, CoupleOut,
    QuestionCreate, QuestionOut,
    AssessmentCreate, AssessmentOut,
    AnswersBulkIn, PredictionOut,
    DashboardOut, DashboardCoupleRow
)
from app.services.predictor import predict_for_assessment

# Create tables (demo; in prod use Alembic)
Base.metadata.create_all(bind=engine)


app = FastAPI(title="Divorce Risk Service", version="0.1.0")

# Root endpoint for health check or welcome message
@app.get("/")
def root():
    return {"message": "Divorce Risk Service API is running."}

# CORS (adjust for your frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

@app.post("/doctors", response_model=DoctorOut)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    exists = db.query(Doctor).filter(Doctor.email == payload.email).first()
    if exists:
        raise HTTPException(400, "Doctor with this email already exists")
    doc = Doctor(name=payload.name, email=payload.email)
    db.add(doc); db.commit(); db.refresh(doc)
    return doc

@app.post("/couples", response_model=CoupleOut)
def create_couple(payload: CoupleCreate, db: Session = Depends(get_db)):
    doc = db.query(Doctor).get(payload.doctor_id)
    if not doc:
        raise HTTPException(404, "Doctor not found")
    c = Couple(
        doctor_id=payload.doctor_id,
        partner_a_name=payload.partner_a_name,
        partner_b_name=payload.partner_b_name
    )
    db.add(c); db.commit(); db.refresh(c)
    return c

@app.post("/questions", response_model=QuestionOut)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    doc = db.query(Doctor).get(payload.doctor_id)
    if not doc:
        raise HTTPException(404, "Doctor not found")
    q = Question(doctor_id=payload.doctor_id, text=payload.text, active=True)
    db.add(q); db.commit(); db.refresh(q)
    return q

@app.post("/assessments", response_model=AssessmentOut)
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db)):
    doc = db.query(Doctor).get(payload.doctor_id)
    if not doc:
        raise HTTPException(404, "Doctor not found")
    couple = db.query(Couple).get(payload.couple_id)
    if not couple:
        raise HTTPException(404, "Couple not found")
    if couple.doctor_id != payload.doctor_id:
        raise HTTPException(400, "Couple does not belong to this doctor")
    a = Assessment(doctor_id=payload.doctor_id, couple_id=payload.couple_id, title=payload.title)
    db.add(a); db.commit(); db.refresh(a)
    return a

@app.post("/assessments/{assessment_id}/answers/bulk")
def add_answers(assessment_id: int, payload: AnswersBulkIn, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).get(assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    rows = []
    for item in payload.items:
        if item.value < 0 or item.value > 4:
            raise HTTPException(400, "Value must be 0..4")
        rows.append(Answer(
            assessment_id=assessment_id,
            question_id=item.question_id,
            partner=PartnerEnum(item.partner),
            value=int(item.value),
            user_text=item.text
        ))
    db.add_all(rows); db.commit()
    return {"inserted": len(rows)}

@app.post("/assessments/{assessment_id}/predict", response_model=PredictionOut)
def do_predict(assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).get(assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    proba, pred_class, vector_json, audit_json = predict_for_assessment(db, assessment_id)
    pred_row = db.query(Prediction).filter(Prediction.assessment_id == assessment_id)\
                                   .order_by(Prediction.created_at.desc()).first()
    return pred_row

@app.get("/doctors/{doctor_id}/dashboard", response_model=DashboardOut)
def doctor_dashboard(doctor_id: int, db: Session = Depends(get_db)):
    doc = db.query(Doctor).get(doctor_id)
    if not doc:
        raise HTTPException(404, "Doctor not found")
    couples = db.query(Couple).filter(Couple.doctor_id == doctor_id).all()
    out_rows: List[DashboardCoupleRow] = []
    for c in couples:
        last_pred = (
            db.query(Prediction)
            .join(Assessment, Prediction.assessment_id == Assessment.id)
            .filter(Assessment.couple_id == c.id)
            .order_by(Prediction.created_at.desc())
            .first()
        )
        out_rows.append(DashboardCoupleRow(
            couple_id=c.id,
            partner_a_name=c.partner_a_name,
            partner_b_name=c.partner_b_name,
            last_proba=(last_pred.proba if last_pred else None),
            last_class=(last_pred.pred_class if last_pred else None),
        ))
    return DashboardOut(doctor_id=doctor_id, couples=out_rows)

@app.get("/doctors/by_email")
def get_doctor_by_email(email: str, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.email == email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor
