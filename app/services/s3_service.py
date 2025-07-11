from app.utils.s3 import generate_presigned_url


async def generate_urls(keys):
    urls = []

    for key in keys:
        url = generate_presigned_url(key)

        urls.append(url)

    return urls
