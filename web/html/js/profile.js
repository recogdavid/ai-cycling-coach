// profile.js - Clean version without mock data
const ATHLETE_INFO_URL = 'https://dabosch.fit/webhook/c29d4bfe-aad8-4fbc-b97f-447b9ac009b9/athletes/get';
const STRAVA_SYNC_URL = 'https://dabosch.fit/webhook/strava/profile-sync';
const UPDATE_GOALS_URL = 'https://dabosch.fit/webhook/athletes/update-goals';

function getAthleteId() {
    const urlParams = new URLSearchParams(window.location.search);
    const athleteId = urlParams.get('athlete_id');
    if (!athleteId) {
        console.error('No athlete_id in URL');
        showMessage('error', 'Missing athlete ID in URL');
        return null;
    }
    return athleteId;
}

function showMessage(type, text) {
    const container = document.getElementById('messageContainer');
    const message = document.createElement('div');
    message.className = `${type}-message`;
    message.textContent = text;
    container.appendChild(message);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        message.remove();
    }, 5000);
}

function showLoading(show) {
    document.getElementById('loadingState').style.display = show ? 'block' : 'none';
}

function formatDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function calculateWkg(ftp, weight) {
    if (!ftp || !weight || weight === 0) return '--';
    return (ftp / weight).toFixed(2);
}

function calculateProgress(current, target) {
    if (!current || !target || target === 0) return 0;
    if (current >= target) return 100;
    return Math.round((current / target) * 100);
}

function calculateDaysToEvent(eventDate) {
    if (!eventDate) return '--';
    const today = new Date();
    const target = new Date(eventDate);
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 'Past';
}

function formatPowerZones(zones) {
    if (!zones || !zones.zones) return '--';
    return zones.zones.map((z, i) => 
        `Z${i+1}: ${z.min}-${z.max === -1 ? '+' : z.max}W`
    ).join(', ');
}

function formatHeartRateZones(zones) {
    if (!zones || !zones.zones) return '--';
    return zones.zones.map((z, i) => 
        `Z${i+1}: ${z.min}-${z.max === -1 ? '+' : z.max}bpm`
    ).join(', ');
}

function updateProfileWithData(data) {
    console.log('Updating profile with data:', data);
    
    // Basic info
    document.getElementById('athleteName').textContent = data.name ? data.name.trim() : 'Unknown Athlete';
    document.getElementById('athleteId').textContent = `Athlete ID: ${data.id || '--'}`;
    
    // Current stats - handle both old and new field names
    const ftp = data.strava_ftp || data.ftp_watts;
    const weight = data.strava_weight_kg || data.weight_kg;
    
    console.log('FTP:', ftp, 'Weight:', weight);
    
    document.getElementById('currentFTP').textContent = `${ftp || '--'} W`;
    document.getElementById('currentWeight').textContent = `${weight || '--'} kg`;
    
    // Calculate and display W/kg
    const wkg = calculateWkg(ftp, weight);
    document.getElementById('currentWkg').textContent = wkg;
    
    // Power zones
    const powerZones = data.strava_power_zones || data.power_zones;
    console.log('Power zones:', powerZones);
    document.getElementById('powerZones').textContent = formatPowerZones(powerZones);
    
    // Heart rate zones
    const hrZones = data.strava_heart_rate_zones || data.heart_rate_zones;
    console.log('HR zones:', hrZones);
    document.getElementById('hrZones').textContent = formatHeartRateZones(hrZones);
    
    // Last synced
    const lastSynced = data.strava_profile_synced_at || data.profile_date;
    document.getElementById('lastSynced').textContent = `Last synced: ${formatDate(lastSynced)}`;
    
    // Store current values for progress calculations
    window.currentAthleteData = {
        ftp: ftp,
        weight_kg: weight
    };
    window.currentProfileData = data; // Store full profile data for baseline values
 
    // Load goals from the profile data
    loadAthleteGoals(data);
}

