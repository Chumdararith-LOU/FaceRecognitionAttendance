import cv2
import face_recognition
import numpy as np
from models import Student

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

def recognize_faces_in_frame(frame):
    """
    Detects and recognizes faces in a video frame, drawing names and boxes.
    """
    # Find all face locations and face encodings in the current frame
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    # Loop through each face found in the frame
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        name = "Unknown"

        if known_face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            
            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                metadata = known_face_metadata[best_match_index]
                name = metadata['full_name']

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    return frame