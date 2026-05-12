"""
Method 2: ARN via Environment Variable
=======================================
Best for: CI/CD pipelines, Docker, ECS task definitions
Speed: ⚡ Fast — direct GetSecretValue call
Names in code: None — ARN comes from environment at runtime

Setup:
  EC2 / Linux:
    export SECRET_ARN="arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret-abc123"

  Or set it permanently in /etc/environment (EC2):
    echo 'SECRET_ARN=arn:aws:...' | sudo tee -a /etc/environment
    source /etc/environment

  Docker:
    docker run -e SECRET_ARN="arn:aws:..." your-image

  ECS Task Definition:
    "environment": [{ "name": "SECRET_ARN", "value": "arn:aws:..." }]
"""

import boto3
import json
import os
from botocore.exceptions import ClientError


def get_secret_from_env(region: str = "us-east-1") -> dict | str | None:
    """
    Fetch a secret whose ARN is injected via the SECRET_ARN environment variable.
    No secret name, no ARN, no tag anywhere in this file.
    """
    secret_arn = os.environ.get("SECRET_ARN")

    if not secret_arn:
        print("Error: SECRET_ARN environment variable is not set.")
        print("Set it with: export SECRET_ARN='arn:aws:secretsmanager:...'")
        return None

    # boto3 auto-detects credentials: EC2 IAM role, ~/.aws/credentials, or env vars
    client = boto3.client("secretsmanager", region_name=region)

    try:
        response = client.get_secret_value(SecretId=secret_arn)
        secret_string = response.get("SecretString")

        try:
            return json.loads(secret_string)
        except (json.JSONDecodeError, TypeError):
            return secret_string

    except ClientError as e:
        print(f"AWS Error: {e}")
        return None


if __name__ == "__main__":
    result = get_secret_from_env()
    print("Secret:", result)
