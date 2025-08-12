import json               # Import the json module to handle JSON data
import time               # Import the time module to measure request duration
import urllib.request     # Import urllib to send HTTP requests
import boto3              # Import boto3 to interact with AWS services (like CloudWatch)
import os                 # Import os module (not used here, but good for environment access)

# Create a CloudWatch client using boto3
cloudwatch = boto3.client('cloudwatch')

# Define the Lambda entry point
def handler(event, context):
    try:
        # Try to open and read the websites.json file from the Lambda deployment package
        with open("/var/task/websites.json") as f:
            websites = json.load(f)  # Load the list of websites from the JSON file
    except Exception as e:
        # If the file can't be opened or read, print the error and return 500
        print("❌ Failed to load websites.json:", e)
        return {
            "statusCode": 500,
            "body": "Error loading websites list."
        }

    results = []  # Create a list to store the result for each website

    # Loop through each website URL in the list
    for url in websites:
        start_time = time.time()  # Record the time before sending the request
        success = False           # Flag to track whether the request is successful
        latency = 0              # Variable to hold the response time

        try:
            # Try to send an HTTP request to the website
            response = urllib.request.urlopen(url, timeout=5)  # 5-second timeout
            latency = time.time() - start_time  # Calculate how long the request took
            success = True  # If no error, the website is reachable
            print(f"✅ {url} is reachable. Status: {response.getcode()}, Latency: {latency:.2f}s")

        except Exception as e:
            # If an error occurs (like timeout), log the error and move on
            latency = time.time() - start_time  # Still calculate latency for failed attempts
            print(f"❌ {url} is not reachable. Error: {e}")

        # Send metrics to CloudWatch for this website
        cloudwatch.put_metric_data(
            Namespace='WebCrawlerMetrics',  # Group name for metrics
            MetricData=[
                {
                    'MetricName': 'Availability',  # Metric 1: Is website available
                    'Dimensions': [{'Name': 'Website', 'Value': url}],  # Grouped by website
                    'Value': 1.0 if success else 0.0,  # 1 = success, 0 = failure
                    'Unit': 'None'
                },
                {
                    'MetricName': 'Latency',  # Metric 2: How long the request took
                    'Dimensions': [{'Name': 'Website', 'Value': url}],  # Grouped by website
                    'Value': latency,  # Measured in seconds
                    'Unit': 'Seconds'
                }
            ]
        )

        # Add this result to the output list
        results.append({
            "url": url,
            "available": success,
            "latency": round(latency, 2)
        })

    # Return the list of results as a JSON string
    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }
