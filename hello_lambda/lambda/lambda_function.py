import urllib.request  # Import the urllib.request module to send HTTP requests.
import time  # Import the time module to measure how long the request takes.

def handler(event, context):
    url = "https://www.bbc.com/"
    start_time = time.time()  # Record the start time before sending the request.

    success = False  # Create a flag to mark if the connection is successful

    try:
        # Send request to the website
        response = urllib.request.urlopen(url)
        success = True

    except:
        # If there is an error (like network issue), set success to False
        success = False

    # Calculate how long the request took (whether it succeeded or failed)
    latency = time.time() - start_time

    if success:
        # Get status code and response content
        status = response.getcode()
        content = response.read()
        content_length = len(content)

        # Return success result
        return {
            "statusCode": 200,
            "body": (
                "✅ Website is reachable!\n"
                "URL: " + url + "\n"
                "Status Code: " + str(status) + "\n"
                "Latency: " + str(round(latency, 2)) + " seconds\n"
                "Response Size: " + str(content_length) + " bytes"
            )
        }

    else:
        # Return failure result
        return {
            "statusCode": 500,
            "body": (
                "❌ Failed to reach website.\n"
                "URL: " + url + "\n"
                "Tried for: " + str(round(latency, 2)) + " seconds"
            )
        }