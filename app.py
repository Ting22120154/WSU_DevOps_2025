#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import aws_cdk as cdk
from pipeline.pipeline_stack import WebHealthPipelineStack

# 允許從環境變數帶入帳號/區域（CI/CD 常用），否則使用預設
ACCOUNT = os.getenv("CDK_DEFAULT_ACCOUNT", "209540198451")
REGION  = os.getenv("CDK_DEFAULT_REGION",  "us-east-2")

app = cdk.App()

# 也可用 cdk context 覆寫（例：cdk deploy -c repo=org/repo -c branch=main -c conn_arn=...）
repo_string    = app.node.try_get_context("repo")     or "wsu-comp3028/wed-7pm-9pm-avenger"
branch         = app.node.try_get_context("branch")   or "main"
connection_arn = app.node.try_get_context("conn_arn") or "arn:aws:codestar-connections:ap-southeast-2:123456789012:connection/XXXXXXXX-XXXX"

WebHealthPipelineStack(
    app,
    "WebHealthPipelineStack",
    repo_string=repo_string,
    branch=branch,
    connection_arn=connection_arn,
    env=cdk.Environment(account=ACCOUNT, region=REGION),
)

app.synth()
