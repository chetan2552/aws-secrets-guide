# Local Development Guide

## Setup (one-time)

```bash
# Install AWS CLI if not already installed
# https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html

# Configure your credentials
aws configure
# AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name [None]: us-east-1
# Default output format [None]: json
```

Credentials are stored in `~/.aws/credentials` — **never in your code, never committed to git**.

## Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows PowerShell

pip install boto3 requests
```

## Running scripts locally

All methods work locally **except** Method 5 (EC2-only).

Use **Method 6** (`method6_full_auto_detect.py`) — it auto-detects the environment and works both locally and on EC2 without any code changes.

```bash
python examples/method6_full_auto_detect.py
# Output: 💻 Running locally — using AWS CLI profile credentials
#         Resolved ARN: arn:aws:secretsmanager:...
#         Secret: {...}
```

## Environment variables (alternative to aws configure)

```bash
# Linux / Mac
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Windows PowerShell
$env:AWS_ACCESS_KEY_ID="your-key"
$env:AWS_SECRET_ACCESS_KEY="your-secret"
$env:AWS_DEFAULT_REGION="us-east-1"
```

boto3 reads these automatically — no code changes needed.

## Verifying your identity

```bash
aws sts get-caller-identity
# Returns: Account, UserId, ARN of whoever boto3 will authenticate as
```

## .gitignore

Make sure these are in your `.gitignore`:

```
.env
*.env
venv/
__pycache__/
.aws/
```
