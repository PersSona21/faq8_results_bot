import nest_asyncio
nest_asyncio.apply()

from parser import parse_grades
from bot import run_bot
import asyncio
import threading
import time


def run_parser_periodically(interval_minutes=10):
    while True:
        print("🔄 Обновляю данные...")
        parse_grades()
        time.sleep(interval_minutes * 60)


async def main():
    # Запуск парсера в отдельном потоке
    parser_thread = threading.Thread(target=run_parser_periodically, args=(10,), daemon=True)
    parser_thread.start()

    await run_bot()


if __name__ == '__main__':
    asyncio.run(main())