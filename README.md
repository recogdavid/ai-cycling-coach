# 🚴 Dave's AI Cycling Coach

An AI-powered cycling training platform that generates personalized training plans using local AI models, Strava integration, and evidence-based RAG (Retrieval-Augmented Generation) system.

## 🌟 Features

- **Strava OAuth Integration** - Secure authentication and activity tracking
- **AI-Generated Training Plans** - Personalized weekly plans based on your goals, FTP, and schedule
- **RAG-Enhanced Coaching** - Training plans based on established methodology (Joe Friel, British Cycling, etc.)
- **Event-Based Periodization** - Automatic phase progression (Base → Build → Peak → Taper)
- **Workout File Export** - Download workouts as .zwo (Zwift) or .fit (Garmin/Wahoo) files
- **Privacy-First Design** - All AI processing runs locally with Ollama (no external API calls)
- **Constraint-Aware Planning** - Respects your available hours and unavailable days

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTPS
       ↓
┌─────────────┐     ┌──────────────┐
│    Caddy    │────→│  Static HTML │
│ (Proxy/SSL) │     │   /web/html/ │
└──────┬──────┘     └──────────────┘
       │
       ↓
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│     n8n     │────→│  PostgreSQL  │────→│  pgvector    │
│ (Workflows) │     │  (Database)  │     │     (RAG)    │
└──────┬──────┘     └──────────────┘     └──────────────┘
       │
       ↓
┌─────────────┐     ┌──────────────┐
│   Ollama    │────→│ deepseek-r1  │
│  (AI Host)  │     │    (Model)   │
└─────────────┘     └──────────────┘
```

## 📋 Prerequisites

- Ubuntu 24.04 (or similar Linux)
- Docker & Docker Compose
- Domain name with DNS configured
- Strava API application credentials

## 🚀 Quick Start

### 1. Clone Repository

```bash
cd ~
git clone https://github.com/yourusername/ai-cycling-coach.git
cd ai-cycling-coach
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
vim .env
```

Required environment variables:
```bash
# Strava API
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret

# Database
DB_PASSWORD=your_secure_password
DB_USER=aicoach_user
DB_DATABASE=aicoach_db

# Domain
DOMAIN=yourdomain.com
```

### 3. Start Services

```bash
docker compose up -d
```

This will start:
- PostgreSQL (with pgvector extension)
- n8n (workflow automation)
- Ollama (local AI)
- Caddy (reverse proxy with automatic SSL)

### 4. Initialize Database

```bash
# Access PostgreSQL
docker exec -it ai-cycling-coach-postgres-1 psql -U aicoach_user -d aicoach_db

# Run schema initialization
\i /path/to/schema.sql
```

### 5. Load AI Model

```bash
# Pull the model
docker exec ollama ollama pull deepseek-r1:1.5b

# Verify it's loaded
docker exec ollama ollama list
```

### 6. Import n8n Workflows

1. Access n8n UI: `https://yourdomain.com/n8n/`
2. Go to Settings → Import
3. Import all workflows from `workflows/2025-11-18/`
4. Activate each workflow

### 7. Configure Strava API

1. Go to https://www.strava.com/settings/api
2. Create application with:
   - **Authorization Callback Domain:** `yourdomain.com`
   - **Authorization Callback URL:** `https://yourdomain.com/webhook/api/strava/callback`
3. Note your Client ID and Client Secret
4. Update `.env` file with credentials

### 8. Test the Application

Visit `https://yourdomain.com` and:
1. Click "Sign Up"
2. Complete onboarding form
3. Authorize Strava
4. View your dashboard
5. Generate a training plan

## 📂 Project Structure

```
~/ai-cycling-coach/
├── docker-compose.yml          # Container orchestration
├── .env                        # Environment variables (not in git)
├── README.md                   # This file
├── web/
│   └── html/
│       ├── index.html          # Landing page
│       ├── onboarding.html     # Registration form
│       ├── dashboard.html      # Main dashboard
│       └── assets/             # Images, logos, etc.
├── workflows/
│   └── 2025-11-18/            # n8n workflow exports
│       ├── Strava_·_API_·_Connect.json
│       ├── Strava_API_Callback.json
│       ├── Athletes_·_API_·_Register.json
│       ├── RAG_Training_Plan_Generator.json
│       └── Download_Workout_File.json
├── scripts/
│   └── export-workflows-cli.sh # Workflow backup script
├── fit-generator/              # Python FIT file generation
│   ├── generate_fit.py
│   └── requirements.txt
└── docs/
    ├── HANDOVER.md             # Detailed session notes
    └── API.md                  # API documentation
```

