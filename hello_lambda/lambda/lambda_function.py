import urllib.request
import time
import boto3

cloudwatch = boto3.client('cloudwatch')

def handler(event, context):
    url = "https://www.bbc.com/"
    start_time = time.time()

    status = 0
    content_length = 0
    success = False

    try:
        # ✅ Add User-Agent header to avoid getting blocked
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        status = response.getcode()
        content = response.read()
        content_length = len(content)

        if status >= 200 and status < 300:
            success = True
            latency = time.time() - start_time

            cloudwatch.put_metric_data(
                Namespace='WebsiteMonitor',
                MetricData=[
                    {'MetricName': 'Latency', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': latency, 'Unit': 'Seconds'},
                    {'MetricName': 'ResponseSize', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': content_length, 'Unit': 'Bytes'},
                    {'MetricName': 'StatusCode', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': status, 'Unit': 'None'},
                    {'MetricName': 'IsSuccess', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': 1, 'Unit': 'Count'}
                ]
            )

            return {
                "statusCode": 200,
                "body": (
                    "✅ Website is reachable!\n"
                    f"URL: {url}\n"
                    f"Status Code: {status}\n"
                    f"Latency: {round(latency, 2)} seconds\n"
                    f"Response Size: {content_length} bytes"
                )
            }

        else:
            latency = time.time() - start_time

            cloudwatch.put_metric_data(
                Namespace='WebsiteMonitor',
                MetricData=[
                    {'MetricName': 'Latency', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': latency, 'Unit': 'Seconds'},
                    {'MetricName': 'ResponseSize', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': content_length, 'Unit': 'Bytes'},
                    {'MetricName': 'StatusCode', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': status, 'Unit': 'None'},
                    {'MetricName': 'IsSuccess', 'Dimensions': [{'Name': 'URL', 'Value': url}], 'Value': 0, 'Unit': 'Count'}
                ]
            )            
            return {
                "statusCode": 500,
                "body": "❌ Website request returned non-2xx status."
            }



    except Exception as e:
        print("Error:", str(e))
        return {
            "statusCode": 500,
            "body": f"❌ Request failed: {str(e)}"
        }

