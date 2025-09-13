document.addEventListener('DOMContentLoaded', function() {
    const studentTable = document.getElementById('student-table');

    if (studentTable) {
        studentTable.addEventListener('click', function(event) {
            // Check if a delete button was clicked
            if (event.target.classList.contains('delete-btn')) {
                const button = event.target;
                const studentId = button.dataset.studentId;
                const studentRow = document.getElementById(`student-row-${studentId}`);
                const studentName = studentRow.cells[1].textContent;

                // Confirm before deleting
                if (confirm(`Are you sure you want to delete ${studentName}? This action cannot be undone.`)) {
                    fetch(`/api/students/${studentId}`, {
                        method: 'DELETE',
                    })
                    .then(response => {
                        if (!response.ok) {
                            // If response is not OK, throw an error to be caught by .catch()
                            return response.json().then(err => { throw new Error(err.error || 'Server error') });
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log(data.message);
                        // Remove the student's row from the table on success
                        studentRow.remove();
                        alert(`Successfully deleted ${studentName}.`);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert(`Failed to delete student: ${error.message}`);
                    });
                }
            }
        });
    }
});