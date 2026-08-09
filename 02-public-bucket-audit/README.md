# Assignment 2 — Audit S3 Buckets for Public Access and Notify

## 1. Objective
Scan every S3 bucket in the account and alert via SNS if any bucket is
publicly accessible — checking Block Public Access configuration, bucket
policy status, and ACL grants (not just ACLs, since new buckets have Block
Public Access on and ACLs disabled by default).

## 2. Architecture
```
EventBridge (daily)  --->  Lambda (Python 3.12)  --->  S3 (list buckets, check each)
                                    |
                                    v
                              SNS Topic  --->  Email
                                    |
                                    v
                            CloudWatch Logs
```

## 3. AWS Resources Created
| Resource | Name | Notes |
|---|---|---|
| S3 Bucket (control) | `santosh-public-audit-private-01` | left on defaults; must NOT be flagged |
| S3 Bucket (test target) | `santosh-public-audit-public-01` | deliberately opened up for testing, then re-secured |
| SNS Topic | `public-bucket-audit-topic` | ARN `arn:aws:sns:us-east-1:575638747404:public-bucket-audit-topic`; email subscription confirmed |
| Lambda Function | `public-bucket-audit` | Python 3.12, timeout raised to 30s (see Challenges) |
| IAM Role | `public-bucket-audit-role` | inline policy `public-bucket-audit-inline`, see `iam_policy.json` |
| EventBridge Rule | *(not created)* | scheduling left as a manual-invoke demo only; see step 11 |

## 4. IAM Role & Policy
See [`iam_policy.json`](./iam_policy.json):
- `s3:ListAllMyBuckets` (account-level, requires `Resource: "*"`)
- `s3:GetBucketPublicAccessBlock`, `s3:GetBucketPolicyStatus`, `s3:GetBucketAcl` — scoped to `arn:aws:s3:::*` (bucket-level, not account-level `*`)
- `sns:Publish` — scoped to the specific topic ARN
- CloudWatch Logs permissions

No `AmazonS3FullAccess` or `AmazonSNSFullAccess` attached.

## 5. Lambda Function
See [`lambda_function.py`](./lambda_function.py).

Environment variables:
| Key | Value |
|---|---|
| `SNS_TOPIC_ARN` | `arn:aws:sns:us-east-1:575638747404:public-bucket-audit-topic` |

## 6. Step-by-Step Implementation

1. **Create the SNS topic**: SNS → Topics → Create topic → Standard →
   name `public-bucket-audit-topic` → Create.
2. **Subscribe your email**: Create subscription → Protocol: Email → enter
   your address → **check your inbox and click Confirm subscription**.
3. **Create 2 test buckets**:
   - `santosh-public-audit-private-01`: leave all defaults (Block Public Access ON) — should NOT be flagged.
   - `santosh-public-audit-public-01`: the "public" test case — see step 8.
4. **Create the IAM role** (Lambda trust) and attach the inline policy from
   `iam_policy.json` (account ID and topic ARN already filled in).
5. **Create the Lambda function** `public-bucket-audit`, Python 3.12, attach
   the role from step 4.
6. **Paste the code**, set env var `SNS_TOPIC_ARN`, Deploy. Also raise the
   function **timeout to 30 seconds** (Configuration → General configuration
   → Edit) up front — see Challenges Faced for why the 3-second default isn't
   enough here.
7. **First test run** (both buckets private): Test → Invoke → confirm
   `public_buckets: []` in the response and CloudWatch Logs.
