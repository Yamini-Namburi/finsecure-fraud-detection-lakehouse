#!/usr/bin/env python3

import os

import aws_cdk as cdk

from stacks.network_stack import NetworkStack
from stacks.storage_stack import StorageStack
from stacks.streaming_stack import StreamingStack


app = cdk.App()

environment = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)


network_stack = NetworkStack(
    app,
    "FinSecureNetworkStack",
    env=environment,
)


storage_stack = StorageStack(
    app,
    "FinSecureStorageStack",
    env=environment,
)


streaming_stack = StreamingStack(
    app,
    "FinSecureStreamingStack",
    raw_bucket=storage_stack.raw_bucket,
    lakehouse_key=storage_stack.lakehouse_key,
    env=environment,
)


app.synth()