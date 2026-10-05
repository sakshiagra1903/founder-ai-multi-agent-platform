from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, filename, original_filename, file_path, file_size, user_id) -> Resume:
        r = Resume(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            user_id=user_id
        )
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def get_by_id(self, resume_id: int, user_id: int) -> Optional[Resume]:
        return self.db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id
        ).first()

    def get_by_ids(self, resume_ids: List[int], user_id: int) -> List[Resume]:
        return self.db.query(Resume).filter(
            Resume.id.in_(resume_ids),
            Resume.user_id == user_id
        ).all()

    def list_by_user(self, user_id: int) -> List[Resume]:
        return self.db.query(Resume).filter(
            Resume.user_id == user_id
        ).order_by(Resume.uploaded_at.desc()).all()

    def delete(self, resume: Resume):
        self.db.delete(resume)
        self.db.commit()
