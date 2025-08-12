from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,  
    aws_events_targets as targets,
    aws_iam as iam, 
    CfnOutput,
    Duration 
)

from constructs import Construct

class HelloLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ✅ Main canary Lambda function (single site check)
        hello_function = _lambda.Function(
            self, "MyHelloLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset("hello_lambda/lambda")
        )

        # ✅ Add permission to put custom metrics to CloudWatch
        hello_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )

        # ✅ New crawler Lambda function (for multi-site checks from JSON)
        crawler_function = _lambda.Function(
            self, "MyCrawlerLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="crawler_function.handler",  
            code=_lambda.Code.from_asset("hello_lambda/lambda"),
            timeout=Duration.seconds(60)
        )

        crawler_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )

        # ✅ Run crawler Lambda every 5 minutes
        rule = events.Rule(
            self, "CrawlerScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(5))
        )
        rule.add_target(targets.LambdaFunction(crawler_function))

        # ✅ Output Lambda function names to CloudFormation outputs
        CfnOutput(self, "LambdaFunctionName", value=hello_function.function_name)
        CfnOutput(self, "CrawlerFunctionName", value=crawler_function.function_name)