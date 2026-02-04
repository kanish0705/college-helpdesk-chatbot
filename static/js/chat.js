/*
============================================================================
AI-Powered College Helpdesk Chatbot - Chat Interface JavaScript
============================================================================

PROJECT: AI-Powered College Helpdesk Chatbot with Controlled Knowledge Scope
PURPOSE: Handle student chat interactions and profile management

============================================================================
GUARDRAILS IMPLEMENTED
============================================================================

1. CHARACTER LIMIT:
   - 500-character hard limit on input
   - Live character counter displayed (bottom-right)
   - Send button disabled when limit exceeded
   - Visual warning when approaching/exceeding limit

2. EMPTY INPUT PREVENTION:
   - Send button disabled when input is empty
   - Form validation prevents empty submissions

3. SCOPE AWARENESS:
   - Visible scope disclaimer in UI
   - All queries processed through controlled backend

============================================================================
*/

// =============================================================================
// DOM ELEMENTS
// =============================================================================

const chatArea = document.getElementById('chatArea');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const charCounter = document.getElementById('charCounter');
const charWarning = document.getElementById('charWarning');
const profileDisplay = document.getElementById('profileDisplay');
const profileText = document.getElementById('profileText');
const profileEdit = document.getElementById('profileEdit');
const profileToggle = document.getElementById('profileToggle');
const toggleText = document.getElementById('toggleText');
const deptSelect = document.getElementById('deptSelect');
const semSelect = document.getElementById('semSelect');
const secSelect = document.getElementById('secSelect');
const notificationsBanner = document.getElementById('notificationsBanner');
const notificationCount = document.getElementById('notificationCount');
const quickActions = document.getElementById('quickActions');

// =============================================================================
// CONSTANTS - GUARDRAILS
// =============================================================================

// Maximum character limit for user input - HARD LIMIT
const MAX_CHAR_LIMIT = 500;

// Warning threshold (show warning color at this percentage)
const WARNING_THRESHOLD = 0.9; // 90%

// =============================================================================
// STATE
// =============================================================================

// Student profile for personalized responses
let studentProfile = {
    dept: '',
    semester: '',
    section: '',
    deptName: ''
};

// Admin data loaded from server
let adminData = {};

// =============================================================================
// INITIALIZATION
// =============================================================================

/**
 * Initialize the chat interface when page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    // Load admin data first
    loadAdminData();
    
    // Load any saved profile from localStorage
    loadSavedProfile();
    
    // Initialize character counter
    updateCharCounter();
    
    // Focus on input field
    messageInput.focus();
});

/**
 * Load admin data from server (departments, semesters, sections)
 * Uses public API endpoint - no authentication required
 */
async function loadAdminData() {
    try {
        const response = await fetch('/api/student-data');
        if (response.ok) {
            adminData = await response.json();
            populateProfileDropdowns();
        }
    } catch (error) {
        console.error('Error loading admin data:', error);
    }
}

/**
 * Populate the profile selection dropdowns
 */
function populateProfileDropdowns() {
    // Populate departments
    if (adminData.departments && adminData.departments.length > 0) {
        deptSelect.innerHTML = '<option value="">Select Department</option>';
        adminData.departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept.id;
            option.textContent = dept.name;
            deptSelect.appendChild(option);
        });
    }
    
    // Populate semesters
    if (adminData.semesters && adminData.semesters.length > 0) {
        semSelect.innerHTML = '<option value="">Select</option>';
        adminData.semesters.forEach(sem => {
            const option = document.createElement('option');
            option.value = sem;
            option.textContent = 'Semester ' + sem;
            semSelect.appendChild(option);
        });
    }
    
    // Populate sections
    if (adminData.sections && adminData.sections.length > 0) {
        secSelect.innerHTML = '<option value="">Select</option>';
        adminData.sections.forEach(sec => {
            const option = document.createElement('option');
            option.value = sec;
            option.textContent = 'Section ' + sec;
            secSelect.appendChild(option);
        });
    }
    
    // Restore saved profile selections
    if (studentProfile.dept) {
        deptSelect.value = studentProfile.dept;
        semSelect.value = studentProfile.semester;
        secSelect.value = studentProfile.section;
    }
}

/**
 * Load saved profile from localStorage
 */
function loadSavedProfile() {
    const saved = localStorage.getItem('studentProfile');
    if (saved) {
        try {
            studentProfile = JSON.parse(saved);
            updateProfileDisplay();
            checkNotifications();
        } catch (e) {
            console.error('Error loading saved profile:', e);
        }
    }
}

// =============================================================================
// CHARACTER COUNTER - GUARDRAIL IMPLEMENTATION
// =============================================================================

/**
 * Update the character counter display
 * Implements the 500-character limit guardrail
 */
