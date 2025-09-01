import urllib.request    # Import urllib to send HTTP requests
import time              # Import time to calculate latency
import boto3             # Import boto3 to send CloudWatch metrics

cloudwatch = boto3.client('cloudwatch')  # Create a CloudWatch client

# Check a single website and report metrics to CloudWatch
def check_website(url):
    start_time = time.time()   # Record start time
    status = 0                # HTTP status code
    content_length = 0        # Content length (bytes)
    success = False           # Is check successful
    error_message = ""        # Error message

    try:
        # Add User-Agent header to avoid being blocked as a bot
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)     # Send HTTP request
        status = response.getcode()                # Get HTTP status code
        content = response.read()                  # Read website content
        content_length = len(content)              # Calculate content length

        latency = time.time() - start_time         # Calculate latency (seconds)

        if 200 <= status < 300:      # Success if status code is 2xx
            success = True
        else:
            error_message = "❌ Website request returned non-2xx status."  # Non-2xx status is error

        # Send metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='WebsiteMonitor',   # Namespace
            MetricData=[
                {'MetricName': 'Latency', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': latency, 'Unit': 'Seconds'},
                {'MetricName': 'ResponseSize', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': content_length, 'Unit': 'Bytes'},
                {'MetricName': 'StatusCode', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': status, 'Unit': 'None'},
                {'MetricName': 'IsSuccess', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': int(success), 'Unit': 'Count'}
            ]
        )

        # Return check result as a dict
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
        # Still report failure metrics if error
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

# Lambda main handler
def handler(event, context):
    # List of websites to monitor
    urls = [
        "https://www.bbc.com/",
        "https://edition.cnn.com/",
        "https://www.news.com.au/"
    ]
    results = []   # Store all website check results
    for url in urls:
        result = check_website(url)
        results.append(result)

    # Combine all check results into response
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
    # If at least one website is successful, statusCode = 200, otherwise 500
    status_code = 200 if any(r["success"] for r in results) else 500

    return {
        "statusCode": status_code,
        "body": body
    }