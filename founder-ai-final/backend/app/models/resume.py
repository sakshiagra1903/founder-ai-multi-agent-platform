from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class Resume(Base):
    __tablename__ = "resumes"

    id                = Column(Integer, primary_key=True, index=True)
    filename          = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path         = Column(String(500), nullable=False)
    file_size         = Column(BigInteger, nullable=False)
    user_id           = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at       = Column(DateTime(timezone=True), server_default=func.now())

    owner     = relationship("User", back_populates="resumes")
    candidate = relationship("Candidate", back_populates="resume", uselist=False, cascade="all, delete-orphan")
