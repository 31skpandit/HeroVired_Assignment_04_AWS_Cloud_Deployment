# AWS Automation with Lambda & Boto3

Graded assignment submission — PPMCAD AWS Module, Assignment 2 (Serverless
Automation with AWS Lambda & Boto3). 4 of the 6 available tasks completed, as
permitted by the assignment guidelines.

**Runtime:** Python 3.12 · **Region:** us-east-1 · **IAM:** least-privilege
inline policies (no `*FullAccess` managed policies)

## Tasks

| # | Folder | Task | Services |
|---|---|---|---|
| 1 | [01-s3-bucket-cleanup](./01-s3-bucket-cleanup) | Delete S3 objects older than 30 days | S3, Lambda |
| 2 | [02-public-bucket-audit](./02-public-bucket-audit) | Detect publicly accessible S3 buckets, alert via SNS | S3, SNS, Lambda, EventBridge |
| 3 | [03-daily-cost-alert](./03-daily-cost-alert) | Daily AWS spend alert via Cost Explorer + SNS | Cost Explorer, SNS, Lambda, EventBridge |
| 4 | [04-ec2-auto-tagging](./04-ec2-auto-tagging) | Auto-tag EC2 instances on launch | EC2, EventBridge, Lambda |

Each task folder contains:
- `lambda_function.py` — the Lambda source
- `iam_policy.json` — the exact least-privilege inline policy attached to the execution role
- `README.md` — 8-section documentation (Objective, Architecture, Resources, IAM, Lambda config, Step-by-step, Testing/Screenshots, Challenges Faced, Discussion, Cleanup)
- `screenshots/` — IAM role, Lambda config, test invocation, CloudWatch logs, final result (numbered in build order)

## Repo-wide setup notes

- Set up a **$1 AWS Budget Alert** (Billing → Budgets) before starting.
- Everything was built and tested in a single AWS region (`us-east-1`).
- Cost Explorer (Assignment 3) was enabled at the start of the session since
  first-time activation can take a few hours.
- No AWS access keys or secrets are committed anywhere in this repo — only
  account IDs inside ARNs, which are not sensitive.

## Cleanup status

All AWS resources created for this submission (Lambda functions, IAM roles,
SNS topics, EventBridge rules, test S3 buckets, test EC2 instance) were
deleted/terminated after screenshots were captured. See the **Cleanup**
section at the bottom of each task's README for the specific checklist.
