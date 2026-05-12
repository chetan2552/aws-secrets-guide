"""
Method 6: Full Auto-Detect — Works Locally AND on EC2
=======================================================
Best for: Development teams who want one script that runs everywhere
Speed: ⚡ Fast in both environments
Names in code: Nothing on EC2 path. Local path uses ListSecrets (finds authorized one).

How it works:
  - On EC2:  reads ARN from instance tags (Method 5)
  - Locally: lists secrets, finds the one your AWS CLI profile can access

Local setup (one-time):
  aws configure
  # Enter your access key, secret key, region
  # Stored in ~/.aws/credentials — never in code, never committed to git
"""

import boto3
import json
import re
import requests
from botocore.exceptions import ClientError

_SECRETS_ARN_PATTERN = re.compile(
    r"arn:aws:secretsmanager:[a-z0-9-]+:\d{12}:secret:.+"
)


# ─────────────────────────────────────────────
# Environment Detection
# ─────────────────────────────────────────────

def _is_on_ec2() -> bool:
    """Check if we're running on an EC2 instance by probing the metadata service."""
    try:
        response = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=1,
        )
        return response.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────
# EC2 Path (Method 5)
# ─────────────────────────────────────────────

def _get_secret_arn_from_ec2_tags(region: str) -> str | None:
    """Read all EC2 tags, find the one whose value is a Secrets Manager ARN."""
    token = requests.put(
        "http://169.254.169.254/latest/api/token",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
        timeout=2,
    ).text

    instance_id = requests.get(
        "http://169.254.169.254/latest/meta-data/instance-id",
        headers={"X-aws-ec2-metadata-token": token},
        timeout=2,
    ).text

    ec2 = boto3.client("ec2", region_name=region)
    response = ec2.describe_instances(InstanceIds=[instance_id])
    tags = response["Reservations"][0]["Instances"][0].get("Tags", [])

    for tag in tags:
        if _SECRETS_ARN_PATTERN.match(tag["Value"]):
            return tag["Value"]

    return None


# ─────────────────────────────────────────────
# Local Path (authorized secret discovery)
# ─────────────────────────────────────────────

def _get_secret_arn_locally(region: str) -> str | None:
    """
    For local use: list all secrets and try to fetch each one.
    Returns the ARN of the first secret this identity is authorized to read.
    Uses ~/.aws/credentials automatically (set via `aws configure`).
    """
    client = boto3.client("secretsmanager", region_name=region)

    paginator = client.get_paginator("list_secrets")
    for page in paginator.paginate():
        for secret in page.get("SecretList", []):
            arn = secret["ARN"]
            try:
                # A cheap describe call to check access before fetching value
                client.describe_secret(SecretId=arn)
                client.get_secret_value(SecretId=arn)
                return arn
            except ClientError:
                continue

    return None


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def get_secret(region: str = "us-east-1") -> dict | str | None:
    """
    Universal secret fetcher. Same code, same function, works on EC2 and locally.
    """
    if _is_on_ec2():
        print("🖥  Running on EC2 — reading ARN from instance tags")
        secret_arn = _get_secret_arn_from_ec2_tags(region)
    else:
        print("💻  Running locally — using AWS CLI profile credentials")
        secret_arn = _get_secret_arn_locally(region)

    if not secret_arn:
        print("Error: Could not resolve a secret ARN in this environment.")
        return None

    print(f"Resolved ARN: {secret_arn}")

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
    result = get_secret()
    print("Secret:", result)
