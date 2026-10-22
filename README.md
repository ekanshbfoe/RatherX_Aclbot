<div align="center">
  <h1>🔥 RatherX_Aclbot</h1>
  <p><b>The ultimate "Would You Rather" Telegram experience. Fast. Social. Scalable.</b></p>
  <p><i>Proudly built by the <b>ACL Community</b>.</i></p>

  ![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
  ![License](https://img.shields.io/badge/License-MIT-green.svg)
  ![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
</div>

---

## 🌟 Features Showcase

RatherX brings unparalleled interactive matchmaking and fast-paced gaming directly to Telegram chats.

### 🎮 Core Gameplay
- **Rapid-Fire Engine:** Play random (`/next`) or spicy (`/nsfw`) questions instantly.
- **17 Categories:** `/categories` opens a menu of 2,100+ questions with real human vote percentages, and **Next Question** stays in the chosen category.
- **Dynamic Group Play:** In group chats, the first vote locks in a 15-second countdown timer! 
- **Inline Mode:** Type `@RatherX_Aclbot` in any chat to instantly beam a challenge to your friends. Add a category name (`@RatherX_Aclbot money`) to pick one. Your 3 most recently used categories show at the top (🕘). *Needs inline feedback enabled in @BotFather (`/setinlinefeedback`).*

### 🗂️ Categories
🤔 Daily · 💰 Money · 🎬 Celebrity · 🤢 Gross · 🏕 Survival · 🎓 School · 💬 Social · 😈 Deal with the Devil · 🍕 Food · 🏆 Sports · 📅 Normal · 🔥 Extreme · 🔮 Fantasy · 🌀 Hard · 💖 Love Life · ⏳ Time Travel · 🌶 NSFW

Questions live in `data/questions_<category>.json` and come from [Would_You_Rather_questions_with_human_votes](https://github.com/ekanshbfoe/Would_You_Rather_questions_with_human_votes). To add a category, drop in a new file with the same schema and add it to `database/categories.py`.

### 💞 Advanced Matchmaking
Powered by our proprietary **Normalized Weighted Score** algorithm, the bot secretly learns how users vote and builds affinity maps in real-time.
- **`/xcouple`:** View the server's Couple Board showing the top 5 most compatible pairs in the group.
- **`/mylove`:** Get a secret DM from the bot revealing your top 5 secret admirers in the group.
- **`/compatibility @user`:** Run an on-demand scan between yourself and any other user.

### 🛠️ Admin & Support Ecosystem
- **`/feedback` FSM System:** Users can submit ideas/bugs (text, photo, or video). Tickets are sent to the admin group with inline buttons (`[Fix]`, `[Ignore]`, `[Added]`) for instant triage.
- **`/broadcast` Engine:** A detached background engine for safely broadcasting announcements to the entire Supabase user base with built-in batching and rate-limiting.
- **Silent Analytics:** Instantly receive beautiful HTML alerts in a dedicated Admin Topic whenever a new user starts the bot or the bot is added to a new group!

---

## 🚀 Architecture Upgrades (v2.0)
This bot has undergone a massive architectural overhaul for production-grade scalability.
1. **aiohttp Webhooks:** We migrated away from Long Polling. The bot now runs on a lightning-fast `aiohttp` web server, making it fully stateless, scale-to-zero compatible, and perfect for platforms like Render and Heroku.
2. **Supabase (PostgreSQL):** All in-memory dictionaries have been ripped out. Votes, matchmaking data, and user registries are now securely persisted in Supabase via an asynchronous client.
3. **True Fire-and-Forget:** All heavy database inserts and matchmaking calculations are detached into `asyncio` background tasks to guarantee the Telegram UI updates instantly (zero perceived latency).

---

## 📁 Project Structure

```text
📦 RatherX_Aclbot
├── 📁 config
│   └── 📄 settings.py          # Centralized Environment Variables
├── 📁 data                     # questions_<category>.json (17 files)
├── 📁 database
│   ├── 📄 categories.py        # Category list (key, emoji, label)
│   ├── 📄 questions.py         # Loads question banks by category
│   └── 📄 supabase_client.py   # Async Supabase Postgres client
├── 📁 handlers
│   ├── 📁 callbacks            # Interactive Button Handlers
│   │   ├── 📄 vote.py          # Fire-and-forget voting logic
│   │   └── 📄 xcouple_board.py
│   ├── 📁 commands             # Chat Commands
│   │   ├── 📄 admin_broadcast.py
│   │   ├── 📄 categories.py    # /categories menu
│   │   ├── 📄 compatibility.py
│   │   ├── 📄 feedback.py      # FSM Ticket System
│   │   ├── 📄 help.py
│   │   ├── 📄 mylove.py
│   │   ├── 📄 next.py
│   │   ├── 📄 nsfw.py
│   │   ├── 📄 start.py         # Smart New-User Tracking
│   │   └── 📄 xcouple.py
│   ├── 📁 events
│   │   └── 📄 notifications.py # ChatMemberUpdated hooks
│   └── 📄 inline.py            # Inline Query Matchmaking
├── 📁 services
│   └── 📄 game_session.py      # Matchmaking Math & DB Fallbacks
├── 📁 migrations               # One-off Supabase SQL migrations
├── 📄 .env.example
├── 📄 main.py                  # aiohttp Webhook Entrypoint
├── 📄 requirements.txt
└── 📄 schema.sql               # Supabase Table Definitions
```

---

## ⚙️ Installation & Deployment

### 1. Requirements
- Python 3.11+
- A [Supabase](https://supabase.com/) Account & Project
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Database Setup
Run the SQL queries found in `schema.sql` in your Supabase SQL Editor to generate the `rather_users`, `rather_votes_local`, `rather_votes_global`, and `rather_chat_mappings` tables.

**Upgrading an existing database from the old sfw/nsfw question sets?** Run `migrations/001_category_ids.sql` once, *before* deploying, so existing votes move to the new category question IDs. It refuses to run twice.

Also run `migrations/002_category_history.sql` to add the `rather_category_history` table used for recently used categories.

### 3. Environment Configuration
Copy the `.env.example` file to `.env` and configure your credentials.

| Variable | Description |
| -------- | ----------- |
| `BOT_TOKEN` | Your Telegram Bot Token. |
| `SUPABASE_URL` | Your Supabase Project URL. |
| `SUPABASE_KEY` | Your Supabase `anon` / `publishable` API Key. |
| `OWNER_ID` | Your Telegram User ID (Used to authorize `/broadcast`). |
| `FEEDBACK_GROUP_ID` | The Chat ID where feedback tickets are sent. |
| `FEEDBACK_TOPIC_ID` | The specific thread ID in the feedback group. |
| `NOTIFICATION_LOG_GROUP` | The Chat ID where bot analytics/growth alerts are sent. |
| `NOTIFICATION_LOG_TOPIC_ID` | The specific thread ID in the notifications group. |
| `WEBHOOK_URL` | Your production HTTPS URL (e.g., `https://app.onrender.com`). **Leave blank for local testing!** |
| `WEBHOOK_PATH` | The route to receive payloads (Default: `/webhook`). |
| `WEBAPP_HOST` | Web server host (Default: `0.0.0.0`). |
| `WEBAPP_PORT` | Web server port (Default: `8080`). |

### 4. Running the Bot

**Local Testing (No Webhook):**
Ensure `WEBHOOK_URL` is blank in your `.env`.
```bash
pip install -r requirements.txt
python main.py
```

**Production (Webhooks):**
Set the `WEBHOOK_URL` in your host's environment dashboard. Deploy `main.py` using your host's standard Python web service configuration. The bot will automatically bind to port `8080` and instruct Telegram to stream traffic to your URL!

---

## 📖 Command Reference

| Command | Type | Description |
|---------|------|-------------|
| `/start` | 👤 User | Initializes the bot and sends the welcome menu. |
| `/help` / `.help` | 👤 User | Shows the beautifully formatted command list. |
| `/next` | 🎮 Game | Generates a random SFW question from all categories. |
| `/categories` | 🎮 Game | Opens the category menu (17 categories). |
| `/nsfw` | 🎮 Game | Generates an 18+ NSFW question. |
| `/xcouple` | 💞 Social | Shows the top 5 most compatible pairs in the group. |
| `/mylove` | 💞 Social | DM's the user their top 5 secret admirers in the group. |
| `/compatibility @user` | 💞 Social | Scans compatibility between two specific users. |
| `/feedback` / `.feedback` | 🛠️ Util | Opens the FSM to submit bugs or feature ideas. |
| `/broadcast` | 👑 Admin | *(Reply to a message)* Batch-forwards the message to all users/groups. |

---

<div align="center">
  <i>Built with ❤️ by the ACL Community</i>
</div>
