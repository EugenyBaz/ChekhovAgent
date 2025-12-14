import asyncio

from app.clients.google_sheets import sheets_client


async def test_find_department():
    result = await sheets_client.find_department("Chekhov Sport")
    print(result)


if __name__ == "__main__":
    asyncio.run(test_find_department())
