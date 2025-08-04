# 🛠️ Lambda Canary Monitoring using AWS CDK

This project demonstrates how to create a simple AWS Lambda-based **canary** using AWS CDK (Cloud Development Kit) in Python. The canary periodically sends an HTTP request to a specified URL (e.g., https://www.bbc.com/) to monitor its availability and performance.

---

## 🚀 How It Works

- The Lambda function sends a GET request to **https://www.bbc.com/**.
- It checks for a successful HTTP 200 response.
- Logs the result to **Amazon CloudWatch**.

---

## 🧠 Lambda Code (lambda_function.py)

```python
import urllib3

http = urllib3.PoolManager()

def handler(event, context):
    try:
        response = http.request('GET', 'https://www.bbc.com/')
        if response.status == 200:
            return {
                "statusCode": 200,
                "body": "Website is healthy!"
            }
        else:
            return {
                "statusCode": response.status,
                "body": f"Unexpected status code: {response.status}"
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error checking website: {str(e)}"
        }

---
🏗️ CDK Stack (hello_lambda_stack.py)
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    CfnOutput,
)
from constructs import Construct

class HelloLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hello_function = _lambda.Function(
            self, "MyHelloLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset("lambda")
        )

        CfnOutput(self, "LambdaFunctionName", value=hello_function.function_name)
