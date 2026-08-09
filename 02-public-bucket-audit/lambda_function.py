import os

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
sns = boto3.client("sns")

SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

PUBLIC_GRANTEE_URIS = {
    "http://acs.amazonaws.com/groups/global/AllUsers",
    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",
}


def is_block_public_access_fully_enabled(bucket_name):
    try:
        resp = s3.get_public_access_block(Bucket=bucket_name)
        cfg = resp["PublicAccessBlockConfiguration"]
        return all(
            [
                cfg.get("BlockPublicAcls", False),
                cfg.get("IgnorePublicAcls", False),
                cfg.get("BlockPublicPolicy", False),
                cfg.get("RestrictPublicBuckets", False),
            ]
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchPublicAccessBlockConfiguration":
            return False
        raise


def is_policy_public(bucket_name):
    try:
        resp = s3.get_bucket_policy_status(Bucket=bucket_name)
        return resp["PolicyStatus"]["IsPublic"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
            return False
        raise


def has_public_acl_grant(bucket_name):
    try:
        resp = s3.get_bucket_acl(Bucket=bucket_name)
        for grant in resp.get("Grants", []):
            if grant.get("Grantee", {}).get("URI") in PUBLIC_GRANTEE_URIS:
                return True
        return False
    except ClientError:
        return False


def lambda_handler(event, context):
    buckets = s3.list_buckets()["Buckets"]
    public_buckets = []

    for b in buckets:
        name = b["Name"]
        bpa_enabled = is_block_public_access_fully_enabled(name)
        policy_public = is_policy_public(name)
        acl_public = has_public_acl_grant(name)

        # A bucket is only actually reachable publicly if Block Public Access
        # is NOT fully enabled AND either the policy or an ACL grants access.
        is_public = (not bpa_enabled) and (policy_public or acl_public)

        print(
            f"{name}: BlockPublicAccessFullyEnabled={bpa_enabled}, "
            f"PolicyIsPublic={policy_public}, ACLHasPublicGrant={acl_public}, "
            f"FLAGGED_PUBLIC={is_public}"
        )

        if is_public:
            public_buckets.append(name)

    if public_buckets:
        message = "The following S3 buckets appear to be PUBLICLY ACCESSIBLE:\n\n" + "\n".join(
            f"- {n}" for n in public_buckets
        )
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="[ALERT] Public S3 Bucket(s) Detected",
            Message=message,
        )
        print(f"SNS alert published for: {public_buckets}")
    else:
        print("No public buckets detected.")

    return {"checked": len(buckets), "public_buckets": public_buckets}
