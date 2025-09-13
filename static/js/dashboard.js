// In static/js/dashboard.js (create this new file)
function updateDashboardStats() {
    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching stats:', data.error);
                return;
            }
            document.getElementById('total-students-stat').textContent = data.total_students;
            document.getElementById('present-today-stat').textContent = data.present_today;
            document.getElementById('absent-today-stat').textContent = data.absent_today;
        })
        .catch(error => console.error('Failed to fetch dashboard stats:', error));
}

document.addEventListener('DOMContentLoaded', () => {
    const attendanceList = document.getElementById('attendance-list');

    async function fetchAndUpdateAttendance() {
        try {
            const response = await fetch('/api/attendance/today');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const records = await response.json();

            // Clear the current list
            attendanceList.innerHTML = '';

            if (records.length === 0) {
                const listItem = document.createElement('li');
                listItem.textContent = 'No students marked present yet.';
                listItem.className = 'no-students';
                attendanceList.appendChild(listItem);
            } else {
                // Add each student to the list
                records.forEach(record => {
                    const listItem = document.createElement('li');
                    listItem.innerHTML = `
                        <span class="student-name">${record.full_name}</span>
                        <span class="timestamp">${record.timestamp}</span>
                    `;
                    attendanceList.appendChild(listItem);
                });
            }
        } catch (error) {
            console.error("Could not fetch attendance data:", error);
            attendanceList.innerHTML = '<li class="error">Could not load data.</li>';
        }
    }
    updateDashboardStats();

    // Fetch data immediately when the page loads, and then every 5 seconds
    fetchAndUpdateAttendance();
    setInterval(fetchAndUpdateAttendance, 10000);
});