function updateCharCounter() {
    const currentLength = messageInput.value.length;
    const remaining = MAX_CHAR_LIMIT - currentLength;
    
    // Update counter text
    charCounter.textContent = `${currentLength}/${MAX_CHAR_LIMIT}`;
    
    // Update counter styling based on usage
    charCounter.classList.remove('warning', 'error');
    
    if (currentLength >= MAX_CHAR_LIMIT) {
        // At limit - show error state
        charCounter.classList.add('error');
        charWarning.style.display = 'block';
        sendButton.disabled = true;
    } else if (currentLength >= MAX_CHAR_LIMIT * WARNING_THRESHOLD) {
        // Approaching limit - show warning
        charCounter.classList.add('warning');
        charWarning.style.display = 'none';
        sendButton.disabled = false;
    } else {
        // Normal state
        charWarning.style.display = 'none';
        sendButton.disabled = currentLength === 0;
    }
}

// =============================================================================
// PROFILE MANAGEMENT
// =============================================================================

/**
 * Toggle the profile edit form visibility
 */
function toggleProfileEdit() {
    const isActive = profileEdit.classList.contains('active');
    
    if (isActive) {
        profileEdit.classList.remove('active');
        toggleText.textContent = 'Edit';
    } else {
        profileEdit.classList.add('active');
        toggleText.textContent = 'Cancel';
    }
}

/**
 * Update profile (called on dropdown change)
 */
function updateProfile() {
    // This function is called on change but doesn't save yet
    // User must click Save Profile button
}

/**
 * Save the student profile
 */
function saveProfile() {
    const dept = deptSelect.value;
    const sem = semSelect.value;
    const sec = secSelect.value;
    
    // Validate all fields are selected
    if (!dept || !sem || !sec) {
        alert('Please select Department, Semester, and Section');
        return;
    }
    
    // Find department name for display
    const deptObj = adminData.departments.find(d => d.id === dept);
    const deptName = deptObj ? deptObj.name : dept;
    
    // Update profile state
    studentProfile = {
        dept: dept,
        semester: sem,
        section: sec,
        deptName: deptName
    };
    
    // Save to localStorage for persistence
    localStorage.setItem('studentProfile', JSON.stringify(studentProfile));
    
    // Update UI
    updateProfileDisplay();
    profileEdit.classList.remove('active');
    toggleText.textContent = 'Edit';
    
    // Show quick actions now that profile is set
    quickActions.style.display = 'flex';
    
    // Check for notifications for this profile
    checkNotifications();
    
    // Show personalized welcome message
    showPersonalizedWelcome();
}

/**
 * Update the profile display text
 */
function updateProfileDisplay() {
    if (studentProfile.dept && studentProfile.semester && studentProfile.section) {
        profileText.textContent = `${studentProfile.deptName} | Semester ${studentProfile.semester} | Section ${studentProfile.section}`;
        profileText.classList.add('has-profile');
        quickActions.style.display = 'flex';
    } else {
        profileText.textContent = 'Please select your department, semester, and section';
        profileText.classList.remove('has-profile');
        quickActions.style.display = 'none';
    }
}

/**
 * Show a personalized welcome message after profile is set
 */
function showPersonalizedWelcome() {
    const welcomeMsg = `Welcome, ${studentProfile.deptName} student!

You are registered as Semester ${studentProfile.semester}, Section ${studentProfile.section}.

I can now provide you with personalized information:
- Your class timetable
- Class notifications and announcements
- Exam schedules
- Assignment deadlines
- Faculty information

What would you like to know?`;
    
    addBotMessage(welcomeMsg);
}

// =============================================================================
// NOTIFICATIONS
// =============================================================================

/**
 * Check for notifications matching the student's profile
 */
function checkNotifications() {
    if (!adminData.notifications || !studentProfile.dept) {
        notificationsBanner.style.display = 'none';
        return;
    }
    
    // Filter notifications for this student's profile
    const myNotifications = adminData.notifications.filter(notif => {
        const target = notif.target;
        
        // Check if notification targets this student
        const deptMatch = target.dept === 'all' || target.dept === studentProfile.dept;
        const semMatch = target.semester === 'all' || target.semester === studentProfile.semester;
        const secMatch = target.section === 'all' || target.section === studentProfile.section;
        
        return deptMatch && semMatch && secMatch;
    });
    
    // Show notification banner if there are notifications
    if (myNotifications.length > 0) {
        notificationCount.textContent = myNotifications.length;
        notificationsBanner.style.display = 'flex';
    } else {
        notificationsBanner.style.display = 'none';
    }
}

/**
 * Show notifications in chat when user clicks View
 */