async function loadAthleteProfile() {
    const athleteId = getAthleteId();
    if (!athleteId) return;
    
    showLoading(true);
    
    try {
        console.log('Fetching athlete profile for ID:', athleteId);
        
        const response = await fetch(`${ATHLETE_INFO_URL}/${athleteId}`);
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const dataArray = await response.json();
        console.log('Athlete profile data (array):', dataArray);
        
        // Extract the first (and only) athlete from the array
        if (!dataArray || dataArray.length === 0) {
            throw new Error('No athlete data found');
        }
        
        const data = dataArray[0];
        // ADD DEBUG LOGGING HERE:
        console.log('DEBUG: Full data object:', data);
        console.log('DEBUG: Does data have target_event_type?', 'target_event_type' in data);
        console.log('DEBUG: Does data have target_event_date?', 'target_event_date' in data);
        console.log('DEBUG: Data keys:', Object.keys(data));
        console.log('DEBUG: target_event_type value:', data.target_event_type);
        console.log('DEBUG: target_event_date value:', data.target_event_date);
	console.log('Extracted athlete data:', data);
        
        // Update the profile page
        updateProfileWithData(data);
        
        showMessage('success', 'Profile loaded successfully');
        
    } catch (error) {
        console.error('Error loading athlete profile:', error);
        showMessage('error', `Failed to load profile: ${error.message}`);
        // No mock data fallback - just show error
    } finally {
        showLoading(false);
    }
}

async function loadAthleteGoals(profileData) {
    try {
        const athleteId = getAthleteId();
        if (!athleteId) return;
        
        // Check if we have goal data in the profile
        if (profileData && (profileData.target_event_type || profileData.training_goal)) {
            console.log('Loading goals from profile data:', profileData);
            
            const goals = {
                targetEventType: profileData.target_event_type || '',
                targetEventDate: profileData.target_event_date || '',
                targetEventDistance: profileData.target_event_distance_km || 120,
                targetFTP: profileData.target_ftp_watts || 260,
                targetWeight: profileData.target_weight_kg || 62,
                weeklyAvailability: profileData.weekly_hours_available || 8,
                trainingGoals: profileData.training_goal || 'Peak for April 12th race, fitness for Majorca camp, reduce weight'
            };
            
            populateGoalsForm(goals);
        } else {
            // Fall back to localStorage
            const savedGoals = localStorage.getItem(`athlete_goals_${athleteId}`);
            
            if (savedGoals) {
                const goals = JSON.parse(savedGoals);
                populateGoalsForm(goals);
            } else {
                // Default values (empty)
                const defaultGoals = {
                    targetEventType: '',
                    targetEventDate: '',
                    targetEventDistance: '',
                    targetFTP: '',
                    targetWeight: '',
                    weeklyAvailability: '',
                    trainingGoals: ''
                };
                populateGoalsForm(defaultGoals);
            }
        }
        
    } catch (error) {
        console.error('Error loading goals:', error);
        showMessage('error', 'Failed to load goals');
    }
}

function populateGoalsForm(goals) {
    document.getElementById('targetEventType').value = goals.targetEventType || '';
    const eventDate = goals.targetEventDate || '';
    document.getElementById('targetEventDate').value = eventDate ? eventDate.split('T')[0] : '';
    document.getElementById('targetEventDistance').value = goals.targetEventDistance || '';
    document.getElementById('targetFTP').value = goals.targetFTP || '';
    document.getElementById('targetWeight').value = goals.targetWeight || '';
    document.getElementById('weeklyAvailability').value = goals.weeklyAvailability || '';
    document.getElementById('trainingGoals').value = goals.trainingGoals || '';
    
    // Store for later use
    window.currentGoals = goals;
    
    // Update progress calculations
    updateProgress();
}


