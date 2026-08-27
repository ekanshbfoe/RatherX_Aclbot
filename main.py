import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config.settings import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT

# Import all routers
from handlers.commands.start import router as start_router
from handlers.commands.help import router as help_router
from handlers.commands.feedback import router as feedback_router
from handlers.commands.next import router as next_router
from handlers.commands.nsfw import router as nsfw_router
from handlers.commands.xcouple import router as xcouple_router
from handlers.commands.mylove import router as mylove_router
from handlers.commands.compatibility import router as compatibility_router
from handlers.commands.admin_broadcast import router as admin_broadcast_router
from handlers.callbacks.vote import router as vote_router
from handlers.callbacks.next_question import router as next_question_router
from handlers.callbacks.xcouple_board import router as xcouple_board_router
from handlers.inline import router as inline_router
from handlers.events.notifications import router as notifications_router

logging.basicConfig(level=logging.INFO)

async def on_startup(bot: Bot):
    # Start periodic game session cleanup
    from services.game_session import cleanup_stale_sessions
    from database.questions import load_questions
    load_questions()
    asyncio.create_task(cleanup_stale_sessions())
    
    if WEBHOOK_URL:
        await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}", allowed_updates=["message", "inline_query", "callback_query", "my_chat_member"])

async def on_shutdown(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        logging.error("Please set your BOT_TOKEN in the .env file")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Register routers
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(feedback_router)
    dp.include_router(next_router)
    dp.include_router(nsfw_router)
    dp.include_router(xcouple_router)
    dp.include_router(mylove_router)
    dp.include_router(compatibility_router)
    dp.include_router(admin_broadcast_router)
    
    dp.include_router(vote_router)
    dp.include_router(next_question_router)
    dp.include_router(xcouple_board_router)
    
    dp.include_router(inline_router)
    dp.include_router(notifications_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)

    logging.info(f"Starting aiohttp webhook server on {WEBAPP_HOST}:{WEBAPP_PORT}...")
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    main()
