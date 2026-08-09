import os
from datetime import date, timedelta

import boto3

# Cost Explorer's API endpoint only exists in us-east-1, regardless of which
# region your other resources live in.
ce = boto3.client("ce", region_name="us-east-1")
sns = boto3.client("sns")

SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
COST_THRESHOLD_USD = float(os.environ.get("COST_THRESHOLD_USD", "50"))


def get_month_to_date_cost():
    today = date.today()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()

    # Cost Explorer requires Start < End; if today is the 1st of the month,
    # bump End forward by a day so the range isn't empty.
    if start == end:
        end = (today + timedelta(days=1)).isoformat()

    response = ce.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    amount = float(response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])
    return amount, start, end


def lambda_handler(event, context):
    amount, start, end = get_month_to_date_cost()
    print(
        f"Month-to-date spend ({start} to {end}): ${amount:.2f} "
        f"(threshold: ${COST_THRESHOLD_USD:.2f})"
    )

    alert_sent = False
    if amount > COST_THRESHOLD_USD:
        message = (
            f"AWS month-to-date spend is ${amount:.2f}, which exceeds your "
            f"threshold of ${COST_THRESHOLD_USD:.2f}."
        )
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="[ALERT] AWS Cost Threshold Exceeded",
            Message=message,
        )
        alert_sent = True
        print("SNS alert published.")
    else:
        print("Spend is within threshold. No alert sent.")

    return {
        "month_to_date_usd": round(amount, 2),
        "threshold_usd": COST_THRESHOLD_USD,
        "alert_sent": alert_sent,
    }
