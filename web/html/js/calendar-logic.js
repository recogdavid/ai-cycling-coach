// Configuration
const API_BASE = "https://dabosch.fit/webhook";

// Get athlete ID from cookie
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
}

function initCalendar() {
    const athleteId = getCookie("athlete_id");

    if (!athleteId) {
        window.location.href = "/";
        return;
    }

    let currentDate = new Date();
    let currentYear = currentDate.getFullYear();
    let currentMonth = currentDate.getMonth() + 1;

    // DOM Elements
    const calendarGrid = document.getElementById('calendar-grid');
    const currentMonthEl = document.getElementById('current-month');
    const dayDetailPanel = document.getElementById('day-detail-panel');
    const dayDetailContent = document.getElementById('day-detail-content');
    const athleteInfoEl = document.getElementById('athleteInfo');

    // Initialize
    document.addEventListener('DOMContentLoaded', () => {
        loadAthleteInfo();
        loadCalendar(currentYear, currentMonth);
    });

    // Load athlete information
    async function loadAthleteInfo() {
        try {
            const url = `${API_BASE}/c29d4bfe-aad8-4fbc-b97f-447b9ac009b9/athletes/get/${athleteId}`;
            const response = await fetch(url, {
                signal: AbortSignal.timeout(10000)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const athlete = await response.json();
            if (athleteInfoEl && athlete.name) {
                athleteInfoEl.innerHTML = `Welcome back, <strong>${athlete.name}</strong>!`;
                document.title = `${athlete.name}'s Training Calendar - Dave's AI Cycling Coach`;
            }
            
        } catch (error) {
            console.error('Failed to load athlete info:', error);
            if (athleteInfoEl) {
                athleteInfoEl.innerHTML = `Welcome to Dave's AI Cycling Coach`;
            }
        }
    }

    // Mock data for testing (to be replaced with real API)
    function getMockCalendarData(year, month) {
        const daysInMonth = new Date(year, month, 0).getDate();
        const days = [];
        
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month - 1, day);
            const dayOfWeek = date.getDay();
            
            // Add some mock workouts
            let workout = null;
            if (day % 7 === 0) {
                workout = {
                    id: day,
                    type: 'endurance',
                    title: 'Long Endurance Ride',
                    duration: '2:30',
                    tss: 65,
                    color: '#4CAF50'
                };
            } else if (day % 5 === 0) {
                workout = {
                    id: day,
                    type: 'interval',
                    title: 'VO2 Max Intervals',
                    duration: '1:15',
                    tss: 85,
                    color: '#FF9800'
                };
            }
            
            days.push({
                day: day,
                day_of_week: dayOfWeek,
                workout: workout,
                has_workout: !!workout
            });
        }
        
        return { success: true, days: days };
    }

    // Load calendar for specific month
    async function loadCalendar(year, month) {
        try {
            showLoading();
            currentMonthEl.textContent = `${getMonthName(month)} ${year}`;
            
            // TODO: Replace with real API call
            // const response = await fetch(`${API_BASE}/api/v1/calendar/${athleteId}/${year}/${month}`);
            // const data = await response.json();
            
            // Using mock data for now
            const data = getMockCalendarData(year, month);
            
            if (data.success) {
                renderCalendar(data.days, year, month);
            } else {
                showError('Failed to load calendar data');
            }
        } catch (error) {
            showError(`Error: ${error.message}`);
        }
    }

    function getMonthName(month) {
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December'];
        return months[month - 1];
    }

    function showLoading() {
        if (calendarGrid) {
            calendarGrid.innerHTML = '<div class="loading">Loading calendar...</div>';
        }
    }

    function showError(message) {
        if (calendarGrid) {
            calendarGrid.innerHTML = `<div class="error">${message}</div>`;
        }
    }

    function renderCalendar(days, year, month) {
        if (!calendarGrid) return;
        
        calendarGrid.innerHTML = '';
        
        // Add day headers
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        dayNames.forEach(day => {
            const header = document.createElement('div');
            header.className = 'day-header';
            header.textContent = day;
            calendarGrid.appendChild(header);
        });
        
        // Create date object for first day of month
        const firstDay = new Date(year, month - 1, 1);
        const startingDay = firstDay.getDay();
        
        // Add empty cells for days before first day of month
        for (let i = 0; i < startingDay; i++) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'day-cell empty';
            calendarGrid.appendChild(emptyCell);
        }
        
        // Add days of the month
        days.forEach(dayData => {
            const dayCell = document.createElement('div');
            dayCell.className = 'day-cell';
            dayCell.dataset.day = dayData.day;
            
            const dayNumber = document.createElement('div');
            dayNumber.className = 'day-number';
            dayNumber.textContent = dayData.day;
            dayCell.appendChild(dayNumber);
            
            if (dayData.has_workout && dayData.workout) {
                const workoutCard = document.createElement('div');
                workoutCard.className = 'workout-card';
                workoutCard.style.borderLeftColor = dayData.workout.color;
                workoutCard.innerHTML = `
                    <strong>${dayData.workout.title}</strong>
                    <div class="workout-meta">${dayData.workout.duration} • TSS: ${dayData.workout.tss}</div>
                `;
                dayCell.appendChild(workoutCard);
            }
            
            calendarGrid.appendChild(dayCell);
        });
    }
}

// Start the calendar initialization
initCalendar();
