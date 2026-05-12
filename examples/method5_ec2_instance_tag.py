"""
Method 5: EC2 Instance Tag → ARN Detection (⭐ RECOMMENDED)
=============================================================
Best for: EC2 instances — this is the gold standard
Speed: ⚡⚡ Fastest — 3 API calls, instant return
Names in code: NOTHING — not even a tag key name

How it works:
  1. Read this EC2 instance's own ID from the metadata service (169.254.169.254)
  2. Call ec2.describe_instances to get ALL tags on this instance
  3. Scan every tag VALUE for one that matches a Secrets Manager ARN pattern
  4. Call get_secret_value(SecretId=that_arn) → done

One-time AWS setup:
  1. Add tag to your EC2 instance:
       Key:   SecretARN
       Value: arn:aws:secretsmanager:us-east-1:527844782951:secret:nglite-stage-secrets-be-CDIl9l

  2. Apply iam-policies/ec2-recommended.json to the EC2 IAM role

This file has ZERO sensitive values. It is fully reusable across any project.
"""

import boto3
import json
import re
import requests
from botocore.exceptions import ClientError

# Standard AWS Secrets Manager ARN pattern — this is a public AWS format, not your secret name
_SECRETS_ARN_PATTERN = re.compile(
    r"arn:aws:secretsmanager:[a-z0-9-]+:\d{12}:secret:.+"
)


def _get_instance_id() -> str:
    """Fetch this EC2 instance's ID from the Instance Metadata Service v2."""
    # Step 1: Get IMDSv2 token (required on modern EC2 instances)
    token = requests.put(
        "http://169.254.169.254/latest/api/token",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
        timeout=2,
    ).text

    # Step 2: Use token to get instance ID
    instance_id = requests.get(
        "http://169.254.169.254/latest/meta-data/instance-id",
        headers={"X-aws-ec2-metadata-token": token},
        timeout=2,
    ).text

    return instance_id


def _find_secret_arn_in_tags(instance_id: str, region: str) -> str | None:
    """Read all EC2 tags on this instance. Return the tag VALUE that is a Secrets Manager ARN."""
    ec2 = boto3.client("ec2", region_name=region)
    response = ec2.describe_instances(InstanceIds=[instance_id])

    tags = response["Reservations"][0]["Instances"][0].get("Tags", [])

    for tag in tags:
        if _SECRETS_ARN_PATTERN.match(tag["Value"]):
            print(f"Found Secrets Manager ARN in tag '{tag['Key']}'")
            return tag["Value"]

    return None


def get_secret(region: str = "us-east-1") -> dict | str | None:
    """
    Fetch the secret whose ARN is stored as a tag on this EC2 instance.
    No secret name, no hardcoded ARN, no tag key name, no credentials.
    """
    try:
        instance_id = _get_instance_id()
        print(f"Instance ID: {instance_id}")

        secret_arn = _find_secret_arn_in_tags(instance_id, region)

        if not secret_arn:
            print("Error: No Secrets Manager ARN found in any EC2 tag.")
            return None

        # Fetch the secret directly
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_arn)
        secret_string = response.get("SecretString")

        try:
            return json.loads(secret_string)
        except (json.JSONDecodeError, TypeError):
            return secret_string

    except requests.exceptions.ConnectionError:
        print("Error: Cannot reach EC2 metadata service. Are you running on EC2?")
        print("For local development, use method6_full_auto_detect.py instead.")
        return None
    except ClientError as e:
        print(f"AWS Error: {e}")
        return None


if __name__ == "__main__":
    result = get_secret()
    print("Secret:", result)
