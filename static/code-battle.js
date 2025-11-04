// Code Battle Client-Side Logic
// ============================================

// Global Variables
let socket;
let currentMatchId = null;
let currentChallengeIndex = 0;
let totalChallenges = 5;
let currentChallenge = null;
let timerInterval = null;
let timeRemaining = 300; // 5 minutes default
let timerEndTime = null; // Server-synchronized end time
let opponentName = 'Opponent';

// CodeMirror Editors
let htmlEditor, cssEditor, jsEditor;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    initializeEditors();
    joinQueue();
});

// ============================================
// CODEMIRROR INITIALIZATION
// ============================================

function initializeEditors() {
    // HTML Editor
    htmlEditor = CodeMirror(document.getElementById('htmlEditor'), {
        mode: 'htmlmixed',
        theme: 'dracula',
        lineNumbers: true,
        autoCloseTags: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        indentUnit: 2,
        tabSize: 2,
        lineWrapping: true,
        extraKeys: {
            'Ctrl-Space': 'autocomplete',
            'Tab': function(cm) {
                if (cm.somethingSelected()) {
                    cm.indentSelection('add');
                } else {
                    cm.replaceSelection('  ', 'end');
                }
            }
        }
    });

    // CSS Editor
    cssEditor = CodeMirror(document.getElementById('cssEditor'), {
        mode: 'css',
        theme: 'dracula',
        lineNumbers: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        indentUnit: 2,
        tabSize: 2,
        lineWrapping: true,
        extraKeys: {
            'Ctrl-Space': 'autocomplete',
            'Tab': function(cm) {
                if (cm.somethingSelected()) {
                    cm.indentSelection('add');
                } else {
                    cm.replaceSelection('  ', 'end');
                }
            }
        }
    });

    // JavaScript Editor
    jsEditor = CodeMirror(document.getElementById('jsEditor'), {
        mode: 'javascript',
        theme: 'dracula',
        lineNumbers: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        indentUnit: 2,
        tabSize: 2,
        lineWrapping: true,
        extraKeys: {
            'Ctrl-Space': 'autocomplete',
            'Tab': function(cm) {
                if (cm.somethingSelected()) {
                    cm.indentSelection('add');
                } else {
                    cm.replaceSelection('  ', 'end');
                }
            }
        }
    });

    // Add input event listeners for auto-trigger hints
    htmlEditor.on('inputRead', function(cm, change) {
        if (!cm.state.completionActive && change.text[0].match(/[a-zA-Z<]/)) {
            CodeMirror.commands.autocomplete(cm, null, {completeSingle: false});
        }
    });

    cssEditor.on('inputRead', function(cm, change) {
        if (!cm.state.completionActive && change.text[0].match(/[a-zA-Z-]/)) {
            CodeMirror.commands.autocomplete(cm, null, {completeSingle: false});
        }
    });

    jsEditor.on('inputRead', function(cm, change) {
        if (!cm.state.completionActive && change.text[0].match(/[a-zA-Z.]/)) {
            CodeMirror.commands.autocomplete(cm, null, {completeSingle: false});
        }
    });

    // Add change listeners for live preview updates
    let previewTimeout;
    function schedulePreviewUpdate() {
        clearTimeout(previewTimeout);
        previewTimeout = setTimeout(updatePreview, 500); // Debounce 500ms
    }

    htmlEditor.on('change', schedulePreviewUpdate);
    cssEditor.on('change', schedulePreviewUpdate);
    jsEditor.on('change', schedulePreviewUpdate);

    console.log('Editors initialized with autocomplete and live preview');
}

// ============================================
// SOCKET.IO CONNECTION
// ============================================

