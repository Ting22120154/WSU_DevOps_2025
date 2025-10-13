from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_dynamodb as dynamodb,
    CfnOutput,
    Duration,
    aws_codedeploy as codedeploy,
)
from aws_cdk.aws_cloudwatch_actions import SnsAction
from constructs import Construct
import json, pathlib

class HelloLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, table, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        memory_mb = 256

        # === 1) Crawler/Monitor Lambda（改：以 TABLE_NAME 讀 DynamoDB）===
        monitor_function = _lambda.Function(
            self, "WebsiteMonitorFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset("hello_lambda/lambda"),
            timeout=Duration.seconds(60),
            environment={
                "TABLE_NAME": table.table_name,  # ✅ 讓 crawler 讀 DB
                "TARGETS_FILE": "targets.json",  # 可選：保留本地 JSON 作為 fallback
            },
            memory_size=memory_mb,
        )

        # 允許 Lambda 寫入自訂 Metric 到 CloudWatch
        monitor_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )

        # ✅ 允許 crawler 讀（或讀寫）DynamoDB
        table.grant_read_data(monitor_function)

        # ✨ 別名（供 EventBridge & CodeDeploy）
        alias = _lambda.Alias(
            self, "CrawlerLambdaAlias",
            alias_name="ProdAlias",
            version=monitor_function.current_version
        )

        # === 2) 排程（每 5 分鐘觸發 alias）===
        rule = events.Rule(
            self, "WebsiteMonitorScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(5))
        )
        rule.add_target(targets.LambdaFunction(alias))

        # === 3) 取得儀表板上要顯示的 URL 清單（可先從本地樣本抓，用於 Widget 維度）===
        targets_path = pathlib.Path(__file__).resolve().parent / "lambda" / "targets.json"
        if targets_path.exists():
            urls = json.loads(targets_path.read_text(encoding="utf-8"))
        else:
            urls = ["https://www.bbc.com/", "https://edition.cnn.com/", "https://www.news.com.au/", "https://idontexist12345.com/"]

        # === 4) CloudWatch Dashboard ===
        dashboard = cloudwatch.Dashboard(self, "WebsiteHealthDashboard", dashboard_name="WebsiteHealthDashboard")

        latency_metrics = [
            cloudwatch.Metric(namespace="WebsiteMonitor", metric_name="Latency", dimensions_map={"URL": url})
            for url in urls
        ]
        dashboard.add_widgets(cloudwatch.GraphWidget(title="Website Latency (seconds)", left=latency_metrics, width=24))

        is_success_metrics = [
            cloudwatch.Metric(namespace="WebsiteMonitor", metric_name="IsSuccess", dimensions_map={"URL": url})
            for url in urls
        ]
        dashboard.add_widgets(cloudwatch.GraphWidget(title="Website Availability (1=Success, 0=Fail)", left=is_success_metrics, width=24))

        crawler_runtime_metric = cloudwatch.Metric(
            namespace="WebsiteMonitorCrawler", metric_name="RunTimeMs", statistic="Average", period=Duration.minutes(5)
        )
        dashboard.add_widgets(cloudwatch.GraphWidget(title="Crawler RunTime (ms)", left=[crawler_runtime_metric], width=24))

        lambda_max_mem_metric = monitor_function.metric(metric_name="MaxMemoryUsed", statistic="Maximum", period=Duration.minutes(5))
        dashboard.add_widgets(cloudwatch.GraphWidget(title="Lambda MaxMemoryUsed (MB)", left=[lambda_max_mem_metric], width=24))

        # === 5) SNS 通知 ===
        alarm_emails = ["ting22120154@gmail.com"]
        alarm_topic = sns.Topic(self, "WebsiteMonitorAlarmTopic")
        for email in alarm_emails:
            alarm_topic.add_subscription(subs.EmailSubscription(email))

        crawler_runtime_alarm = cloudwatch.Alarm(
            self, "CrawlerRunTimeHigh",
            metric=crawler_runtime_metric, threshold=2000, evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Crawler RunTimeMs too high",
        )
        crawler_runtime_alarm.add_alarm_action(SnsAction(alarm_topic))

        mem_threshold = int(memory_mb * 0.8)
        lambda_memory_alarm = cloudwatch.Alarm(
            self, "CrawlerMaxMemoryHigh",
            metric=lambda_max_mem_metric, threshold=mem_threshold, evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description=f"Lambda MaxMemoryUsed > {mem_threshold}MB",
        )
        lambda_memory_alarm.add_alarm_action(SnsAction(alarm_topic))

        CfnOutput(self, "DashboardName", value=dashboard.dashboard_name)
        CfnOutput(self, "LambdaFunctionName", value=monitor_function.function_name)

        # === 6) 針對每個 URL 建 Availability / Latency 告警 ===
        for url in urls:
            is_success_metric = cloudwatch.Metric(
                namespace="WebsiteMonitor", metric_name="IsSuccess", dimensions_map={"URL": url},
                statistic="Minimum", period=Duration.minutes(5)
            )
            availability_alarm = cloudwatch.Alarm(
                self, f"AvailabilityAlarm_{url.replace('https://','').replace('.','_').replace('/','_')}",
                metric=is_success_metric, threshold=1, evaluation_periods=2,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                alarm_description=f"Website {url} is unavailable!", actions_enabled=True,
            )
            availability_alarm.add_alarm_action(SnsAction(alarm_topic))

            latency_metric = cloudwatch.Metric(
                namespace="WebsiteMonitor", metric_name="Latency", dimensions_map={"URL": url},
                statistic="Average", period=Duration.minutes(5)
            )
            latency_alarm = cloudwatch.Alarm(
                self, f"LatencyAlarm_{url.replace('https://','').replace('.','_').replace('/','_')}",
                metric=latency_metric, threshold=1.0, evaluation_periods=3,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Website {url} latency > 1.0s!", actions_enabled=True,
            )
            latency_alarm.add_alarm_action(SnsAction(alarm_topic))

        # === 7) 事件告警記錄表（Project 1 要求 NoSQL logging）===
        alarm_table = dynamodb.Table(
            self,
            "WebHealthAlarmsTable",
            partition_key=dynamodb.Attribute(name="AlarmName", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="StateChangeTime", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_name="WebHealthAlarmsTable",
        )
        CfnOutput(self, "AlarmTableName", value=alarm_table.table_name)

        # Alarm Logger Lambda（SNS → Lambda → DynamoDB）
        alarm_logger_fn = _lambda.Function(
            self, "AlarmLoggerFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="alarm_logger.handler",
            code=_lambda.Code.from_asset("hello_lambda/alarm_logger"),
            timeout=Duration.seconds(30),
            environment={"TABLE_NAME": alarm_table.table_name},
        )
        alarm_table.grant_write_data(alarm_logger_fn)
        alarm_topic.add_subscription(subs.LambdaSubscription(alarm_logger_fn))

        # === 8) Lambda 自身健康監控 + CodeDeploy 自動回滾 ===
        lambda_invocations_alarm = cloudwatch.Alarm(
            self, "CrawlerLambdaInvocationsAlarm",
            metric=monitor_function.metric_invocations(), threshold=5, evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Crawler Lambda invoked too frequently."
        )
        lambda_duration_alarm = cloudwatch.Alarm(
            self, "CrawlerLambdaDurationAlarm",
            metric=monitor_function.metric_duration(), threshold=2000, evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Crawler Lambda average duration too high."
        )
        lambda_errors_alarm = cloudwatch.Alarm(
            self, "CrawlerLambdaErrorsAlarm",
            metric=monitor_function.metric_errors(), threshold=1, evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            alarm_description="Crawler Lambda has errors."
        )
        for a in [lambda_invocations_alarm, lambda_duration_alarm, lambda_errors_alarm]:
            a.add_alarm_action(SnsAction(alarm_topic))

        codedeploy.LambdaDeploymentGroup(
            self, "CrawlerDeploymentGroup",
            alias=alias,
            alarms=[lambda_invocations_alarm, lambda_duration_alarm, lambda_errors_alarm, crawler_runtime_alarm, lambda_memory_alarm],
            auto_rollback=codedeploy.AutoRollbackConfig(
                failed_deployment=True, stopped_deployment=True, deployment_in_alarm=True
            ),
            deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_5_MINUTES,
        )
