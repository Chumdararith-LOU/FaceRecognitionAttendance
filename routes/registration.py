from flask import Blueprint, request, jsonify
from models.database import db
from models.student import Student
from services.face_recognition import get_face_embedding_from_image

# Create a Blueprint
registration_bp = Blueprint('registration_api', __name__)

@registration_bp.route('/api/register', methods=['POST'])
def register_student():
    """
    Handles student registration. Expects multipart/form-data with:
    - student_code (string)
    - full_name (string)
    - image (file)
    """
    # 1. --- Validate Input ---
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    student_code = request.form.get('student_code')
    full_name = request.form.get('full_name')

    if not all([student_code, full_name, image_file]):
        return jsonify({"error": "Missing required fields: student_code, full_name, or image"}), 400

    # 2. --- Check for Existing Student ---
    if Student.query.filter_by(student_code=student_code).first():
        return jsonify({"error": f"Student with code {student_code} already exists"}), 409 # 409 Conflict

    # 3. --- Process Image and Get Embedding ---
    try:
        embedding, num_faces = get_face_embedding_from_image(image_file)
    except (TypeError, ValueError) as e:
        # This will catch the "cannot unpack non-iterable NoneType object" error
        # and any other potential unpacking errors.
        print(f"ERROR: Could not unpack result from face embedding service: {e}")
        embedding, num_faces = None, 0 # Set default failure values
    except Exception as e:
        # Catch any other unexpected errors from the service
        print(f"ERROR: An unexpected exception occurred in face embedding service: {e}")
        embedding, num_faces = None, 0 # Set default failure values

    if embedding is None:
        if num_faces == 0:
            error_message = "No face could be detected in the image. Please try again with better lighting."
        else:
            error_message = f"Found {num_faces} faces. Please provide a photo with only one face."
        return jsonify({"error": error_message}), 400

    # 4. --- Create and Save New Student ---
    try:
        new_student = Student(
            student_code=student_code,
            full_name=full_name
        )
        new_student.set_embedding(embedding)
        
        db.session.add(new_student)
        db.session.commit()

        return jsonify({
            "message": "Student registered successfully",
            "student_id": new_student.id,
            "student_code": new_student.student_code
        }), 201 # 201 Created

    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({"error": "An internal error occurred while saving the student."}), 500