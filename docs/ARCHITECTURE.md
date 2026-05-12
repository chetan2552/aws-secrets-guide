# Architecture Deep Dive

## Why ListSecrets Behaves Differently

`ListSecrets` is an **account-level catalog** operation. It answers: *"What secrets exist in this account/region?"* — not *"What secrets can I read?"*

This is why:
- `Resource: *` is required — it cannot be scoped to a specific ARN
- The `secretsmanager:Name` condition key is **not supported** on `ListSecrets`
- Adding a `Condition` block to `ListSecrets` doesn't filter — it causes `AccessDeniedException`

```
❌ WRONG — this blocks ListSecrets entirely:
{
  "Action": "secretsmanager:ListSecrets",
  "Resource": "*",
  "Condition": {
    "StringLike": { "secretsmanager:Name": "my-secret-*" }  ← NOT SUPPORTED
  }
}

✅ CORRECT — ListSecrets always needs Resource: *
{
  "Action": "secretsmanager:ListSecrets",
  "Resource": "*"
  // No Condition. Scoping happens in the GetSecretValue statement.
}
```

## The "ListSecrets Returns Everything" Problem

When you call `list_secrets()` with `Resource: *`, AWS returns ALL secrets in the account alphabetically — including ones your role cannot read. This is the root cause of the *"picked the wrong secret first"* error.

Solutions:
1. Use `batch_get_secret_value` with a tag filter (server-side filtering)
2. Use EC2 instance tags to store the specific ARN (bypass listing entirely)
3. Use SSM Parameter Store as a pointer (bypass listing entirely)

## EC2 IAM Role Auth Flow

```
Python Script
    │
    ▼
boto3.client('secretsmanager')
    │
    ▼  (no credentials in code)
boto3 SDK checks credentials in order:
    1. Environment variables (AWS_ACCESS_KEY_ID etc.)
    2. ~/.aws/credentials (local dev)
    3. EC2 Instance Metadata Service ← this is used on EC2
    │
    ▼
Temporary credentials from attached IAM Role
    │
    ▼
AWS Secrets Manager API call authenticated
    │
    ▼
IAM checks: does this role have GetSecretValue on this ARN?
    │
    ├── YES → returns secret value ✅
    └── NO  → AccessDeniedException ❌
```

## Why `batch_get_secret_value` Works Without ListSecrets

`BatchGetSecretValue` is a **resource-level** API. When given a tag filter, AWS evaluates the filter server-side and only returns secrets that:
1. Match the filter criteria (tag key/value)
2. The caller has `GetSecretValue` permission on

This means you never see the 99 secrets you can't read — they don't come back at all.

## EC2 Instance Tag Pattern (Why It's the Best)

```
The insight: AWS infrastructure IS the identifier.
Your code doesn't need to know anything — it just asks EC2:
"What tags do you have that look like Secrets Manager ARNs?"

EC2 Metadata Service (always available, always authoritative)
    │
    ▼
Instance ID (169.254.169.254/latest/meta-data/instance-id)
    │
    ▼
ec2.describe_instances(InstanceIds=[instance_id])
    │
    ▼
All tags → scan for Secrets Manager ARN pattern
    │
    ▼
arn:aws:secretsmanager:... found in tag value
    │
    ▼
get_secret_value(SecretId=that_arn)
    │
    ▼
Your secret, fetched cleanly ✅
```

The ARN pattern (`arn:aws:secretsmanager:region:account:secret:name`) is a **public AWS standard**, not specific to your secret. No sensitive information appears anywhere in the code.
