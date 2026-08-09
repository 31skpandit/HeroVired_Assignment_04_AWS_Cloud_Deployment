import os
from datetime import datetime, timedelta, timezone

import boto3

s3 = boto3.client("s3")

BUCKET_NAME = os.environ.get("BUCKET_NAME", "REPLACE-WITH-YOUR-BUCKET-NAME")
AGE_THRESHOLD_DAYS = int(os.environ.get("AGE_THRESHOLD_DAYS", "30"))


def lambda_handler(event, context):
    cutoff = datetime.now(timezone.utc) - timedelta(days=AGE_THRESHOLD_DAYS)
    paginator = s3.get_paginator("list_objects_v2")

    deleted_keys = []
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            if obj["LastModified"] < cutoff:
                s3.delete_object(Bucket=BUCKET_NAME, Key=obj["Key"])
                deleted_keys.append(obj["Key"])
                print(f"Deleted: {obj['Key']} (LastModified={obj['LastModified']})")

    print(f"Bucket={BUCKET_NAME} | ThresholdDays={AGE_THRESHOLD_DAYS} | "
          f"TotalDeleted={len(deleted_keys)}")

    return {
        "bucket": BUCKET_NAME,
        "age_threshold_days": AGE_THRESHOLD_DAYS,
        "deleted_count": len(deleted_keys),
        "deleted_keys": deleted_keys,
    }