function initializeSocket() {
    socket = io();

    // Connection events
    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        showError('Connection lost. Please refresh the page.');
    });

    // Queue events
    socket.on('queue_status', handleQueueStatus);
    socket.on('match_found', handleMatchFound);

    // Battle events
    socket.on('code_battle_start', handleBattleStart);
    socket.on('challenge_result', handleChallengeResult);
    socket.on('opponent_progress', handleOpponentProgress);
    socket.on('next_challenge', handleNextChallenge);
    socket.on('no_more_challenges', handleNoMoreChallenges);
    socket.on('code_battle_end', handleBattleEnd);

    // Error handling
    socket.on('error', (data) => {
        console.error('Socket error:', data);
        showError(data.message || 'An error occurred');
    });
}

// ============================================
// MATCHMAKING FUNCTIONS
// ============================================

function joinQueue() {
    console.log('Joining queue...');
    socket.emit('code_battle_queue', {});
    document.getElementById('queueStatus').textContent = 'Searching for opponent...';
}

function cancelQueue() {
    console.log('Canceling queue...');
    if (socket && socket.connected) {
        socket.emit('cancel_code_queue');
    }
    window.location.href = '/user/competitive';
}

function leaveBattle() {
    if (confirm('Are you sure you want to leave? This will count as a loss.')) {
        console.log('Leaving battle...');
        if (socket && socket.connected) {
            socket.emit('leave_code_battle', { match_id: currentMatchId });
        }
        window.location.href = '/user/competitive';
    }
}

function handleQueueStatus(data) {
    console.log('Queue status:', data);
    const status = data.status;
    
    if (status === 'queued') {
        document.getElementById('queueStatus').textContent = 
            `Waiting for opponent...`;
    } else if (status === 'cancelled') {
        document.getElementById('queueStatus').textContent = 'Queue cancelled';
    }
}

function handleMatchFound(data) {
    console.log('Match found:', data);
    currentMatchId = data.match_id;
    opponentName = data.opponent || 'Opponent';
    
    // Show match found animation
    const animation = document.getElementById('matchFoundAnimation');
    document.getElementById('player1Name').textContent = data.your_name || 'You';
    document.getElementById('player1Rating').textContent = data.your_rating || '1000';
    document.getElementById('player2Name').textContent = opponentName;
    document.getElementById('player2Rating').textContent = data.opponent_rating || '1000';
    
    animation.classList.add('active');
    
    // Hide animation after 3 seconds
    setTimeout(() => {
        animation.classList.remove('active');
    }, 3000);
    
    // Transition will happen when battle starts
}

// ============================================
// BATTLE FUNCTIONS
// ============================================

function handleBattleStart(data) {
    console.log('Battle starting:', data);
    
    currentMatchId = data.match_id;
    totalChallenges = data.total_challenges;
    currentChallengeIndex = 0;
    
    // Hide queue, show battle
    document.getElementById('queueScreen').classList.add('hidden');
    document.getElementById('battleScreen').style.display = 'flex';
    
    // Load first challenge
    loadChallenge(data.challenge);
    
    // Start timer for ENTIRE battle (6 minutes total for 5 challenges)
    startTimer(360); // 6 minutes = 360 seconds
    
    // Update opponent name
    document.getElementById('opponentName').textContent = opponentName;
}

