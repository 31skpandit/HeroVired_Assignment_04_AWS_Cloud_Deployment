# Assignment 1 — Automated S3 Bucket Cleanup (Objects Older Than 30 Days)

## 1. Objective
Automatically delete objects in an S3 bucket that are older than a configurable
retention period (30 days in production; lowered to minutes during testing),
using a Lambda function triggered manually (and optionally on an EventBridge
schedule).

## 2. Architecture
```
Manual Invoke  --->  Lambda (Python 3.12)  --->  S3 Bucket (list + delete)
                              |
                              v
                       CloudWatch Logs
```

## 3. AWS Resources Created
| Resource | Name (fill in) | Notes |
|---|---|---|
| S3 Bucket | `` | Holds test objects |
| Lambda Function | `s3-bucket-cleanup` | Python 3.12 runtime |
| IAM Role | `s3-bucket-cleanup-role` | Inline policy, see `iam_policy.json` |

## 4. IAM Role & Policy
Least-privilege inline policy used (see [`iam_policy.json`](./iam_policy.json)):
- `s3:ListBucket` — scoped to the bucket ARN
- `s3:DeleteObject` — scoped to the bucket's object ARN (`/*`)
- CloudWatch Logs permissions (auto-added by the console's basic execution role, or included manually)

No `AmazonS3FullAccess` or similar managed policy was attached.

## 5. Lambda Function
See [`lambda_function.py`](./lambda_function.py).

Environment variables:
| Key | Value | Notes |
|---|---|---|
| `BUCKET_NAME` | your bucket name | required |
| `AGE_THRESHOLD_DAYS` | `30` (use a small value like `0` while testing) | optional, defaults to 30 |

## 6. Step-by-Step Implementation

1. **Create the S3 bucket** (Console → S3 → Create bucket). Use a globally
   unique name, region `us-east-1`, keep all defaults (Block Public Access ON).
2. **Upload test files** — upload 3–5 small files.
3. **Create the IAM role**:
   - IAM → Roles → Create role → Trusted entity: **Lambda**.
   - Skip attaching a managed policy for now → create the role.
   - Open the role → **Add permissions → Create inline policy** → JSON tab →
     paste the contents of `iam_policy.json` (replace the bucket name) → name
     it `s3-bucket-cleanup-inline` → Create policy.
4. **Create the Lambda function**:
   - Lambda → Create function → Author from scratch.
   - Name: `s3-bucket-cleanup`, Runtime: **Python 3.12**, Architecture: x86_64.
   - Permissions → Use an existing role → select the role from step 3.
5. **Paste the code** from `lambda_function.py` into the inline code editor,
   click **Deploy**.
6. **Set environment variables** (Configuration → Environment variables):
   `BUCKET_NAME=<your-bucket>`, `AGE_THRESHOLD_DAYS=0` (for the first test run,
   so today's uploads are immediately "old enough" to delete).
7. **Test**: Configuration → Test → create a test event (empty `{}` JSON is
   fine) → Invoke. Confirm the deleted keys appear in the response and in
   CloudWatch Logs.
8. **Re-upload files**, set `AGE_THRESHOLD_DAYS=30` back to the real value,
   redeploy/save, and do a final confirmation run (should delete nothing,
   since the files are brand new).
9. *(Optional)* Add an EventBridge schedule rule (e.g. `rate(1 day)`) as the
   trigger if you want this to run automatically.

## 7. Testing & Verification
Screenshots in `screenshots/`, in the order the work happened (see
`screenshots/MANIFEST.md` for full captions):

1. `01-create-bucket.png` — S3 create-bucket form
2. `02-upload-test-files.png` — 3 test files uploaded
3. `03-iam-role-inline-policy.png` — IAM role + inline policy attached
4. `04-lambda-create-function.png` — Lambda create-function form
5. `05-lambda-execution-role.png` — execution role linked
6. `06-lambda-function-created.png` — function created confirmation
7. `07-lambda-code-deployed.png` — code deployed
8. `08-env-vars-threshold-0.png` — env vars set, threshold=0 for testing
9. `09-test-invocation-succeeded.png` — test result, 3 objects deleted
10. `10-cloudwatch-logs-deletions.png` — per-file deletion log lines
11. `11-s3-bucket-empty-final.png` — bucket empty after cleanup
12. `12-env-vars-threshold-30.png` — threshold reset to 30 for production

Extra/near-duplicate screenshots archived (not deleted) in `screenshots/extra/`.

## 8. Challenges Faced
_(Fill in genuinely — e.g. timezone-naive vs aware datetime comparison errors,
IAM permission typos, pagination gotchas, etc.)_

- ...
- ...

## 9. Discussion Point
In production, **S3 Lifecycle Rules** handle this natively with zero code —
just a bucket-level rule with an expiration action. Lambda is worth it instead
when you need: conditional logic based on object metadata/tags, naming-pattern
based rules Lifecycle can't express, cross-service side effects (e.g. logging
to DynamoDB or notifying via SNS on delete), or deletion logic that spans
multiple buckets in one run.

## 10. Cleanup
- [ ] Deleted the test S3 bucket (or emptied it)
- [ ] Deleted the Lambda function
- [ ] Deleted the IAM role
- [ ] Deleted the EventBridge rule (if created)
