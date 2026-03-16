from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.central_bank.routes import router

load_dotenv()
TOKEN = getenv("CENTRAL_BANK_TOKEN")

dp = Dispatcher()

dp.include_router(router)

async def main():
    bot = Bot(token=TOKEN)
    
    print("Central Bank is starting...")
    
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")