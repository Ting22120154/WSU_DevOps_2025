# --- at top: 保留你原本的 import，再加 json, os ---
import urllib.request
import time
import boto3
import json, os   # ← 新增

cloudwatch = boto3.client('cloudwatch')

def load_targets():
    file_name = os.getenv("TARGETS_FILE", "targets.json")
    path = os.path.join(os.path.dirname(__file__), file_name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_website(url):
    start_time = time.time()
    status = 0
    content_length = 0
    success = False
    error_message = ""

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            content = response.read()
            content_length = len(content)

        latency = time.time() - start_time
        success = 200 <= status < 300
        if not success:
            error_message = "❌ Website request returned non-2xx status."

        cloudwatch.put_metric_data(
            Namespace='WebsiteMonitor',
            MetricData=[
                {'MetricName': 'Latency', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': latency, 'Unit': 'Seconds'},
                {'MetricName': 'ResponseSize', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': content_length, 'Unit': 'Bytes'},
                {'MetricName': 'StatusCode', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': status, 'Unit': 'None'},
                {'MetricName': 'IsSuccess', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': int(success), 'Unit': 'Count'}
            ]
        )
        return {"url": url, "status": status, "latency": round(latency, 2), "content_length": content_length, "success": success, "error": error_message}

    except Exception as e:
        latency = time.time() - start_time
        cloudwatch.put_metric_data(
            Namespace='WebsiteMonitor',
            MetricData=[
                {'MetricName': 'Latency', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': latency, 'Unit': 'Seconds'},
                {'MetricName': 'IsSuccess', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': 0, 'Unit': 'Count'}
            ]
        )
        return {"url": url, "status": None, "latency": round(latency, 2), "content_length": 0, "success": False, "error": f"❌ Request failed: {str(e)}"}

def handler(event, context):
    overall_start = time.time()

    urls = load_targets()               # ← 改：從 JSON 檔讀
    results = [check_website(u) for u in urls]

    # 發佈「本次爬蟲執行時間」與「檢查站點數」
    runtime_ms = int((time.time() - overall_start) * 1000)
    cloudwatch.put_metric_data(
        Namespace='WebsiteMonitorCrawler',
        MetricData=[
            {'MetricName': 'RunTimeMs', 'Value': runtime_ms, 'Unit': 'Milliseconds'},
            {'MetricName': 'SitesChecked', 'Value': len(urls), 'Unit': 'Count'}
        ]
    )

    # 回應格式維持你原本
    ok_any = any(r["success"] for r in results)
    body_lines = []
    for r in results:
        if r["success"]:
            body_lines.append(f"✅ Website is reachable!\nURL: {r['url']}\nStatus Code: {r['status']}\nLatency: {r['latency']} seconds\nResponse Size: {r['content_length']} bytes\n")
        else:
            body_lines.append(f"❌ Website check failed!\nURL: {r['url']}\nError: {r['error']}\n")
    return {"statusCode": 200 if ok_any else 500, "body": "\n".join(body_lines)}