function updateProgress() {
    const athlete = window.currentAthleteData;
    const goals = window.currentGoals;
    const profileData = window.currentProfileData;
    
    if (!athlete || !goals) return;
    
    // Get baseline values (from database or fallback to current)
    const baselineFTP = (profileData && profileData.baseline_ftp_watts) || athlete.ftp;
    const baselineWeight = (profileData && profileData.baseline_weight_kg) || athlete.weight_kg;
    
    // Calculate days and weeks to event
    const daysToEvent = calculateDaysToEvent(goals.targetEventDate);
    const weeksToEvent = Math.max(1, Math.ceil(daysToEvent / 7));
    
    // ===== FTP SECTION =====
    // FTP: baseline → current → target
    const ftpValuesElement = document.getElementById('ftpProgressValues');
    if (ftpValuesElement) {
        ftpValuesElement.innerHTML = `
            <span class="value baseline-value">${baselineFTP}W</span>
            <span class="arrow">→</span>
            <span class="value current-value">${athlete.ftp}W</span>
            <span class="arrow">→</span>
            <span class="value target-value">${goals.targetFTP}W</span>
        `;
    }
    
    // FTP gap calculations
    const ftpGap = goals.targetFTP - athlete.ftp;
    const weeklyFTPTarget = (ftpGap / weeksToEvent).toFixed(1);
    
    const ftpGapElement = document.getElementById('ftpGapMetrics');
    if (ftpGapElement) {
        ftpGapElement.innerHTML = `
            <div class="gap-item">
                <span class="gap-label">Gap:</span>
                <span class="gap-value ${ftpGap > 0 ? 'positive' : 'negative'}">
                    ${ftpGap > 0 ? '+' : ''}${ftpGap}W to target
                </span>
            </div>
            <div class="gap-item">
                <span class="gap-label">Weekly:</span>
                <span class="gap-value weekly">
                    ${weeklyFTPTarget > 0 ? '+' : ''}${weeklyFTPTarget}W/week
                </span>
            </div>
        `;
    }
    
    // ===== WEIGHT SECTION =====
    // Weight: baseline → current → target  
    const weightValuesElement = document.getElementById('weightProgressValues');
    if (weightValuesElement) {
        weightValuesElement.innerHTML = `
            <span class="value baseline-value">${baselineWeight}kg</span>
            <span class="arrow">→</span>
            <span class="value current-value">${athlete.weight_kg}kg</span>
            <span class="arrow">→</span>
            <span class="value target-value">${goals.targetWeight}kg</span>
        `;
    }
    
    // Weight gap calculations (inverse - we want to lose weight)
    // Weight gap calculations (inverse - we want to lose weight)
    const weightGap = athlete.weight_kg - goals.targetWeight;
    const weeklyWeightTarget = (weightGap / weeksToEvent).toFixed(1);
    
    // Round weight gap to 1 decimal place
    const roundedWeightGap = Math.abs(weightGap).toFixed(1);
    const roundedWeeklyTarget = Math.abs(weeklyWeightTarget).toFixed(1);
    
    const weightGapElement = document.getElementById('weightGapMetrics');
    if (weightGapElement) {
        weightGapElement.innerHTML = `
            <div class="gap-item">
                <span class="gap-label">Gap:</span>
                <span class="gap-value ${weightGap > 0 ? 'negative' : 'positive'}">
                    ${weightGap > 0 ? '-' : '+'}${roundedWeightGap}kg to target
                </span>
            </div>
            <div class="gap-item">
                <span class="gap-label">Weekly:</span>
                <span class="gap-value weekly">
                    ${weightGap > 0 ? '-' : '+'}${roundedWeeklyTarget}kg/week
                </span>
            </div>
        `;
    }
    // ===== OTHER METRICS =====
    // Days to event
    const daysElement = document.getElementById('daysToEvent');
    if (daysElement) {
        daysElement.textContent = daysToEvent;
    }
    
    // Target W/kg
    const targetWkg = calculateWkg(goals.targetFTP, goals.targetWeight);
    const wkgElement = document.getElementById('targetWkg');
    if (wkgElement) {
        wkgElement.textContent = targetWkg;
    }
    
    // Training phase (simplified - would come from your training plan)
    const phaseElement = document.getElementById('trainingPhase');
    if (phaseElement) {
        phaseElement.textContent = 'Race Preparation';
    }
}async function saveAthleteGoals(goals) {
    try {
        const athleteId = getAthleteId();
        if (!athleteId) return false;
        
        // Try to save to database via n8n endpoint
        const response = await fetch(UPDATE_GOALS_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                athlete_id: athleteId,
                ...goals
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Goals saved to database:', result);
            showMessage('success', 'Goals saved to database!');
            
            // Also save to localStorage as backup
            localStorage.setItem(`athlete_goals_${athleteId}`, JSON.stringify(goals));
            
            // Update current goals
            window.currentGoals = goals;
            
            // Update progress
            updateProgress();
            
            return true;
        } else {
            throw new Error('Failed to save to database');
        }
        
    } catch (error) {
        console.error('Error saving goals to database:', error);
        
        // Fall back to localStorage
        const athleteId = getAthleteId();
        if (athleteId) {
            localStorage.setItem(`athlete_goals_${athleteId}`, JSON.stringify(goals));
        }
        
        // Update current goals
        window.currentGoals = goals;
        
        // Update progress
        updateProgress();
        
        showMessage('warning', 'Goals saved locally (database update failed)');
        return true; // Still successful with localStorage
    }
}

