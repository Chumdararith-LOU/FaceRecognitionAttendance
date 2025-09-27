document.addEventListener('DOMContentLoaded', () => {
    const studentTableBody = document.getElementById('student-table-body');

    if (studentTableBody) {
        studentTableBody.addEventListener('click', (event) => {
            if (event.target.classList.contains('delete-btn') || event.target.closest('.delete-btn')) {
                const button = event.target.closest('.delete-btn');
                const row = button.closest('tr');
                const studentId = row.getAttribute('data-student-id');
                const studentName = row.cells[1].textContent;

                if (confirm(`Are you sure you want to delete ${studentName}? This action cannot be undone.`)) {
                    deleteStudent(studentId, row);
                }
            }
        });
    }
});

function deleteStudent(studentId, rowElement) {
    // Get the CSRF token from the meta tag or hidden input
    let csrfToken;
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    const inputToken = document.querySelector('input[name="csrf_token"]');
    
    if (metaToken) {
        csrfToken = metaToken.getAttribute('content');
    } else if (inputToken) {
        csrfToken = inputToken.value;
    } else {
        console.error('CSRF token not found');
        alert('Security error: CSRF token missing');
        return;
    }

    fetch(`/api/students/${studentId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { 
                throw new Error(err.error || 'Server error') 
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Success:', data.message);
        // Remove the row from the table on success
        rowElement.remove();
        
        // Show success message
        showNotification(`Successfully deleted student: ${data.deleted_student}`, 'success');
        
        // If no students left, show empty message
        const remainingRows = document.querySelectorAll('#student-table-body tr');
        if (remainingRows.length === 0) {
            studentTableBody.innerHTML = '<tr><td colspan="5">No students found.</td></tr>';
        }
    })
    .catch(error => {
        console.error('Error deleting student:', error);
        showNotification(`Failed to delete student: ${error.message}`, 'error');
    });
}

// Helper function to show notifications
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existingNotification = document.querySelector('.ajax-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `ajax-notification flash-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${message}
    `;
    
    // Add styles if not already in CSS
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
        ${type === 'success' ? 'background-color: #28a745;' : 'background-color: #dc3545;'}
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Add CSS animations for notifications
if (!document.querySelector('#notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}