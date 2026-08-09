# Assignment 4 — Auto-Tagging EC2 Instances on Launch

## 1. Objective
Automatically tag newly launched EC2 instances (LaunchDate, Owner,
Environment) for resource tracking and cost allocation, triggered by an
EventBridge rule on the instance's "running" state-change event.

## 2. Architecture
```
EC2 instance launched --> state changes to "running"
        |
        v
EventBridge Rule (source: aws.ec2, detail-type: EC2 Instance State-change
Notification, detail.state: running)
        |
        v
Lambda (Python 3.12) --> ec2:CreateTags on the instance
        |
        v
CloudWatch Logs
```

## 3. AWS Resources Created
| Resource | Name | Notes |
|---|---|---|
| EC2 Instance (test) | `auto-tag-test-instance` (`i-0b015ccdd9ffca6ea`) | t3.micro, Amazon Linux 2023, terminated right after screenshots |
| Lambda Function | `ec2-auto-tagging` | Python 3.12, timeout 15s |
| IAM Role | `ec2-auto-tagging-role` | inline policy `ec2-auto-tagging-inline`, see `iam_policy.json` |
| EventBridge Rule | `ec2-auto-tag-on-running` | event pattern below; fired automatically on real launch |

## 4. IAM Role & Policy
See [`iam_policy.json`](./iam_policy.json):
- `ec2:CreateTags` — scoped to `instance/*` resources only (not volumes,
  snapshots, or other EC2 resource types)
- `ec2:DescribeInstances` — must be `Resource: "*"` (this action does not
  support resource-level scoping in IAM)
- CloudWatch Logs permissions

No `AmazonEC2FullAccess` attached. `CreateTags` resource ARN scoped to
account `575638747404`.

## 5. Lambda Function
See [`lambda_function.py`](./lambda_function.py). No environment variables
required — it reads `detail.instance-id` and `detail.state` straight from the
EventBridge event payload.

## 6. Step-by-Step Implementation

1. **Create the IAM role** (Lambda trust) + inline policy from
   `iam_policy.json` (fill in your account ID).
2. **Create the Lambda function** `ec2-auto-tagging`, Python 3.12, attach the
   role.
3. **Paste the code**, Deploy.
4. **Create the EventBridge rule**:
   - EventBridge → Rules → Create rule.
   - Name: `ec2-auto-tag-on-running`.
   - Event bus: default. Rule type: **Event pattern**.
   - Event pattern (JSON):
     ```json
     {
       "source": ["aws.ec2"],
       "detail-type": ["EC2 Instance State-change Notification"],
       "detail": {
         "state": ["running"]
       }
     }
     ```
   - Target: your Lambda function `ec2-auto-tagging`.
5. **Manual "unit test" first** (before touching real EC2): Lambda console →
   Test → use a sample EventBridge EC2 state-change event as the test JSON
   (AWS provides a sample event template named "EC2 Instance State-change
   Notification" in the test event dropdown) → Invoke → confirm it doesn't
   error even against a fake/nonexistent instance ID handling path.
6. **Real test**: Launch a **t3.micro** EC2 instance (any AMI, e.g. Amazon
   Linux 2023). Wait ~30–60 seconds after it reaches "running".
7. **Verify tags**: EC2 console → Instances → select the instance → Tags tab
   → confirm `LaunchDate`, `Owner`, `Environment` are present.
8. **Check CloudWatch Logs** for the Lambda execution confirming the
   instance ID and tags applied.
9. **Terminate the test instance immediately** after screenshots.

## 7. Testing & Verification
Screenshots in `screenshots/`, in the order the work happened (see
`screenshots/MANIFEST.md` for full captions):

1. `01-iam-role-created.png` — IAM role created
2. `02-iam-inline-policy-json.png` — inline policy JSON
3. `03-iam-policy-attached-confirmed.png` — policy attached
4. `04-lambda-function-created-default-code.png` — function created
5. `05-lambda-final-code-pasted.png` — final handler code deployed
6. `06-eventbridge-event-pattern-json.png` — event pattern configured
7. `07-eventbridge-target-lambda-selected.png` — Lambda set as target
8. `08-eventbridge-rule-created-confirmed.png` — rule created
9. `09-mock-test-fake-instance-event-json.png` — mock event with a fake instance ID
10. `10-mock-test-failed-clienterror-invalidid.png` — expected failure (proves wiring before touching real EC2)
11. `11-cloudwatch-logs-mock-test-error.png` — same error confirmed in logs
12. `12-ec2-launch-wizard-t2-micro-default-mistake.png` — wizard defaulted to t2.micro (caught before launch)
13. `13-ec2-instance-running-t3-micro-corrected.png` — real instance running, corrected to t3.micro
14. `14-cloudwatch-logs-automatic-trigger-success.png` — EventBridge auto-triggered the Lambda, tags applied
15. `15-ec2-tags-applied.png` — Tags tab showing LaunchDate/Owner/Environment

Extra/near-duplicate screenshots archived (not deleted) in `screenshots/extra/`.

**Not captured** (no screenshot exists for these — optional, not required since
the automatic-trigger proof above already demonstrates success end-to-end):
Lambda Triggers tab view, a clean Test-tab re-run against the real instance
ID, and the instance-termination confirmation. Take these now if you'd like
fuller documentation, otherwise the current set is sufficient.

## 8. Challenges Faced

- **Default instance type mismatch.** The EC2 launch wizard defaults to
  `t2.micro`, not `t3.micro`. Both are free-tier eligible, so it's an easy
  detail to miss — caught it in the launch summary panel before hitting
  "Launch instance" and switched to `t3.micro` to match the assignment spec.

- **Mock test intentionally "failed" — and that's the useful part.** Before
  launching a real instance, I ran a mock EventBridge event with a fake
  instance ID (`i-0fakefake0000000`) through the Test tab. It correctly threw
  `ClientError: InvalidID` at the `ec2.create_tags` call — proving the event
  parsing (`detail.instance-id`, `detail.state`) and IAM wiring were correct
  *before* any real AWS resource was involved, and that the failure mode is
  the expected one (a real, existing instance ID would not hit this path).
  This caught issues cheaply instead of debugging against a live instance.

- **No manual invoke needed for the real test.** Once the EventBridge rule
  was attached and the real `t3.micro` instance was launched, the Lambda
  fired automatically within seconds of the instance reaching `running` —
  confirmed in CloudWatch Logs (`Received EventBridge event for
  instance=i-0b015ccdd9ffca6ea, state=running` → `Tagged instance ...`) with
  no manual trigger at all, which is the actual end-to-end proof this task is
  meant to demonstrate.

## 9. Discussion Point (Bonus)
To also capture *who* launched the instance, you'd add a second EventBridge
rule matching CloudTrail's `RunInstances` API call event (source
`aws.ec2`, event name `RunInstances`), extract `userIdentity.arn` from the
event detail, and add it as an `Owner` tag instead of the static placeholder
used here — a common interview follow-up question.

## 10. Cleanup
- [ ] Terminated the test EC2 instance
- [ ] Deleted the Lambda function
- [ ] Deleted the IAM role
- [ ] Deleted the EventBridge rule
