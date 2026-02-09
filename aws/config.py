import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

aws_access_key_id = os.getenv('aws_access_key_id')
aws_secret_access_key = os.getenv('aws_secret_access_key')
aws_session_token = os.getenv('aws_session_token')

sqs = boto3.client(
    "sqs",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_session_token=aws_session_token,
    region_name="us-east-1",
    config=Config(
        retries={"max_attempts": 3},
        connect_timeout=5,
        read_timeout=5,
        tcp_keepalive=False
    )
)
