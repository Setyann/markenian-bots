import os
import asyncio
import aiogram # type: ignore
import dotenv # type: ignore
from handlers.linar_bank.routes import router

dotenv.load_dotenv()
TOKEN = os.getenv("LINAR_BANK_TOKEN")

dp = aiogram.Dispatcher()

dp.include_router(router)

async def main():
    bot = aiogram.Bot(token=TOKEN)
    
    print("Linar Bank is starting...")
    
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")