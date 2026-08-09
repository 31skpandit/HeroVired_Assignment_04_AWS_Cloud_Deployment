# Screenshot Manifest — Public S3 Bucket Audit (Lambda + SNS)

Documentation-quality sequence for study/revision. 13 of 17 original screenshots were kept;
the other 4 (near-duplicate retakes of the same screen, taken seconds apart) were archived to `extra/`.

| Filename | What it shows | Step |
|---|---|---|
| `01-sns-topic-created.png` | SNS console: topic `public-bucket-audit-topic` created successfully, showing its ARN and empty subscriptions list. | 1. Create SNS topic |
| `02-sns-email-subscription-pending.png` | SNS console: email subscription created for `santy.datascience@gmail.com`, status "Pending confirmation". | 1. Create email subscription |
| `03-confirmation-email-in-gmail-spam.png` | Gmail (Spam folder): "AWS Notification - Subscription Confirmation" email from AWS, with the "Confirm subscription" link. | 1. Locate confirmation email |
| `04-sns-subscription-confirmed.png` | AWS SNS confirmation landing page: "Subscription confirmed! You have successfully subscribed." | 1. Confirm subscription |
| `05-s3-test-buckets-created.png` | S3 console: Buckets list showing the newly created test buckets (`santosh-public-audit-private-01`, etc.) alongside pre-existing buckets. | 2. Create test buckets |
| `06-iam-role-inline-policy-created.png` | IAM console: role `public-bucket-audit-role` with inline policy `public-bucket-audit-inline` attached, "Policy created" banner. | 3. Create IAM role + inline policy |
| `07-lambda-function-created-code-pasted.png` | Lambda console: function `public-bucket-audit` created, code editor showing `lambda_function.py` (boto3 s3/sns clients, `PUBLIC_GRANTEE_URIS`, audit logic). | 4. Create Lambda function, paste code |
| `08-lambda-env-var-sns-topic-arn.png` | Lambda Configuration → Environment variables: `SNS_TOPIC_ARN` set to the topic ARN. | 5. Set environment variable |
| `09-first-test-run-no-public-buckets.png` | Lambda Test tab: execution succeeded, response `{"checked": 4, "public_buckets": []}`; log output confirms all buckets private, "No public buckets detected." | 6. First test run (both buckets private) |
| `10-wrong-bucket-policy-error.png` | S3 bucket policy editor for `santosh-public-audit-private-01` (the wrong bucket): pasted policy referencing `santosh-public-audit-public-01` triggers "Unknown Error — Policy has invalid resource." | 7. Troubleshooting — edited policy on wrong bucket |
| `11-retest-timeout-error.png` | Lambda Test tab: execution **failed** with `Sandbox.Timedout` ("Task timed out after 3.00 seconds"); log output shows detection logic already correctly flagged the public bucket before the timeout cut it off. | 9. Re-test hits timeout despite correct detection |
| `12-timeout-fixed-public-bucket-detected-sns-published.png` | "Successfully updated the function" (timeout raised to 30s) followed by a successful re-test: response `{"checked": 4, "public_buckets": ["santosh-public-audit-public-01"]}`; log output shows `SNS alert published for: ['santosh-public-audit-public-01']`. | 10–12. Timeout increased, retest succeeds, SNS alert published |
| `13-sns-alert-email-received.png` | Gmail inbox: received email "[ALERT] Public S3 Bucket(s) Detected" listing `santosh-public-audit-public-01` as publicly accessible. | 13. SNS email alert received |

## Archived (`extra/`)

Near-duplicate or intermediate setup screens kept for reference but not part of the main story:

| Filename | Why archived |
|---|---|
| `Screenshot 2026-08-05 224251.png` | Test event "Create new event" setup screen — superseded by the saved/executed test in `09-first-test-run-no-public-buckets.png`. |
| `Screenshot 2026-08-05 224945.png` | Test event "manualTest" just saved, not yet executed — intermediate step before `09-first-test-run-no-public-buckets.png`. |
| `Screenshot 2026-08-05 225512.png` | Same first-test success as `09-first-test-run-no-public-buckets.png` but with response details collapsed (less informative duplicate). |
| `Screenshot 2026-08-08 212139.png` | A later repeat of the successful public-bucket-detected test run — same result as `12-timeout-fixed-public-bucket-detected-sns-published.png`, run again 3 days later. |
