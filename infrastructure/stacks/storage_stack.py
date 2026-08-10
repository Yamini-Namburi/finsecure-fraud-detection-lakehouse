from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_kms as kms,
    aws_s3 as s3,
)
from constructs import Construct


class StorageStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------
        # KMS KEY
        # ---------------------------------------------------------

        self.lakehouse_key = kms.Key(
            self,
            "FinSecureLakehouseKey",
            alias="alias/finsecure-lakehouse",
            description="KMS key for FinSecure fraud detection lakehouse",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ---------------------------------------------------------
        # RAW DATA BUCKET
        # ---------------------------------------------------------

        self.raw_bucket = s3.Bucket(
            self,
            "RawBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.lakehouse_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    expiration=Duration.days(30),
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ---------------------------------------------------------
        # PROCESSED DATA BUCKET
        # ---------------------------------------------------------

        self.processed_bucket = s3.Bucket(
            self,
            "ProcessedBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.lakehouse_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ---------------------------------------------------------
        # SCRIPTS BUCKET
        # ---------------------------------------------------------

        self.scripts_bucket = s3.Bucket(
            self,
            "ScriptsBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.lakehouse_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ---------------------------------------------------------
        # CLOUDFORMATION OUTPUTS
        # ---------------------------------------------------------

        CfnOutput(
            self,
            "RawBucketName",
            value=self.raw_bucket.bucket_name,
            description="S3 bucket for raw transaction data",
        )

        CfnOutput(
            self,
            "ProcessedBucketName",
            value=self.processed_bucket.bucket_name,
            description="S3 bucket for processed and Iceberg data",
        )

        CfnOutput(
            self,
            "ScriptsBucketName",
            value=self.scripts_bucket.bucket_name,
            description="S3 bucket for Glue and other processing scripts",
        )

        CfnOutput(
            self,
            "LakehouseKmsKeyArn",
            value=self.lakehouse_key.key_arn,
            description="KMS key used to encrypt FinSecure lakehouse data",
        )