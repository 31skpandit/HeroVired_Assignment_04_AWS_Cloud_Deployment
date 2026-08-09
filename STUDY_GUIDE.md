# AWS Lambda & Boto3 — Study Guide

Personal revision notes for the 4 completed assignments. This is separate
from the per-task `README.md` files (which are the graded submission docs) —
this file is organized for **learning and interview prep**: concepts first,
then the exact steps, then the traps that actually got hit while building
these.

---

## Cross-assignment lessons (read this section first)

These are the patterns that showed up more than once — the stuff worth
actually remembering, not just the assignment-specific details.

1. **Lambda's default timeout is 3 seconds — too short for almost anything
   that makes more than one API call.** Hit this directly in Assignment 2
   (4 buckets × 3 S3 calls + 1 SNS publish timed out) even though the logic
   was already correct. Fix: bump Configuration → General configuration →
   Timeout to 15–30s on any function that loops over resources or chains
   multiple AWS API calls. A single-call function (like EC2 auto-tagging)
   can usually stay at the default, but there's no downside to raising it
   anyway.

2. **S3 bucket policies must reference the exact bucket they're attached
   to.** The `Resource` ARN inside the policy JSON has to match the bucket
   you're currently editing, or S3 rejects it with `"Policy has invalid
   resource"`. Easy mistake when you have multiple similarly-named test
   buckets open in different tabs — always check the breadcrumb/URL, not
   just which tab you think you're on.

3. **Cost Explorer (`ce` client) only has an endpoint in `us-east-1`,
   regardless of which region the rest of your resources live in.** Always
   hardcode `region_name="us-east-1"` when creating the boto3 `ce` client.
   Also: Cost Explorer needs to be manually enabled once per account and can
   take hours to populate historical data the first time — enable it early.

4. **IAM resource-level scoping is inconsistent across services/actions** —
   worth knowing case by case instead of assuming:
   - `s3:ListBucket` / `s3:DeleteObject` → scopeable to a specific bucket ARN.
   - `s3:ListAllMyBuckets` → account-level, **must** be `Resource: "*"`.
   - `s3:GetBucketPublicAccessBlock` / `GetBucketPolicyStatus` / `GetBucketAcl`
     → scopeable to `arn:aws:s3:::*` (any bucket, but still bucket-level, not
     account-level `*`).
   - `ce:GetCostAndUsage` → does not support resource-level scoping at all,
     must be `"*"`.
   - `ec2:CreateTags` → scopeable to a resource-type ARN, e.g.
     `arn:aws:ec2:*:ACCOUNT_ID:instance/*` (restricts to tagging instances
     only, not volumes/snapshots/etc).
   - `ec2:DescribeInstances` → does not support resource-level scoping,
     must be `"*"`.
   Least-privilege doesn't always mean a narrow ARN — sometimes the action
   itself is the only lever you have, and `"*"` on a single, specific action
   is still far tighter than a `*FullAccess` managed policy.

5. **EC2 launch wizard defaults to `t2.micro`, not `t3.micro`.** Both are
   free-tier eligible, so it's easy to not notice — check the instance type
   field before clicking Launch if the assignment spec calls out t3.

6. **Test cheaply before testing for real.** In Assignment 4, running a mock
   EventBridge event with a fake instance ID through the Lambda Test tab
   caught event-parsing and IAM issues *before* any real EC2 instance was
   involved — it's fine (expected, even) for that mock run to fail on the
   AWS API call itself, as long as it fails at the right place.

---

## Assignment 1 — S3 Bucket Cleanup (delete objects older than N days)

**Concept:** paginate through a bucket's objects, compare `LastModified`
(timezone-aware) against a UTC cutoff, delete anything older.

**Why not just use S3 Lifecycle Rules?** In production you would — this is
the zero-code, native answer. Lambda earns its place when you need
conditional logic Lifecycle can't express (naming patterns, cross-service
side effects, custom logging) — not for a flat age-based deletion.

**Steps:**
1. S3 → Create bucket → defaults are fine → upload a few test files.
2. IAM → Roles → Create role → AWS service → Lambda → skip managed policies →
   name it → Create role.
3. Open the role → Add permissions → Create inline policy → JSON → paste the
   least-privilege policy (see below) → name → Create.
