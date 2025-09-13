# In services/attendance_service.py, replace the entire file content:
import os
import cv2
import numpy as np
from datetime import datetime, timedelta
import openvino.runtime as ov
from scipy.spatial.distance import cosine

# Import database models and session
from models import Student, AttendanceRecord
from models.database import db

# Get the absolute path of the directory where this file is located 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the project root 
PROJECT_ROOT = os.path.dirname(BASE_DIR)
# --- OpenVINO Model and App Configuration ---
core = ov.Core()
face_detection_model_xml = "intel/intel/face-detection-retail-0005/FP16/face-detection-retail-0005.xml"
face_embedding_model_xml = "intel/intel/face-reidentification-retail-0095/FP16/face-reidentification-retail-0095.xml"

# Load models
face_detection_model = core.read_model(model=face_detection_model_xml)
face_embedding_model = core.read_model(model=face_embedding_model_xml)

# Compile models for the target device (e.g., CPU or GPU)
compiled_face_detection_model = core.compile_model(model=face_detection_model, device_name="CPU")
compiled_face_embedding_model = core.compile_model(model=face_embedding_model, device_name="CPU")

# Get input and output nodes
detection_input_layer = compiled_face_detection_model.input(0)
detection_output_layer = compiled_face_detection_model.output(0)
embedding_input_layer = compiled_face_embedding_model.input(0)
embedding_output_layer = compiled_face_embedding_model.output(0)

# In-memory cache for known faces
known_face_encodings = []
known_face_metadata = []

# Cooldown tracking for attendance logging
last_seen_students = {}
ATTENDANCE_COOLDOWN = timedelta(seconds=10) # Reduced cooldown for testing performance
RECOGNITION_THRESHOLD = 0.4 # Cosine distance threshold (lower is stricter)

def load_known_faces():
    """Loads all student face embeddings from the database into memory."""
    from app import app
    global known_face_encodings, known_face_metadata
    known_face_encodings.clear()
    known_face_metadata.clear()

    with app.app_context():
        students = Student.query.filter(Student.face_embedding.isnot(None)).all()
        for student in students:
            known_face_encodings.append(student.get_embedding())
            known_face_metadata.append({
                'student_id': student.id,
                'full_name': student.full_name
            })
    print(f"Loaded {len(known_face_encodings)} known faces.")

def preprocess_frame(frame, target_shape):
    """Preprocesses a frame to the model's required input shape."""
    n, c, h, w = target_shape
    resized_frame = cv2.resize(frame, (w, h))
    transposed_frame = resized_frame.transpose(2, 0, 1) # HWC to CHW
    input_tensor = np.expand_dims(transposed_frame, 0).astype(np.float32) # Add batch dimension
    return input_tensor

def recognize_and_log_attendance(frame):
    """
    Performs face detection and recognition using OpenVINO.
    """
    from app import app
    original_h, original_w = frame.shape[:2]
    
    # Preprocess and detect faces
    input_tensor = preprocess_frame(frame, detection_input_layer.shape)
    detection_results = compiled_face_detection_model([input_tensor])[detection_output_layer]

    current_time = datetime.now()

    for detection in detection_results[0][0]:
        confidence = float(detection[2])
        if confidence > 0.8:
            xmin = int(detection[3] * original_w)
            ymin = int(detection[4] * original_h)
            xmax = int(detection[5] * original_w)
            ymax = int(detection[6] * original_h)

            # Crop the face from the original frame
            face_crop = frame[ymin:ymax, xmin:xmax]
            if face_crop.size == 0: continue

            # Preprocess and get embedding for the cropped face
            embedding_tensor = preprocess_frame(face_crop, embedding_input_layer.shape)
            face_embedding = compiled_face_embedding_model([embedding_tensor])[embedding_output_layer][0]
            
            name = "Unknown"
            if known_face_encodings:
                distances = [cosine(face_embedding, known_embedding) for known_embedding in known_face_encodings]
                best_match_index = np.argmin(distances)
                
                if distances[best_match_index] < RECOGNITION_THRESHOLD:
                    metadata = known_face_metadata[best_match_index]
                    name = metadata['full_name']
                    student_id = metadata['student_id']

                    # --- ATTENDANCE LOGIC ---
                    last_seen_time = last_seen_students.get(student_id)
                    if last_seen_time is None or (current_time - last_seen_time) > ATTENDANCE_COOLDOWN:
                        with app.app_context():
                            try:
                                new_record = AttendanceRecord(student_id=student_id)
                                db.session.add(new_record)
                                db.session.commit()
                                last_seen_students[student_id] = current_time
                                print(f"Logged attendance for {name} at {current_time}")
                            except Exception as e:
                                db.session.rollback()
                                print(f"Error logging attendance: {e}")

            # Draw bounding box and name
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            cv2.putText(frame, name, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
    return frame

def get_face_embedding_from_image(image_file):
    """
    Finds a single face in an image and returns its OpenVINO embedding.
    This function is now used by the registration route.
    """
    image_data = np.frombuffer(image_file.read(), np.uint8)
    frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    original_h, original_w = frame.shape[:2]

    input_tensor = preprocess_frame(frame, detection_input_layer.shape)
    detection_results = compiled_face_detection_model([input_tensor])[detection_output_layer]

    detections = [d for d in detection_results[0][0] if d[2] > 0.8]
    if len(detections) != 1:
        return None # Ensure only one face for registration

    detection = detections[0]
    xmin = int(detection[3] * original_w)
    ymin = int(detection[4] * original_h)
    xmax = int(detection[5] * original_w)
    ymax = int(detection[6] * original_h)
    
    face_crop = frame[ymin:ymax, xmin:xmax]
    if face_crop.size == 0: return None
    
    embedding_tensor = preprocess_frame(face_crop, embedding_input_layer.shape)
    face_embedding = compiled_face_embedding_model([embedding_tensor])[embedding_output_layer][0]
    
    return face_embedding