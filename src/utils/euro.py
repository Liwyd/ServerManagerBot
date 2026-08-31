import aiohttp


async def get_euro() -> int:
    """Fetch EUR to TRY exchange rate."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url="https://api.exchangerate-api.com/v4/latest/EUR") as res:
            res.raise_for_status()
            data = await res.json()
            return int(data["rates"]["TRY"])
