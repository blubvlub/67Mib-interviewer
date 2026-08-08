/**
 * Frontend logic for AI Interview Agent
 */

const API_BASE_URL = 'http://localhost:8000/api';
let candidatesData = [];
let currentSessionId = null;

// Timer State
let timerInterval = null;
let timeRemaining = 15 * 60; // 15 minutes standard
let isOvertime = false;
const overtimeTotal = 60; // 1 minute overtime

// DOM Elements
const candidateSelect = document.getElementById('candidate-select');
const candidateDetails = document.getElementById('candidate-details');
const startBtn = document.getElementById('start-btn');
const endBtn = document.getElementById('end-btn');
const setupPanel = document.getElementById('setup-panel');
const sessionInfo = document.getElementById('session-info');
const chatMessages = document.getElementById('chat-messages');
const chatInputArea = document.getElementById('chat-input-area');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const emptyState = document.getElementById('empty-state');
const feedbackModal = document.getElementById('feedback-modal');
const feedbackContent = document.getElementById('feedback-content');
const closeModalBtn = document.getElementById('close-modal-btn');
const newInterviewBtn = document.getElementById('new-interview-btn');
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');

// Theme initialization
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "light") {
    document.body.classList.add("light-theme");
    themeIcon.textContent = "dark_mode";
}

// Theme toggle listener
themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("light-theme");
    if (document.body.classList.contains("light-theme")) {
        localStorage.setItem("theme", "light");
        themeIcon.textContent = "dark_mode";
    } else {
        localStorage.setItem("theme", "dark");
        themeIcon.textContent = "light_mode";
    }
});

// Initialize markdown parser
marked.setOptions({
    breaks: true,
    gfm: true
});

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    
    // Enable/disable send button
    if (this.value.trim() !== '') {
        sendBtn.removeAttribute('disabled');
    } else {
        sendBtn.setAttribute('disabled', 'true');
    }
});

// Handle Enter to send (Shift+Enter for newline)
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (this.value.trim() !== '') {
            chatForm.dispatchEvent(new Event('submit'));
        }
    }
});

// Fetch candidates on load
async function fetchCandidates() {
    try {
        const response = await fetch(`${API_BASE_URL}/candidates`);
        if (!response.ok) throw new Error('Failed to fetch candidates');
        
        const data = await response.json();
        candidatesData = data.candidates || data;
        
        // Populate select
        candidateSelect.innerHTML = '<option value="">Select a candidate...</option>';
        candidatesData.forEach((c, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `${c.member.name} - ${c.member.jobRole}`;
            candidateSelect.appendChild(option);
        });
        
        candidateSelect.removeAttribute('disabled');
    } catch (error) {
        console.error('Error loading candidates:', error);
        candidateSelect.innerHTML = '<option value="">Error loading candidates</option>';
    }
}

// Handle candidate selection
candidateSelect.addEventListener('change', (e) => {
    const index = e.target.value;
    if (index === '') {
        candidateDetails.innerHTML = '';
        startBtn.setAttribute('disabled', 'true');
        return;
    }
    
    const candidate = candidatesData[index];
    const passed = candidate.missions.filter(m => m.passed).length;
    const total = candidate.missions.length;
    
    candidateDetails.innerHTML = `
        <p>Role: <span class="value">${candidate.member.jobRole}</span></p>
        <p>Experience: <span class="value">${candidate.member.yearsExperience} years</span></p>
        <p>Missions Passed: <span class="value">${passed} / ${total}</span></p>
        <p>Status: <span class="value">${candidate.member.status}</span></p>
    `;
    
    startBtn.removeAttribute('disabled');
});

// Generate a random session ID
function generateSessionId() {
    return 'sess_' + Math.random().toString(36).substring(2, 9);
}

// Progress Bar and Timer Logic
const interviewStats = document.getElementById('interview-stats');
const timerDisplay = document.getElementById('timer-display');
const statTimer = document.getElementById('interview-timer');
const progressText = document.getElementById('progress-text');
const progressFill = document.getElementById('progress-fill');

