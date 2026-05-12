"""
Method 3: IAM Role Loop (Try / Skip)
======================================
Best for: Low secret count (< 20), when no other method is possible
Speed: 🐌 Slow for 100+ secrets — makes one API call per unauthorized secret
Names in code: None — relies entirely on IAM deny behaviour

How it works:
  1. List all secrets in the account (metadata only, no values)
  2. Try GetSecretValue on each ARN
  3. Skip (AccessDeniedException) secrets you're not allowed to read
  4. Return the first one that succeeds

⚠️  WARNING: With 100+ secrets, this can take 10–30 seconds.
    Prefer Method 1 (tags) or Method 5 (EC2 tag) instead.
"""

import boto3
import json
from botocore.exceptions import ClientError


def get_authorized_secret(region: str = "us-east-1") -> dict | str | None:
    """
    Loop through all secrets, return the first one this identity can read.
    Relies on IAM GetSecretValue being scoped to a specific ARN prefix.
    """
    client = boto3.client("secretsmanager", region_name=region)

    try:
        # Paginate through ALL secrets (metadata only — no values exposed)
        paginator = client.get_paginator("list_secrets")

        for page in paginator.paginate():
            for secret in page.get("SecretList", []):
                target_arn = secret["ARN"]

                try:
                    response = client.get_secret_value(SecretId=target_arn)
                    print(f"✅ Authorized secret found: {target_arn}")

                    secret_string = response.get("SecretString")
                    try:
                        return json.loads(secret_string)
                    except (json.JSONDecodeError, TypeError):
                        return secret_string

                except ClientError as e:
                    if e.response["Error"]["Code"] == "AccessDeniedException":
                        print(f"⏭  Skipping (no access): {secret['Name']}")
                        continue
                    else:
                        print(f"Unexpected error on {target_arn}: {e}")
                        continue

        return None  # Nothing found

    except ClientError as e:
        print(f"AWS Error: {e}")
        return None


if __name__ == "__main__":
    result = get_authorized_secret()
    print("Secret:", result)
