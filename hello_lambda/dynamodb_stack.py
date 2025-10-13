from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
)
from constructs import Construct

class DynamoDBStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 供 Crawler 與 CRUD API 使用的目標表
        self.table = dynamodb.Table(
            self,
            "CrawlerTargets",
            partition_key=dynamodb.Attribute(
                name="targetId",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_name="CrawlerTargets",  # 固定名稱便於 Lambda 直接查
        )
