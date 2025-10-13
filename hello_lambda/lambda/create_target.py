import os, json, uuid, time
import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)

def handler(event, context):
    start = time.time()
    body = json.loads(event.get("body") or "{}")
    url = body.get("url")
    if not url:
        return {"statusCode": 400, "body": json.dumps({"error": "url is required"})}

    item = {
        "targetId": str(uuid.uuid4()),
        "url": url,
        "active": bool(body.get("active", True)),
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tags": body.get("tags") or [],
        "notes": body.get("notes") or "",
    }
    table.put_item(Item=item)
    latency = round((time.time() - start) * 1000, 2)
    return {"statusCode": 201, "body": json.dumps({"item": item, "dynamoLatencyMs": latency})}
