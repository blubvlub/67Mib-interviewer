/**
 * Frontend logic for AI Interview Agent
 */

const API_BASE_URL = 'http://localhost:8000/api';
let candidatesData = [];
let currentSessionId = null;

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

// Add message to chat UI
function addMessage(role, content, animate = true) {
    emptyState.classList.add('hidden');
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const icon = role === 'ai' ? 'smart_toy' : 'person';
    
    // Parse markdown if it's the AI's message
    const parsedContent = role === 'ai' ? marked.parse(content) : content.replace(/\n/g, '<br>');
    
    msgDiv.innerHTML = `
        <div class="avatar">
            <span class="material-symbols-rounded">${icon}</span>
        </div>
        <div class="message-content">
            ${parsedContent}
        </div>
    `;
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTyping() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai typing-message';
    msgDiv.id = 'typing-indicator';
    
    msgDiv.innerHTML = `
        <div class="avatar">
            <span class="material-symbols-rounded">smart_toy</span>
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
function handleInterviewComplete(feedback) {
    messageInput.setAttribute('disabled', 'true');
    messageInput.placeholder = "Interview completed.";
    sendBtn.setAttribute('disabled', 'true');
    endBtn.setAttribute('disabled', 'true');
    
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
endBtn.addEventListener('click', async () => {
    if (!currentSessionId || !confirm("Are you sure you want to end the interview early?")) return;
    
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
        if (data.feedback) {
            handleInterviewComplete(data.feedback);
        }
    } catch (error) {
        hideTyping();
        addMessage('ai', 'Interview ended.');
        resetUI();
    }
});

function resetUI() {
    setupPanel.classList.remove('hidden');
    sessionInfo.classList.add('hidden');
    chatInputArea.classList.add('hidden');
    feedbackModal.classList.add('hidden');
    endBtn.removeAttribute('disabled');
    currentSessionId = null;
    
    chatMessages.innerHTML = '';
    chatMessages.appendChild(emptyState);
    emptyState.classList.remove('hidden');
}

// Modal controls
closeModalBtn.addEventListener('click', () => {
    feedbackModal.classList.add('hidden');
});

newInterviewBtn.addEventListener('click', () => {
    resetUI();
});

// Init
fetchCandidates();
