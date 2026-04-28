// global.js - Shared utilities for entire app

// Cookie utilities
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function getCookie(name) {
    // Try multiple approaches for cross-browser compatibility
    const cookies = document.cookie;
    
    // Standard approach
    const value = `; ${cookies}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        const cookieValue = parts.pop().split(';').shift();
        console.log(`Found cookie ${name}=${cookieValue}`);
        return cookieValue;
    }
    
    // Try without leading space (some browsers)
    const parts2 = cookies.split(`${name}=`);
    if (parts2.length === 2) {
        const cookieValue = parts2.pop().split(';').shift();
        console.log(`Found cookie ${name}=${cookieValue} (no space)`);
        return cookieValue;
    }
    
    console.log(`Cookie ${name} not found`);
    return null;
}
    // Modern browsers: SameSite=Lax (good default)
    cookieString += '; SameSite=Lax';
    
    // Only add Secure flag on HTTPS
    if (isHttps) {
        cookieString += '; Secure';
    }
    
    document.cookie = cookieString;
    console.log(`Set cookie: ${name}=${value} (domain: ${hostname}, Secure: ${isHttps})`);
}
function deleteCookie(name) {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

// Auth utilities
function getAthleteId() {
    return getCookie('athlete_id') || 
           new URLSearchParams(window.location.search).get('athlete_id');
}

function requireAuth(redirectUrl = 'index.html') {
    const athleteId = getAthleteId();
    if (!athleteId) {
        window.location.href = redirectUrl;
        return null;
    }
    return athleteId;
}

function redirectIfAuthenticated(targetUrl = 'profile.html') {
    const athleteId = getAthleteId();
    if (athleteId) {
        window.location.href = `${targetUrl}?athlete_id=${athleteId}`;
        return true;
    }
    return false;
}

// API utilities
async function apiRequest(endpoint, options = {}) {
    const baseUrl = 'https://dabosch.fit/webhook';
    const athleteId = getAthleteId();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(athleteId && { 'X-Athlete-ID': athleteId })
        }
    };
    
    try {
        const response = await fetch(`${baseUrl}/${endpoint}`, {
            ...defaultOptions,
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// UI utilities
function showMessage(elementId, type, text) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.textContent = text;
    element.className = `message message-${type}`;
    element.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}

function hideMessage(elementId) {
    const element = document.getElementById(elementId);
    if (element) element.style.display = 'none';
}

// Loading state
function setLoading(button, isLoading, loadingText = 'Loading...') {
    if (!button) return;
    
    if (isLoading) {
        button.dataset.originalText = button.textContent;
        button.innerHTML = `<span class="loading-spinner"></span> ${loadingText}`;
        button.disabled = true;
    } else {
        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
    }
}

// Strava OAuth
function getStravaOAuthUrl(clientId, redirectUri, state = '') {
    const params = new URLSearchParams({
        client_id: clientId,
        redirect_uri: redirectUri,
        response_type: 'code',
        approval_prompt: 'auto',
        scope: 'read,activity:read,profile:read_all',
        ...(state && { state: state })
    });
    
    return `https://www.strava.com/oauth/authorize?${params.toString()}`;
}

// Export for use in other files (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCookie,
        setCookie,
        deleteCookie,
        getAthleteId,
        requireAuth,
        redirectIfAuthenticated,
        apiRequest,
        showMessage,
        hideMessage,
        setLoading,
        getStravaOAuthUrl
    };
}
