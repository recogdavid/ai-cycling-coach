const VALIDATE_URL = 'https://dabosch.fit/webhook/auth/validate-code';

let validatedCode = null;

function showMessage(elementId, type, text) {
    const element = document.getElementById(elementId);
    element.textContent = text;
    element.className = `message ${type}`;
    element.style.display = 'block';
}

async function validateCode() {
    const codeInput = document.getElementById('inviteCode');
    const validateBtn = document.getElementById('validateBtn');
    const code = codeInput.value.trim().toUpperCase();
    
    if (!code) {
        showMessage('codeMessage', 'error', 'Please enter an invite code');
        return;
    }
    
    if (code.length !== 6) {
        showMessage('codeMessage', 'error', 'Code must be 6 characters');
        return;
    }
    
    validateBtn.disabled = true;
    validateBtn.textContent = 'Validating...';
    
    try {
        const response = await fetch(VALIDATE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });
        
        const result = await response.json();
        
        if (result.valid) {
            showMessage('codeMessage', 'success', '✓ Code validated!');
            validatedCode = code;
            document.getElementById('stravaBtn').disabled = false;
            localStorage.setItem('validated_invite_code', code);
            codeInput.disabled = true;
        } else {
            showMessage('codeMessage', 'error', result.message || 'Invalid code');
            validatedCode = null;
            document.getElementById('stravaBtn').disabled = true;
        }
    } catch (error) {
        showMessage('codeMessage', 'error', 'Network error');
    }
    
    validateBtn.disabled = false;
    validateBtn.textContent = 'Validate';
}

function connectStrava() {
    if (!validatedCode) {
        showMessage('stravaMessage', 'error', 'Validate code first');
        return;
    }
    
    console.log('Connecting to Strava with validated code:', validatedCode);
    
    // Get the button and show loading state
    const btn = document.getElementById('stravaBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = `
        <div class="loading-spinner" style="width: 20px; height: 20px; border-width: 2px; display: inline-block; margin-right: 10px;"></div>
        Redirecting to Strava...
    `;
    btn.disabled = true;
    
    // FIX 1: Get athlete ID from localStorage (set by validateCode)
    const athleteId = localStorage.getItem('athlete_id');
    
    if (!athleteId) {
        console.error('No athlete ID found. Please validate code again.');
        btn.innerHTML = originalText;
        btn.disabled = false;
        showMessage('stravaMessage', 'error', 'Please validate code again');
        return;
    }
    
    console.log('Athlete ID for Strava connection:', athleteId);
    
    // Strava OAuth configuration
    const clientId = '180641';
    const redirectUri = encodeURIComponent('https://dabosch.fit/webhook/api/strava/callback');
    const scope = 'read,activity:read,profile:read_all';
    const state = 'onboarding_' + Math.random().toString(36).substring(2) + Date.now().toString(36);

    // Store state for verification
    localStorage.setItem('strava_oauth_state', state);
    localStorage.setItem('strava_athlete_id', athleteId);

    // Redirect to Strava
    const stravaUrl = `https://www.strava.com/oauth/authorize?client_id=${clientId}&response_type=code&redirect_uri=${redirectUri}&scope=${scope}&state=${state}&approval_prompt=force`;

    console.log('Redirecting to Strava:', stravaUrl);
    window.location.href = stravaUrl;
}
function init() {
    const savedCode = localStorage.getItem('validated_invite_code');
    if (savedCode) {
        document.getElementById('inviteCode').value = savedCode;
        showMessage('codeMessage', 'info', 'Code found. Click Validate.');
    }
    
    document.getElementById('validateBtn').addEventListener('click', validateCode);
    document.getElementById('stravaBtn').addEventListener('click', connectStrava);
    
    document.getElementById('inviteCode').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') validateCode();
    });
    
    document.getElementById('inviteCode').addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
    });
}

document.addEventListener('DOMContentLoaded', init);
