
# WSU_DevOps_2025 - Lambda Canary Monitoring Project

## 📌 Overview
This project is developed for the DevOps 2025 course. It demonstrates the use of **AWS CDK** to deploy a **Lambda function as a canary** that monitors the availability of an external website ([https://www.bbc.com](https://www.bbc.com)).

## 🚀 Objective
To simulate a canary deployment by:
- Using AWS Lambda to monitor a web resource
- Measuring availability and performance
- Practicing Infrastructure as Code (IaC) using AWS CDK

## 🛠️ Technologies Used
- AWS CDK (Python)
- AWS Lambda
- IAM Roles
- CloudFormation
- Python 3.9

## 🧠 Functionality
- A Python-based Lambda function is deployed using CDK.
- The function checks the status of https://www.bbc.com.
- The result is returned in a structured JSON response.
- The function can be tested via the AWS Lambda Console.

## 🧪 Testing

The Lambda function was manually tested using the AWS Console.  
It sends an HTTP GET request to [https://www.bbc.com](https://www.bbc.com) and returns the result.

### ✅ Successful Response Example:
```json
{
  "statusCode": 200,
  "body": "https://www.bbc.com is UP. Status code: 200"
}
If the site is down or unreachable, the function handles the error gracefully and returns:

json

{
  "statusCode": 500,
  "body": "Error: Unable to reach https://www.bbc.com"
}