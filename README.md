
# WSU_DevOps_2025 - Lambda Canary Monitoring Project

## 📌 Overview
This project is part of the **DevOps 2025** coursework.  
It demonstrates how to use **AWS CDK** to deploy a Python-based **Lambda function** that monitors the health and performance of an external website (https://www.bbc.com).

---

## 🚀 Objective
- ✅ Monitor website availability using AWS Lambda
- ⏱️ Measure response latency (in seconds)
- 📦 Report response size (in bytes)
- 📄 Return structured JSON results
- ☁️ Practice Infrastructure as Code (IaC) with AWS CDK

---

## 🧰 Technologies Used
- AWS Lambda
- AWS CDK (Python)
- IAM Roles
- Python 3.12+
- CloudFormation (via CDK)

---

## 🧠 Functionality
- Sends an HTTP GET request to `https://www.bbc.com`
- If successful, it returns:
  - HTTP status code (e.g., 200)
  - Response time (latency)
  - Response length (in bytes)
- If the request fails, it returns an error message and elapsed time

---

## 🧪 Example Lambda Output

### ✅ Success Response:
```json
{
  "statusCode": 200,
  "body": "✅ Website is reachable!\nURL: https://www.bbc.com/\nStatus Code: 200\nLatency: 0.42 seconds\nResponse Size: 178254 bytes"
}
❌ Failure Response:
{
  "statusCode": 500,
  "body": "❌ Failed to reach website.\nURL: https://www.bbc.com/\nTried for: 3.10 seconds"
}

🛠️ Deployment Steps
bash

# Install Python dependencies
pip install -r requirements.txt

# Bootstrap your environment (once per AWS account)
cdk bootstrap

# Deploy the Lambda function
cdk deploy
📂 Project Structure
graphql

WSU_DevOps_2025/
├── lambda/
│   └── lambda_function.py       # The Lambda canary code
├── hello_lambda_stack.py        # CDK Stack: defines the Lambda resource
├── app.py                       # CDK application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
