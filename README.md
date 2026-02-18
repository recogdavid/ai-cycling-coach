# 🚴 Dave's AI Cycling Coach v4.1

An AI-powered conversational cycling coaching platform that provides evidence-based, personalized coaching through natural conversation with actionable feedback loops.

## 🌟 Core Philosophy Shift

**From:** Static plan generation → **To:** Dynamic coaching conversations  
**From:** One-time plan creation → **To:** Continuous adaptation loop  
**From:** Data retrieval Q&A → **To:** Coach-led recommendations with actions  
**From:** Plain text responses → **To:** Rich, structured responses with actionable buttons  
**From:** Hardcoded athlete IDs → **To:** Secure authentication with invite codes

## 🎯 Key Features

### 🤖 **AI Agent Chat System**
- **Conversational Coaching**: Natural conversations with Dave, your AI coach
- **Actionable Responses**: Rich formatting with buttons for workflow integration
- **Evidence-Informed**: RAG-enhanced responses based on established training methodology
- **Dynamic Tool Selection**: AI agent intelligently selects from available tools

### 🔐 **Secure Authentication**
- **Invite Code System**: Controlled access with unique invite codes
- **Cookie-Based Sessions**: Secure HTTP-only cookies with SameSite protection
- **Strava OAuth Integration**: Seamless connection to Strava for activity tracking
- **No Hardcoded IDs**: Complete removal of hardcoded athlete IDs

### 📊 **Athlete Profile Management**
- **Three-Point Progress Tracking**: Baseline → Current → Target visualization
- **Formatted Zone Display**: Clear, readable power and heart rate zones
- **Goals Management**: Editable target fields with coach guidance
- **Re-baseline Functionality**: Manual trigger with confirmation

### 📅 **Training Management**
- **AI-Generated Training Plans**: Personalized weekly plans based on goals, FTP, and schedule
- **Training Calendar**: Interactive calendar with workout details and feedback
- **Workout File Export**: Download workouts as .zwo (Zwift) or .fit (Garmin/Wahoo) files
- **Feedback Integration**: Rate workouts and provide notes for AI adaptation

### 🔄 **Complete Feedback Loop**
- **Plan → Execute → Analyze → Adjust**: Continuous coaching cycle
- **Compliance Tracking**: Compare planned vs. actual performance
- **Adaptive Recommendations**: AI suggests adjustments based on feedback
- **Progress Visualization**: Clear tracking toward goals

