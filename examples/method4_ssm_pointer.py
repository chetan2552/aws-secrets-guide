"""
Method 4: SSM Parameter Store as a Pointer
============================================
Best for: Multi-environment setups, when you want one config location
Speed: ⚡ Fast — exactly 2 API calls total
Names in code: Only the SSM path (e.g. /myapp/secret-arn) — not the secret name

The pattern:
  SSM Parameter /myapp/secret-arn  →  stores the full secret ARN
  Code reads SSM path  →  gets ARN  →  fetches secret value

This is useful because:
  - The SSM path never changes even when secret ARNs rotate
  - You can change which secret is used by updating SSM only
  - Code is completely generic and reusable

One-time setup (AWS CLI):
  aws ssm put-parameter \\
      --name "/myapp/secret-arn" \\
      --value "arn:aws:secretsmanager:us-east-1:527844782951:secret:nglite-stage-secrets-be-CDIl9l" \\
      --type "String" \\
      --region us-east-1
"""

import boto3
import json
from botocore.exceptions import ClientError

# The SSM path is not a secret — it's just an infrastructure pointer
SSM_PATH = "/myapp/secret-arn"


def get_secret_via_ssm(ssm_path: str = SSM_PATH, region: str = "us-east-1") -> dict | str | None:
    """
    Step 1: Read the secret ARN from SSM Parameter Store.
    Step 2: Use that ARN to fetch the actual secret value.
    """
    session = boto3.Session(region_name=region)
    ssm = session.client("ssm")
    sm  = session.client("secretsmanager")

    try:
        # Step 1: Get the ARN stored in SSM (fast single call)
        param = ssm.get_parameter(Name=ssm_path)
        secret_arn = param["Parameter"]["Value"]
        print(f"Resolved ARN from SSM: {secret_arn}")

        # Step 2: Fetch the actual secret using the resolved ARN
        response = sm.get_secret_value(SecretId=secret_arn)
        secret_string = response.get("SecretString")

        try:
            return json.loads(secret_string)
        except (json.JSONDecodeError, TypeError):
            return secret_string

    except ClientError as e:
        print(f"AWS Error: {e}")
        return None


if __name__ == "__main__":
    result = get_secret_via_ssm()
    print("Secret:", result)
