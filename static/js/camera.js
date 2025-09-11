// In static/js/camera.js

document.addEventListener('DOMContentLoaded', () => {
    // Get references to all the HTML elements we'll need
    const video = document.getElementById('camera-feed');
    const canvas = document.getElementById('photo-canvas');
    const studentForm = document.getElementById('student-form');
    const statusMessage = document.getElementById('status-message');

    // --- 1. ACCESS THE CAMERA ---
    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 300, height: 375 } 
            });
            video.srcObject = stream;
        } catch (err) {
            console.error("Error accessing the camera: ", err);
            statusMessage.textContent = "Error: Could not access camera. Please grant permission.";
            statusMessage.style.color = 'red';
        }
    }

    // --- 2. HANDLE FORM SUBMISSION ---
    studentForm.addEventListener('submit', async (event) => {
        // Stop the default browser form submission
        event.preventDefault(); 
        
        statusMessage.textContent = 'Processing...';
        statusMessage.style.color = 'blue';

        // a. Capture a photo from the video feed
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // b. Convert the captured image on the canvas to a file (Blob)
        canvas.toBlob(async (blob) => {
            // c. Create a FormData object to send to the backend
            const formData = new FormData();
            formData.append('full_name', document.getElementById('full_name').value);
            formData.append('student_code', document.getElementById('student_code').value);
            formData.append('image', blob, 'registration_photo.jpg');

            // d. Send the data to the /api/register endpoint
            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    body: formData // No headers needed, browser sets it for FormData
                });

                const result = await response.json();

                if (response.ok) {
                    statusMessage.textContent = `Success! ${result.message}`;
                    statusMessage.style.color = 'green';
                    studentForm.reset(); // Clear the form
                } else {
                    statusMessage.textContent = `Error: ${result.error}`;
                    statusMessage.style.color = 'red';
                }
            } catch (error) {
                console.error('Error submitting form:', error);
                statusMessage.textContent = 'A network error occurred. Please try again.';
                statusMessage.style.color = 'red';
            }
        }, 'image/jpeg');
    });

    // Start the camera as soon as the page loads
    startCamera();
});