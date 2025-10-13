import os, json, time
import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)

def handler(event, context):
    start = time.time()
    qs = event.get("queryStringParameters") or {}
    active_filter = qs.get("active")
    items, resp = [], table.scan()
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))

    if active_filter is not None:
        val = active_filter.lower() == "true"
        items = [i for i in items if bool(i.get("active", True)) == val]

    latency = round((time.time() - start) * 1000, 2)
    return {"statusCode": 200, "body": json.dumps({"items": items, "count": len(items), "dynamoLatencyMs": latency})}
