import os, json, time
import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)

def handler(event, context):
    start = time.time()
    target_id = event["pathParameters"].get("targetId")
    resp = table.get_item(Key={"targetId": target_id})
    item = resp.get("Item")
    latency = round((time.time() - start) * 1000, 2)
    if not item:
        return {"statusCode": 404, "body": json.dumps({"error": "not found", "dynamoLatencyMs": latency})}
    return {"statusCode": 200, "body": json.dumps({"item": item, "dynamoLatencyMs": latency})}
