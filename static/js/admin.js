/**
 * ============================================================================
 * AI-Powered College Helpdesk Chatbot - Admin Dashboard JavaScript
 * ============================================================================
 * 
 * PROJECT: AI-Powered College Helpdesk Chatbot with Controlled Knowledge Scope
 * PURPOSE: Handle all admin panel operations for managing college data
 * 
 * ============================================================================
 * FUNCTIONALITY:
 * - Department management (add/remove)
 * - Semester and Section configuration
 * - Timetable management
 * - Room directory
 * - Faculty information
 * - Exam schedules
 * - Notifications management
 * - Fee structure
 * - Contact information
 * - Custom sections
 * ============================================================================
 */

// =============================================================================
// GLOBAL STATE
// =============================================================================

/**
 * Admin data object - stores all college information
 * This is synced with the server
 */
let adminData = {
    departments: [],
    semesters: [],
    sections: [],
    timetables: {},
    room_directory: {},
    notifications: [],
    faculty: {},
    exam_schedule: {},
    contact_info: {},
    fee_structure: {},
    custom_sections: [],
    period_timings: [],
    last_updated: new Date().toLocaleDateString()
};

// =============================================================================
// INITIALIZATION
// =============================================================================

/**
 * Initialize the admin dashboard when page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    loadAdminData();
});

/**
 * Load admin data from server
 * NOTE: Uses secure admin API endpoint (/secure-admin/data)
 */
async function loadAdminData() {
    try {
        const response = await fetch('/secure-admin/data');
        if (response.ok) {
            const data = await response.json();
            adminData = { ...adminData, ...data };
        } else if (response.status === 401 || response.status === 302) {
            // Unauthorized - redirect to login
            window.location.href = '/secure-admin/login';
            return;
        }
    } catch (error) {
        console.log('Loading fresh data or server unavailable');
    }
    
    // Initialize all UI sections with loaded data
    renderDepartments();
    renderSections();
    renderRooms();
    renderNotifications();
    populateDropdowns();
    renderFeeStructure();
    renderContactInfo();
    renderExamSchedule();
    renderCustomSectionsNav();
    renderFacultyDeptDropdown();
    
    // Update last updated timestamp
    document.getElementById('lastUpdated').textContent = adminData.last_updated || 'Never';
}

/**
 * Save admin data to server
 * NOTE: Uses secure admin API endpoint (/secure-admin/data)
 */
async function saveAdminData() {
    adminData.last_updated = new Date().toLocaleString();
    
    try {
        const response = await fetch('/secure-admin/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(adminData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Data saved successfully!', 'success');
            document.getElementById('lastUpdated').textContent = adminData.last_updated;
        } else {
            showStatus('Error saving data: ' + result.error, 'error');
        }
    } catch (error) {
        showStatus('Error connecting to server', 'error');
    }
}

// =============================================================================
// UI HELPERS
// =============================================================================

/**
 * Show a specific admin section
 * @param {string} sectionId - The ID of the section to show
 */
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.admin-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Add active class to clicked nav link
    const clickedLink = document.querySelector(`a[href="#${sectionId}"]`);
    if (clickedLink) {
        clickedLink.classList.add('active');
    }
}

/**
 * Show status message toast
 * @param {string} message - The message to display
 * @param {string} type - 'success' or 'error'
 */
function showStatus(message, type) {
    const statusEl = document.getElementById('statusMessage');
    statusEl.textContent = message;
    statusEl.className = 'status-toast ' + type;
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        statusEl.className = 'status-toast';
    }, 3000);
}

// =============================================================================
// DEPARTMENT MANAGEMENT
// =============================================================================

/**
 * Render the departments list
 */
function renderDepartments() {
    const container = document.getElementById('deptListContainer');
    if (!container) return;
    
    const departments = adminData.departments || [];
    
    if (departments.length === 0) {
        container.innerHTML = '<p class="empty-state">No departments added yet.</p>';
        return;
    }
    
    let html = '<ul class="dept-list">';
    departments.forEach((dept, index) => {
        html += `
            <li class="dept-item">
                <span><strong>${dept.id}</strong> - ${dept.name}</span>
                <button onclick="removeDepartment(${index})" class="btn btn-danger btn-small">Remove</button>
            </li>
        `;
    });
    html += '</ul>';
    
    container.innerHTML = html;
}