function updateProgress(progressData) {
    if (!progressData) return;
    const { current, total } = progressData;
    progressText.textContent = `${current}/${total}`;
    const percent = Math.min(100, Math.round((current / total) * 100));
    progressFill.style.width = `${percent}%`;
}

function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;
    statTimer.classList.remove('danger');
}

function startTimer() {
    stopTimer();
    timeRemaining = 15 * 60;
    isOvertime = false;
    
    interviewStats.classList.remove('hidden');
    updateTimerDisplay(timeRemaining);
    
    timerInterval = setInterval(() => {
        timeRemaining--;
        
        if (timeRemaining <= 0) {
            if (!isOvertime) {
                // Enter overtime
                isOvertime = true;
                timeRemaining = overtimeTotal;
                statTimer.classList.add('danger');
            } else {
                // Overtime exhausted, force end
                stopTimer();
                forceEndInterview();
                return;
            }
        }
        
        // Pulse red if under 2 minutes of standard time
        if (!isOvertime && timeRemaining <= 120) {
            statTimer.classList.add('danger');
        } else if (!isOvertime) {
            statTimer.classList.remove('danger');
        }
        
        updateTimerDisplay(timeRemaining);
    }, 1000);
}

function updateTimerDisplay(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    timerDisplay.textContent = `${isOvertime ? '-' : ''}${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Add message to chat UI
function addMessage(role, content, animate = true) {
    emptyState.classList.add('hidden');
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const icon = role === 'ai' ? 'memory' : 'person';
    
    msgDiv.innerHTML = `
        <div class="avatar">
            <span class="material-symbols-rounded">${icon}</span>
        </div>
        <div class="message-content">
        </div>
    `;
    
    chatMessages.appendChild(msgDiv);
    const contentDiv = msgDiv.querySelector('.message-content');
    
    const parsedContent = role === 'ai' ? marked.parse(content) : content.replace(/\n/g, '<br>');
    contentDiv.innerHTML = parsedContent;
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTyping() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai typing-message';
    msgDiv.id = 'typing-indicator';
    
    msgDiv.innerHTML = `
        <div class="avatar">
            <span class="material-symbols-rounded">memory</span>
        </div>
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hide typing indicator
function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) {
        typing.remove();
    }
}

// Start Interview
startBtn.addEventListener('click', async () => {
    const selectedIndex = candidateSelect.value;
    if (selectedIndex === '') return;
    
    const candidate = candidatesData[selectedIndex];
    currentSessionId = generateSessionId();
    
    // Update UI state
    setupPanel.classList.add('hidden');
    sessionInfo.classList.remove('hidden');
    document.getElementById('active-candidate-name').textContent = candidate.member.name;
    document.getElementById('active-candidate-role').textContent = candidate.member.jobRole;
    chatInputArea.classList.remove('hidden');
    
    chatMessages.innerHTML = '';
    emptyState.classList.add('hidden');
    showTyping();
    messageInput.setAttribute('disabled', 'true');
    sendBtn.setAttribute('disabled', 'true');
    
    try {
        const response = await fetch(`${API_BASE_URL}/interview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sessionId: currentSessionId,
                candidate: candidate
            })
        });
        
        if (!response.ok) throw new Error('API request failed');
        const data = await response.json();
        
        hideTyping();
        addMessage('ai', data.reply);
        if (data.progress) updateProgress(data.progress);
        
        startTimer(); // Start the timer on the first question!
        
        messageInput.removeAttribute('disabled');
        messageInput.focus();
    } catch (error) {
        console.error('Error starting interview:', error);
        hideTyping();
        addMessage('ai', '⚠️ Error connecting to the interview server. Please check if the backend is running.');
        resetUI();
    }
});

// Handle sending messages
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || !currentSessionId) return;
    
    // Reset input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    messageInput.setAttribute('disabled', 'true');
    sendBtn.setAttribute('disabled', 'true');
    
    addMessage('user', message);
    showTyping();
    
    try {
        const response = await fetch(`${API_BASE_URL}/interview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sessionId: currentSessionId,
                message: message
            })
        });
        
        if (!response.ok) throw new Error('API request failed');
        const data = await response.json();
        
        hideTyping();
        addMessage('ai', data.reply);
        if (data.progress) updateProgress(data.progress);
        
        if (data.done) {
            handleInterviewComplete(data.feedback);
        } else {
            messageInput.removeAttribute('disabled');
            messageInput.focus();
        }
    } catch (error) {
        console.error('Error sending message:', error);
        hideTyping();
        addMessage('ai', '⚠️ Error communicating with the server. Please try again.');
        messageInput.removeAttribute('disabled');
        messageInput.focus();
    }
});

