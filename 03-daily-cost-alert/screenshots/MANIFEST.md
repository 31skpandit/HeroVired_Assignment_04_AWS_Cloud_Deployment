# Screenshot Manifest — Daily AWS Cost Alert (Lambda + Cost Explorer + SNS)

Documentation-quality sequence of screenshots captured while building the
`daily-cost-alert` Lambda function. Ordered to tell the build story: SNS
topic first (so its ARN could be referenced when scoping IAM permissions),
then the IAM role, then the Lambda function itself, configuration, testing,
and verification via CloudWatch Logs and the delivered email alert.

Six near-duplicate/in-progress retakes were archived to `extra/` (not
deleted) — see note at the bottom.

| Filename | What it shows | Step |
|---|---|---|
| `01-sns-topic-created-subscription-pending.png` | SNS console, topic `daily-cost-alert-topic` details page; one EMAIL subscription listed with status "Pending confirmation" for santy.datascience@gmail.com. | 1. Create SNS topic + email subscription |
| `02-sns-subscription-confirmation-email.png` | Gmail Spam folder — "AWS Notification - Subscription Confirmation" email from AWS Notifications, with the "Confirm subscription" link. | 2. Receive SNS confirmation email (landed in spam) |
| `03-sns-subscription-confirmed.png` | SNS confirmation landing page: "Subscription confirmed! You have successfully subscribed," with the subscription ARN. | 3. Confirm SNS subscription |
| `04-iam-role-trusted-entity-lambda.png` | IAM Create Role wizard, Step 1 "Select trusted entity" — AWS service selected, use case set to Lambda. | 4. IAM role: choose Lambda as trusted entity |
| `05-iam-add-permissions-skipped-managed-policy-list.png` | IAM Create Role wizard, Step 2 "Add permissions" — the full list of 1,211 AWS managed policies. Shown intentionally to document that no managed policy was selected here; a custom inline policy was attached after role creation instead. | 5. IAM role: managed-policy list (intentionally skipped) |
| `06-iam-inline-policy-created-permissions-review.png` | IAM "Review and create" page for policy `daily-cost-alert-inline`, listing the 3 granted permissions: CloudWatch Logs (Limited: Write), Cost Explorer Service (Limited: Read, all resources), and SNS (Limited: Write, scoped to `daily-cost-alert-topic`). | 6. Create scoped inline policy |
| `07-iam-role-created-inline-policy-attached.png` | IAM role `daily-cost-alert-role` detail page with success banner "Policy daily-cost-alert-inline created" and the policy listed under Permissions policies. | 7. IAM role + inline policy confirmed |
| `08-lambda-create-function-form.png` | Lambda "Create function" form — Author from scratch, function name `daily-cost-alert`, runtime Python 3.12, custom execution role set to `daily-cost-alert-role`. | 8. Create Lambda function |
| `09-lambda-function-created.png` | Lambda function page for `daily-cost-alert` right after creation, success banner, empty Code source editor. | 9. Lambda function created |
| `10-lambda-code-pasted.png` | Code source editor with `lambda_function.py` pasted — imports boto3, defines `ce`/`sns` clients, `SNS_TOPIC_ARN`/`COST_THRESHOLD_USD` env vars, and `get_month_to_date_cost()` calling `ce.get_cost_and_usage`. "Successfully updated the function" banner. | 10. Paste and deploy function code |
| `11-lambda-timeout-configured-30s.png` | Configuration → General configuration: Timeout raised to 0 min 30 sec (from the 3-second default), Memory 128 MB. | 11. Increase timeout to 30s |
| `12-lambda-env-vars-threshold-001.png` | Configuration → Environment variables (2): `COST_THRESHOLD_USD = 0.01` and `SNS_TOPIC_ARN = arn:aws:sns:us-east-1:...:daily-cost-alert-topic`. Threshold deliberately set tiny to force an alert on test. | 12. Set env vars (threshold lowered to force alert) |
| `13-lambda-test-invocation-alert-triggered.png` | Test tab, "Executing function: succeeded." Response JSON: `{"month_to_date_usd": 0.06, "threshold_usd": 0.01, "alert_sent": true}`. | 13. Invoke test event — alert triggered |
| `14-cloudwatch-log-group-created.png` | CloudWatch → Log groups → `/aws/lambda/daily-cost-alert` overview page, showing 1 log stream created 2 minutes prior. | 14. Confirm CloudWatch log group auto-created |
| `15-cloudwatch-logs-spend-and-alert-published.png` | CloudWatch Log events for the invocation: `Month-to-date spend (2026-08-01 to 2026-08-08): $0.06 (threshold: $0.01)` followed by `SNS alert published.`, plus the REPORT line with duration/memory stats. | 15. Verify log output |
| `16-gmail-alert-email-received.png` | Gmail inbox — "[ALERT] AWS Cost Threshold Exceeded" from AWS Notifications: "AWS month-to-date spend is $0.06, which exceeds your threshold of $0.01." | 16. Confirm SNS email alert delivered |
| `17-lambda-threshold-reset-to-50.png` | Configuration → Environment variables after cleanup: `COST_THRESHOLD_USD` reset from `0.01` to `50` (realistic production value), `SNS_TOPIC_ARN` unchanged, "Updating the function" banner. | 17. Reset threshold to production value ($50) |

## Archived (`extra/`)

Not deleted, just excluded from the numbered sequence — either an exact
retake of an adjacent kept screenshot or a transient/in-progress state:

| Filename | Why archived |
|---|---|
| `Screenshot 2026-08-08 221221.png` | Retake of the same "Add permissions" 1,211-policy list already captured in `05-...png`. |
| `Screenshot 2026-08-08 221710.png` | Same Lambda "Create function" form as `08-...png`, just scrolled further down. |
| `Screenshot 2026-08-08 222037.png` | Mid-edit state of the Test tab (event name field showing a transient "This field is required" validation error before the event was saved). |
| `Screenshot 2026-08-08 222052.png` | Test event saved with the generic default `key1/key2/key3` JSON template, before the real invocation result shown in `13-...png`. |
| `Screenshot 2026-08-08 222636.png` | Duplicate of the CloudWatch log events view already captured in `15-...png`. |
| `Screenshot 2026-08-08 222645.png` | Duplicate of the Gmail alert email already captured in `16-...png` (same email, viewed a few minutes later). |

## Note

No screenshot of the initial Cost Explorer check (Total cost $2.01,
Feb–Jul 2026 monthly breakdown) was found among the 23 raw screenshots in
this folder — it was likely taken in an earlier session and not saved here.
