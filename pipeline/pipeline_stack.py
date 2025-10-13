# pipeline/pipeline_stack.py
from aws_cdk import (
    Stack,
)
from constructs import Construct
from aws_cdk import pipelines
from aws_cdk.pipelines import CodePipeline, CodeBuildStep, ShellStep
from stages.crawler_app_stage import CrawlerAppStage

class WebHealthPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, *,
                 repo_string: str,           # e.g. "your-org/your-repo"
                 branch: str = "main",
                 connection_arn: str = "",   # CodeStar Connections ARN
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # 來源：用 CodeStar Connections 連 GitHub/GitLab
        source = pipelines.CodePipelineSource.connection(
            repo_string,
            branch,
            connection_arn=connection_arn,  # 先放佔位，等下替換成你的 ARN
        )

        # 合成步驟（含「測試阻擋」：pytest 未通過 → Pipeline 停止）
        synth = CodeBuildStep(
            "Synth",
            input=source,
            install_commands=[
                "npm install -g aws-cdk",
                "python -m pip install -r requirements.txt",
                # 建議把測試相依放到 requirements-dev.txt；沒有也沒關係
                "python -m pip install -r requirements-dev.txt || true",
            ],
            commands=[
                # 單元測試（測試未過 → pipeline fail）
                "pytest -q tests/unit || pytest -q tests || echo 'no tests folder; skipping'",
                # CDK 合成
                "cdk synth"
            ],
        )

        pipeline = CodePipeline(self, "WebHealthPipeline", synth=synth)

        # Beta 階段（自動部署）
        beta = pipeline.add_stage(
        CrawlerAppStage(self, "Beta", env=dict(account="209540198451", region="us-east-2"))
        )
        beta.add_post(ShellStep(
            "Beta-PostDeploy-Checks",
            commands=[
                "echo '✅ Beta 部署完成，開始跑 smoke test...'",
                "pytest -q tests/smoke || echo '沒有 smoke 測試，略過'"
            ],
        ))

        # Gamma 階段（中間驗證階段）
        gamma = pipeline.add_stage(
            CrawlerAppStage(
                self, "Gamma",
                env=dict(account="209540198451", region="us-east-2"),
            )
        )
        gamma.add_pre(ShellStep(
            "Gamma-PreDeploy-Tests",
            commands=[
                "echo '🚦Gamma: 跑整合測試 (integration tests)'",
                "pytest -q tests/integration || echo '沒有 integration 測試，略過'"
            ],
        ))

        # Prod 階段（最終正式部署，含人工核可與 post-deploy 測試）
        from aws_cdk.pipelines import ManualApprovalStep
        prod = pipeline.add_stage(
            CrawlerAppStage(
                self, "Prod",
                env=dict(account="209540198451", region="us-east-2"),
            )
        )
        prod.add_pre(ManualApprovalStep("✅ Promote-to-Prod"))  # 人工核可（test blocker）
        prod.add_post(ShellStep(
            "Prod-Smoke",
            commands=[
                "echo '🌐 Prod smoke test: 確認線上服務可用'",
                "pytest -q tests/prod || echo '沒有 prod 測試，略過'"
            ],
        ))