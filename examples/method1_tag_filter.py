"""
Method 1: batch_get_secret_value with Tag Filter
=================================================
Best for: Any environment where you can tag secrets
Speed: ⚡ Fast — single API call, AWS filters server-side
Names in code: Tag key/value only (not secret name or ARN)

Prerequisites:
  1. Tag your secret in AWS Console:
       Key:   App
       Value: Nglite
  2. Apply iam-policies/batch-get-with-tags.json to your IAM user/role
"""

import boto3
import json
from botocore.exceptions import ClientError


def get_secret_by_tag(tag_key: str, tag_value: str, region: str = "us-east-1") -> dict | str | None:
    """
    Fetch a secret using a tag filter. No secret name or ARN required.

    Args:
        tag_key:   The tag key on the secret (e.g. "App")
        tag_value: The tag value on the secret (e.g. "Nglite")
        region:    AWS region

    Returns:
        Parsed dict if secret is JSON, raw string otherwise, None on failure.
    """
    # boto3 uses IAM Role on EC2, or ~/.aws/credentials locally
    client = boto3.client("secretsmanager", region_name=region)

    try:
        response = client.batch_get_secret_value(
            Filters=[
                {"Key": "tag-key",   "Values": [tag_key]},
                {"Key": "tag-value", "Values": [tag_value]},
            ]
        )

        secrets = response.get("SecretValues", [])

        if not secrets:
            print("No secret found with the given tag.")
            return None

        secret_string = secrets[0].get("SecretString")

        try:
            return json.loads(secret_string)
        except (json.JSONDecodeError, TypeError):
            return secret_string

    except ClientError as e:
        print(f"AWS Error: {e}")
        return None


if __name__ == "__main__":
    # Only tag key/value here — not the secret name itself
    result = get_secret_by_tag(tag_key="App", tag_value="Nglite")
    print("Secret:", result)
