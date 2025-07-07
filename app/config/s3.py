import boto3
from botocore.config import Config as s3Config
from starlette.config import Config

config = Config(".env")

s3_config = s3Config(
    region_name="ap-northeast-2",
    signature_version="v4",
    retries={"max_attempts": 10, "mode": "standard"},
)

s3_client = boto3.client(
    "s3",
    aws_access_key_id=config("CREDENTIALS_ACCESS_KEY"),
    aws_secret_access_key=config("CREDENTIALS_SECRET_KEY"),
    config=s3_config,
)
