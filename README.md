# Would You Rather Telegram Bot

A highly modular and fully-featured "Would You Rather" game bot for Telegram, built using `aiogram` 3.x and Python 3. It supports single-player, group chat, and inline modes with dynamic 15-second voting timers and percent-based results.

## Features

- **Single Player:** Play directly with the bot via `/next` or `/nsfw`. Votes are registered instantly.
- **Group Play:** Add the bot to a group. Type `/next@YourBotUsername` to start a round. Once the first player votes, a 15-second timer starts, allowing others to join in before the final percentages are revealed.
- **Inline Mode:** Type `@YourBotUsername` in any chat to select a question and challenge a friend. It supports the same dynamic 15-second voting timer as group play!
- **Keep-Alive Server:** Includes a lightweight Flask server built-in to keep the bot alive if hosted on platforms like Replit or Render.

## Project Structure

The project is structured for high maintainability with individual files for commands and handlers:

```text
would_you_rather_bot/
├── .env                       # Stores environment variables (BOT_TOKEN)
├── requirements.txt           # Python dependencies
├── main.py                    # Entry point: initializes bot and registers routers
├── keep_alive.py              # Background Flask server to keep the bot running
├── config/
│   └── settings.py            # Environment variable loader
├── database/
│   └── questions.py           # Mock database of SFW and NSFW questions
├── services/
│   └── game_session.py        # Logic for managing active games and timers
├── handlers/
│   ├── commands/
│   │   ├── start.py           # /start command
│   │   ├── help.py            # /help command
│   │   ├── feedback.py        # /feedback command
│   │   ├── next.py            # /next command
│   │   └── nsfw.py            # /nsfw command
│   ├── callbacks/
│   │   ├── vote.py            # Handles inline voting clicks
│   │   └── next_question.py   # Handles 'Next Question' button
│   └── inline.py              # Handles inline mode (@botname) queries
└── utils/
    └── formatting.py          # Helper functions to build dynamic message texts
```

## Installation & Setup

1. **Clone or Download** the repository.
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment:**
   Create a `.env` file in the root directory and add your Telegram Bot Token:
   ```env
   BOT_TOKEN=your_bot_token_here
   ```
4. **Run the Bot:**
   ```bash
   python main.py
   ```

## Bot Commands

- `/start` - Displays the welcome message and instructions.
- `/help` - Displays the help message.
- `/next` - Get a new SFW Would You Rather question.
- `/nsfw` - Get a new NSFW (18+) Would You Rather question.
- `/feedback` - Send feedback or suggestions to the developers.

## Tech Stack
- [Python 3](https://www.python.org/)
- [aiogram 3.x](https://docs.aiogram.dev/en/latest/) (Async Telegram Bot API framework)
- [Flask](https://flask.palletsprojects.com/) (For keep-alive background thread)
"# RatherX_Aclbot" 