function loadChallenge(challenge) {
    console.log('Loading challenge:', challenge);
    currentChallenge = challenge;
    
    // Update header
    document.getElementById('challengeTitle').textContent = challenge.title;
    document.getElementById('challengeProgress').textContent = 
        `${currentChallengeIndex + 1}/${totalChallenges}`;
    
    // Update difficulty badge
    const difficultyBadge = document.getElementById('difficultyBadge');
    difficultyBadge.textContent = challenge.difficulty.toUpperCase();
    difficultyBadge.className = `meta-badge difficulty-${challenge.difficulty}`;
    
    // Update points
    document.getElementById('pointsValue').textContent = challenge.points;
    
    // Update description
    const descContainer = document.getElementById('challengeDescription');
    descContainer.querySelector('p').textContent = challenge.description;
    
    // Update hint
    const hintSection = document.getElementById('hintSection');
    const hintText = document.getElementById('hintText');
    const showHintBtn = document.getElementById('showHintBtn');
    
    if (challenge.hint) {
        hintText.textContent = challenge.hint;
        showHintBtn.classList.remove('hidden');
        hintSection.classList.add('hidden');
    } else {
        showHintBtn.classList.add('hidden');
        hintSection.classList.add('hidden');
    }
    
    // Enable/disable tabs based on requirements
    const htmlTab = document.getElementById('htmlTab');
    const cssTab = document.getElementById('cssTab');
    const jsTab = document.getElementById('jsTab');
    
    htmlTab.disabled = !challenge.requires_html;
    cssTab.disabled = !challenge.requires_css;
    jsTab.disabled = !challenge.requires_js;
    
    // Load starter code
    const starterCode = challenge.starter_code || {};
    htmlEditor.setValue(starterCode.html || '');
    cssEditor.setValue(starterCode.css || '');
    jsEditor.setValue(starterCode.javascript || starterCode.js || '');
    
    // Switch to first enabled tab
    if (challenge.requires_html) {
        switchTab('html');
    } else if (challenge.requires_css) {
        switchTab('css');
    } else {
        switchTab('js');
    }
    
    // Clear test results
    document.getElementById('testResults').innerHTML = `
        <h4><i class="fas fa-vial"></i> Test Results</h4>
        <p style="color: var(--text-secondary);">Submit your code to see results...</p>
    `;
    
    // Hide next button, show submit
    document.getElementById('submitBtn').classList.remove('hidden');
    document.getElementById('nextBtn').classList.add('hidden');
    
    // Enable submit button
    document.getElementById('submitBtn').disabled = false;
    
    // Update preview
    updatePreview();
}

function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.editor-tab').forEach(t => t.classList.remove('active'));
    document.getElementById(tab + 'Tab').classList.add('active');
    
    // Update editor visibility
    document.querySelectorAll('.code-editor').forEach(e => e.classList.remove('active'));
    document.getElementById(tab + 'Editor').classList.add('active');
    
    // Refresh CodeMirror
    if (tab === 'html') htmlEditor.refresh();
    if (tab === 'css') cssEditor.refresh();
    if (tab === 'js') jsEditor.refresh();
}

function showHint() {
    document.getElementById('hintSection').classList.remove('hidden');
    document.getElementById('showHintBtn').classList.add('hidden');
}

