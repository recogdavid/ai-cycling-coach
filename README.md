# ai-cycling-coach
AI Cycling Coach
## 🚴‍♂️ AI Cycling Coach – Infrastructure Overview

This repository contains the **Dockerized infrastructure** for the AI Cycling Coach platform.
It provisions a complete and secure environment to host **n8n** (the automation/workflow engine) with a **PostgreSQL** database and an **Nginx + Certbot** reverse-proxy for automatic HTTPS certificates.

---

### 🧱 Stack Summary

| Service      | Role                                        | Ports                   | Notes                                          |
| ------------ | ------------------------------------------- | ----------------------- | ---------------------------------------------- |
| **Postgres** | Persistent database for n8n                 | `5432` (internal only)  | Uses a mounted volume under `./data/postgres`  |
| **n8n**      | Workflow automation editor and runtime      | `5678` (proxied)        | Accessible via HTTPS at `https://dabosch.fit`  |
| **Nginx**    | Reverse proxy, HTTPS termination            | `80` → redirect → `443` | Serves SSL and proxies requests to n8n         |
| **Certbot**  | Automated Let’s Encrypt certificate renewal | —                       | Renews every 12 hours using webroot validation |

---

### 🚀 Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/recogdavid/ai-cycling-coach.git
   cd ai-cycling-coach
   ```

2. **Create a `.env` file**

   ```bash
   cp .env.example .env
   ```

   Edit values such as:

   ```bash
   N8N_HOST=dabosch.fit
   N8N_PROTOCOL=https
   N8N_BASIC_AUTH_USER=admin
   N8N_BASIC_AUTH_PASSWORD=<strong_password>
   N8N_ENCRYPTION_KEY=<random_secure_key>
   POSTGRES_USER=aicoach_user
   POSTGRES_PASSWORD=<strong_db_password>
   POSTGRES_DB=aicoach_db
   ```

3. **Bring the stack up**

   ```bash
   docker compose up -d
   ```

4. **Access n8n**

   * Visit 👉 [`https://dabosch.fit`](https://dabosch.fit)
   * Log in using your basic-auth credentials.
   * The editor UI is now live and secure.

---

### 🧰 Maintenance

| Task                        | Command                                            |
| --------------------------- | -------------------------------------------------- |
| View logs                   | `docker compose logs -f n8n`                       |
| Restart a service           | `docker compose restart <service>`                 |
| Stop all containers         | `docker compose down`                              |
| Check certificate expiry    | `docker compose exec certbot certbot certificates` |
| Manually renew certificates | `docker compose run --rm certbot renew`            |

---

### 🔒 Security Notes

* HTTPS handled automatically by **Let’s Encrypt + Certbot**
* Basic Auth protects the n8n editor
* `.env`, `data/`, `certbot/conf/`, and `ssl/` are ignored by Git
* Database and workflow data persist in `./data/`

---

### 🏷️ Version Info

Current baseline: **v0.1-https-stack**
Stable configuration with working HTTPS, reverse proxy, and persistent Postgres database.

---


