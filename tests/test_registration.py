import pytest
from app import create_app, db
from models.student import Student
from unittest.mock import patch, MagicMock
import numpy as np
import io

@pytest.fixture(scope='module')
def test_client():
    """Create a test client for the Flask application."""
    flask_app = create_app()
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "postgresql://testuser:testpass@localhost/testdb",
        "SERVER_NAME": "localhost.test" # Add this for url_for to work
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app.test_client()
        db.session.remove()
        db.drop_all()

# Mock the AI service to isolate the web layer for testing
@patch('routes.registration.get_face_embedding_from_image')
@patch('routes.registration.add_student_to_known_faces')
def test_register_student_success(mock_add_to_cache, mock_get_embedding, test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/register' endpoint is posted to with valid data
    THEN check that a 201 status code is returned and the student is in the database
    """
    # Configure the mock to return a valid embedding
    mock_get_embedding.return_value = (np.random.rand(256), 1)
    
    data = {
        'student_code': 'STU123',
        'full_name': 'Test Student',
        'face_image': (io.BytesIO(b"someimagedata"), 'test.jpg')
    }

    response = test_client.post('/api/register', data=data, content_type='multipart/form-data')

    # Assertions
    assert response.status_code == 201
    assert response.json['message'] == "Student registered successfully!"
    
    # Check if mocks were called
    mock_get_embedding.assert_called_once()
    mock_add_to_cache.assert_called_once()

    # Check database
    student = Student.query.filter_by(student_code='STU123').first()
    assert student is not None
    assert student.full_name == 'Test Student'

def test_register_student_invalid_file_type(test_client):
    """
    GIVEN a Flask application
    WHEN the '/api/register' endpoint is posted to with an invalid file type
    THEN check that a 400 status code is returned
    """
    data = {
        'student_code': 'STU456',
        'full_name': 'Bad File Student',
        'face_image': (io.BytesIO(b"thisisnotanimage"), 'test.txt')
    }
    response = test_client.post('/api/register', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert "Invalid image format" in response.json['error']