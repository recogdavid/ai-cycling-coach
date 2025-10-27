# 🚴‍♂️ AI Cycling Coach

An intelligent, self-hosted cycling training system that generates personalized training plans, analyzes ride performance, and adapts recommendations using local AI (Ollama + Mistral).

## ✨ Features

### Currently Working
- ✅ **Strava Integration** - OAuth2 authentication with automatic token refresh
- ✅ **Ride Analysis** - AI-powered coaching feedback on completed activities  
- ✅ **FTP Tracking** - Automatic FTP recommendations based on performance trends
- ✅ **Training Plan Generation** - AI creates week-long structured training plans
- ✅ **Personalized Workouts** - Plans adapt to athlete's FTP, goals, and schedule constraints
- ✅ **Local AI** - Privacy-first: all AI processing runs locally via Ollama (no external API costs)

### In Development
- 🚧 Workout execution tracking (match planned vs actual rides)
- 🚧 .FIT/.ZWO file export for Garmin/Wahoo/Zwift
- 🚧 Multi-athlete support (currently single-user prototype)
- 🚧 Web dashboard UI

---

## 🏗️ Architecture

### Infrastructure Stack

| Component | Purpose | Access |
|-----------|---------|--------|
| **PostgreSQL 15** | Application database | Internal only |
| **n8n 1.112.6** | Workflow engine & API orchestration | `https://dabosch.fit` (Basic Auth) |
| **Nginx** | Reverse proxy, HTTPS termination | Ports 80/443 |
| **Certbot** | Automatic SSL certificate renewal | Background service |
| **Ollama** | Local AI inference (Mistral 7B) | Host OS: port 11434 |

### Database Schema

**Core Tables:**
- `athletes` - User profiles, FTP, preferences, Strava tokens
- `rides` - Completed activity data from Strava
- `ai_feedback` - AI-generated coaching insights per ride
- `training_plans` - Multi-week training plan records
- `planned_workouts` - Individual prescribed workouts with intervals
- `athlete_ftp_suggestions` - Automated FTP recommendations

See `migrations/` for full schema definitions.

---

## 🚀 Setup

### Prerequisites
- Ubuntu server (6+ cores, 12GB RAM recommended for good AI performance)
- Docker & Docker Compose
- Domain name with DNS configured
- Strava API application credentials

### 1. Clone Repository
```bash
git clone https://github.com/recogdavid/ai-cycling-coach.git
cd ai-cycling-coach
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Required variables:
```bash
# Domain & Protocol
N8N_HOST=your-domain.com
N8N_PROTOCOL=https

# n8n Security
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<strong_password>
N8N_ENCRYPTION_KEY=<random_32char_key>

# Database
POSTGRES_USER=aicoach_user
POSTGRES_PASSWORD=<strong_password>
POSTGRES_DB=aicoach_db

# Strava OAuth
STRAVA_CLIENT_ID=<your_strava_client_id>
STRAVA_CLIENT_SECRET=<your_strava_client_secret>
```

### 3. Install Ollama (on host OS)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral
```

### 4. Launch Stack
```bash
docker compose up -d
```

### 5. Run Database Migrations
```bash
docker exec -i ai-cycling-coach-postgres-1 psql -U aicoach_user -d aicoach_db < migrations/001_initial_schema.sql
docker exec -i ai-cycling-coach-postgres-1 psql -U aicoach_user -d aicoach_db < migrations/002_add_training_plans.sql
```

### 6. Configure Strava Webhook

In Strava API settings, set callback URL to:
```
https://your-domain.com/webhook/api/strava/callback
```

---

## 📊 Performance Notes

### AI Generation Times (Mistral 7B Q4_K_M)

| Hardware | Simple Feedback | Training Plan |
|----------|----------------|---------------|
| 3-core/8GB | 2-3 minutes | Timeouts |
| 6-core/12GB | 20-30 seconds | 60-90 seconds |
| 8-core/32GB | 10-20 seconds | 30-45 seconds |

**Current setup:** 6-core/12GB VPS (~90 seconds for plan generation)

---

## 🔧 Usage

### Generate Training Plan
```bash
curl -X POST https://your-domain.com/webhook/generate-plan \
  -H "Content-Type: application/json" \
  -d '{"athlete_id": 9}'
```

### Query Planned Workouts
```sql
SELECT scheduled_date, workout_type, description, duration_minutes, target_tss
FROM planned_workouts
WHERE athlete_id = 9
ORDER BY scheduled_date;
```

### View Latest FTP Recommendations
```sql
SELECT * FROM athlete_ftp_summary WHERE athlete_id = 9;
```

---

## 🧰 Maintenance

| Task | Command |
|------|---------|
| View n8n logs | `docker compose logs -f n8n` |
| Restart services | `docker compose restart` |
| Check SSL certs | `docker compose exec certbot certbot certificates` |
| Database backup | `docker exec postgres pg_dump -U aicoach_user aicoach_db > backup.sql` |
| Check Ollama status | `systemctl status ollama` |

---

## 🔒 Security

- ✅ HTTPS via Let's Encrypt (auto-renewal)
- ✅ n8n protected by Basic Authentication  
- ✅ Database credentials in `.env` (not committed)
- ✅ Strava tokens stored encrypted in database
- ✅ All AI processing local (no data sent to external APIs)

**Sensitive files in `.gitignore`:**
- `.env`, `data/`, `certbot/conf/`, SSL certificates

---

## 🗺️ Roadmap

### Phase 1: Core Training Plan System ✅
- [x] Database schema for plans and workouts
- [x] AI plan generation workflow
- [x] Athlete preferences (FTP, goals, availability)

### Phase 2: Workout Execution (In Progress)
- [ ] Match completed rides to planned workouts
- [ ] Execution quality analysis
- [ ] Plan adaptation based on compliance

### Phase 3: Workout Export
- [ ] Generate .FIT files (Garmin/Wahoo)
- [ ] Generate .ZWO files (Zwift)
- [ ] Email/download delivery

### Phase 4: Web Dashboard
- [ ] User authentication
- [ ] View training calendar
- [ ] Accept/reject FTP recommendations
- [ ] Download workout files

### Phase 5: Multi-User
- [ ] User onboarding flow
- [ ] Strava API quota increase approval
- [ ] User management

---

## 📝 Documentation

- **Handover Doc:** `docs/handover.md` - Infrastructure and workflow details
- **Architecture:** `docs/architecture.md` - System design and UML diagrams  
- **Migrations:** `migrations/` - Database schema changes

---

## 🐛 Known Limitations

- Single-user prototype (hardcoded athlete_id = 9 in workflows)
- No automatic Strava ride backfill
- Strava API limited to 1 athlete until quota approval
- No UI yet (API/database only)
- Training plans are 1-week duration (4-week plans planned)

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

Built with:
- [n8n](https://n8n.io) - Workflow automation
- [Ollama](https://ollama.ai) - Local LLM inference  
- [Strava API](https://developers.strava.com) - Activity data
- [Mistral 7B](https://mistral.ai) - AI model

---

**Version:** 0.2.0-training-plans  
**Last Updated:** October 27, 2025
