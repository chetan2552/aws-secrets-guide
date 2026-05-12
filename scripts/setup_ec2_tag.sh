#!/bin/bash
# setup_ec2_tag.sh
# =================
# One-time script to tag your EC2 instance with the Secrets Manager ARN.
# Run this ONCE from your local machine (with aws configure already set up).
#
# Usage:
#   chmod +x scripts/setup_ec2_tag.sh
#   ./scripts/setup_ec2_tag.sh

set -e

# ── Configure these values ──────────────────────────────────────────────────
EC2_INSTANCE_ID="i-0341d6621b0542b11"
SECRET_ARN="arn:aws:secretsmanager:us-east-1:527844782951:secret:nglite-stage-secrets-be-CDIl9l"
REGION="us-east-1"
TAG_KEY="SecretARN"
# ────────────────────────────────────────────────────────────────────────────

echo "Tagging EC2 instance $EC2_INSTANCE_ID with $TAG_KEY..."

aws ec2 create-tags \
    --region "$REGION" \
    --resources "$EC2_INSTANCE_ID" \
    --tags "Key=$TAG_KEY,Value=$SECRET_ARN"

echo "Done! Tag added:"
echo "  Key:   $TAG_KEY"
echo "  Value: $SECRET_ARN"
echo ""
echo "The EC2 instance can now self-discover its secret ARN at runtime."
echo "Run: python examples/method5_ec2_instance_tag.py"
