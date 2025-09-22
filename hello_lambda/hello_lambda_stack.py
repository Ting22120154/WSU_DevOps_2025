from aws_cdk import (
    Stack,                          # Stack groups all AWS resources into one deployable unit
    aws_lambda as _lambda,          # AWS Lambda for serverless functions
    aws_events as events,           # EventBridge for scheduling (cron/rate)
    aws_events_targets as targets,  # EventBridge targets (invoke Lambda)
    aws_iam as iam,                 # IAM permissions and roles
    aws_cloudwatch as cloudwatch,   # CloudWatch metrics, dashboards, alarms
    aws_sns as sns,                 # SNS topics for notifications
    aws_sns_subscriptions as subs,  # SNS subscription types (Email, Lambda, etc.)
    aws_dynamodb as dynamodb,       # DynamoDB for NoSQL storage
    CfnOutput,                      # CloudFormation output values after deploy
    Duration                        # Time helper (seconds, minutes)
)
from aws_cdk.aws_cloudwatch_actions import SnsAction  # Alarm -> SNS action
from constructs import Construct                        # Base class for all CDK constructs


class HelloLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        # Initialize the base Stack (required for all CDK stacks)
        super().__init__(scope, construct_id, **kwargs)

        # === 1) Monitoring Lambda: checks websites and publishes custom metrics ===
        monitor_function = _lambda.Function(
            self, "WebsiteMonitorFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,           # Python 3.12 runtime
            handler="lambda_function.handler",             # Entry point in your code folder
            code=_lambda.Code.from_asset("hello_lambda/lambda"),  # Path to Lambda source
            timeout=Duration.seconds(60)                   # Prevent long-running executions
        )
        # Allow the Lambda to push custom metrics to CloudWatch
        monitor_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]  # For demo simplicity; scope down in production
            )
        )

        # === 2) Schedule: run the monitoring Lambda every 5 minutes ===
        rule = events.Rule(
            self, "WebsiteMonitorScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(5))
        )
        rule.add_target(targets.LambdaFunction(monitor_function))

        # === 3) URLs to monitor (used by dashboard and alarms) ===
        urls = [
            "https://www.bbc.com/",
            "https://edition.cnn.com/",
            "https://www.news.com.au/",
            "https://idontexist12345.com/" #wrong one
        ]

        # === 4) CloudWatch Dashboard: visualize latency and availability ===
        dashboard = cloudwatch.Dashboard(
            self, "WebsiteHealthDashboard",
            dashboard_name="WebsiteHealthDashboard"
        )

        # Latency graph (seconds) — one metric per URL
        latency_metrics = [
            cloudwatch.Metric(
                namespace="WebsiteMonitor",                 # Must match your Lambda's Namespace
                metric_name="Latency",                      # Custom metric name
                dimensions_map={"URL": url}                 # Dimension: URL
            ) for url in urls
        ]
        dashboard.add_widgets(cloudwatch.GraphWidget(
            title="Website Latency (seconds)",
            left=latency_metrics,
            width=24
        ))

        # Availability graph (1 = success, 0 = fail)
        is_success_metrics = [
            cloudwatch.Metric(
                namespace="WebsiteMonitor",
                metric_name="IsSuccess",
                dimensions_map={"URL": url}
            ) for url in urls
        ]
        dashboard.add_widgets(cloudwatch.GraphWidget(
            title="Website Availability (1=Success, 0=Fail)",
            left=is_success_metrics,
            width=24
        ))

        # Output names for quick reference after deploy
        CfnOutput(self, "DashboardName", value=dashboard.dashboard_name)
        CfnOutput(self, "LambdaFunctionName", value=monitor_function.function_name)

        # === 5) SNS Topic + Email subscriptions for alarm notifications ===
        alarm_emails = ["ting22120154@gmail.com"]          # Add more emails if needed
        alarm_topic = sns.Topic(self, "WebsiteMonitorAlarmTopic")
        for email in alarm_emails:
            alarm_topic.add_subscription(subs.EmailSubscription(email))

        # === 6) CloudWatch Alarms for each URL ===
        for url in urls:
            # Availability alarm: triggers if value < 1 (i.e., at least one failure)
            is_success_metric = cloudwatch.Metric(
                namespace="WebsiteMonitor",
                metric_name="IsSuccess",
                dimensions_map={"URL": url},
                statistic="Minimum",                       # 0 if any failure occurred
                period=Duration.minutes(5)
            )
            availability_alarm = cloudwatch.Alarm(
                self, f"AvailabilityAlarm_{url.replace('https://','').replace('.','_').replace('/','_')}",
                metric=is_success_metric,
                threshold=1,
                evaluation_periods=2,                      # 2 consecutive periods (10 mins)
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description=f"Website {url} is unavailable!",
                actions_enabled=True,
            )
            availability_alarm.add_alarm_action(SnsAction(alarm_topic))

            # Latency alarm: triggers if avg latency > 1s for 3 periods
            latency_metric = cloudwatch.Metric(
                namespace="WebsiteMonitor",
                metric_name="Latency",
                dimensions_map={"URL": url},
                statistic="Average",
                period=Duration.minutes(5)
            )
            latency_alarm = cloudwatch.Alarm(
                self, f"LatencyAlarm_{url.replace('https://','').replace('.','_').replace('/','_')}",
                metric=latency_metric,
                threshold=1.0,
                evaluation_periods=3,                      # 15 mins over threshold
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Website {url} latency > 1.0s!",
                actions_enabled=True,
            )
            latency_alarm.add_alarm_action(SnsAction(alarm_topic))

        # === 7) DynamoDB table: store alarm events (NoSQL logging requirement) ==========
        alarm_table = dynamodb.Table(
            self,
            "WebHealthAlarmsTable",                        # Logical ID in CloudFormation
            partition_key=dynamodb.Attribute(
                name="AlarmName",                          # PK groups events by alarm
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="StateChangeTime",                    # SK orders events by time
                type=dynamodb.AttributeType.STRING         # Use ISO8601 strings
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # No capacity planning
            table_name="WebHealthAlarmsTable"             # Fixed physical name for easy lookup
        )

        # Output the DynamoDB table name for easy verification after deploy
        CfnOutput(
            self, "AlarmTableName",
            value=alarm_table.table_name,
            description="DynamoDB table for storing CloudWatch alarm events"
        )

        # === 8) Alarm Logger Lambda: subscribe to SNS and write items to DynamoDB ===
        alarm_logger_fn = _lambda.Function(
            self, "AlarmLoggerFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,                     # Use Python 3.12 runtime
            handler="alarm_logger.handler",                          # Module.function in the code folder
            code=_lambda.Code.from_asset("hello_lambda/alarm_logger"),  # Path to logger code
            timeout=Duration.seconds(30),                            # Keep it short
            environment={
                "TABLE_NAME": alarm_table.table_name,                # Pass DynamoDB table via env var
            },
        )

        # Grant write permissions to the DynamoDB table
        alarm_table.grant_write_data(alarm_logger_fn)

        # Subscribe the logger Lambda to the existing SNS topic (it will receive all alarm messages)
        alarm_topic.add_subscription(subs.LambdaSubscription(alarm_logger_fn))
