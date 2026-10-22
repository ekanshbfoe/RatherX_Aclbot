import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import orjson
from aiogram.client.session.aiohttp import AiohttpSession
from config.settings import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, WEBHOOK_SECRET

# Import all routers
from handlers.commands.start import router as start_router
from handlers.commands.help import router as help_router
from handlers.commands.feedback import router as feedback_router
from handlers.commands.next import router as next_router
from handlers.commands.nsfw import router as nsfw_router
from handlers.commands.categories import router as categories_router
from handlers.commands.xcouple import router as xcouple_router
from handlers.commands.mylove import router as mylove_router
from handlers.commands.compatibility import router as compatibility_router
from handlers.commands.admin_broadcast import router as admin_broadcast_router
from handlers.callbacks.vote import router as vote_router
from handlers.callbacks.xcouple_board import router as xcouple_board_router
from handlers.inline import router as inline_router
from handlers.events.notifications import router as notifications_router
from handlers.commands.alive import router as alive_router

logging.basicConfig(level=logging.INFO)

async def health_check(request):
    return web.Response(text="RatherX Bot is running healthy!", status=200)

async def on_startup(bot: Bot):
    # Start periodic game session cleanup
    from services.game_session import cleanup_stale_sessions
    from database.questions import load_questions
    load_questions()
    asyncio.create_task(cleanup_stale_sessions())
    
    webhook_url = os.getenv("WEBHOOK_URL", "https://ratherx-aclbot.onrender.com")
    logging.info(f"Setting webhook to: {webhook_url}/webhook")
    await bot.set_webhook(
        url=f"{webhook_url}/webhook", 
        drop_pending_updates=True,
        allowed_updates=["message", "inline_query", "chosen_inline_result", "callback_query", "my_chat_member"],
        secret_token=WEBHOOK_SECRET or None
    )

async def on_shutdown(bot: Bot):
    await bot.session.close()

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        logging.error("Please set your BOT_TOKEN in the .env file")
        return

    session = AiohttpSession(
        json_loads=orjson.loads,
        json_dumps=lambda data: orjson.dumps(data).decode("utf-8")
    )
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()

    # Register routers
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(feedback_router)
    dp.include_router(next_router)
    dp.include_router(nsfw_router)
    dp.include_router(categories_router)
    dp.include_router(xcouple_router)
    dp.include_router(mylove_router)
    dp.include_router(compatibility_router)
    dp.include_router(admin_broadcast_router)
    
    dp.include_router(vote_router)
    dp.include_router(xcouple_board_router)
    
    dp.include_router(inline_router)
    dp.include_router(notifications_router)
    dp.include_router(alive_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    app = web.Application()
    app.router.add_get("/", health_check)
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET or None
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)

    PORT = int(os.getenv("PORT", 8080))
    HOST = "0.0.0.0"

    logging.info(f"Starting aiohttp webhook server on {HOST}:{PORT}...")
    web.run_app(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main()