8. **Make `santosh-public-audit-public-01` public for the test**:
   - Bucket → Permissions → Block Public Access → **Edit** → uncheck all
     four boxes → confirm.
   - Permissions → Bucket Policy → add a public-read policy:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [{
         "Sid": "PublicReadTest",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::santosh-public-audit-public-01/*"
       }]
     }
     ```
9. **Re-invoke the Lambda** → confirm `santosh-public-audit-public-01` now
   appears in `public_buckets`, an SNS email arrives, and CloudWatch Logs show
   the flag.
10. **Immediately re-secure `santosh-public-audit-public-01`**: remove the
    bucket policy and re-enable all 4 Block Public Access settings.
11. *(Optional, not done for this submission)* Add an EventBridge daily
    schedule rule as a second trigger — the manual-invoke test above is
    sufficient to demonstrate the logic end-to-end.

## 7. Testing & Verification
Screenshots in `screenshots/`, in the order the work happened (see
`screenshots/MANIFEST.md` for full captions):

1. `01-sns-topic-created.png` — SNS topic `public-bucket-audit-topic` created
2. `02-sns-email-subscription-pending.png` — email subscription created, pending confirmation
3. `03-confirmation-email-in-gmail-spam.png` — AWS confirmation email (landed in spam)
4. `04-sns-subscription-confirmed.png` — subscription confirmed
5. `05-s3-test-buckets-created.png` — test buckets created in S3
6. `06-iam-role-inline-policy-created.png` — IAM role + inline policy
7. `07-lambda-function-created-code-pasted.png` — Lambda function created, code pasted
8. `08-lambda-env-var-sns-topic-arn.png` — `SNS_TOPIC_ARN` environment variable set
9. `09-first-test-run-no-public-buckets.png` — first test run, both buckets private, empty result
10. `10-wrong-bucket-policy-error.png` — troubleshooting: policy edited on the wrong bucket, "Policy has invalid resource"
11. `11-retest-timeout-error.png` — troubleshooting: `Sandbox.Timedout`, detection logic already correct in the logs
12. `12-timeout-fixed-public-bucket-detected-sns-published.png` — timeout raised to 30s, retest succeeds, public bucket detected, SNS alert published
13. `13-sns-alert-email-received.png` — "[ALERT] Public S3 Bucket(s) Detected" email received

Extra/near-duplicate screenshots archived (not deleted) in `screenshots/extra/`.

## 8. Challenges Faced

- **Bucket policy applied to the wrong bucket.** While making the test target
  public, I pasted the public-read bucket policy while still on
  `santosh-public-audit-private-01` (the control bucket) instead of
  `santosh-public-audit-public-01`. S3 rejected it with `"Policy has invalid
  resource"`, since the policy's `Resource` ARN referenced a bucket different
  from the one it was being attached to. Fixed by navigating to the correct
  bucket before re-pasting the policy — a reminder to double-check the
  breadcrumb/URL, not just the tab title, before editing bucket-level
  settings.

- **Lambda timed out mid-execution despite correct logic.** The first real
  test against the public bucket failed with `Sandbox.Timedout: Task timed
  out after 3.00 seconds`. The default Lambda timeout (3s) wasn't enough
  for 4 buckets × 3 S3 API calls each (`get_public_access_block`,
  `get_bucket_policy_status`, `get_bucket_acl`) plus one `sns.publish` call —
  the CloudWatch log showed every bucket had already been checked correctly
  (private bucket → not flagged, public bucket → flagged) but execution was
  killed before the SNS publish could complete, so no alert went out. Fixed
  by raising the function timeout to 30 seconds under Configuration → General
  configuration. Take-away: the 3-second default is only really safe for
  single-API-call functions like the auto-tagging task; anything looping over
  multiple resources with multiple calls per resource needs headroom.

## 9. Discussion Point
AWS **Access Analyzer for S3** and **IAM Access Analyzer** provide managed,
continuous public-access findings without custom code. A custom Lambda is
worth it when you want a specific alerting channel/format, need to combine
findings across accounts, or want to trigger auto-remediation (e.g.
automatically re-enabling Block Public Access) instead of just alerting.

## 10. Cleanup
- [ ] Deleted both test S3 buckets
- [ ] Deleted the SNS topic
- [ ] Deleted the Lambda function
- [ ] Deleted the IAM role
- [ ] Deleted the EventBridge rule (if created)
