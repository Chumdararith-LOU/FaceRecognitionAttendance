// In static/js/dashboard.js (create this new file)

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

    // Fetch data immediately when the page loads, and then every 5 seconds
    fetchAndUpdateAttendance();
    setInterval(fetchAndUpdateAttendance, 5000);
});