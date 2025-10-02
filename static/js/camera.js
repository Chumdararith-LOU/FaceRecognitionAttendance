document.addEventListener('DOMContentLoaded', () => {
    // Get references to all the HTML elements we'll need
    const video = document.getElementById('camera-feed');
    const canvas = document.getElementById('photo-canvas');
    const studentForm = document.getElementById('student-form');
    const statusMessage = document.getElementById('status-message');
    const submitBtn = studentForm.querySelector('button[type="submit"]'); // Get submit button

    // --- 1. ACCESS THE CAMERA ---
    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 500, height: 375 } 
            });
            video.srcObject = stream;
        } catch (err) {
            console.error("Error accessing the camera: ", err);
            statusMessage.textContent = "Error: Could not access camera. Please grant permission.";
            statusMessage.style.color = 'red';
        }
    }

    // --- 2. HANDLE FORM SUBMISSION ---
    studentForm.addEventListener('submit', (event) => {
        // Stop the default browser form submission
        event.preventDefault(); 
        
        statusMessage.textContent = 'Processing...';
        statusMessage.style.color = 'blue';
        
        // Disable submit button to prevent multiple submissions
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        // --- ADDED NEW VALIDATION BLOCK ---
        // Check if the video has enough data to capture a frame
        if (video.readyState < video.HAVE_ENOUGH_DATA) {
            alert('Camera is not ready yet. Please wait a moment for the video to fully load and try again.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Register';
            statusMessage.textContent = 'Camera not ready. Please wait.';
            statusMessage.style.color = 'red';
            return; // Stop the submission
        }
        // --- END OF NEW VALIDATION BLOCK ---

        // Get CSRF token from meta tag
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!csrfToken) {
            console.error('CSRF token not found');
            statusMessage.textContent = 'Security error. Please refresh the page and try again.';
            statusMessage.style.color = 'red';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Register';
            return;
        }

        // Set canvas dimensions to match the video feed
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // a. Capture a photo from the video feed
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // b. Convert the captured image on the canvas to a file (Blob)
        canvas.toBlob((blob) => {
            // --- ADDED VALIDATION BLOCK ---
            if (!blob) {
                alert('Could not capture image from camera. Please try again.');
                statusMessage.textContent = 'Error: Could not capture image';
                statusMessage.style.color = 'red';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Register';
                return;
            }
            // --- END OF VALIDATION BLOCK ---

            // c. Create a FormData object to send to the backend
            const formData = new FormData();
            formData.append('full_name', document.getElementById('full_name').value);
            formData.append('student_code', document.getElementById('student_code').value);
            formData.append('department', document.getElementById('department').value); // Added department field
            formData.append('image', blob, 'registration_photo.jpg');

            // d. Send the data to the /api/register endpoint
            fetch('/api/register', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => {
                // Check if the response is successful, if not, parse the error JSON
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(errorData.error || 'An unknown error occurred.');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log(data);
                statusMessage.textContent = `Success! ${data.message || 'Student registered successfully!'}`;
                statusMessage.style.color = 'green';
                studentForm.reset(); // Clear the form
                
                // Optional: Show success alert and reload
                alert('Student registered successfully!');
                window.location.reload();
            })
            .catch(error => {
                console.error('Error submitting form:', error.message);
                statusMessage.textContent = `Error: ${error.message || 'Registration failed'}`;
                statusMessage.style.color = 'red';
                
                // Display the specific error message from the server
                alert(`Registration Failed: ${error.message}`);
                
                // Re-enable submit button on error
                submitBtn.disabled = false;
                submitBtn.textContent = 'Register';
            });
        }, 'image/jpeg');
    });

    startCamera();
});