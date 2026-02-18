// onboarding-core.js - Core step management for onboarding
console.log('🚴 Onboarding Core loaded');

class OnboardingManager {
    constructor() {
        this.athleteId = null;
        this.currentStep = 1;
        this.completedSteps = new Set();
        this.init();
    }
    
    init() {
        console.log('Initializing OnboardingManager...');
        
        // 1. Get athlete_id from URL
        this.loadAthleteId();
        
        // 2. Check for Strava connection parameter
        this.checkStravaConnection();
        
        // 3. Initialize step system
        this.initSteps();
        
        // 4. Show current step
        this.showStep(this.currentStep);
        
        console.log(`✅ Ready. Athlete ID: ${this.athleteId}, Current Step: ${this.currentStep}`);
    }
    
    loadAthleteId() {
        const urlParams = new URLSearchParams(window.location.search);
        this.athleteId = urlParams.get('athlete_id');
        
        if (!this.athleteId) {
            console.error('❌ No athlete_id in URL');
            // In production, redirect to index.html
            return false;
        }
        
        console.log(`📋 Loaded athlete_id: ${this.athleteId}`);
        return true;
    }
    
    checkStravaConnection() {
        const urlParams = new URLSearchParams(window.location.search);
        const stravaConnected = urlParams.get('strava_connected');
        
        if (stravaConnected === 'true') {
            console.log('✅ Strava connected detected');
            this.completedSteps.add(2); // Mark Step 2 as completed
            // Remove parameter from URL without reload
            this.updateUrlParam('strava_connected', null);
        }
    }
    
    updateUrlParam(key, value) {
        const url = new URL(window.location);
        if (value === null) {
            url.searchParams.delete(key);
        } else {
            url.searchParams.set(key, value);
        }
        window.history.replaceState({}, '', url);
    }
    
    initSteps() {
        // Create step containers if they don't exist
        const stepsContainer = document.getElementById('steps-container');
        if (!stepsContainer) {
            this.createStepContainers();
        }
        
        // Setup event listeners for navigation
        this.setupNavigation();
    }
    
    createStepContainers() {
        console.log('Creating step containers...');
        
        // This is a fallback - your HTML should already have these
        const container = document.createElement('div');
        container.id = 'steps-container';
        container.innerHTML = `
            <div class="step" data-step="1">
                <h2>Step 1: Welcome</h2>
                <p>Welcome to AI Cycling Coach!</p>
                <button class="next-btn">Continue</button>
            </div>
            <div class="step" data-step="2" style="display: none;">
                <h2>Step 2: Connect Strava</h2>
                <div id="strava-status">Not connected</div>
                <button id="strava-connect-btn">Connect to Strava</button>
                <button class="prev-btn">Back</button>
                <button class="next-btn" disabled>Continue</button>
            </div>
            <div class="step" data-step="3" style="display: none;">
                <h2>Step 3: Your Profile</h2>
                <p>Profile form will go here</p>
                <button class="prev-btn">Back</button>
                <button class="next-btn">Continue</button>
            </div>
            <div class="step" data-step="4" style="display: none;">
                <h2>Step 4: Your Goals</h2>
                <p>Goals form will go here</p>
                <button class="prev-btn">Back</button>
                <button id="generate-plan-btn">Generate Training Plan</button>
            </div>
        `;
        
        document.body.appendChild(container);
    }
    
    setupNavigation() {
        // Next buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('next-btn')) {
                const currentStepEl = e.target.closest('.step');
                const currentStep = parseInt(currentStepEl.dataset.step);
                this.completeStep(currentStep);
                this.showStep(currentStep + 1);
            }
            
            if (e.target.classList.contains('prev-btn')) {
                const currentStepEl = e.target.closest('.step');
                const currentStep = parseInt(currentStepEl.dataset.step);
                this.showStep(currentStep - 1);
            }
        });
        
        // Strava connect button
        document.addEventListener('click', (e) => {
            if (e.target.id === 'strava-connect-btn') {
                this.connectStrava();
            }
        });
        
        // Generate plan button
        document.addEventListener('click', (e) => {
            if (e.target.id === 'generate-plan-btn') {
                this.generatePlan();
            }
        });
    }
    
    showStep(stepNumber) {
        if (stepNumber < 1 || stepNumber > 4) return;
        
        // Hide all steps
        document.querySelectorAll('.step').forEach(step => {
            step.style.display = 'none';
        });
        
        // Show target step
        const targetStep = document.querySelector(`[data-step="${stepNumber}"]`);
        if (targetStep) {
            targetStep.style.display = 'block';
            this.currentStep = stepNumber;
            console.log(`📱 Now showing Step ${stepNumber}`);
            
            // Update UI based on completed steps
            this.updateStepUI(stepNumber);
        }
    }
    
    completeStep(stepNumber) {
        this.completedSteps.add(stepNumber);
        console.log(`✅ Completed Step ${stepNumber}`);
    }
    
    updateStepUI(stepNumber) {
        // Enable/disable next buttons based on completion
        if (stepNumber === 2) {
            const nextBtn = document.querySelector('[data-step="2"] .next-btn');
            if (this.completedSteps.has(2)) {
                nextBtn.disabled = false;
                document.getElementById('strava-status').innerHTML = 
                    '<span style="color: green;">✓ Connected to Strava</span>';
                document.getElementById('strava-connect-btn').style.display = 'none';
            }
        }
    }
    
    connectStrava() {
        console.log('Connecting to Strava...');
        // This should be configured with your actual Strava client ID
        const stravaClientId = 'YOUR_STRAVA_CLIENT_ID'; // You need to set this
        const redirectUri = encodeURIComponent(`${window.location.origin}/strava-callback.html`);
        const stravaUrl = `https://www.strava.com/oauth/authorize?client_id=${stravaClientId}&redirect_uri=${redirectUri}&response_type=code&scope=activity:read_all,profile:read_all&state=${this.athleteId}`;
        
        window.location.href = stravaUrl;
    }
    
    generatePlan() {
        console.log('Generating training plan...');
        // This will be implemented in onboarding-step4.js
        alert('Plan generation will be implemented in Step 4 module');
    }
    
    // Public API
    getAthleteId() { return this.athleteId; }
    getCurrentStep() { return this.currentStep; }
    isStepCompleted(step) { return this.completedSteps.has(step); }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.onboardingManager = new OnboardingManager();
});
