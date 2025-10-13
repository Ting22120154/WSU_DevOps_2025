import os, json, time
import boto3
from boto3.dynamodb.conditions import Attr

TABLE_NAME = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)

def handler(event, context):
    start = time.time()
    target_id = event["pathParameters"].get("targetId")
    body = json.loads(event.get("body") or "{}")

    # 僅允許更新這些欄位
    fields = {k: v for k, v in body.items() if k in ["url", "active", "tags", "notes"]}
    if not fields:
        return {"statusCode": 400, "body": json.dumps({"error": "no updatable fields"})}

    # 動態組 UpdateExpression
    expr_names, expr_values, sets = {}, {}, []
    for i, (k, v) in enumerate(fields.items(), start=1):
        expr_names[f"#f{i}"] = k
        expr_values[f":v{i}"] = v
        sets.append(f"#f{i} = :v{i}")
    # updatedAt
    expr_names["#u"] = "updatedAt"
    expr_values[":now"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    sets.append("#u = :now")

    resp = table.update_item(
        Key={"targetId": target_id},
        UpdateExpression="SET " + ", ".join(sets),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
        ConditionExpression=Attr("targetId").exists(),
        ReturnValues="ALL_NEW",
    )
    latency = round((time.time() - start) * 1000, 2)
    return {"statusCode": 200, "body": json.dumps({"item": resp["Attributes"], "dynamoLatencyMs": latency})}