function setupEventListeners() {
    // Refresh Strava button
    // Refresh Strava button
const refreshBtn = document.getElementById('refreshStravaBtn');
if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
        showMessage('info', 'Refreshing Strava data...');
        
        try {
            const athleteId = getAthleteId();
            if (!athleteId) return;
            
            // Call the Strava sync endpoint
            const response = await fetch(STRAVA_SYNC_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    athlete_id: athleteId
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('Strava sync result:', result);
                showMessage('success', 'Strava data refreshed!');
                
                // Reload the profile to show updated data
                setTimeout(() => {
                    loadAthleteProfile();
                }, 2000); // Wait 2 seconds for sync to complete
            } else {
                throw new Error('Sync failed');
            }
        } catch (error) {
            console.error('Error syncing Strava:', error);
            showMessage('error', 'Failed to refresh Strava data');
        }
    });
}
    // Save goals form
    const goalsForm = document.getElementById('goalsForm');
    if (goalsForm) {
        goalsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const goals = {
                targetEventType: document.getElementById('targetEventType').value,
                targetEventDate: document.getElementById('targetEventDate').value,
                targetEventDistance: parseFloat(document.getElementById('targetEventDistance').value) || 0,
                targetFTP: parseFloat(document.getElementById('targetFTP').value) || 0,
                targetWeight: parseFloat(document.getElementById('targetWeight').value) || 0,
                weeklyAvailability: parseFloat(document.getElementById('weeklyAvailability').value) || 0,
                trainingGoals: document.getElementById('trainingGoals').value
            };
            
            // Validate date is in future
            if (goals.targetEventDate) {
                const eventDate = new Date(goals.targetEventDate);
                const today = new Date();
                if (eventDate <= today) {
                    showMessage('error', 'Target event date must be in the future');
                    return;
                }
            }
            
            // Show loading
            const saveBtn = document.getElementById('saveGoalsBtn');
            if (saveBtn) {
                const originalText = saveBtn.innerHTML;
                saveBtn.disabled = true;
                saveBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="animation: spin 1s linear infinite;"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg> Saving...';
                
                await saveAthleteGoals(goals);
                
                // Restore button
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalText;
            }
        });
    }
    
    // Reset goals button
    const resetBtn = document.getElementById('resetGoalsBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (confirm('Reset all goals to defaults?')) {
                const athleteId = getAthleteId();
                if (athleteId) {
                    localStorage.removeItem(`athlete_goals_${athleteId}`);
                }
                loadAthleteGoals({});
                showMessage('success', 'Goals reset to defaults');
            }
        });
    }
}

async function initProfile() {
    console.log('Initializing profile page...');
    
    // Set up event listeners
    setupEventListeners();
    
    // Load data
    await loadAthleteProfile();
    
    console.log('Profile page initialized');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initProfile);
