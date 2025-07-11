from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

config = Config(".env")
oauth = OAuth(config)

oauth.register(
    client_id=config("GOOGLE_CLIENT_ID"),
    client_secret=config("GOOGLE_CLIENT_SECRET"),
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
