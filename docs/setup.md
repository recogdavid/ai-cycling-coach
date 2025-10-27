# Setup Guide

## Prerequisites

- Ubuntu 20.04+ server
- 6+ CPU cores, 12GB+ RAM (for reasonable AI performance)
- Docker and Docker Compose installed
- Domain name with DNS configured
- Strava Developer Account

## Installation Steps

### 1. Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral
systemctl enable ollama
```

### 2. Clone Repository
```bash
git clone https://github.com/recogdavid/ai-cycling-coach.git
cd ai-cycling-coach
```

### 3. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` with your values:
```bash
# Domain Configuration
N8N_HOST=your-domain.com
N8N_PROTOCOL=https

# n8n Authentication
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_secure_password

# Database
POSTGRES_USER=aicoach_user
POSTGRES_PASSWORD=your_secure_db_password
POSTGRES_DB=aicoach_db

# Strava API
STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
```

### 4. Start Services
```bash
docker compose up -d
```

### 5. Run Database Migrations
```bash
docker exec -i ai-cycling-coach-postgres-1 psql -U aicoach_user -d aicoach_db < migrations/002_add_training_plans.sql
```

### 6. Import n8n Workflows

1. Access n8n at `https://your-domain.com`
2. Log in with Basic Auth credentials
3. Import workflows from `/workflows` directory (when available)
4. Configure Postgres credentials in each workflow
5. Activate workflows

### 7. Configure Strava Application

In your Strava API settings:
- **Authorization Callback Domain:** `your-domain.com`
- **Callback URL:** `https://your-domain.com/webhook/api/strava/callback`

## Verification

Test the setup:
```bash
# Check services are running
docker compose ps

# Check Ollama
curl http://localhost:11434/api/tags

# Test database connection
docker exec -it ai-cycling-coach-postgres-1 psql -U aicoach_user -d aicoach_db -c "SELECT version();"
```

## Troubleshooting

### Ollama not responding
```bash
systemctl status ollama
journalctl -u ollama -n 50
```

### n8n workflows failing
Check logs:
```bash
docker compose logs -f n8n
```

### SSL certificate issues
```bash
docker compose logs certbot
```
