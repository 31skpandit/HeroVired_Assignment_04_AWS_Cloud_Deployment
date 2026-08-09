from datetime import date

import boto3

ec2 = boto3.client("ec2")


def lambda_handler(event, context):
    detail = event.get("detail", {})
    instance_id = detail.get("instance-id")
    state = detail.get("state")

    print(f"Received EventBridge event for instance={instance_id}, state={state}")

    if not instance_id or state != "running":
        print("Not a 'running' state-change event, skipping.")
        return {"skipped": True, "instance_id": instance_id, "state": state}

    tags = [
        {"Key": "LaunchDate", "Value": date.today().isoformat()},
        {"Key": "Owner", "Value": "auto-tag-lambda"},
        {"Key": "Environment", "Value": "dev"},
    ]

    ec2.create_tags(Resources=[instance_id], Tags=tags)

    print(f"Tagged instance {instance_id} with: {tags}")
    return {"tagged_instance": instance_id, "tags": tags}
