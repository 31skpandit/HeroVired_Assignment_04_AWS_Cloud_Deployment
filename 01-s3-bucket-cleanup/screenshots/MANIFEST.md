# Screenshot Manifest — S3 Bucket Cleanup Lambda

Documentation-quality sequence of screenshots for the `01-s3-bucket-cleanup` assignment.
Originals are timestamped raw Windows screenshots; 12 of 33 were selected as the clearest,
most complete shot of each build step. The other 21 (near-duplicate retakes, in-progress
form states, and unrelated browser tabs like Billing/Budgets and the AWS console home page)
are archived in `extra/` — nothing was deleted.

| Filename | What it shows | Step |
|---|---|---|
| `01-create-bucket.png` | S3 "Create bucket" form with bucket name `santosh-s3-cleanup-demo-03.08` typed in, region US East (N. Virginia). | 1. Create S3 bucket |
| `02-upload-test-files.png` | Upload status page: 3 test PDFs (`Assignment_Submission_Requirements.pdf`, `aws-assignment-announcement.pdf`, `PracticeAssignment-ServerlessAssignment.pdf`) all show "Succeeded", destination `s3://santosh-s3-cleanup-demo-03.08`. | 1. Upload test files |
| `03-iam-role-inline-policy.png` | IAM role `s3-bucket-cleanup-role.` detail page with green banner "Policy s3-bucket-cleanup-inline created" and the inline policy listed under Permissions policies (1). | 2. Create IAM role + attach inline policy |
| `04-lambda-create-function.png` | Lambda "Create function" form: Author from scratch, function name `s3-bucket-cleanup`, Runtime = Python 3.12. | 3. Create Lambda function |
| `05-lambda-execution-role.png` | Same create-function form scrolled down to "Custom execution role", showing IAM permissions linked to `s3-bucket-cleanup-role.` before the function is created. | 3. Attach execution role to function |
| `06-lambda-function-created.png` | Green "Successfully created the function s3-bucket-cleanup" banner, function overview diagram, Code tab active. | 3. Function created confirmation |
| `07-lambda-code-deployed.png` | Code editor showing the full `lambda_function.py`: boto3 client, paginated `list_objects_v2`, age-threshold comparison against `LastModified`, `delete_object` calls, print statements, and JSON response — status bar reads "Lambda Deployed". | 3. Paste and deploy Lambda code |
| `08-env-vars-threshold-0.png` | Configuration → Environment variables (2): `AGE_THRESHOLD_DAYS = 0`, `BUCKET_NAME = santosh-s3-cleanup-demo-03.08`, set after Save. | 4. Configure environment variables (threshold forced to 0 for testing) |
| `09-test-invocation-succeeded.png` | Test tab response panel: `"deleted_count": 3`, `"deleted_keys"` listing all 3 uploaded PDFs, plus the execution log output (Duration, Billed Duration, Memory Used). | 5. Invoke test event — execution succeeded |
| `10-cloudwatch-logs-deletions.png` | CloudWatch Logs → `/aws/lambda/s3-bucket-cleanup` log stream: one `Deleted: <key> (LastModified=...)` line per object plus the summary line `Bucket=... | ThresholdDays=0 | TotalDeleted=3`. | 6. Verify CloudWatch Logs |
| `11-s3-bucket-empty-final.png` | S3 bucket `santosh-s3-cleanup-demo-03.08` → Objects (0) — "You don't have any objects in this bucket," confirming the cleanup deleted everything. | 7. Verify bucket is empty after cleanup |
| `12-env-vars-threshold-30.png` | "Successfully updated the function" banner, Environment variables (2) now showing `AGE_THRESHOLD_DAYS = 30` (reset from the testing value of 0), `BUCKET_NAME` unchanged. | 7. Reset threshold to production value (30 days) |

## Archived (`extra/`)

21 screenshots not used in the numbered sequence — kept for reference, not deleted:
- AWS Console home page and Billing/Budgets pages (unrelated to this assignment, other browser tabs left open)
- Near-duplicate retakes taken seconds apart of the same screen (e.g. two shots of the upload-succeeded page, two of the inline-policy-created page, two of the CloudWatch log page)
- Intermediate/in-progress form states superseded by a later, more complete screenshot of the same screen (e.g. empty "Objects" list right after bucket creation, the create-bucket form scrolled to encryption settings, the "Add permissions" dropdown mid-click, empty Environment Variables tab before values were added, the code editor scrolled to the top of the file, the Test tab's top half before scrolling to the response)
