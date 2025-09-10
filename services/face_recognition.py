# In services/face_recognition.py (create this new file)

import face_recognition
import numpy as np
from typing import Optional

def get_face_embedding_from_image(image_file) -> Optional[np.ndarray]:
    """
    Finds a single face in an image and returns its 128D embedding.

    Args:
        image_file: A file-like object from the request.

    Returns:
        A numpy array of the face embedding, or None if no single face is found.
    """
    try:
        # Load the image file
        image = face_recognition.load_image_file(image_file)

        # Find face locations in the image
        face_locations = face_recognition.face_locations(image)

        # --- Business Logic: Ensure exactly one face is in the registration photo ---
        if len(face_locations) != 1:
            print(f"Error: Found {len(face_locations)} faces. Expected 1.")
            return None

        # Generate the face encoding (the 128D embedding)
        face_encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
        
        return face_encodings[0]

    except Exception as e:
        print(f"An error occurred in face recognition service: {e}")
        return None