// Render feedback and show modal
function handleInterviewComplete(feedback, isForced = false) {
    stopTimer();
    messageInput.setAttribute('disabled', 'true');
    messageInput.placeholder = "Interview completed.";
    sendBtn.setAttribute('disabled', 'true');
    endBtn.setAttribute('disabled', 'true');
    
    const modalTitle = document.querySelector('.modal-header h2');
    if (isForced) {
        modalTitle.innerHTML = '<span style="color: var(--danger);">Interview Terminated Early</span>';
    } else {
        modalTitle.textContent = 'Interview Complete';
    }
    
    if (feedback) {
        let html = `
            <div class="feedback-section">
                <h3><span class="material-symbols-rounded">assessment</span> Summary</h3>
                <p>${feedback.summary}</p>
            </div>
            <div class="feedback-section">
                <h3 class="strengths-title"><span class="material-symbols-rounded">thumb_up</span> Strengths</h3>
                <ul>${feedback.strengths.map(s => `<li>${s}</li>`).join('')}</ul>
            </div>
            <div class="feedback-section">
                <h3 class="gaps-title"><span class="material-symbols-rounded">trending_down</span> Areas for Improvement</h3>
                <ul>${feedback.gaps.map(g => `<li>${g}</li>`).join('')}</ul>
            </div>
            <div class="feedback-section">
                <h3 class="next-title"><span class="material-symbols-rounded">rocket_launch</span> Recommended Next Steps</h3>
                <ul>${feedback.next.map(n => `<li>${n}</li>`).join('')}</ul>
            </div>
        `;
        feedbackContent.innerHTML = html;
        setTimeout(() => {
            feedbackModal.classList.remove('hidden');
        }, 1500); // Show modal slightly after the final message
    }
}

// Force end interview early
endBtn.addEventListener('click', () => {
    if (!currentSessionId || !confirm("Are you sure you want to end the interview early?")) return;
    forceEndInterview();
});

async function forceEndInterview() {
    stopTimer();
    messageInput.setAttribute('disabled', 'true');
    sendBtn.setAttribute('disabled', 'true');
    addMessage('user', "I need to stop the interview here.");
    showTyping();
    
    try {
        const response = await fetch(`${API_BASE_URL}/interview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sessionId: currentSessionId,
                message: "FORCE_END_INTERVIEW"
            })
        });
        
        if (!response.ok) throw new Error('API request failed');
        const data = await response.json();
        
        hideTyping();
        addMessage('ai', data.reply);
        if (data.progress) updateProgress(data.progress);
        if (data.feedback) {
            handleInterviewComplete(data.feedback, true);
        }
    } catch (error) {
        hideTyping();
        addMessage('ai', 'Interview ended.');
        resetUI();
    }
}

function resetSidebar() {
    stopTimer();
    interviewStats.classList.add('hidden');
    progressFill.style.width = '0%';
    progressText.textContent = '0/12';
    
    setupPanel.classList.remove('hidden');
    sessionInfo.classList.add('hidden');
    chatInputArea.classList.add('hidden');
    feedbackModal.classList.add('hidden');
    endBtn.removeAttribute('disabled');
    candidateSelect.removeAttribute('disabled');
    if (candidateSelect.value !== "") {
        startBtn.removeAttribute('disabled');
    }
    currentSessionId = null;
}

function resetUI() {
    resetSidebar();
    chatMessages.innerHTML = '';
    chatMessages.appendChild(emptyState);
    emptyState.classList.remove('hidden');
}

// Modal controls
closeModalBtn.addEventListener('click', () => {
    resetSidebar();
});
newInterviewBtn.addEventListener('click', resetUI);

// Init
fetchCandidates();
