# alarm_logger.py
# -----------------------------------------------------------------------------
# Purpose
#   This Lambda is subscribed to an SNS topic that receives CloudWatch Alarm
#   notifications. Every time an alarm transitions state (ALARM, OK, INSUFFICIENT_DATA),
#   SNS invokes this function with a payload that contains the alarm details.
#   The function parses the message and writes a normalized record into a
#   DynamoDB table so that you can query alarm history later.
#
# Data model (matches your DynamoDB table keys)
#   - Partition key (PK):  AlarmName            -> string
#   - Sort key (SK):       StateChangeTime      -> ISO8601 string
#
# Why Decimal conversion?
#   DynamoDB's low-level API does not accept Python float due to precision issues.
#   Boto3 expects numbers to be Decimal. The helper _to_decimal() converts any
#   floats nested inside dicts/lists to Decimal so put_item won't fail.
# -----------------------------------------------------------------------------

import os
import json
import boto3
import logging
from datetime import datetime, timezone
from decimal import Decimal
from botocore.exceptions import ClientError
from typing import Any, Dict

# -----------------------------------------------------------------------------
# Configuration & clients
# -----------------------------------------------------------------------------
# Read the DynamoDB table name from environment variables. CDK sets this on the
# Lambda function (see environment={"TABLE_NAME": alarm_table.table_name}).
TABLE_NAME = os.environ["TABLE_NAME"]

# Construct high-level DynamoDB resource client and bind to the target table.
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

# Configure structured logging. The logs go to CloudWatch Logs by default.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
def _to_decimal(v: Any) -> Any:
    """
    Recursively convert Python floats to Decimal so the object is safe to write
    to DynamoDB. Supports scalars, lists, and dicts. All other types are passed
    through unchanged.
    """
    if isinstance(v, float):
        # Use str() to avoid binary floating-point artifacts (e.g., 0.30000000004)
        return Decimal(str(v))
    if isinstance(v, list):
        return [_to_decimal(x) for x in v]
    if isinstance(v, dict):
        return {k: _to_decimal(x) for k, x in v.items()}
    return v

def _now_iso_utc() -> str:
    """Return the current time in UTC as an ISO8601 string with timezone."""
    return datetime.now(timezone.utc).isoformat()

# -----------------------------------------------------------------------------
# Lambda entry point
# -----------------------------------------------------------------------------
def handler(event: Dict[str, Any], context) -> Dict[str, Any]:


    # Defensive: event may not have Records if misconfigured
    records = event.get("Records", [])
    if not records:
        logger.warning("SNS event contained no Records; nothing to do.")
        return {"statusCode": 200, "body": "no-records"}

    written = 0  # counter for successful writes

    for idx, record in enumerate(records):
        # 1) Validate the event source so we only process SNS-origin messages.
        if record.get("EventSource") != "aws:sns":
            logger.info("Skipping non-SNS record at index %s: %s", idx, record.get("EventSource"))
            continue

        # 2) Extract the raw SNS message string.
        msg = record.get("Sns", {}).get("Message", "")
        if not msg:
            logger.warning("SNS record %s had empty Message; skipping.", idx)
            continue

        # 3) Parse the SNS message as JSON. If parsing fails, keep the raw text.
        try:
            alarm = json.loads(msg)
            parsed_ok = True
        except json.JSONDecodeError:
            alarm = {"RawMessage": msg}
            parsed_ok = False
            logger.warning("SNS message %s was not valid JSON; storing as RawMessage.", idx)

        # 4) Extract normalized fields with safe defaults.
        alarm_name = alarm.get("AlarmName", "UNKNOWN")
        new_state = alarm.get("NewStateValue", "UNKNOWN")
        reason = alarm.get("NewStateReason", "")
        # CloudWatch may provide StateChangeTime; if missing, use now().
        state_change_time = alarm.get("StateChangeTime") or _now_iso_utc()

        # Trigger section contains metric context (namespace, metric, dimensions, etc.)
        trigger = alarm.get("Trigger", {}) if parsed_ok else {}
        metric_name = trigger.get("MetricName")
        namespace = trigger.get("Namespace")

        # Dimensions come as a list of {"name": "...", "value": "..."}; flatten to dict.
        dims: Dict[str, str] = {}
        if isinstance(trigger.get("Dimensions"), list):
            dims = {d.get("name"): d.get("value") for d in trigger["Dimensions"] if isinstance(d, dict)}

        # 5) Construct the item to be written to DynamoDB.
        item: Dict[str, Any] = {
            "AlarmName": alarm_name,                   # PK: groups all events for the same alarm
            "StateChangeTime": state_change_time,      # SK: chronological ordering within PK
            "NewStateValue": new_state,                # e.g., ALARM / OK / INSUFFICIENT_DATA
            "NewStateReason": reason,                  # human-readable explanation from CW
            "MetricNamespace": namespace or "N/A",     # CW metric namespace if available
            "MetricName": metric_name or "N/A",        # CW metric name if available
            "Dimensions": _to_decimal(dims),           # flattened dimension map
            "Raw": _to_decimal(alarm),                 # full payload for audits/debugging
        }

        # 6) Write the item. We catch and log any ClientError so one bad record
        #    doesn't fail the whole batch (SNS will retry on failure otherwise).
        try:
            table.put_item(Item=item)
            written += 1
            logger.info("Wrote alarm event: %s @ %s (%s)", alarm_name, state_change_time, new_state)
        except ClientError as e:
            logger.error("Failed to write item for alarm '%s': %s", alarm_name, e, exc_info=True)

    return {"statusCode": 200, "body": f"ok (written={written})"}
