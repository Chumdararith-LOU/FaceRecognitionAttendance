import numpy as np
from typing import Optional
from .database import db
from pgvector.sqlalchemy import VECTOR

class Student(db.Model):
    """
    Represents a student in the system.
    """
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    face_embedding = db.Column(VECTOR(256), nullable=True) # Will be nullable until registration is complete
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def set_embedding(self, embedding: np.ndarray):
        """Converts a numpy array to a list for storing in the database."""
        if isinstance(embedding, np.ndarray):
            self.face_embedding = embedding.tolist()
        else:
            self.face_embedding = embedding

    def get_embedding(self) -> Optional[np.ndarray]:
        """Retrieves the embedding as a numpy array."""
        if self.face_embedding is not None:
            return np.array(self.face_embedding)
        return None

    def __repr__(self):
        return f"<Student {self.student_code} - {self.full_name}>"