4. Lambda → Create function → Python 3.12 → attach the role from step 3.
5. Paste the code → Deploy.
6. Configuration → Environment variables: `BUCKET_NAME`, `AGE_THRESHOLD_DAYS`
   (set to `0` temporarily to prove deletion works against today's uploads).
7. Test tab → Create event → Invoke → confirm deleted keys in the response
   and in CloudWatch Logs.
8. Reset `AGE_THRESHOLD_DAYS` back to `30` for the real/final state.

**IAM policy shape:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "ListBucket", "Effect": "Allow", "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::BUCKET_NAME" },
    { "Sid": "DeleteObjects", "Effect": "Allow", "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::BUCKET_NAME/*" },
    { "Sid": "Logs", "Effect": "Allow",
      "Action": ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:*" }
  ]
}
```

**Core logic (full code in `01-s3-bucket-cleanup/lambda_function.py`):**
```python
cutoff = datetime.now(timezone.utc) - timedelta(days=AGE_THRESHOLD_DAYS)
paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=BUCKET_NAME):
    for obj in page.get("Contents", []):
        if obj["LastModified"] < cutoff:
            s3.delete_object(Bucket=BUCKET_NAME, Key=obj["Key"])
```
Key point: **always use the paginator**, never assume `list_objects_v2`
returns everything in one call (it caps at 1000 keys per page).

---

## Assignment 2 — Audit S3 Buckets for Public Access, Alert via SNS

**Concept:** since April 2023, new buckets default to Block Public Access ON
and ACLs disabled — so "is this bucket public" can't be answered by ACLs
alone anymore. Correct check is three-part:
1. Is Block Public Access **fully** enabled (all 4 sub-settings)?
2. Does `get_bucket_policy_status` report `IsPublic: true`?
3. Does the ACL grant access to `AllUsers` / `AuthenticatedUsers`?

A bucket is actually reachable publicly only if BPA is **not** fully
enabled **and** (policy is public **or** ACL grants public access).

**Why not just use IAM/S3 Access Analyzer?** It's the managed, continuous
alternative. Custom Lambda earns its place for a specific alert
channel/format or auto-remediation (e.g. automatically re-enabling BPA).

**Steps:**
1. SNS → Create topic (Standard) → Create subscription (Email) → **confirm
   from your inbox** (nothing arrives until you do this).
2. Create 2 test buckets: one left on defaults (control), one to
   deliberately expose later.
3. IAM role + inline policy (below).
4. Lambda, Python 3.12, attach role, paste code, Deploy.
5. Set env var `SNS_TOPIC_ARN`. **Set timeout to 30s up front** (see lesson
   #1 above).
6. Test with both buckets private → expect `public_buckets: []`.
7. Make the second bucket public: Permissions → Block Public Access → Edit →
   uncheck all 4 → confirm. Then Bucket Policy → Edit → paste a public-read
   policy **referencing that exact bucket's ARN**.
8. Re-test → expect the bucket to appear in `public_buckets`, SNS email
   arrives, CloudWatch Logs show the flag.
9. **Immediately re-secure**: delete the bucket policy, re-enable all 4 BPA
   settings.

**IAM policy shape:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "ListAllBuckets", "Effect": "Allow", "Action": "s3:ListAllMyBuckets", "Resource": "*" },
    { "Sid": "InspectBucketPublicStatus", "Effect": "Allow",
      "Action": ["s3:GetBucketPublicAccessBlock","s3:GetBucketPolicyStatus","s3:GetBucketAcl"],
      "Resource": "arn:aws:s3:::*" },
    { "Sid": "PublishAlert", "Effect": "Allow", "Action": "sns:Publish",
      "Resource": "arn:aws:sns:REGION:ACCOUNT_ID:TOPIC_NAME" },
    { "Sid": "Logs", "Effect": "Allow",
      "Action": ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:*" }
  ]
}
```

**Core logic (full code in `02-public-bucket-audit/lambda_function.py`):**
```python
is_public = (not bpa_fully_enabled) and (policy_is_public or acl_has_public_grant)
```

---

## Assignment 3 — Daily AWS Cost Alert (Cost Explorer + SNS)

**Concept:** query month-to-date `UnblendedCost` via `ce.get_cost_and_usage`,
compare against a threshold, alert via SNS if exceeded.

**Why not just use AWS Budgets?** It's the managed, no-code alternative —
alerts on forecasted or actual spend out of the box. Custom Lambda earns its
place for per-service cost breakdowns, delivery to a channel Budgets doesn't
support, or custom anomaly logic beyond a flat threshold.

**Steps:**
1. **Enable Cost Explorer first** (Billing → Cost Explorer → Enable) — do
   this as early as possible, first-time activation can take hours.
2. SNS topic + confirmed email subscription.
3. IAM role + inline policy (below).
4. Lambda, Python 3.12, paste code, Deploy. **Set timeout to 30s.**
5. Env vars: `SNS_TOPIC_ARN`, `COST_THRESHOLD_USD=0.01` (low, to force an
   alert during testing).
6. Test → expect `alert_sent: true` and an SNS email.
7. Reset `COST_THRESHOLD_USD` to a realistic value (e.g. `50`).
8. **Don't over-invoke** — each `GetCostAndUsage` call costs ≈₹1. 5–10 total
   test invocations is the guidance; no EventBridge schedule needed for
   grading (scheduling this daily is a real-money commitment).

