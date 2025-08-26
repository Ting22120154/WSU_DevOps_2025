from aws_cdk import (
    Stack,  # Represents an AWS infrastructure stack (all resources in one deployable unit)
    aws_lambda as _lambda,  # AWS Lambda for running code without servers
    aws_events as events,  # EventBridge (CloudWatch Events) for scheduling jobs (cron, rate)
    aws_events_targets as targets,  # Targets let EventBridge invoke Lambda directly
    aws_iam as iam,  # IAM manages permissions and access for Lambda and other resources
    aws_cloudwatch as cloudwatch,  # CloudWatch is used for metrics, dashboards, alarms
    aws_sns as sns,  # SNS (Simple Notification Service) to send notifications (e.g. email alerts)
    aws_sns_subscriptions as subs,  # Manage SNS subscriptions, such as email recipients
    CfnOutput,  # Outputs information after deployment (for referencing resources)
    Duration  # Represents units of time (seconds, minutes, etc.)
)
from aws_cdk.aws_cloudwatch_actions import SnsAction  # Allows CloudWatch alarms to trigger SNS actions
from constructs import Construct  # Base class for all AWS CDK resources

class HelloLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        # Initialize the CDK stack (all resources are created inside this stack)
        super().__init__(scope, construct_id, **kwargs)

        # ✅ 1. Create the main Lambda Function — handles website health monitoring
        monitor_function = _lambda.Function(
            self, "WebsiteMonitorFunction",  # Logical name for the Lambda (shown in AWS Console)
            runtime=_lambda.Runtime.PYTHON_3_12,  # Runtime environment: Python 3.12
            handler="lambda_function.handler",    # Entry point (filename.handler_function_name)
            code=_lambda.Code.from_asset("hello_lambda/lambda"),  # Path to Lambda code directory
            timeout=Duration.seconds(60)  # Max Lambda execution time (prevents infinite loops)
        )
        # Grant Lambda permission to publish custom metrics to CloudWatch
        monitor_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],  # Permission to publish metrics
                resources=["*"]  # Applies to all resources (could be restricted for production)
            )
        )

        # ✅ 2. EventBridge Rule — schedules the Lambda to run every 5 minutes
        rule = events.Rule(
            self, "WebsiteMonitorScheduleRule",  # Name of the schedule rule
            schedule=events.Schedule.rate(Duration.minutes(5))  # Runs every 5 minutes
        )
        rule.add_target(targets.LambdaFunction(monitor_function))  # Lambda is triggered by the rule

        # ✅ 3. List of websites to monitor
        urls = [
            "https://www.bbc.com/",      # BBC News
            "https://edition.cnn.com/",  # CNN International
            "https://www.news.com.au/"   # News.com.au (Australia)
        ]

        # ✅ 4. CloudWatch Dashboard — displays monitoring data in AWS Console
        dashboard = cloudwatch.Dashboard(
            self, "WebsiteHealthDashboard",   # Logical name for the dashboard
            dashboard_name="WebsiteHealthDashboard"
        )
        # Add a latency graph for all monitored URLs
        latency_metrics = [
            cloudwatch.Metric(
                namespace="WebsiteMonitor",  # Must match metric namespace sent by Lambda
                metric_name="Latency",       # Name of the metric
                dimensions_map={"URL": url}  # Group by URL
            ) for url in urls
        ]
        dashboard.add_widgets(cloudwatch.GraphWidget(
            title="Website Latency (seconds)",  # Chart title
            left=latency_metrics,               # Data series for Y-axis
            width=24                            # Chart width (max 24 units)
        ))
        # Add an availability graph (1=success, 0=failure)
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

        # ✅ 5. Output resource names for easy reference after deployment
        CfnOutput(self, "DashboardName", value=dashboard.dashboard_name)  # Outputs dashboard name
        CfnOutput(self, "LambdaFunctionName", value=monitor_function.function_name)  # Outputs Lambda name

        # ✅ 6. SNS Alert Email — sends automatic email alerts when alarms are triggered
        alarm_emails = ["ting22120154@gmail.com"]  # List of email addresses for alarm notifications
        alarm_topic = sns.Topic(self, "WebsiteMonitorAlarmTopic")  # SNS topic for alarms
        for email in alarm_emails:
            alarm_topic.add_subscription(subs.EmailSubscription(email))  # Add email recipients

        # ✅ 7. CloudWatch Alarms — automatically create alarms for each website URL
        for url in urls:
            # 7-1. Availability Alarm — triggers if there are 2 consecutive failures
            is_success_metric = cloudwatch.Metric(
                namespace="WebsiteMonitor",
                metric_name="IsSuccess",
                dimensions_map={"URL": url},
                statistic="Minimum",              # Minimum in period; 0 means at least one failure
                period=Duration.minutes(5)        # Each period is 5 minutes
            )
            availability_alarm = cloudwatch.Alarm(
                self, f"AvailabilityAlarm_{url.replace('https://','').replace('.','_').replace('/','_')}",  # Unique alarm name per URL
                metric=is_success_metric,
                threshold=1,                      # Alarm if value drops below 1 (i.e., 0)
                evaluation_periods=2,             # Alarm if below threshold for 2 periods (10 min)
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description=f"Website {url} is unavailable!",  # Alarm description (shown in email/console)
                actions_enabled=True,
            )
            availability_alarm.add_alarm_action(SnsAction(alarm_topic))  # On alarm, notify SNS (sends email)

            # 7-2. Latency Alarm — triggers if average latency > 1 second for 3 periods
            latency_metric = cloudwatch.Metric(
                namespace="WebsiteMonitor",
                metric_name="Latency",
                dimensions_map={"URL": url},
                statistic="Average",              # Use average latency in each period
                period=Duration.minutes(5)
            )
            latency_alarm = cloudwatch.Alarm(
                self, f"LatencyAlarm_{url.replace('https://','').replace('.','_').replace('/','_')}",  # Unique alarm name per URL
                metric=latency_metric,
                threshold=1.0,                    # Alarm if average latency > 1.0 second
                evaluation_periods=3,             # Alarm if above threshold for 3 periods (15 min)
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Website {url} latency > 1.0s!",
                actions_enabled=True,
            )
            latency_alarm.add_alarm_action(SnsAction(alarm_topic))  # On alarm, notify SNS (sends email)