function updatePreview() {
    const html = htmlEditor.getValue();
    const css = cssEditor.getValue();
    const js = jsEditor.getValue();
    
    const iframe = document.getElementById('previewFrame');
    
    const content = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>${css}</style>
        </head>
        <body>
            ${html}
            <script>
                try {
                    ${js}
                } catch (e) {
                    console.error('JavaScript error:', e);
                }
            <\/script>
        </body>
        </html>
    `;
    
    // Use srcdoc to avoid cross-origin issues
    iframe.srcdoc = content;
}

function submitCode() {
    console.log('Submitting code...');
    
    // Disable submit button
    document.getElementById('submitBtn').disabled = true;
    document.getElementById('submitBtn').innerHTML = 
        '<i class="fas fa-spinner fa-spin"></i> Validating...';
    
    const code = {
        html: htmlEditor.getValue(),
        css: cssEditor.getValue(),
        javascript: jsEditor.getValue()
    };
    
    socket.emit('submit_code_challenge', {
        match_id: currentMatchId,
        challenge_index: currentChallengeIndex,
        code: code
    });
}

function handleChallengeResult(data) {
    console.log('Challenge result:', data);
    
    // Re-enable submit button
    document.getElementById('submitBtn').disabled = false;
    document.getElementById('submitBtn').innerHTML = 
        '<i class="fas fa-check"></i> Submit Solution';
    
    // Update score
    document.getElementById('yourScore').textContent = data.total_score;
    
    // Display test results
    displayTestResults(data.test_results, data.passed);
    
    // Show next button if passed and not last challenge
    if (data.passed && currentChallengeIndex < totalChallenges - 1) {
        document.getElementById('submitBtn').classList.add('hidden');
        document.getElementById('nextBtn').classList.remove('hidden');
    }
    
    // Show notification
    if (data.passed) {
        showNotification('success', 
            `✅ Correct! +${data.points_earned} points`, 3000);
    } else {
        showNotification('error', 
            '❌ Some tests failed. Try again!', 3000);
    }
}

function displayTestResults(results, passed) {
    const container = document.getElementById('testResults');
    
    let html = `<h4><i class="fas fa-vial"></i> Test Results</h4>`;
    
    if (!results || results.length === 0) {
        html += `<p style="color: var(--text-secondary);">No test results available</p>`;
    } else {
        results.forEach(test => {
            const status = test.passed ? 'passed' : 'failed';
            const icon = test.passed ? 'fa-check-circle' : 'fa-times-circle';
            
            // Format expected/actual values properly
            const formatValue = (val) => {
                if (val === null || val === undefined) return 'N/A';
                if (typeof val === 'object') {
                    // For CSS tests: {property: 'display', value: 'flex'}
                    if (val.property && val.value !== undefined) {
                        return `${val.property}: ${val.value}`;
                    }
                    // For other objects, stringify nicely
                    return JSON.stringify(val, null, 2);
                }
                return String(val);
            };
            
            html += `
                <div class="test-case ${status}">
                    <div class="test-case-header">
                        <span>Test ${test.test_number} (${test.type})</span>
                        <i class="fas ${icon} test-icon ${status}"></i>
                    </div>
                    ${test.error ? `<div style="color: var(--danger-color); font-size: 0.9rem;">Error: ${test.error}</div>` : ''}
                    ${!test.passed ? `
                        <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                            ${test.type === 'js' && test.expected !== undefined ? `
                                <div>Expected: <code>${formatValue(test.expected)}</code></div>
                            ` : ''}
                            <div>Got: <code>${formatValue(test.actual)}</code></div>
                        </div>
                    ` : ''}
                </div>
            `;
        });
    }
    
    container.innerHTML = html;
}

function handleOpponentProgress(data) {
    console.log('Opponent progress:', data);
    
    // Update opponent score
    document.getElementById('opponentScore').textContent = data.score;
    
    // Update progress bar
    const completed = data.completed || 0;
    const percentage = (completed / totalChallenges) * 100;
    document.getElementById('opponentProgressBar').style.width = percentage + '%';
    document.getElementById('opponentCompleted').textContent = 
        `${completed}/${totalChallenges} completed`;
}

function nextChallenge() {
    console.log('Requesting next challenge...');
    currentChallengeIndex++;
    
    socket.emit('request_next_challenge', {
        match_id: currentMatchId
    });
}

function handleNextChallenge(data) {
    console.log('Next challenge received:', data);
    currentChallengeIndex = data.challenge_index;
    loadChallenge(data.challenge);
    
    // Don't reset timer - it continues for entire battle
}

function handleNoMoreChallenges(data) {
    console.log('No more challenges:', data);
    showNotification('info', 'All challenges completed! Waiting for opponent...', 5000);
    document.getElementById('nextBtn').classList.add('hidden');
}

function handleBattleEnd(data) {
    console.log('Battle ended:', data);
    
    // Stop timer
    stopTimer();
    
    // Hide battle screen
    document.getElementById('battleScreen').style.display = 'none';
    
    // Show results
    displayResults(data);
}

// ============================================
// TIMER FUNCTIONS
// ============================================

function startTimer(seconds) {
    stopTimer(); // Clear any existing timer
    
    // Calculate end time based on server time (use current time + seconds)
    timerEndTime = Date.now() + (seconds * 1000);
    
    // Update immediately
    updateTimerDisplay();
    
    // Update every 100ms for smooth countdown even when tab is inactive
    timerInterval = setInterval(() => {
        updateTimerDisplay();
        
        if (timeRemaining <= 0) {
            stopTimer();
            showNotification('warning', 'Time is up!', 3000);
        }
    }, 100);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    timerEndTime = null;
}

function updateTimerDisplay() {
    // Calculate remaining time based on end time (immune to tab throttling)
    if (timerEndTime) {
        const now = Date.now();
        timeRemaining = Math.max(0, Math.floor((timerEndTime - now) / 1000));
    }
    
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    const timerElement = document.getElementById('timer');
    timerElement.textContent = display;
    
    // Update styling based on time
    timerElement.classList.remove('warning', 'danger');
    if (timeRemaining <= 30) {
        timerElement.classList.add('danger');
    } else if (timeRemaining <= 60) {
        timerElement.classList.add('warning');
    }
}

// ============================================
// RESULTS FUNCTIONS
// ============================================

function displayResults(data) {
    const resultsScreen = document.getElementById('resultsScreen');
    const resultsTrophy = document.getElementById('resultsTrophy');
    const resultsTitle = document.getElementById('resultsTitle');
    const resultsStats = document.getElementById('resultsStats');
    
    // Check if opponent left
    if (data.reason === 'opponent_left') {
        // Hide battle screen
        document.getElementById('battleScreen').style.display = 'none';
        
        // Show opponent left notification
        const notification = document.getElementById('opponentLeftNotification');
        notification.classList.add('active');
        
        // Redirect to menu after 4 seconds
        setTimeout(() => {
            window.location.href = '/user/competitive';
        }, 4000);
        
        return;
    }
    
    // Determine outcome
    const isWin = data.winner && data.scores && 
        data.scores[Object.keys(data.scores)[0]] > data.scores[Object.keys(data.scores)[1]];
    const isDraw = data.winner === 'Draw';
    
    // Update trophy and title
    if (isWin) {
        resultsTrophy.textContent = '🏆';
        resultsTitle.textContent = 'VICTORY!';
        resultsTitle.className = 'results-title victory';
    } else if (isDraw) {
        resultsTrophy.textContent = '🤝';
        resultsTitle.textContent = 'DRAW!';
        resultsTitle.className = 'results-title draw';
    } else {
        resultsTrophy.textContent = '💀';
        resultsTitle.textContent = 'DEFEAT';
        resultsTitle.className = 'results-title defeat';
    }
    
    // Build stats
    let statsHtml = '';
    
    if (data.scores) {
        for (const [player, score] of Object.entries(data.scores)) {
            statsHtml += `
                <div class="stat-row">
                    <span class="stat-label">${player}</span>
                    <span class="stat-value">${score} points</span>
                </div>
            `;
        }
    }
    
    if (data.completed) {
        for (const [player, completed] of Object.entries(data.completed)) {
            statsHtml += `
                <div class="stat-row">
                    <span class="stat-label">${player} Completed</span>
                    <span class="stat-value">${completed}/${data.total_challenges}</span>
                </div>
            `;
        }
    }
    
    if (data.duration) {
        const minutes = Math.floor(data.duration / 60);
        const seconds = data.duration % 60;
        statsHtml += `
            <div class="stat-row">
                <span class="stat-label">Duration</span>
                <span class="stat-value">${minutes}m ${seconds}s</span>
            </div>
        `;
    }
    
    statsHtml += `
        <div class="stat-row">
            <span class="stat-label">Reason</span>
            <span class="stat-value">${data.reason || 'completed'}</span>
        </div>
    `;
    
    resultsStats.innerHTML = statsHtml;
    
    // Show results screen
    resultsScreen.style.display = 'flex';
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function showNotification(type, message, duration = 3000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? 'var(--success-color)' : 
                     type === 'error' ? 'var(--danger-color)' : 
                     type === 'warning' ? 'var(--intermediate-color)' : 
                     'var(--accent-color)'};
        color: ${type === 'success' ? '#000' : '#fff'};
        border-radius: 8px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        z-index: 10000;
        font-weight: 600;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

function showError(message) {
    alert('Error: ' + message);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

console.log('Code Battle client initialized');
