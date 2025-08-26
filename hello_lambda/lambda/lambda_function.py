import urllib.request    # 導入 urllib 來發送 HTTP 請求 / Import urllib to send HTTP requests
import time              # 導入 time 用來計算延遲 / Import time to calculate latency
import boto3             # 導入 boto3 來上報 CloudWatch 指標 / Import boto3 to send CloudWatch metrics

cloudwatch = boto3.client('cloudwatch')  # 建立 CloudWatch 客戶端 / Create a CloudWatch client

# 檢查單一網站並上報 CloudWatch / Check a single website and report metrics to CloudWatch
def check_website(url):
    start_time = time.time()   # 記錄開始時間 / Record start time
    status = 0                # HTTP 狀態碼 / HTTP status code
    content_length = 0        # 內容長度 / Content length (bytes)
    success = False           # 是否成功 / Is check successful
    error_message = ""        # 錯誤訊息 / Error message

    try:
        # 加 User-Agent 避免被擋 / Add User-Agent header to avoid being blocked as a bot
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)     # 發送 HTTP 請求 / Send HTTP request
        status = response.getcode()                # 取得 HTTP 狀態碼 / Get HTTP status code
        content = response.read()                  # 讀取網頁內容 / Read website content
        content_length = len(content)              # 計算內容長度 / Calculate content length

        latency = time.time() - start_time         # 計算延遲（秒）/ Calculate latency (seconds)

        if 200 <= status < 300:      # 只要是 2xx 狀態碼就是成功 / Success if status code is 2xx
            success = True
        else:
            error_message = "❌ Website request returned non-2xx status."  # 不是 2xx 就記錯誤 / Non-2xx status is error

        # 上報 CloudWatch 指標 / Send metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='WebsiteMonitor',   # 命名空間 / Namespace
            MetricData=[
                {'MetricName': 'Latency', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': latency, 'Unit': 'Seconds'},
                {'MetricName': 'ResponseSize', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': content_length, 'Unit': 'Bytes'},
                {'MetricName': 'StatusCode', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': status, 'Unit': 'None'},
                {'MetricName': 'IsSuccess', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': int(success), 'Unit': 'Count'}
            ]
        )

        # 整理回傳結果 / Return check result as a dict
        result = {
            "url": url,
            "status": status,
            "latency": round(latency, 2),
            "content_length": content_length,
            "success": success,
            "error": error_message
        }
        return result

    except Exception as e:
        # 出錯仍要上報 CloudWatch / Still report failure metrics if error
        latency = time.time() - start_time
        cloudwatch.put_metric_data(
            Namespace='WebsiteMonitor',
            MetricData=[
                {'MetricName': 'Latency', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': latency, 'Unit': 'Seconds'},
                {'MetricName': 'IsSuccess', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': 0, 'Unit': 'Count'}
            ]
        )
        return {
            "url": url,
            "status": None,
            "latency": round(latency, 2),
            "content_length": 0,
            "success": False,
            "error": f"❌ Request failed: {str(e)}"
        }

# Lambda handler 入口 / Lambda main handler
def handler(event, context):
    # 監控多個網址 / List of websites to monitor
    urls = [
        "https://www.bbc.com/",
        "https://edition.cnn.com/",
        "https://www.news.com.au/"
    ]
    results = []   # 儲存所有網站檢查結果 / Store all website check results
    for url in urls:
        result = check_website(url)
        results.append(result)

    # 彙整回傳訊息 / Combine all check results into response
    body = ""
    for r in results:
        if r["success"]:
            body += (
                f"✅ Website is reachable!\n"
                f"URL: {r['url']}\n"
                f"Status Code: {r['status']}\n"
                f"Latency: {r['latency']} seconds\n"
                f"Response Size: {r['content_length']} bytes\n\n"
            )
        else:
            body += (
                f"❌ Website check failed!\n"
                f"URL: {r['url']}\n"
                f"Error: {r['error']}\n\n"
            )
    # 只要有一個網站成功就 statusCode = 200，全部失敗才 500
    status_code = 200 if any(r["success"] for r in results) else 500

    return {
        "statusCode": status_code,
        "body": body
    }