## 🗄️ Database Schema

### Core Tables

**athletes**
- Stores athlete profiles, FTP, goals, Strava credentials

**training_plans**
- Parent records for generated training plans

**planned_workouts**
- Individual workout records with intervals

**training_knowledge** (RAG)
- Embedded training methodology for AI context

See `docs/HANDOVER.md` for complete schema details.

## 🔄 Key Workflows

### 1. Authentication Flow
- User authorizes via Strava OAuth
- Tokens stored securely in database
- Cookie-based session management

### 2. Training Plan Generation
1. User clicks "Generate Plan" on dashboard
2. n8n fetches athlete data (FTP, goals, constraints)
3. Calculates weekly TSS distribution
4. AI generates week structure with RAG context
5. Loops through each day to create specific workouts
6. Inserts workouts into database
7. Dashboard polls and displays results

### 3. Workout File Download
- User clicks download button (.zwo or .fit)
- n8n fetches workout data
- Generates file in requested format
- Returns file for download

## 🤖 AI & RAG System

### Models Used
- **Primary:** `deepseek-r1:1.5b` - Fast inference, good structured output
- **Embedding:** `all-MiniLM-L6-v2` - 384-dimensional sentence embeddings

### RAG Knowledge Base
Training methodology embedded from:
- Joe Friel's Training Bible
- British Cycling guidelines
- TrainerRoad methodology
- Sports science literature

### How RAG Works
1. Semantic search finds relevant training guidance
2. Top 3-5 passages injected into AI prompt
3. AI generates workouts following evidence-based principles
4. Result: Plans based on established methodology, not random generation

## ⚙️ Configuration

### Docker Compose Services

```yaml
services:
  postgres:     # Database with pgvector
  n8n:          # Workflow engine
  caddy:        # Reverse proxy + SSL
  ollama:       # Local AI inference
```

### Caddy Reverse Proxy

```
yourdomain.com {
  # Static files
  root * /var/www/html
  file_server
  
  # n8n webhooks
  reverse_proxy /webhook/* n8n:5678
  
  # n8n UI
  reverse_proxy /n8n/* n8n:5678
}
```

### n8n Environment

Key settings in `docker-compose.yml`:
```yaml
environment:
  - DB_TYPE=postgresdb
  - DB_HOST=postgres
  - N8N_HOST=${DOMAIN}
  - WEBHOOK_URL=https://${DOMAIN}
  - STRAVA_CLIENT_ID=${STRAVA_CLIENT_ID}
  - STRAVA_CLIENT_SECRET=${STRAVA_CLIENT_SECRET}
```

## 🔧 Maintenance

### Backup Database

```bash
# Create backup
docker exec ai-cycling-coach-postgres-1 pg_dump -U aicoach_user aicoach_db > backup_$(date +%Y%m%d).sql

# Restore backup
docker exec -i ai-cycling-coach-postgres-1 psql -U aicoach_user -d aicoach_db < backup_20251122.sql
```

### Export Workflows

```bash
cd ~/ai-cycling-coach/scripts
./export-workflows-cli.sh
```

Creates dated backup in `workflows/YYYY-MM-DD/`

### View Logs

```bash
# n8n logs
docker logs ai-cycling-coach-n8n-1 --tail 100 -f

# PostgreSQL logs
docker logs ai-cycling-coach-postgres-1 --tail 50

# Ollama logs
docker logs ollama --tail 50

# All services
docker compose logs -f
```

### Update AI Model

```bash
# Pull latest model
docker exec ollama ollama pull deepseek-r1:1.5b

# List installed models
docker exec ollama ollama list

# Remove old model
docker exec ollama ollama rm model_name
```

## 🐛 Troubleshooting

### Common Issues

**"Cannot connect to database"**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Restart if needed
docker restart ai-cycling-coach-postgres-1
```

**"Ollama model not found"**
```bash
# Pull the model
docker exec ollama ollama pull deepseek-r1:1.5b