## 🏗 Architecture v4.1

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Browser)                      │
│  • Landing Page (index.html)                                │
│  • Onboarding (onboarding.html)                             │
│  • Dashboard (dashboard.html)                               │
│  • Chat Interface (coach-chat.html)                         │
│  • Training Calendar (training-calendar.html)               │
│  • Athlete Profile (profile.html)                           │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                     Caddy Reverse Proxy                     │
│  • Static file serving (/web/html/)                         │
│  • Automatic SSL (Let's Encrypt)                            │
│  • Webhook routing to n8n                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                      n8n Workflow Engine                    │
│  • AI Agent Chat (conversational coaching)                  │
│  • Authentication & Session Management                      │
│  • Training Plan Generation (RAG-enhanced)                  │
│  • Strava Integration & Sync                                │
│  • Workout File Generation                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  PostgreSQL   │ │    Ollama     │ │   Strava API  │
│  • Athlete Data│ │  • DeepSeek   │ │  • Activities │
│  • Workouts    │ │  • Embeddings │ │  • Auth       │
│  • RAG Vectors │ └───────────────┘ └───────────────┘
│  • Invite Codes│
└───────────────┘
```

## 📂 Project Structure

```
~/ai-cycling-coach/
├── docker-compose.yml          # Container orchestration
├── .env                        # Environment variables
├── README.md                   # This file
├── web/                        # Static web files
│   └── html/
│       ├── index.html          # Landing page
│       ├── onboarding.html     # 4-step onboarding
│       ├── dashboard.html      # Main dashboard
│       ├── coach-chat.html     # AI conversational chat
│       ├── training-calendar.html # Interactive calendar
│       ├── profile.html        # Athlete profile & progress
│       ├── invite.html         # Invite code entry
│       ├── css/                # Stylesheets
│       │   ├── global.css      # Global styles
│       │   ├── chat.css        # Chat interface styles
│       │   ├── profile.css     # Profile page styles
│       │   └── calendar-styles.css
│       └── js/                 # JavaScript
│           ├── global.js       # Shared utilities
│           ├── chat.js         # Chat functionality
│           ├── profile.js      # Profile management
│           └── onboarding-core.js
├── workflows/                  # n8n workflow exports
│   ├── AI Agent Chat (4).json  # Conversational AI coaching
│   ├── Strava API Callback (5).json
│   ├── Athletes API - Get Workouts.json
│   ├── RAG Training Plan Generator.json
│   ├── Generate AI Feedback (Ollama).json
│   ├── Register Athlete.json
│   └── invite code validation.json
├── scripts/                    # Utility scripts
│   └── export-workflows-cli.sh # Workflow backup
├── docs/                       # Documentation
│   └── HANDOVER.md            # Detailed technical notes
├── data/                      # Database data
├── migrations/                # Database migrations
├── nginx/                     # Nginx configuration
├── certbot/                   SSL certificates
└── backups/                   # System backups
```

## 🔄 Core Coaching Scenarios

### 1. **Planning Conversations**
- **Athlete**: "What's my plan for the week?"
- **Coach**: Analyzes phase/goals → Recommends hours/TSS → Presents action buttons

### 2. **Adaptation Conversations**
- **Athlete**: "It's too cold to train outdoors"
- **Coach**: Suggests indoor alternatives → Maintains training stress → Creates .fit file

### 3. **Feedback Loop Conversations**
- **After ride**: Coach analyzes compliance → Explains physiological impact → Suggests adjustments
- **Weekly**: Reviews compliance trends → Shows progress → Adjusts next week
- **Monthly**: Analyzes block progress → Updates goals → Generates next block

### 4. **Substitution Conversations**
- **Athlete**: "Can I substitute for a chain gang?"
- **Coach**: Compares physiological impact → Recommends adjustments → Updates plan

## 🛠 Tool Architecture

### **Data Retrieval Tools**
- `get_athlete_profile` - FTP, weight, goals, availability
- `get_training_phase` - Current phase, rationale, progress
- `get_recent_rides` - Last 5 rides with TSS, power, HR
- `search_training_knowledge` - Evidence-based principles (pgvector RAG)

### **Analysis Tools**
- `analyze_session_compliance` - Planned vs. actual performance
- `calculate_training_adaptations` - Physiological impact mapping
- `track_goal_progress` - Progress toward FTP/event goals
- `analyze_fitness_trends` - CTL, ATL, TSB tracking

### **Action Tools**
- `suggest_workout_adaptation` - Weather/schedule alternatives
- `generate_weekly_schedule` - Calls existing workflow
- `create_workout_suggestion` - Generates .fit via existing workflow

## 🔐 Authentication Flow

1. **Invite Code Entry**: User enters unique invite code at `/invite.html`
2. **Code Validation**: n8n workflow validates code and creates session
3. **Strava OAuth**: User connects Strava account (enabled after code validation)
4. **Session Creation**: Secure HTTP-only cookie with athlete ID
5. **Onboarding**: 4-step process to set goals, FTP, and event
6. **Dashboard Access**: Full access to coaching features

## 🗄 Database Schema (Key Tables)

### **athletes**
- `id`, `strava_id`, `firstname`, `lastname`, `profile_picture`
- `ftp`, `weight`, `power_zones`, `hr_zones`
- `target_ftp`, `target_weight`, `baseline_ftp`, `baseline_weight`
- `strava_access_token`, `strava_refresh_token`, `strava_token_expires`

### **invite_codes**
- `code` (unique), `created_by`, `created_at`, `expires_at`, `used_by`, `used_at`

### **training_plans**
- `id`, `athlete_id`, `week_start_date`, `total_tss`, `phase`, `status`

### **planned_workouts**
- `id`, `training_plan_id`, `athlete_id`, `scheduled_date`, `workout_type`
- `description`, `intervals_json`, `tss`, `duration_minutes`
- `athlete_feedback_rpe`, `athlete_feedback_notes`

### **training_knowledge** (RAG)
- `id`, `content`, `source`, `embedding` (pgvector)

## 🤖 AI & RAG System

### **Models Used**
- **Primary**: `deepseek-r1:1.5b` - Fast inference, good structured output
- **Embedding**: `nomic-embed-text:latest` - High-quality sentence embeddings

### **RAG Knowledge Base**
Training methodology embedded from:
- Joe Friel's Training Bible
- British Cycling guidelines
- TrainerRoad methodology
- Sports science literature

### **How RAG Works in Conversations**
1. Semantic search finds relevant training guidance
2. Top 3-5 passages injected into AI prompt
3. AI generates evidence-based responses
4. Result: Coaching based on established methodology

## ⚙ Configuration

### **Environment Variables (.env)**
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

# Session
SESSION_SECRET=your_session_secret
```

### **Docker Compose Services**
```yaml
services:
  postgres:     # Database with pgvector extension
  n8n:          # Workflow automation engine
  caddy:        # Reverse proxy + automatic SSL
  ollama:       # Local AI inference (DeepSeek + embeddings)
```

## 🔧 Maintenance

### **Backup Database**
```bash
docker exec ai-cycling-coach-postgres-1 pg_dump -U aicoach_user aicoach_db > backup_$(date +%Y%m%d).sql
```

### **Export Workflows**
```bash
cd ~/ai-cycling-coach/scripts
./export-workflows-cli.sh
```

### **View Logs**
```bash
# n8n logs
docker logs ai-cycling-coach-n8n-1 --tail 100 -f

# All services
docker compose logs -f
```

## 🚧 Implementation Status (v4.1)

### ✅ **Completed**
- Database schema analysis and planning
- Goals update n8n workflow (`/athletes/update-goals`)
- Database columns added (`target_*`, `baseline_*`)
- Profile page basic structure
- Invite code authentication system
- Cookie-based session management

### 🟡 **In Progress**
- Zone formatting implementation
- Progress display logic
- AI Agent Chat integration
- Rich response formatting with buttons

### ⏳ **Next Up**
- Create `invite_codes` table
- Build onboarding page with invite validation
- Create new n8n onboarding callback
- Remove remaining hardcoded athlete IDs

### 📋 **Pending**
- Re-baseline functionality
- Advanced progress visualizations
- Mobile responsiveness polish
- Comprehensive testing

## 📊 Monitoring & Health Checks

### **Database Queries**
```sql
-- Active athletes with sessions
SELECT COUNT(DISTINCT athlete_id) FROM sessions WHERE expires_at > NOW();

-- Plans generated this month
SELECT COUNT(*) FROM training_plans WHERE created_at > NOW() - INTERVAL '30 days';

-- Invite code usage
SELECT COUNT(*) as total, COUNT(used_by) as used FROM invite_codes;
```

### **Health Endpoints**
- `https://yourdomain.com` - Landing page
- `https://yourdomain.com/webhook/health` - System health
- `https://yourdomain.com/n8n/` - n8n admin interface

## 🔒 Security Measures

### **Implemented**
- ✅ HTTPS with automatic SSL (Let's Encrypt)
- ✅ Secure cookies (HTTP-only, Secure, SameSite=Lax)
- ✅ Environment variable secrets
- ✅ Invite code access control
- ✅ No hardcoded athlete IDs
- ✅ Database password protection

### **Planned**
- [ ] API rate limiting
- [ ] Session timeouts
- [ ] CSRF protection
- [ ] Encrypted Strava tokens at rest
- [ ] Audit logging

## 🛣 Roadmap

### **Phase 2: Enhanced Coaching**
- Multi-week plan generation
- Automatic phase transitions
- Advanced compliance analytics
- Social features (clubs/teams)

### **Phase 3: Mobile Experience**
- Progressive Web App (PWA)
- Mobile-optimized interfaces
- Offline workout support
- Push notifications

### **Phase 4: Advanced Analytics**
- Machine learning predictions
- Injury risk assessment
- Performance benchmarking
- Race day recommendations

## 📚 Documentation

- **[HANDOVER.md](docs/HANDOVER.md)** - Detailed technical notes and session history
- **[Design Spec v4.1](Dave's AI Cycle Coach - Updated Design v4.1.md)** - Current implementation blueprint
- **[Strava API Docs](https://developers.strava.com/docs/)** - Strava integration reference
- **[n8n Docs](https://docs.n8n.io/)** - Workflow automation guide

## 🤝 Contributing

This is a personal project with active development. Areas that could benefit from contributions:

1. **Frontend Design** - Improve UI/UX and mobile responsiveness
2. **Testing** - Add automated tests for workflows and interfaces
3. **Documentation** - Expand user guides and API documentation
4. **Training Knowledge** - Add more methodology to RAG system
5. **Security** - Implement additional security measures

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Joe Friel** - Training methodology foundation
- **Strava** - Activity tracking and API
- **n8n** - Workflow automation platform
- **Ollama** - Local AI inference
- **DeepSeek** - AI model provider
- **pgvector** - Vector similarity search

## 📈 Status

**Current Version:** v4.1 (Conversational AI Coaching)  
**Status:** 🚧 Active Development  
**Last Updated:** February 2025

