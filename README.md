# Lambda Canary Monitoring using AWS CDK

This project demonstrates how to create a simple AWS Lambda-based canary using AWS CDK (Cloud Development Kit) in Python. The canary periodically sends an HTTP request to a specified URL (e.g., https://www.bbc.com/) to check its availability and performance. The infrastructure is fully defined using AWS CDK.

## 🔧 Project Structure
WSU_DevOps_2025/
├── lambda/
│ └── lambda_function.py # The Lambda function that acts as a canary
├── hello_lambda/
│ └── hello_lambda_stack.py # CDK stack definition
├── app.py # CDK entry point
├── requirements.txt # Python dependencies
├── README.md # Project documentation
└── cdk.json # CDK config


## 🚀 How It Works

- The Lambda function makes an HTTP GET request to `https://www.bbc.com/`.
- It checks for a successful response (status code 200).
- Logs success or failure to Amazon CloudWatch.

## 🖥️ Lambda Function (`lambda_function.py`)

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


📦 Deployment Steps
Install dependencies


pip install -r requirements.txt
Bootstrap your environment (if not already)

cdk bootstrap
Deploy the stack

cdk deploy
Test the Lambda Function in the AWS Console

