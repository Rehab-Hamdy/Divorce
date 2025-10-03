# app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base
import enum

class PartnerEnum(str, enum.Enum):
    A = "A"
    B = "B"

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    couples = relationship("Couple", back_populates="doctor", cascade="all,delete")
    questions = relationship("Question", back_populates="doctor", cascade="all,delete")

class Couple(Base):
    __tablename__ = "couples"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    partner_a_name = Column(String(120), nullable=False)
    partner_b_name = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="couples")
    assessments = relationship("Assessment", back_populates="couple", cascade="all,delete")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    text = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="questions")

class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True)
    couple_id = Column(Integer, ForeignKey("couples.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    couple = relationship("Couple", back_populates="assessments")
    answers = relationship("Answer", back_populates="assessment", cascade="all,delete")
    predictions = relationship("Prediction", back_populates="assessment", cascade="all,delete")

    recommendation = relationship("Recommendation", back_populates="assessment", uselist=False)

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)  # optional
    partner = Column(Enum(PartnerEnum), nullable=False)  # "A" or "B"
    value = Column(Integer, nullable=False)  # 0..4
    user_text = Column(Text, nullable=False)  # snapshot of the question text used
    created_at = Column(DateTime, default=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="answers")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    proba = Column(Float, nullable=False)
    pred_class = Column(Integer, nullable=False)  # 0/1
    vector_json = Column(JSON, nullable=False)    # {"Atr1": 1.0, ...}
    audit_json = Column(JSON, nullable=False)     # list of logs (A/B combined)
    created_at = Column(DateTime, default=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="predictions")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    domains_json = Column(JSON, nullable=False)       # risk scores + bands
    modules_json = Column(JSON, nullable=False)       # base deterministic modules
    personalized_text = Column(Text, nullable=False)  # final LLM recommendation

    assessment = relationship("Assessment", back_populates="recommendation")
