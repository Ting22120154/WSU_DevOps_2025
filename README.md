# Website Health Monitor
This project uses **AWS Lambda + CloudWatch + EventBridge** to monitor website uptime and performance. It:

---

## Features
- Checks website every 5 minutes  
- Publishes custom metrics to CloudWatch  
- Dashboard auto-generated  
- Sends email alerts via SNS

---

## About me
Hi! I'm TING. I am building a cloud-based website monitoring system using AWS Lambda and CloudWatch.

<details>
<summary>Monitored Websites</summary>

| Rank | Website              |
|-----:|----------------------|
|     1| https://www.bbc.com/ |
|     2| https://cnn.com/     |
|     3| https://news.com.au/ |

</details>

---

## Installation & Deployment

To deploy this monitoring system in your AWS environment:

1. **Install prerequisites**:
   - [Node.js](https://nodejs.org/)
   - [AWS CLI](https://aws.amazon.com/cli/)
   - [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html)
   - Python 3.12

2. **Clone the repository**:
   ```bash
   git clone https://github.com/Ting22120154/WSU_DevOps_2025.git
   cd WSU_DevOps_2025
   ```

3. **Bootstrap the CDK** (only once per AWS account/region):
   ```bash
   cdk bootstrap
   ```

4. **Deploy the stack**:
   ```bash
   cdk deploy
   ```

5. **Confirm email subscription**:
   - Check your inbox and **confirm** the SNS subscription request to receive alerts.

---

##  Architecture Overview

This AWS CDK stack provisions the following components:

| Component           | Description                                                        |
|---------------------|--------------------------------------------------------------------|
| **Lambda Function** | Checks website avalibility, latency, and HTTP response codes       |
| **EventBridge Rule**| Triggers the Lambda function every 5 minutes (schedule rule)       |
| **CloudWatch**      | Collects custom metrics and displays dashboards                    |
| **SNS Topic**       | Sends email alerts when alarms are triggered                       |
| **CloudWatch Alarms** | Detects failures or high latency and triggers notifications      |
| **CDK Outputs**     | Prints out the CloudWatch dashboard. The dashboard shows two graphs: latency (in seconds) and availability       |


---
##  Lambda Function Overview

This project uses an AWS Lambda function to check the health of websites.

For each URL in the list, the Lambda:

1. Sends an HTTP request using Python's `urllib`.
2. Measures:
   - Response Latency (how long it takes)
   - Response Size
   - Success (1) or Failure (0)
   - HTTP Status Code
3. Sends these metrics to CloudWatch.
4. Returns a human-readable report (used for alerts or debugging).

The function runs every 5 minutes, triggered by an EventBridge rule.

---

## Metrics Tracked

The Lambda function sends 4 key metrics to CloudWatch under the namespace `WebsiteMonitor`:

| Metric Name    | Description                           | Unit     |
|----------------|---------------------------------------|----------|
| `Latency`      | How long the website took to respond  | Seconds  |
| `IsSuccess`    | 1 if response is 2xx, else 0          | Count    |
| `StatusCode`   | HTTP status code of the response      | None     |
| `ResponseSize` | Size of the webpage content           | Bytes    |

These are visualized in the CloudWatch dashboard and used to trigger alarms.

---

## SNS Integration

This project uses **Amazon SNS (Simple Notification Service)** to send email alerts.

- A CloudWatch Alarm is triggered when a website fails or has high latency.
- The alarm sends a message to an SNS Topic.
- That topic is subscribed to your email.
- You receive the alert via email.

SNS can also support other types of notifications (e.g. SMS, Lambda triggers, webhooks) if extended in the future.

---

##  Email Alerts

When an alarm is triggered (e.g. a website is down or slow), an email is sent via Amazon SNS.

### How to receive email alerts:

1. In `app.py`, update the `alarm_emails` list with your email address.
2. Deploy the stack.
3. Go to your inbox and confirm the subscription (check spam folder).
---

## Project Structure

```text
HELLO-LAMBDA/
│
├── hello_lambda/               # CDK application source
│   ├
│   ├── lambda/                 # Lambda function code
│   │   ├── lambda_function.py  # Main logic to check websites
│   │ 
│   └── hello_lambda_stack.py   # CDK Stack definition (all infra defined here)
│
├── app.py                      # Entry point for CDK (calls HelloLambdaStack)
├── cdk.json                    # CDK configuration
├── README.md                   # Project documentation