# Verify
docker exec ollama ollama list
```

**"Strava OAuth error"**
- Verify redirect URI matches exactly in Strava app settings
- Check STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in .env
- Ensure domain has valid SSL certificate

**"Workouts not generating"**
- Check n8n executions for errors: `https://yourdomain.com/n8n/executions`
- Verify athlete data exists: `SELECT * FROM athletes WHERE id = X;`
- Check Ollama is responding: `curl http://localhost:11434/api/tags`

See `docs/HANDOVER.md` for detailed troubleshooting guide.

## 📊 Monitoring

### Health Checks

```bash
# Check all containers
docker ps

# Check resource usage
docker stats

# Test endpoints
curl https://yourdomain.com
curl https://yourdomain.com/webhook/health
```

### Database Queries

```sql
-- Active athletes
SELECT COUNT(DISTINCT athlete_id) 
FROM planned_workouts 
WHERE created_at > NOW() - INTERVAL '30 days';

-- Plans generated today
SELECT COUNT(*) 
FROM training_plans 
WHERE DATE(created_at) = CURRENT_DATE;

-- Average plan generation time
-- (check n8n execution logs)
```

## 🔒 Security

### Current Measures
- ✅ HTTPS with automatic SSL (Let's Encrypt)
- ✅ Secure cookies (Secure, SameSite=Lax)
- ✅ Environment variable secrets
- ✅ Database password protection
- ✅ Same-origin policy (no CORS issues)

### Recommended Improvements
- [ ] Add API rate limiting
- [ ] Implement session timeouts
- [ ] Add CSRF protection
- [ ] Encrypt Strava tokens at rest
- [ ] Add audit logging
- [ ] Input sanitization/validation

## 🚧 Known Issues

1. **Event data not influencing plans** - Prompt construction needs updating
2. **Plans lack variety** - Despite temperature 0.8, plans too similar
3. **Athletes Register workflow** - Doesn't accept new onboarding fields yet
4. **No profile editing** - Users can't update FTP, goals, etc. after registration

See `docs/HANDOVER.md` Priority sections for detailed fix plans.

## 🛣️ Roadmap

### Phase 2: Activity Analysis
- Sync completed workouts from Strava
- Compare planned vs. actual performance
- Adaptive plan adjustments based on compliance

### Phase 3: Advanced Periodization
- Multi-week plan generation
- Automatic phase transitions
- Workout library with templates

### Phase 4: Mobile App
- iOS/Android native app
- Bluetooth trainer integration
- Offline workout support

### Phase 5: Social Features
- Training clubs/teams
- Shared workouts
- Coach dashboard for managing athletes

See `docs/HANDOVER.md` Future Roadmap for detailed feature descriptions.

## 📚 Documentation

- **[HANDOVER.md](docs/HANDOVER.md)** - Detailed session notes, technical deep dive
- **[API.md](docs/API.md)** - API endpoint documentation (TODO)
- **[Strava API Docs](https://developers.strava.com/docs/)** - Strava integration reference
- **[n8n Docs](https://docs.n8n.io/)** - Workflow automation guide
- **[Ollama Docs](https://github.com/ollama/ollama)** - Local AI setup
- **[pgvector Docs](https://github.com/pgvector/pgvector)** - Vector database extension

## 🤝 Contributing

This is currently a personal project, but contributions welcome! Areas that need help:

1. **Frontend Design** - Improve UI/UX
2. **Testing** - Add automated tests
3. **Documentation** - Expand guides and tutorials
4. **Training Knowledge** - Add more methodology to RAG
5. **Mobile App** - Start React Native development

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Joe Friel** - Training methodology foundation
- **Strava** - Activity tracking platform
- **n8n** - Workflow automation
- **Ollama** - Local AI inference
- **pgvector** - Vector similarity search

## 💬 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: david@dabosch.fit
- See troubleshooting guide in `docs/HANDOVER.md`

## 📈 Status

**Current Version:** MVP v1.0  
**Status:** ⚠️ Beta - Active development  
**Last Updated:** November 22, 2025

---

**Built with ❤️ for cyclists who want evidence-based, personalized training plans without sharing their data with external AI services.**
