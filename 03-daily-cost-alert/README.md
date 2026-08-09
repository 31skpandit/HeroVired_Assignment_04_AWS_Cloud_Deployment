# Assignment 3 — Daily AWS Cost Alert Using Cost Explorer API and SNS

## 1. Objective
Query month-to-date AWS spend via the Cost Explorer API and publish an SNS
alert when it exceeds a configurable threshold.

## 2. Architecture
```
EventBridge (daily)  --->  Lambda (Python 3.12)  --->  Cost Explorer (ce:GetCostAndUsage)
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
| SNS Topic | `daily-cost-alert-topic` | ARN `arn:aws:sns:us-east-1:575638747404:daily-cost-alert-topic`; email subscription confirmed |
| Lambda Function | `daily-cost-alert` | Python 3.12, timeout set to 30s |
| IAM Role | `daily-cost-alert-role` | inline policy `daily-cost-alert-inline`, see `iam_policy.json` |
| EventBridge Rule | *(not created)* | manual invoke used for grading demo; see step 8 |

## 4. IAM Role & Policy
See [`iam_policy.json`](./iam_policy.json):
- `ce:GetCostAndUsage` — Cost Explorer does not support resource-level
  scoping, so this must be `Resource: "*"`; it is still least-privilege in
  that only this one action is granted (not `ce:*` or Billing full access).
- `sns:Publish` — scoped to the specific topic ARN.
- CloudWatch Logs permissions.

## 5. Lambda Function
See [`lambda_function.py`](./lambda_function.py).

Environment variables:
| Key | Value |
|---|---|
| `SNS_TOPIC_ARN` | `arn:aws:sns:us-east-1:575638747404:daily-cost-alert-topic` |
| `COST_THRESHOLD_USD` | `0.01` during testing (forced an alert against real month-to-date spend of $0.06); reset to `50` for the final submitted state |

## 6. Step-by-Step Implementation

> ⚠️ **Do this first, today** — Cost Explorer needs to be enabled in your
> account and it can take a few hours to activate historical data the first
> time. Console → Billing and Cost Management → **Cost Explorer** → Enable
> Cost Explorer.

1. **Set up a $1 AWS Budget Alert** (Billing → Budgets → Create budget) if
   you haven't already — this is a one-time account safety net, not part of
   this Lambda.
2. **Create the SNS topic** `daily-cost-alert-topic`, subscribe your email,
   confirm the subscription from your inbox.
3. **Create the IAM role** + inline policy from `iam_policy.json` (fill in
   account ID and topic ARN).
4. **Create the Lambda function** `daily-cost-alert`, Python 3.12, attach the
   role.
5. **Paste the code**, set env vars `SNS_TOPIC_ARN` and
   `COST_THRESHOLD_USD=0.01` (low, to force an alert on the first test),
   Deploy. Also set **Configuration → General configuration → Timeout to 30
   seconds** up front (see Challenges Faced).
6. **Test**: Test tab → Invoke. You should see the current month-to-date
   spend logged and an SNS email arrive (since $0.01 is easy to exceed).
7. **Set `COST_THRESHOLD_USD` back to a realistic value** (e.g. `50`) and do
   one final confirmation run — expect `alert_sent: false` unless you're
   actually over budget.
8. **Add the EventBridge schedule** (`rate(1 day)`) as the trigger for the
   final architecture — but do not manually invoke it repeatedly; each
   invocation costs ≈₹1 via the Cost Explorer API. **5–10 test invocations
   total is enough.**

## 7. Testing & Verification
Screenshots in `screenshots/`, in the order the work happened (see
`screenshots/MANIFEST.md` for full captions):

1. `01-sns-topic-created-subscription-pending.png` — SNS topic created, subscription pending
2. `02-sns-subscription-confirmation-email.png` — confirmation email (landed in spam)
3. `03-sns-subscription-confirmed.png` — subscription confirmed
4. `04-iam-role-trusted-entity-lambda.png` — IAM role wizard, Lambda as trusted entity
5. `05-iam-add-permissions-skipped-managed-policy-list.png` — the AWS managed-policy list, intentionally not used
6. `06-iam-inline-policy-created-permissions-review.png` — custom inline policy created
7. `07-iam-role-created-inline-policy-attached.png` — role + policy confirmed
8. `08-lambda-create-function-form.png` — Lambda function creation form
9. `09-lambda-function-created.png` — function created
10. `10-lambda-code-pasted.png` — code deployed
11. `11-lambda-timeout-configured-30s.png` — timeout raised to 30s
12. `12-lambda-env-vars-threshold-001.png` — env vars set, threshold=$0.01 to force a test alert
13. `13-lambda-test-invocation-alert-triggered.png` — test succeeded, `alert_sent: true`
14. `14-cloudwatch-log-group-created.png` — log group overview
15. `15-cloudwatch-logs-spend-and-alert-published.png` — spend calculation + SNS publish log lines
16. `16-gmail-alert-email-received.png` — alert email received
17. `17-lambda-threshold-reset-to-50.png` — threshold reset to a realistic $50

Extra/near-duplicate screenshots archived (not deleted) in `screenshots/extra/`.

## 8. Challenges Faced

- **Applied a lesson from Assignment 2 up front.** The public-bucket-audit
  Lambda had timed out on its default 3-second limit because it made several
  sequential API calls before finishing. `ce:GetCostAndUsage` is a single
  call, but it's a heavier API than a simple S3 read, so I set the timeout to
  30 seconds during initial configuration instead of waiting to hit a
  timeout error first. The test run completed in 703ms, well within budget —
  cheap insurance that avoided repeating the same class of failure.

- **This account is shared with other students/activity** (institute-provided
  AWS account), so month-to-date spend was already non-zero ($0.06 at test
  time, part of a larger $2.01 total visible in Cost Explorer) purely from
  existing account activity. That made the low-threshold test
  (`COST_THRESHOLD_USD=0.01`) trigger immediately without needing to
  provision anything extra just to generate cost.

## 9. Discussion Point
**AWS Budgets** is the managed, no-code alternative — it can alert on
forecasted or actual spend against a threshold out of the box. A custom
Lambda + Cost Explorer approach is worth it when you need per-service cost
breakdowns, delivery to a channel Budgets doesn't support natively (e.g. a
custom Slack/Teams webhook format), or custom anomaly logic beyond a flat
threshold.

## 10. Cleanup
- [ ] Deleted the SNS topic
- [ ] Deleted the Lambda function
- [ ] Deleted the IAM role
- [ ] Deleted (or disabled) the EventBridge schedule rule — do not leave this
      scheduled, since each invocation costs money
