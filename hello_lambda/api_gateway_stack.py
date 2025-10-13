from aws_cdk import (
    Stack, Duration,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
)
from constructs import Construct

class ApiGatewayStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, table, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 共用參數：設定 TABLE_NAME 供 Lambda 程式讀取
        lambda_kwargs = {
            "runtime": _lambda.Runtime.PYTHON_3_12,
            "code": _lambda.Code.from_asset("hello_lambda/lambda"),
            "timeout": Duration.seconds(30),
            "environment": {"TABLE_NAME": table.table_name},
        }

        create_fn = _lambda.Function(self, "CreateTargetFn", handler="create_target.handler", **lambda_kwargs)
        get_fn    = _lambda.Function(self, "GetTargetFn",    handler="get_target.handler",    **lambda_kwargs)
        update_fn = _lambda.Function(self, "UpdateTargetFn", handler="update_target.handler", **lambda_kwargs)
        delete_fn = _lambda.Function(self, "DeleteTargetFn", handler="delete_target.handler", **lambda_kwargs)
        list_fn   = _lambda.Function(self, "ListTargetsFn",  handler="list_targets.handler",  **lambda_kwargs)

        # 給每支 Lambda 讀寫表的權限
        for fn in [create_fn, get_fn, update_fn, delete_fn, list_fn]:
            table.grant_read_write_data(fn)

        # 建 API Gateway 路由
        api = apigw.RestApi(
            self,
            "CrawlerTargetsApi",
            deploy_options=apigw.StageOptions(
                metrics_enabled=True,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=False,
            ),
        )

        # /targets
        targets = api.root.add_resource("targets")
        targets.add_method("POST", apigw.LambdaIntegration(create_fn))
        targets.add_method("GET",  apigw.LambdaIntegration(list_fn))

        # /targets/{targetId}
        target_id = targets.add_resource("{targetId}")
        target_id.add_method("GET",    apigw.LambdaIntegration(get_fn))
        target_id.add_method("PUT",    apigw.LambdaIntegration(update_fn))
        target_id.add_method("DELETE", apigw.LambdaIntegration(delete_fn))

        # 可選：輸出 API URL（若你習慣在此輸出）
        # from aws_cdk import CfnOutput
        # CfnOutput(self, "ApiUrl", value=api.url)
