# Screenshot Manifest — EC2 Auto-Tagging Lambda (Assignment 04)

This folder documents, step by step, the build of an EventBridge + Lambda
pipeline that automatically tags newly-launched EC2 instances. Screenshots
are numbered in narrative order (not always raw chronological order — a
couple of CloudWatch Logs screenshots were captured later in the session but
document earlier events, and are placed where they belong in the story).

Files not listed here (near-duplicate retakes, intermediate wizard scrolls,
redundant confirmation pages) were archived in `extra/` rather than deleted.

| Filename | What it shows | Step |
|---|---|---|
| 01-iam-role-created.png | IAM console: role `ec2-auto-tagging-role` created (0 policies attached yet), ARN and creation date visible. | 1. IAM role setup |
| 02-iam-inline-policy-json.png | IAM policy JSON editor: the inline policy being written, with three statements — `ec2:CreateTags` scoped to `instance/*` ARNs, `ec2:DescribeInstances`, and CloudWatch Logs permissions (`CreateLogGroup`/`CreateLogStream`/`PutLogEvents`). | 1. IAM inline policy |
| 03-iam-policy-attached-confirmed.png | IAM role page after save: "Policy ec2-auto-tagging-inline created", now showing 1 permissions policy attached to the role. | 1. IAM policy attached |
| 04-lambda-function-created-default-code.png | Lambda console: function `ec2-auto-tagging` just created (Python 3.12), still showing the default boilerplate "Hello from Lambda!" code before editing. | 2. Lambda function created |
| 05-lambda-final-code-pasted.png | Lambda code editor with the final handler pasted and deployed: reads `detail.instance-id` / `detail.state` from the EventBridge event, skips if not "running", and calls `ec2.create_tags` with LaunchDate/Owner/Environment tags. | 2. Lambda code deployed |
| 06-eventbridge-event-pattern-json.png | EventBridge "Create rule" wizard, Step 2: custom JSON event pattern — `source: aws.ec2`, `detail-type: EC2 Instance State-change Notification`, `detail.state: running`. | 3. EventBridge event pattern |
| 07-eventbridge-target-lambda-selected.png | EventBridge wizard, Step 3: target type "AWS service" → Lambda function `ec2-auto-tagging` selected, with a default IAM invoke role being created for the rule. | 3. EventBridge target set |
| 08-eventbridge-rule-created-confirmed.png | EventBridge Rules list: "Rule ec2-auto-tag-on-running was created successfully", rule shown as Enabled alongside other account rules. | 3. EventBridge rule created |
| 09-mock-test-fake-instance-event-json.png | Lambda Test tab: saved test event `mockRunningEvent` with a deliberately fake/nonexistent instance ID `i-0fakefake0000000` and `state: running`, crafted to validate event parsing before touching real AWS resources. | 6. Mock test (pre-launch safety check) |
| 10-mock-test-failed-clienterror-invalidid.png | Lambda Test tab result: "Executing function: failed" — `ClientError`, `InvalidID` — "The ID 'i-0fakefake0000000' is not valid" at the `create_tags` call. This failure was expected and correct: it proves the event parsing and IAM wiring worked before any real instance existed. | 6. Mock test — expected failure |
| 11-cloudwatch-logs-mock-test-error.png | CloudWatch Logs console for `/aws/lambda/ec2-auto-tagging`: log stream confirming "Received EventBridge event for instance=i-0fakefake0000000, state=running" followed by the same InvalidID ClientError, viewed directly in CloudWatch (not just the Lambda console). | 6. Mock test — CloudWatch confirmation |
| 12-ec2-launch-wizard-t2-micro-default-mistake.png | EC2 "Launch an instance" wizard: name `auto-tag-test-instance`, AMI Amazon Linux 2023 selected — but the instance-type summary defaulted to **t2.micro**, the mistake that had to be caught and corrected before launching. | 5. EC2 launch — mistake caught |
| 13-ec2-instance-running-t3-micro-corrected.png | EC2 Instances list + detail panel: `auto-tag-test-instance` (`i-0b015ccdd9ffca6ea`) now **Running** as the corrected **t3.micro** type, in security group `launch-wizard-1` (default SSH-open group, unchanged) with no key pair. | 5. EC2 instance launched (corrected) |
| 14-cloudwatch-logs-automatic-trigger-success.png | CloudWatch Logs for `/aws/lambda/ec2-auto-tagging`: real, automatic invocation triggered by EventBridge (no manual Test click) — "Received EventBridge event for instance=i-0b015ccdd9ffca6ea, state=running" followed by "Tagged instance ... with: [LaunchDate, Owner, Environment]". | 7. Automatic EventBridge trigger — success |
| 15-ec2-tags-applied.png | EC2 console, instance Tags tab for `auto-tag-test-instance`: the three tags actually applied by the Lambda — `Owner=auto-tag-lambda`, `LaunchDate=2026-08-09`, `Environment=dev` — plus the `Name` tag. | 8. Tags applied — final proof |

## Not captured in this set

- **Lambda Configuration → Triggers tab** showing the EventBridge rule attached to the function (no screenshot of this specific tab was found among the raw captures).
- **Clean re-test of the Test tab using the real instance ID** after it was already tagged (the real trigger was automatic via EventBridge, so no manual "succeeded" Test-tab screenshot exists).
- **Instance termination** (final cleanup) — no screenshot of the Terminate action or confirmation was found in the raw captures.

These were left out rather than substituted with a screenshot that didn't actually show them.
