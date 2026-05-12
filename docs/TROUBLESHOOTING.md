# Troubleshooting Guide

## Error: AccessDeniedException on ListSecrets

```
User: arn:aws:sts::527844782951:assumed-role/CloudWatch-Monitoring/i-...
is not authorized to perform: secretsmanager:ListSecrets
because no identity-based policy allows the secretsmanager:ListSecrets action
```

**Cause A:** `ListSecrets` is not in the IAM policy at all.  
**Fix:** Add `secretsmanager:ListSecrets` with `Resource: *`.

**Cause B:** You have `ListSecrets` but with a `Condition` block.  
**Fix:** Remove the `Condition` block. `ListSecrets` does not support conditions.

**Cause C:** You scoped `ListSecrets` to a specific ARN (`Resource: "arn:aws:..."`)  
**Fix:** Change to `Resource: *`. ListSecrets is account-level and rejects specific ARNs.

---

## Error: AccessDeniedException on GetSecretValue (wrong secret)

```
not authorized to perform: secretsmanager:GetSecretValue on resource:
arn:aws:secretsmanager:...:secret:aws_certifyme_ses-m9V4eN
```

**Cause:** `list_secrets` returned secrets alphabetically. `aws_certifyme_ses` comes before `nglite-stage-secrets-be` alphabetically, so the code tried it first and got denied.

**Fix Options:**
1. Use `batch_get_secret_value` with a tag filter (Method 1) — AWS does the filtering
2. Use EC2 instance tag to store the correct ARN (Method 5) — skip listing entirely
3. Loop with try/except, skip on `AccessDeniedException` (Method 3) — slow but works

---

## Error: No module named 'boto3'

```
ModuleNotFoundError: No module named 'boto3'
```

**Fix on Amazon Linux 2023 / EC2:**
```bash
pip3 install boto3 --user
# or in a virtual environment:
python3 -m venv venv
source venv/bin/activate
pip install boto3
```

---

## Error: Metadata service timeout (local dev)

```
requests.exceptions.ConnectionError: HTTPConnectionPool(host='169.254.169.254', ...)
```

**Cause:** You're running Method 5 locally. The EC2 metadata service only works on EC2.  
**Fix:** Use Method 6 (`method6_full_auto_detect.py`) which detects the environment first.

---

## Python 3.9 Deprecation Warning

```
PythonDeprecationWarning: Boto3 will no longer support Python 3.9 starting April 29, 2026.
```

**Fix:**
```bash
sudo dnf install python3.11 python3.11-pip -y
python3.11 your-script.py
```

---

## boto3 picks up wrong credentials locally

**Cause:** boto3 checks credentials in priority order:
1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. `~/.aws/credentials`
3. EC2 metadata service

If you have stale environment variables set, they override your `aws configure` profile.

**Fix:**
```bash
# Check which credentials are active
aws sts get-caller-identity

# Clear env vars if they're wrong
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
```

---

## IAM changes not taking effect

IAM policy changes propagate within **seconds** on most calls. If a change doesn't seem to be working:
- Wait 30 seconds and retry
- Check you saved the policy correctly (no JSON syntax errors)
- Verify the role is actually attached to the EC2 instance (`EC2 → Instance → Security tab`)
