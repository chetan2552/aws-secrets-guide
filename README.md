# 🔐 AWS Secrets Manager — Zero-Hardcode Retrieval Guide

> **The complete reference for fetching AWS Secrets Manager secrets from EC2 without ever putting a secret name, ARN, tag, or credentials in your code.**

---

## 🗺️ Table of Contents

- [The Core Problem](#the-core-problem)
- [Quick Decision Tree](#quick-decision-tree)
- [Techniques Overview](#techniques-overview)
- [EC2 Best Practice (Recommended)](#ec2-best-practice-recommended)
- [IAM Policy Reference](#iam-policy-reference)
- [All Techniques With Code](#all-techniques-with-code)
- [Local Development](#local-development)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## The Core Problem

You have **100+ secrets** in AWS Secrets Manager. You want to fetch exactly **one specific secret** from an EC2 instance — without:

| Constraint | Why |
|---|---|
| ❌ No secret name in code | Security / rotation flexibility |
| ❌ No ARN in code | Hardcoding AWS internals |
| ❌ No `.env` files | Secrets should not touch disk |
| ❌ No tag key/value in code | Avoid any identifier leakage |
| ❌ No looping 100+ secrets | Too slow, bad practice |
| ❌ No AWS keys in code | EC2 has IAM roles for this |

---

## Quick Decision Tree

```
Are you on EC2?
│
├── YES → Use EC2 Instance Tag + IAM Role (Method 5 ⭐ RECOMMENDED)
│         Zero credentials, zero names, single API call
│
└── NO (Local Dev) → Use aws configure once, then auto-detect environment
                     Same code runs locally AND on EC2
```

---

## Techniques Overview

| # | Method | Names in Code | Speed | Best For |
|---|--------|--------------|-------|----------|
| 1 | Tag-based `batch_get_secret_value` | ❌ Tag only | ⚡ Fast | Any environment |
| 2 | Environment Variable injection | ❌ No | ⚡ Fast | CI/CD pipelines |
| 3 | IAM Role loop (try/skip) | ❌ No | 🐌 Slow (100+ secrets) | Last resort |
| 4 | SSM Parameter Store pointer | ❌ SSM path only | ⚡ Fast | Multi-environment |
| 5 | EC2 Instance Tag + IAM Role | ❌ Nothing | ⚡⚡ Fastest | **EC2 (BEST)** |
| 6 | ARN regex from EC2 tags | ❌ Nothing | ⚡ Fast | EC2, no key name |

---

## EC2 Best Practice (Recommended)

> **The winning architecture**: Store the secret's ARN as an EC2 instance tag. The code reads all tags, finds the one that looks like a Secrets Manager ARN using a regex, and fetches it. **Zero identifiers of any kind in code.**

### Architecture Diagram

```
EC2 Instance
├── IAM Role: CloudWatch-Monitoring
│   └── Policy: Allow GetSecretValue on nglite-stage-secrets-be-*
│   └── Policy: Allow DescribeInstances (to read own tags)
├── Tag: [Key=SecretARN, Value=arn:aws:secretsmanager:...:secret:nglite-...]
│
└── Python Code (NOTHING sensitive inside)
      │
      ├── 1. Read own Instance ID from metadata (169.254.169.254)
      ├── 2. Describe self → get ALL tags
      ├── 3. Find tag whose VALUE matches Secrets Manager ARN pattern
      └── 4. get_secret_value(SecretId=that_arn) → done ✅
```

### One-Time AWS Setup

**Step 1: Tag your EC2 instance**
```
Key:   SecretARN
Value: arn:aws:secretsmanager:us-east-1:527844782951:secret:nglite-stage-secrets-be-CDIl9l
```

**Step 2: IAM Role Policy** — see [`iam-policies/ec2-recommended.json`](iam-policies/ec2-recommended.json)

### The Code

```python
# See examples/method5_ec2_instance_tag.py
```

---

## IAM Policy Reference

| Policy File | Use Case |
|---|---|
| [`iam-policies/ec2-recommended.json`](iam-policies/ec2-recommended.json) | EC2 tag-based retrieval (recommended) |
| [`iam-policies/batch-get-with-tags.json`](iam-policies/batch-get-with-tags.json) | BatchGetSecretValue with tag filter |
| [`iam-policies/list-and-get.json`](iam-policies/list-and-get.json) | ListSecrets + scoped GetSecretValue |
| [`iam-policies/ssm-pointer.json`](iam-policies/ssm-pointer.json) | SSM Parameter Store pointer pattern |

---

## All Techniques With Code

| File | Description |
|---|---|
| [`examples/method1_tag_filter.py`](examples/method1_tag_filter.py) | `batch_get_secret_value` with tag filter |
| [`examples/method2_env_variable.py`](examples/method2_env_variable.py) | ARN from environment variable |
| [`examples/method3_iam_loop.py`](examples/method3_iam_loop.py) | Loop and try (slow, avoid on 100+) |
| [`examples/method4_ssm_pointer.py`](examples/method4_ssm_pointer.py) | SSM Parameter Store as pointer |
| [`examples/method5_ec2_instance_tag.py`](examples/method5_ec2_instance_tag.py) | ⭐ EC2 tag ARN detection (recommended) |
| [`examples/method6_full_auto_detect.py`](examples/method6_full_auto_detect.py) | Works locally AND on EC2 (same file) |

---

## Local Development

When you're not on EC2, the metadata service (`169.254.169.254`) is unavailable. Use the auto-detect script:

```python
# examples/method6_full_auto_detect.py handles both cases automatically
python examples/method6_full_auto_detect.py
```

Local setup (one-time):
```bash
aws configure
# Enter access key, secret key, region — stored in ~/.aws/credentials
# Never committed to git
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `AccessDeniedException on ListSecrets` | `ListSecrets` needs `Resource: *` | See `iam-policies/list-and-get.json` |
| `AccessDeniedException on GetSecretValue` | Wrong secret picked (alphabetical) | Use tag filter or EC2 tag method |
| `No module named boto3` | boto3 not installed | `pip3 install boto3 --user` |
| Metadata timeout | Not running on EC2 | Use auto-detect script (Method 6) |
| 100+ secrets — slow loop | Looping all secrets | Switch to Method 1 or Method 5 |

---

## API Reference

| AWS API | Resource Scope | Notes |
|---|---|---|
| `ListSecrets` | ⚠️ Must be `*` | Account-level catalog only |
| `GetSecretValue` | ✅ Specific ARN | Lock this down tightly |
| `DescribeSecret` | ✅ Specific ARN | Metadata only, no values |
| `BatchGetSecretValue` | ✅ with filters | Best for tag-based bulk fetch |
| `ec2:DescribeInstances` | ✅ or `*` | Needed to read own instance tags |

> ⚠️ `ListSecrets` does **not** support `secretsmanager:Name` as a condition key. Adding it silently blocks all list calls.

---

## 📁 Repo Structure

```
aws-secrets-guide/
├── README.md                        ← You are here
├── examples/
│   ├── method1_tag_filter.py
│   ├── method2_env_variable.py
│   ├── method3_iam_loop.py
│   ├── method4_ssm_pointer.py
│   ├── method5_ec2_instance_tag.py  ← RECOMMENDED
│   └── method6_full_auto_detect.py  ← LOCAL + EC2
├── iam-policies/
│   ├── ec2-recommended.json
│   ├── batch-get-with-tags.json
│   ├── list-and-get.json
│   └── ssm-pointer.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── TROUBLESHOOTING.md
│   └── LOCAL_DEV.md
└── scripts/
    └── setup_ec2_tag.sh             ← One-time EC2 setup
```

---

## License

MIT — use freely, contribute back.
