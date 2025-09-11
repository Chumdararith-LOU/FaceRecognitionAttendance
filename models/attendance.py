from .database import db

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    
    # Establishes the relationship to the Student model
    student = db.relationship('Student', backref=db.backref('attendance_records', lazy=True))