// ===== CHECKIN STEP SYSTEM =====
let currentStep = 1;
const totalSteps = 6;

const pillarNames = {
    1: 'A — AWARENESS',
    2: 'S — STRATEGY',
    3: 'C — COGNITION',
    4: 'E — EMOTIONAL INTELLIGENCE',
    5: 'N — NETWORK',
    6: 'D — DEVELOPMENT'
};

function updateProgress() {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressLetter = document.getElementById('progress-letter');
    if (!progressFill) return;
    const percent = ((currentStep - 1) / totalSteps) * 100;
    progressFill.style.width = percent + '%';
    progressText.innerText = `PILLAR ${currentStep} OF ${totalSteps}`;
    progressLetter.innerText = pillarNames[currentStep];
}

function nextStep() {
    const currentTextarea = document.querySelector(`#step-${currentStep} textarea`);
    if (!currentTextarea.value.trim()) {
        currentTextarea.style.borderBottom = '2px solid #ff0000';
        currentTextarea.placeholder = 'ASCEND requires honesty. Fill this in.';
        return;
    }
    document.getElementById(`step-${currentStep}`).classList.remove('active');
    currentStep++;
    document.getElementById(`step-${currentStep}`).classList.add('active');
    document.getElementById('prev-btn').style.display = 'block';
    updateProgress();
    if (currentStep === totalSteps) {
        document.getElementById('next-btn').style.display = 'none';
        document.getElementById('submit-btn').style.display = 'block';
    }
}

function prevStep() {
    document.getElementById(`step-${currentStep}`).classList.remove('active');
    currentStep--;
    document.getElementById(`step-${currentStep}`).classList.add('active');
    document.getElementById('next-btn').style.display = 'block';
    document.getElementById('submit-btn').style.display = 'none';
    updateProgress();
    if (currentStep === 1) {
        document.getElementById('prev-btn').style.display = 'none';
    }
}

async function submitCheckin() {
    const awareness = document.getElementById('awareness').value;
    const strategy = document.getElementById('strategy').value;
    const cognition = document.getElementById('cognition').value;
    const emotional = document.getElementById('emotional').value;
    const network = document.getElementById('network').value;
    const development = document.getElementById('development').value;

    document.getElementById('response-box').style.display = 'block';
    document.getElementById('response-text').innerText = 'ASCEND is analyzing you...';
    document.getElementById('submit-btn').style.display = 'none';

    const response = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ awareness, strategy, cognition, emotional, network, development })
    });

    const data = await response.json();
    document.getElementById('progress-fill').style.width = '100%';
    document.getElementById('progress-text').innerText = 'COMPLETE';
    document.getElementById('progress-letter').innerText = 'ASCEND HAS SPOKEN';
    document.getElementById('response-text').innerText = data.feedback;
}

if (document.getElementById('progress-fill')) {
    loadContext();
}

async function loadContext() {
    const response = await fetch('/get_context');
    const context = await response.json();
    
    updateProgress();
    
    if (!context.has_context) return;
    
    const hints = {
        'awareness': `Yesterday you noticed: "${context.awareness.substring(0, 60)}..." — Did this pattern repeat today?`,
        'strategy': `Yesterday's decision: "${context.strategy.substring(0, 60)}..." — What did you decide today?`,
        'cognition': `Yesterday on learning: "${context.cognition.substring(0, 60)}..." — What did you apply today?`,
        'emotional': `Yesterday you were triggered by: "${context.emotional.substring(0, 60)}..." — Same trigger or different today?`,
        'network': `Yesterday socially: "${context.network.substring(0, 60)}..." — How were your interactions today?`,
        'development': `Yesterday on training: "${context.development.substring(0, 60)}..." — Did you train today?`
    };
    
const ids = ['awareness', 'strategy', 'cognition', 'emotional', 'network', 'development'];
setTimeout(() => {
    ids.forEach(id => {
        const hint = document.querySelector(`#step-${ids.indexOf(id)+1} .step-hint`);
        if (hint && hints[id]) {
            hint.innerText = hints[id];
        }
    });
}, 500);
}


// ===== QUICK LOG SYSTEM =====
function toggleQuickLog() {
    const panel = document.getElementById('quicklog-panel');
    if (!panel) return;
    if (panel.style.display === 'none') {
        panel.style.display = 'flex';
        loadTodayLogs();
    } else {
        panel.style.display = 'none';
    }
}

async function saveQuickLog() {
    const note = document.getElementById('quicklog-text').value;
    const pillar = document.getElementById('quicklog-pillar').value;
    if (!note.trim()) return;

    const response = await fetch('/start_incident', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note, pillar })
    });

    const data = await response.json();
    if (data.incident_id) {
        window.location.href = '/incident/' + data.incident_id;
    }
}

async function loadTodayLogs() {
    const response = await fetch('/getlogs');
    const data = await response.json();
    const container = document.getElementById('today-logs');
    if (!container) return;

    if (data.logs.length === 0) {
        container.innerHTML = '<p class="no-logs">No logs yet today.</p>';
        return;
    }

    container.innerHTML = data.logs.map(log => `
        <div class="log-entry">
            <span class="log-time">${log.time}</span>
            <span class="log-pillar">${log.pillar.toUpperCase()}</span>
            <span class="log-note">${log.note}</span>
        </div>
    `).join('');
}