function showNotifications() {
    if (!adminData.notifications || !studentProfile.dept) {
        addBotMessage('Please set your profile first to see notifications.');
        return;
    }
    
    // Filter notifications for this student
    const myNotifications = adminData.notifications.filter(notif => {
        const target = notif.target;
        const deptMatch = target.dept === 'all' || target.dept === studentProfile.dept;
        const semMatch = target.semester === 'all' || target.semester === studentProfile.semester;
        const secMatch = target.section === 'all' || target.section === studentProfile.section;
        return deptMatch && semMatch && secMatch;
    });
    
    if (myNotifications.length === 0) {
        addBotMessage('No notifications for you at the moment.');
        return;
    }
    
    // Build notification message
    let response = '**YOUR NOTIFICATIONS:**\n\n';
    
    myNotifications.forEach(notif => {
        const priority = notif.priority === 'high' ? '[IMPORTANT] ' : '';
        const type = notif.type.toUpperCase();
        response += `**${priority}${notif.title}** (${type})\n`;
        response += `${notif.message}\n`;
        response += `Date: ${notif.date}\n\n`;
    });
    
    addBotMessage(response);
    
    // Hide the notification banner after viewing
    notificationsBanner.style.display = 'none';
}

// =============================================================================
// QUICK ACTIONS
// =============================================================================

/**
 * Quick action button handler
 * @param {string} question - The predefined question to ask
 */
function askQuestion(question) {
    addUserMessage(question);
    sendMessage(question);
}

// =============================================================================
// MESSAGE HANDLING
// =============================================================================

/**
 * Add a user message to the chat area
 * @param {string} text - The message text
 */
function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-user';
    messageDiv.innerHTML = `
        <div class="message-label">You</div>
        <div class="message-bubble">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    chatArea.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Add a bot message to the chat area
 * @param {string} text - The message text
 */
function addBotMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-bot';
    const formattedText = formatBotResponse(text);
    messageDiv.innerHTML = `
        <div class="message-label">Helpdesk</div>
        <div class="message-bubble">
            ${formattedText}
        </div>
    `;
    chatArea.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Format bot response text to HTML
 * Handles bold text, lists, and paragraphs
 * @param {string} text - Raw response text
 * @returns {string} Formatted HTML
 */
function formatBotResponse(text) {
    const lines = text.split('\n');
    let html = '';
    let inList = false;
    let listType = 'ul';
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        
        // Skip empty lines but close any open list
        if (line === '') {
            if (inList) {
                html += `</${listType}>`;
                inList = false;
            }
            continue;
        }
        
        // Convert **text** to <strong>text</strong>
        line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        
        // Handle bullet points (- or *)
        if (line.startsWith('- ') || line.startsWith('* ')) {
            if (!inList) {
                html += '<ul>';
                inList = true;
                listType = 'ul';
            }
            html += '<li>' + line.substring(2) + '</li>';
        }
        // Handle numbered lists
        else if (/^\d+\.\s/.test(line)) {
            if (!inList) {
                html += '<ol>';
                inList = true;
                listType = 'ol';
            }
            html += '<li>' + line.replace(/^\d+\.\s/, '') + '</li>';
        }
        // Handle headings (lines ending with : and short)
        else if (line.endsWith(':') && line.length < 60) {
            if (inList) {
                html += `</${listType}>`;
                inList = false;
            }
            html += '<p class="response-heading">' + line + '</p>';
        }
        // Regular paragraph
        else {
            if (inList) {
                html += `</${listType}>`;
                inList = false;
            }
            html += '<p>' + line + '</p>';
        }
    }
    
    // Close any remaining open list
    if (inList) {
        html += `</${listType}>`;
    }
    
    return html;
}

/**
 * Scroll chat area to bottom
 */
function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// =============================================================================
// FORM SUBMISSION
// =============================================================================

/**
 * Handle form submission
 * @param {Event} event - Form submit event
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const messageText = messageInput.value.trim();
    
    // GUARDRAIL: Check for empty input
    if (!messageText) {
        return;
    }
    
    // GUARDRAIL: Check for character limit
    if (messageText.length > MAX_CHAR_LIMIT) {
        alert('Message exceeds 500 character limit. Please shorten your message.');
        return;
    }
    
    // Add user message to chat
    addUserMessage(messageText);
    
    // Clear input and reset counter
    messageInput.value = '';
    updateCharCounter();
    
    // Disable send button while processing
    sendButton.disabled = true;
    
    // Send message to server
    await sendMessage(messageText);
    
    // Re-enable send button
    sendButton.disabled = false;
    messageInput.focus();
}

/**
 * Send message to server and handle response
 * @param {string} messageText - The message to send
 */
async function sendMessage(messageText) {
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: messageText,
                profile: studentProfile
            })
        });
        
        const data = await response.json();
        
        if (data.response) {
            addBotMessage(data.response);
        } else if (data.error) {
            addBotMessage('Sorry, an error occurred. Please try again.');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        addBotMessage('Sorry, I could not connect to the server. Please try again later.');
    }
}

// =============================================================================
// EVENT LISTENERS
// =============================================================================

// Listen for input changes to update character counter
messageInput.addEventListener('input', updateCharCounter);

// Prevent form submission on Enter if over limit
messageInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        if (messageInput.value.length > MAX_CHAR_LIMIT || messageInput.value.trim() === '') {
            event.preventDefault();
        }
    }
});
