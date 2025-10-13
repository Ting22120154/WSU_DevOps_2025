import os, json, time
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)

def handler(event, context):
    start = time.time()
    target_id = event["pathParameters"].get("targetId")
    try:
        table.delete_item(Key={"targetId": target_id}, ConditionExpression="attribute_exists(targetId)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            latency = round((time.time() - start) * 1000, 2)
            return {"statusCode": 404, "body": json.dumps({"error": "not found", "dynamoLatencyMs": latency})}
        raise
    latency = round((time.time() - start) * 1000, 2)
    return {"statusCode": 204, "body": json.dumps({"dynamoLatencyMs": latency})}
