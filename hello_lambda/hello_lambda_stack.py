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
            code=_lambda.Code.from_asset("hello_lambda/lambda")

        )

        CfnOutput(self, "LambdaFunctionName", value=hello_function.function_name)