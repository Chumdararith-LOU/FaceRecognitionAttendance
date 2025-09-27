document.addEventListener('DOMContentLoaded', () => {
    // --- UI Element Selectors ---
    const totalStudentsEl = document.getElementById('total-students-stat');
    const presentTodayEl = document.getElementById('present-today-stat');
    const absentTodayEl = document.getElementById('absent-today-stat');
    const attendanceListEl = document.getElementById('attendance-list');
    const checkInListEl = document.getElementById('check-in-list');

    // --- Helper Functions to Update UI ---
    const updateStatsUI = (stats) => {
        totalStudentsEl.textContent = stats.total_students;
        presentTodayEl.textContent = stats.present_today;
        absentTodayEl.textContent = stats.absent_today;
    };

    const renderTodaysAttendance = (records) => {
        attendanceListEl.innerHTML = ''; // Clear the list
        if (records.length === 0) {
            attendanceListEl.innerHTML = '<li class="no-students">No students marked present yet.</li>';
            return;
        }
        records.forEach(record => {
            const listItem = document.createElement('li');
            listItem.className = 'attendance-item';
            const localTimestamp = new Date(record.timestamp + 'Z').toLocaleTimeString();
            listItem.innerHTML = `<span class="student-name">${record.full_name}</span>              <span class="timestamp">${record.timestamp}</span>`;
            attendanceListEl.appendChild(listItem);
        });
    };

    const addRecentCheckIn = (checkIn) => {
        // Remove the initial "Waiting..." message
        const waitingMessage = checkInListEl.querySelector('.loading');
        if (waitingMessage) {
            waitingMessage.remove();
        }

        const newItem = document.createElement('li');
        newItem.className = 'check-in-item';
        const localTimestamp = new Date(checkIn.timestamp + 'Z').toLocaleString();
        
        newItem.innerHTML = `
            <i class="fas fa-user-check success-icon"></i>
            <div class="check-in-details">
                <span class="student-name">${checkIn.full_name}</span>
                <span class="student-id">(${checkIn.student_code})</span>
                checked in at 
                <span class="timestamp">${checkIn.timestamp}</span>
            </div>
        `;
        
        checkInListEl.prepend(newItem);

        // Keep the list from getting too long
        while (checkInListEl.children.length > 10) {
            checkInListEl.removeChild(checkInListEl.lastChild);
        }
    };

    // --- WebSocket Connection ---
    const socket = io();

    socket.on('connect', () => {
        console.log('Connected to WebSocket server! Waiting for initial state.');
    });

    // Event for loading the dashboard for the first time
    socket.on('initial_state', (data) => {
        console.log('Initial state received:', data);
        updateStatsUI(data.stats);
        renderTodaysAttendance(data.todays_attendance);
    });

    // Event for when a new student is marked present
    socket.on('attendance_update', (data) => {
        console.log('Attendance Update Received:', data);
        addRecentCheckIn(data.new_check_in);
        updateStatsUI(data.dashboard_data.stats);
        renderTodaysAttendance(data.dashboard_data.todays_attendance);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket server.');
    });
});