/**
 * Add a new department
 */
function addDepartment() {
    const id = document.getElementById('newDeptId').value.trim().toUpperCase();
    const name = document.getElementById('newDeptName').value.trim();
    
    if (!id || !name) {
        showStatus('Please enter both Department ID and Name', 'error');
        return;
    }
    
    // Check for duplicates
    if (adminData.departments.some(d => d.id === id)) {
        showStatus('Department with this ID already exists', 'error');
        return;
    }
    
    adminData.departments.push({ id, name });
    
    // Clear inputs
    document.getElementById('newDeptId').value = '';
    document.getElementById('newDeptName').value = '';
    
    // Update UI
    renderDepartments();
    populateDropdowns();
    saveAdminData();
}

/**
 * Remove a department
 * @param {number} index - Index of department to remove
 */
function removeDepartment(index) {
    if (confirm('Are you sure you want to remove this department?')) {
        adminData.departments.splice(index, 1);
        renderDepartments();
        populateDropdowns();
        saveAdminData();
    }
}

// =============================================================================
// SECTION MANAGEMENT
// =============================================================================

/**
 * Render the sections tags
 */
function renderSections() {
    const container = document.getElementById('sectionsDisplay');
    if (!container) return;
    
    const sections = adminData.sections || ['A', 'B', 'C', 'D'];
    
    // Initialize sections if empty
    if (adminData.sections.length === 0) {
        adminData.sections = ['A', 'B', 'C', 'D'];
    }
    
    let html = '';
    adminData.sections.forEach((sec, index) => {
        html += `
            <span class="tag">
                Section ${sec}
                <button onclick="removeSection(${index})" class="tag-remove">&times;</button>
            </span>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Add a new section
 */
function addSection() {
    const newSection = document.getElementById('newSection').value.trim().toUpperCase();
    
    if (!newSection) {
        showStatus('Please enter a section letter', 'error');
        return;
    }
    
    if (adminData.sections.includes(newSection)) {
        showStatus('This section already exists', 'error');
        return;
    }
    
    adminData.sections.push(newSection);
    document.getElementById('newSection').value = '';
    
    renderSections();
    populateDropdowns();
    saveAdminData();
}

/**
 * Remove a section
 * @param {number} index - Index of section to remove
 */
function removeSection(index) {
    if (confirm('Are you sure you want to remove this section?')) {
        adminData.sections.splice(index, 1);
        renderSections();
        populateDropdowns();
        saveAdminData();
    }
}

/**
 * Update maximum semester count
 */
function updateSemesters() {
    const maxSem = parseInt(document.getElementById('maxSemester').value);
    
    if (maxSem < 1 || maxSem > 12) {
        showStatus('Semester count must be between 1 and 12', 'error');
        return;
    }
    
    // Generate semester array
    adminData.semesters = [];
    for (let i = 1; i <= maxSem; i++) {
        adminData.semesters.push(i.toString());
    }
    
    populateDropdowns();
    saveAdminData();
    showStatus('Semesters updated successfully', 'success');
}

// =============================================================================
// DROPDOWN POPULATION
// =============================================================================

/**
 * Populate all dropdowns across the admin panel
 */
function populateDropdowns() {
    // Ensure semesters exist
    if (!adminData.semesters || adminData.semesters.length === 0) {
        adminData.semesters = ['1', '2', '3', '4', '5', '6', '7', '8'];
    }
    
    // Ensure sections exist
    if (!adminData.sections || adminData.sections.length === 0) {
        adminData.sections = ['A', 'B', 'C', 'D'];
    }
    
    // Timetable dropdowns
    populateSelect('ttDept', adminData.departments, 'id', 'name', '-- Select Department --');
    populateSelect('ttSem', adminData.semesters.map(s => ({id: s, name: `Semester ${s}`})), 'id', 'name', '-- Select Semester --');
    populateSelect('ttSec', adminData.sections.map(s => ({id: s, name: `Section ${s}`})), 'id', 'name', '-- Select Section --');
    
    // Notification dropdowns
    populateSelectWithAll('notifDept', adminData.departments, 'id', 'name', 'All Departments');
    populateSelectWithAll('notifSem', adminData.semesters.map(s => ({id: s, name: `Semester ${s}`})), 'id', 'name', 'All Semesters');
    populateSelectWithAll('notifSec', adminData.sections.map(s => ({id: s, name: `Section ${s}`})), 'id', 'name', 'All Sections');
    
    // Faculty dropdown
    populateSelect('facultyDept', adminData.departments, 'id', 'name', '-- Select Department --');
    
    // Exam target dropdown
    populateSelectWithAll('newExamTarget', adminData.departments, 'id', 'name', 'All Students');
}

/**
 * Helper to populate a select element
 */
function populateSelect(elementId, items, valueKey, textKey, placeholder) {
    const select = document.getElementById(elementId);
    if (!select) return;
    
    select.innerHTML = `<option value="">${placeholder}</option>`;
    items.forEach(item => {
        const option = document.createElement('option');
        option.value = typeof item === 'object' ? item[valueKey] : item;
        option.textContent = typeof item === 'object' ? item[textKey] : item;
        select.appendChild(option);
    });
}

/**
 * Helper to populate a select with "All" option
 */
function populateSelectWithAll(elementId, items, valueKey, textKey, allText) {
    const select = document.getElementById(elementId);
    if (!select) return;
    
    select.innerHTML = `<option value="all">${allText}</option>`;
    items.forEach(item => {
        const option = document.createElement('option');
        option.value = typeof item === 'object' ? item[valueKey] : item;
        option.textContent = typeof item === 'object' ? item[textKey] : item;
        select.appendChild(option);
    });
}

// =============================================================================
// TIMETABLE MANAGEMENT
// =============================================================================

/**
 * Load timetable for selected class
 */
function loadTimetable() {
    const dept = document.getElementById('ttDept').value;
    const sem = document.getElementById('ttSem').value;
    const sec = document.getElementById('ttSec').value;
    
    const editor = document.getElementById('timetableEditor');
    const noTimetable = document.getElementById('noTimetable');
    
    if (!dept || !sem || !sec) {
        editor.style.display = 'none';
        noTimetable.style.display = 'block';
        return;
    }
    
    editor.style.display = 'block';
    noTimetable.style.display = 'none';
    
    // Load period timings
    renderPeriodTimings();
    
    // Load schedule
    renderSchedule(dept, sem, sec);
}

/**
 * Render period timings table
 */
function renderPeriodTimings() {
    const tbody = document.getElementById('periodTimingsBody');
    if (!tbody) return;
    
    const timings = adminData.period_timings || [];
    
    if (timings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No period timings configured.</td></tr>';
        return;
    }
    
    let html = '';
    timings.forEach((timing, index) => {
        html += `
            <tr>
                <td>Period ${timing.period}</td>
                <td>${timing.start}</td>
                <td>${timing.end}</td>
                <td>
                    <button onclick="removePeriodTiming(${index})" class="btn btn-danger btn-small">Remove</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

/**
 * Add period timing
 */
function addPeriodTiming() {
    const period = document.getElementById('newPeriodNum').value;
    const start = document.getElementById('newPeriodStart').value;
    const end = document.getElementById('newPeriodEnd').value;
    
    if (!period || !start || !end) {
        showStatus('Please fill all period timing fields', 'error');
        return;
    }
    
    if (!adminData.period_timings) {
        adminData.period_timings = [];
    }
    
    adminData.period_timings.push({ period, start, end });
    adminData.period_timings.sort((a, b) => parseInt(a.period) - parseInt(b.period));
    
    // Clear inputs
    document.getElementById('newPeriodNum').value = '';
    document.getElementById('newPeriodStart').value = '';
    document.getElementById('newPeriodEnd').value = '';
    
    renderPeriodTimings();
    saveAdminData();
}

/**
 * Remove period timing
 */
function removePeriodTiming(index) {
    adminData.period_timings.splice(index, 1);
    renderPeriodTimings();
    saveAdminData();
}

/**
 * Render weekly schedule table
 */
function renderSchedule(dept, sem, sec) {
    const tbody = document.getElementById('scheduleBody');
    if (!tbody) return;
    
    const key = `${dept}_${sem}_${sec}`;
    const schedule = adminData.timetables[key] || {};
    
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    let html = '';
    days.forEach(day => {
        const daySchedule = schedule[day.toLowerCase()] || {};
        html += `
            <tr>
                <td><strong>${day}</strong></td>
                <td><input type="text" class="schedule-input" id="sched_${day}_1" value="${daySchedule.period1 || ''}" placeholder="Subject - Room"></td>
                <td><input type="text" class="schedule-input" id="sched_${day}_2" value="${daySchedule.period2 || ''}" placeholder="Subject - Room"></td>
                <td><input type="text" class="schedule-input" id="sched_${day}_3" value="${daySchedule.period3 || ''}" placeholder="Subject - Room"></td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

/**
 * Save timetable
 */
function saveTimetable() {
    const dept = document.getElementById('ttDept').value;
    const sem = document.getElementById('ttSem').value;
    const sec = document.getElementById('ttSec').value;
    
    if (!dept || !sem || !sec) {
        showStatus('Please select department, semester, and section', 'error');
        return;
    }
    
    const key = `${dept}_${sem}_${sec}`;
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    const schedule = {};
    days.forEach(day => {
        schedule[day.toLowerCase()] = {
            period1: document.getElementById(`sched_${day}_1`).value,
            period2: document.getElementById(`sched_${day}_2`).value,
            period3: document.getElementById(`sched_${day}_3`).value
        };
    });
    
    adminData.timetables[key] = schedule;
    saveAdminData();
    showStatus('Timetable saved successfully', 'success');
}

// =============================================================================
// ROOM DIRECTORY
// =============================================================================

/**
 * Render rooms table
 */
function renderRooms() {
    const tbody = document.getElementById('roomsTableBody');
    if (!tbody) return;
    
    const rooms = adminData.room_directory || {};
    const roomKeys = Object.keys(rooms);
    
    if (roomKeys.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No rooms added yet.</td></tr>';
        return;
    }
    
    let html = '';
    roomKeys.forEach(roomNum => {
        const room = rooms[roomNum];
        html += `
            <tr>
                <td><strong>${roomNum}</strong></td>
                <td>${room.floor || '-'}</td>
                <td>${room.wing || '-'}</td>
                <td>${room.type || '-'}</td>
                <td>${room.capacity || '-'}</td>
                <td>
                    <button onclick="removeRoom('${roomNum}')" class="btn btn-danger btn-small">Remove</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

/**
 * Add a room
 */
function addRoom() {
    const roomNum = document.getElementById('newRoomNum').value.trim();
    const floor = document.getElementById('newRoomFloor').value.trim();
    const wing = document.getElementById('newRoomWing').value.trim();
    const type = document.getElementById('newRoomType').value;
    const capacity = document.getElementById('newRoomCapacity').value;
    
    if (!roomNum) {
        showStatus('Please enter room number', 'error');
        return;
    }
    
    if (!adminData.room_directory) {
        adminData.room_directory = {};
    }
    
    adminData.room_directory[roomNum] = {
        floor: floor,
        wing: wing,
        type: type,
        capacity: capacity
    };
    
    // Clear inputs
    document.getElementById('newRoomNum').value = '';
    document.getElementById('newRoomFloor').value = '';
    document.getElementById('newRoomWing').value = '';
    document.getElementById('newRoomCapacity').value = '';
    
    renderRooms();
    saveAdminData();
}

/**
 * Remove a room
 */
function removeRoom(roomNum) {
    if (confirm(`Are you sure you want to remove room ${roomNum}?`)) {
        delete adminData.room_directory[roomNum];
        renderRooms();
        saveAdminData();
    }
}

/**
 * Search rooms
 */
function searchRooms() {
    const searchTerm = document.getElementById('roomSearch').value.toLowerCase();
    const tbody = document.getElementById('roomsTableBody');
    const rows = tbody.querySelectorAll('tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

// =============================================================================
// FACULTY MANAGEMENT
// =============================================================================

/**
 * Render faculty department dropdown
 */
function renderFacultyDeptDropdown() {
    populateSelect('facultyDept', adminData.departments, 'id', 'name', '-- Select Department --');
}

/**
 * Load faculty list for selected department
 */
function loadFacultyList() {
    const dept = document.getElementById('facultyDept').value;
    const container = document.getElementById('facultyList');
    
    if (!dept || !container) {
        if (container) container.innerHTML = '';
        return;
    }
    
    const faculty = adminData.faculty[dept] || [];
    
    if (faculty.length === 0) {
        container.innerHTML = `
            <div class="admin-card">
                <h3 class="card-title">Faculty Members</h3>
                <div class="card-body">
                    <p class="empty-state">No faculty added for this department.</p>
                </div>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="admin-card">
            <h3 class="card-title">Faculty Members - ${dept}</h3>
            <div class="card-body">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Subject</th>
                            <th>Cabin</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    faculty.forEach((fac, index) => {
        html += `
            <tr>
                <td>${fac.name}</td>
                <td>${fac.subject}</td>
                <td>${fac.cabin || '-'}</td>
                <td>
                    <button onclick="removeFaculty('${dept}', ${index})" class="btn btn-danger btn-small">Remove</button>
                </td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Add faculty member
 */
function addFaculty() {
    const dept = document.getElementById('facultyDept').value;
    const name = document.getElementById('newFacultyName').value.trim();
    const subject = document.getElementById('newFacultySubject').value.trim();
    const cabin = document.getElementById('newFacultyCabin').value.trim();
    
    if (!dept) {
        showStatus('Please select a department first', 'error');
        return;
    }
    
    if (!name || !subject) {
        showStatus('Please enter faculty name and subject', 'error');
        return;
    }
    
    if (!adminData.faculty[dept]) {
        adminData.faculty[dept] = [];
    }
    
    adminData.faculty[dept].push({ name, subject, cabin });
    
    // Clear inputs
    document.getElementById('newFacultyName').value = '';
    document.getElementById('newFacultySubject').value = '';
    document.getElementById('newFacultyCabin').value = '';
    
    loadFacultyList();
    saveAdminData();
}

/**
 * Remove faculty member
 */
function removeFaculty(dept, index) {
    if (confirm('Are you sure you want to remove this faculty member?')) {
        adminData.faculty[dept].splice(index, 1);
        loadFacultyList();
        saveAdminData();
    }
}

// =============================================================================
// EXAM SCHEDULE
// =============================================================================

/**
 * Render exam schedule
 */
function renderExamSchedule() {
    const schedule = adminData.exam_schedule || {};
    
    // Populate form fields
    if (document.getElementById('examInternal')) {
        document.getElementById('examInternal').value = schedule.internal || '';
    }
    if (document.getElementById('examOdd')) {
        document.getElementById('examOdd').value = schedule.odd_semester || '';
    }
    if (document.getElementById('examEven')) {
        document.getElementById('examEven').value = schedule.even_semester || '';
    }
    
    // Render upcoming exams
    const container = document.getElementById('upcomingExamsList');
    if (!container) return;
    
    const upcoming = schedule.upcoming || [];
    
    if (upcoming.length === 0) {
        container.innerHTML = '<p class="empty-state">No upcoming exams scheduled.</p>';
        return;
    }
    
    let html = '<ul class="exam-list">';
    upcoming.forEach((exam, index) => {
        html += `
            <li>
                <span><strong>${exam.name}</strong> - ${exam.date} (${exam.target || 'All'})</span>
                <button onclick="removeUpcomingExam(${index})" class="btn btn-danger btn-small">Remove</button>
            </li>
        `;
    });
    html += '</ul>';
    
    container.innerHTML = html;
}

/**
 * Add upcoming exam
 */
function addUpcomingExam() {
    const name = document.getElementById('newExamName').value.trim();
    const date = document.getElementById('newExamDate').value;
    const target = document.getElementById('newExamTarget').value;
    
    if (!name || !date) {
        showStatus('Please enter exam name and date', 'error');
        return;
    }
    
    if (!adminData.exam_schedule.upcoming) {
        adminData.exam_schedule.upcoming = [];
    }
    
    adminData.exam_schedule.upcoming.push({ name, date, target });
    
    // Clear inputs
    document.getElementById('newExamName').value = '';
    document.getElementById('newExamDate').value = '';
    
    renderExamSchedule();
    saveAdminData();
}

/**
 * Remove upcoming exam
 */
function removeUpcomingExam(index) {
    adminData.exam_schedule.upcoming.splice(index, 1);
    renderExamSchedule();
    saveAdminData();
}

/**
 * Save exam schedule
 */
function saveExamSchedule() {
    adminData.exam_schedule = {
        internal: document.getElementById('examInternal').value,
        odd_semester: document.getElementById('examOdd').value,
        even_semester: document.getElementById('examEven').value,
        upcoming: adminData.exam_schedule.upcoming || []
    };
    
    saveAdminData();
    showStatus('Exam schedule saved successfully', 'success');
}

// =============================================================================
// NOTIFICATIONS
// =============================================================================

/**
 * Render notifications list
 */
function renderNotifications() {
    const container = document.getElementById('notificationsList');
    if (!container) return;
    
    const notifications = adminData.notifications || [];
    
    if (notifications.length === 0) {
        container.innerHTML = '<p class="empty-state">No notifications posted yet.</p>';
        return;
    }
    
    let html = '';
    notifications.forEach((notif, index) => {
        const priorityClass = notif.priority === 'high' ? 'priority-high' : '';
        const target = notif.target || {};
        const targetText = `Dept: ${target.dept || 'All'} | Sem: ${target.semester || 'All'} | Sec: ${target.section || 'All'}`;
        
        html += `
            <div class="notification-item ${priorityClass}">
                <div class="notif-header">
                    <strong>${notif.title}</strong>
                    <span class="notif-type">${notif.type || 'general'}</span>
                    <span class="notif-date">${notif.date || ''}</span>
                </div>
                <p>${notif.message}</p>
                <div class="notif-footer">
                    <span class="notif-target">Target: ${targetText}</span>
                    <button onclick="removeNotification(${index})" class="btn btn-danger btn-small">Remove</button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Add notification
 */
function addNotification() {
    const title = document.getElementById('notifTitle').value.trim();
    const message = document.getElementById('notifMessage').value.trim();
    const type = document.getElementById('notifType').value;
    const priority = document.getElementById('notifPriority').value;
    const dept = document.getElementById('notifDept').value;
    const sem = document.getElementById('notifSem').value;
    const sec = document.getElementById('notifSec').value;
    
    if (!title || !message) {
        showStatus('Please enter title and message', 'error');
        return;
    }
    
    if (!adminData.notifications) {
        adminData.notifications = [];
    }
    
    adminData.notifications.unshift({
        title: title,
        message: message,
        type: type,
        priority: priority,
        date: new Date().toLocaleDateString(),
        target: {
            dept: dept,
            semester: sem,
            section: sec
        }
    });
    
    // Clear inputs
    document.getElementById('notifTitle').value = '';
    document.getElementById('notifMessage').value = '';
    
    renderNotifications();
    saveAdminData();
    showStatus('Notification posted successfully', 'success');
}

/**
 * Remove notification
 */
function removeNotification(index) {
    if (confirm('Are you sure you want to remove this notification?')) {
        adminData.notifications.splice(index, 1);
        renderNotifications();
        saveAdminData();
    }
}

// =============================================================================
// FEE STRUCTURE
// =============================================================================

/**
 * Render fee structure table
 */
function renderFeeStructure() {
    const tbody = document.getElementById('feeTableBody');
    if (!tbody) return;
    
    const fees = adminData.fee_structure || {};
    const courses = Object.keys(fees);
    
    if (courses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="empty-state">No fee information added.</td></tr>';
        return;
    }
    
    let html = '';
    courses.forEach(course => {
        html += `
            <tr>
                <td>${course}</td>
                <td>${fees[course]}</td>
                <td>
                    <button onclick="removeFee('${course}')" class="btn btn-danger btn-small">Remove</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

/**
 * Save fee entry
 */
function saveFee() {
    const course = document.getElementById('feeCourse').value.trim();
    const amount = document.getElementById('feeAmount').value.trim();
    
    if (!course || !amount) {
        showStatus('Please enter course name and fee amount', 'error');
        return;
    }
    
    if (!adminData.fee_structure) {
        adminData.fee_structure = {};
    }
    
    adminData.fee_structure[course] = amount;
    
    // Clear inputs
    document.getElementById('feeCourse').value = '';
    document.getElementById('feeAmount').value = '';
    
    renderFeeStructure();
    saveAdminData();
}

/**
 * Remove fee entry
 */
function removeFee(course) {
    if (confirm(`Remove fee for ${course}?`)) {
        delete adminData.fee_structure[course];
        renderFeeStructure();
        saveAdminData();
    }
}

// =============================================================================
// CONTACT INFO
// =============================================================================

/**
 * Render contact information
 */
function renderContactInfo() {
    const contact = adminData.contact_info || {};
    
    const fields = {
        'contactAddress': 'address',
        'contactPhone': 'phone',
        'contactEmail': 'email',
        'contactWebsite': 'website',
        'contactAdmissions': 'admissions_email',
        'contactExams': 'exams_email',
        'contactPlacements': 'placements_email'
    };
    
    Object.keys(fields).forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            element.value = contact[fields[elementId]] || '';
        }
    });
}

/**
 * Save contact information
 */
function saveContactInfo() {
    adminData.contact_info = {
        address: document.getElementById('contactAddress').value,
        phone: document.getElementById('contactPhone').value,
        email: document.getElementById('contactEmail').value,
        website: document.getElementById('contactWebsite').value,
        admissions_email: document.getElementById('contactAdmissions').value,
        exams_email: document.getElementById('contactExams').value,
        placements_email: document.getElementById('contactPlacements').value
    };
    
    saveAdminData();
    showStatus('Contact information saved successfully', 'success');
}

// =============================================================================
// CUSTOM SECTIONS
// =============================================================================

/**
 * Render custom sections navigation
 */
function renderCustomSectionsNav() {
    const container = document.getElementById('customSectionsNav');
    if (!container) return;
    
    const sections = adminData.custom_sections || [];
    
    let html = '';
    sections.forEach((section, index) => {
        const sectionId = `custom-${index}`;
        html += `
            <li class="nav-item">
                <a href="#${sectionId}" class="nav-link" onclick="showCustomSection(${index})">
                    <span class="nav-icon">*</span>
                    ${section.name}
                </a>
            </li>
        `;
    });
    
    container.innerHTML = html;
    
    // Also render the custom sections content
    renderCustomSectionsContent();
}

/**
 * Render custom sections content areas
 */
function renderCustomSectionsContent() {
    const container = document.getElementById('customSectionsContainer');
    if (!container) return;
    
    const sections = adminData.custom_sections || [];
    
    let html = '';
    sections.forEach((section, index) => {
        const sectionId = `custom-${index}`;
        const keywords = section.keywords ? section.keywords.split(',').map(k => `<span>${k.trim()}</span>`).join('') : '';
        
        html += `
            <section id="${sectionId}" class="admin-section">
                <div class="section-header">
                    <h2>${section.name}</h2>
                    <p class="section-desc">Custom section content</p>
                </div>
                
                <div class="admin-card">
                    <h3 class="card-title">Section Details</h3>
                    <div class="card-body">
                        <div class="custom-section-card">
                            <h4>${section.name}</h4>
                            <div class="keywords">${keywords}</div>
                            <div class="content-preview">${section.content || ''}</div>
                            <div class="card-actions">
                                <button onclick="removeCustomSection(${index})" class="btn btn-danger btn-small">Remove Section</button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Show custom section
 */
function showCustomSection(index) {
    showSection(`custom-${index}`);
}

/**
 * Add custom section
 */
function addCustomSection() {
    const name = document.getElementById('newSectionName').value.trim();
    const keywords = document.getElementById('newSectionKeywords').value.trim();
    const content = document.getElementById('newSectionContent').value.trim();
    
    if (!name || !content) {
        showStatus('Please enter section name and content', 'error');
        return;
    }
    
    if (!adminData.custom_sections) {
        adminData.custom_sections = [];
    }
    
    adminData.custom_sections.push({
        name: name,
        keywords: keywords,
        content: content
    });
    
    // Clear inputs
    document.getElementById('newSectionName').value = '';
    document.getElementById('newSectionKeywords').value = '';
    document.getElementById('newSectionContent').value = '';
    
    renderCustomSectionsNav();
    saveAdminData();
    showStatus('Custom section created successfully', 'success');
}

/**
 * Remove custom section
 */
function removeCustomSection(index) {
    if (confirm('Are you sure you want to remove this custom section?')) {
        adminData.custom_sections.splice(index, 1);
        renderCustomSectionsNav();
        saveAdminData();
        showSection('departments'); // Go back to departments
    }
}
