#!/usr/bin/env python3

import os

import aws_cdk as cdk

from stacks.network_stack import NetworkStack
from stacks.storage_stack import StorageStack


app = cdk.App()


NetworkStack(
    app,
    "FinSecureNetworkStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)


StorageStack(
    app,
    "FinSecureStorageStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)


app.synth()