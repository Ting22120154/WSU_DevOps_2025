# stages/crawler_app_stage.py
from aws_cdk import Stage, Environment
from constructs import Construct

from hello_lambda.dynamodb_stack import DynamoDBStack
from hello_lambda.api_gateway_stack import ApiGatewayStack
from hello_lambda.hello_lambda_stack import HelloLambdaStack

class CrawlerAppStage(Stage):
    """
    一個 Stage 代表一個部署環境（例如 Beta/Gamma/Prod）
    在此 Stage 內，我們依序部署：
      1) DynamoDB 資料表
      2) API Gateway + CRUD Lambdas（接資料表）
      3) Crawler Lambda（每 5 分鐘跑，從資料表讀 targets）
    """
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 1) 先建資料表（其餘堆疊會用到）
        self.ddb = DynamoDBStack(self, "CrawlerDynamoDB")

        # 2) 部署 API（傳入 table）
        self.api = ApiGatewayStack(
            self,
            "CrawlerApi",
            table=self.ddb.table,
        )
        self.api.add_dependency(self.ddb)  # 確保順序：先表再 API

        # 3) 部署 Crawler（傳入 table）
        self.crawler = HelloLambdaStack(
            self,
            "HelloLambda",
            table=self.ddb.table,
        )
        self.crawler.add_dependency(self.ddb)  # 確保順序：先表再 Crawler
