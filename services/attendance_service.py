import cv2
import face_recognition
import numpy as np
from models import Student, AttendanceRecord
from datetime import datetime, timedelta
from models.database import db

last_seen_students = {}
ATTENDANCE_COOLDOWN = timedelta(minutes=1) # Set cooldown to 1 minute


# In-memory cache for known faces
known_face_encodings = []
known_face_metadata = []

def load_known_faces():
    """
    Loads all student face embeddings from the database into memory.
    This should be called once at application startup.
    """
    global known_face_encodings, known_face_metadata
    
    # Clear existing lists
    known_face_encodings.clear()
    known_face_metadata.clear()

    students = Student.query.filter(Student.face_embedding.isnot(None)).all()
    for student in students:
        known_face_encodings.append(student.get_embedding())
        known_face_metadata.append({
            'student_id': student.id,
            'student_code': student.student_code,
            'full_name': student.full_name
        })
    print(f"Loaded {len(known_face_encodings)} known faces.")

def recognize_and_log_attendance(frame):
    """
    Recognizes faces, logs attendance with a cooldown, and draws on the frame.
    """
    from app import app
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    current_time = datetime.now()

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        name = "Unknown"
        metadata = None

        if known_face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                metadata = known_face_metadata[best_match_index]
                name = metadata['full_name']
                student_id = metadata['student_id']

                # --- ATTENDANCE LOGIC ---
                last_seen_time = last_seen_students.get(student_id)

                if last_seen_time is None or (current_time - last_seen_time) > ATTENDANCE_COOLDOWN:
                    print(f"DEBUG: Attempting to log student_id: {student_id}, type: {type(student_id)}")
                    # Log attendance to the database
                    with app.app_context():
                        try:
                            new_record = AttendanceRecord(student_id=student_id)
                            db.session.add(new_record)
                            db.session.commit()
                            
                            # Update the last seen time
                            last_seen_students[student_id] = current_time
                            print(f"Logged attendance for {name} at {current_time}")

                        except Exception as e:
                            db.session.rollback()
                            print(f"Error logging attendance: {e}")

        # --- DRAWING LOGIC ---
        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    return frame