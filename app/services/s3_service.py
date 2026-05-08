from app.storage import get_storage


async def generate_urls(keys):
    storage = get_storage()
    urls = []

    for key in keys:
        url = await storage.generate_read_url(key)

        urls.append(url)

    return urls