**IAM policy shape:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "CostExplorerRead", "Effect": "Allow", "Action": "ce:GetCostAndUsage", "Resource": "*" },
    { "Sid": "PublishAlert", "Effect": "Allow", "Action": "sns:Publish",
      "Resource": "arn:aws:sns:us-east-1:ACCOUNT_ID:TOPIC_NAME" },
    { "Sid": "Logs", "Effect": "Allow",
      "Action": ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:*" }
  ]
}
```

**Core logic (full code in `03-daily-cost-alert/lambda_function.py`):**
```python
ce = boto3.client("ce", region_name="us-east-1")   # always us-east-1
start = today.replace(day=1).isoformat()
end = today.isoformat()
if start == end:                                     # 1st-of-month edge case
    end = (today + timedelta(days=1)).isoformat()
response = ce.get_cost_and_usage(
    TimePeriod={"Start": start, "End": end},
    Granularity="MONTHLY",
    Metrics=["UnblendedCost"],
)
```

---

## Assignment 4 — Auto-Tag EC2 Instances on Launch

**Concept:** EventBridge fires an `EC2 Instance State-change Notification`
event whenever an instance's state changes; filter for `state: running`,
extract `detail.instance-id`, apply tags via `ec2.create_tags`.

**Why not a scheduled poll instead?** Event-driven is strictly better here —
tags get applied within seconds of launch instead of on the next poll cycle,
and there's no wasted invocation when nothing launched.

**Bonus (not implemented, but a common interview follow-up):** to capture
*who* launched the instance, add a second EventBridge rule matching
CloudTrail's `RunInstances` API call event, extract `userIdentity.arn`, use
it as the `Owner` tag instead of a static placeholder.

**Steps:**
1. IAM role + inline policy (below).
2. Lambda, Python 3.12, attach role, paste code, Deploy.
3. EventBridge → Create rule → Event pattern (JSON, below) → Target: the
   Lambda function.
4. **Mock test first**, before touching real EC2: Test tab with a fake
   `instance-id` — expect it to fail at the `create_tags` API call (that's
   the correct failure point, proves everything upstream works).
5. Launch a real **t3.micro** instance (double-check — wizard defaults to
   t2.micro), no key pair needed.
6. Wait ~30–60s after "running" — the EventBridge rule fires the Lambda
   automatically, **no manual invoke needed**.
7. Verify tags on the instance (Tags tab) and the CloudWatch log entry.
8. **Terminate immediately.**

**Event pattern:**
```json
{
  "source": ["aws.ec2"],
  "detail-type": ["EC2 Instance State-change Notification"],
  "detail": { "state": ["running"] }
}
```

**IAM policy shape:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "TagInstancesOnly", "Effect": "Allow", "Action": "ec2:CreateTags",
      "Resource": "arn:aws:ec2:*:ACCOUNT_ID:instance/*" },
    { "Sid": "DescribeInstances", "Effect": "Allow", "Action": "ec2:DescribeInstances", "Resource": "*" },
    { "Sid": "Logs", "Effect": "Allow",
      "Action": ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:*" }
  ]
}
```

**Core logic (full code in `04-ec2-auto-tagging/lambda_function.py`):**
```python
detail = event.get("detail", {})
instance_id = detail.get("instance-id")
if detail.get("state") == "running":
    ec2.create_tags(Resources=[instance_id], Tags=[
        {"Key": "LaunchDate", "Value": date.today().isoformat()},
        {"Key": "Owner", "Value": "auto-tag-lambda"},
        {"Key": "Environment", "Value": "dev"},
    ])
```

---

## Quick interview-style Q&A (self-test)

- **Q: Why does the S3 cleanup function use a paginator instead of just
  calling `list_objects_v2` once?**
  A: `list_objects_v2` caps at 1000 keys per response; a paginator
  transparently walks all pages so large buckets aren't silently
  under-processed.

- **Q: Why does Block Public Access alone not tell you if a bucket is
  public?**
  A: BPA controls whether public ACLs/policies are *allowed to take effect*,
  not whether one *exists*. You also need to check policy status and ACL
  grants — a bucket with BPA off but no public policy/ACL still isn't
  actually public.

- **Q: Why hardcode `us-east-1` for the Cost Explorer client?**
  A: Cost Explorer is a global service exposed through a single regional
  API endpoint (`us-east-1`) regardless of where your billed resources run.

- **Q: Why prefer adjusting Auto Scaling Group desired capacity over
  launching/terminating raw EC2 instances from Lambda?** *(general
  AWS pattern, not built here, but a common follow-up)*
  A: ASGs handle health checks, AZ balancing, and lifecycle hooks natively;
  raw instance management from Lambda duplicates that logic poorly and
  doesn't integrate with target groups the way ASG scaling does.
