from aws_cdk import (
    CfnOutput,
    Stack,
    aws_iam as iam,
    aws_kinesis as kinesis,
    aws_kinesisfirehose as firehose,
)
from constructs import Construct


class StreamingStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        raw_bucket,
        lakehouse_key,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------
        # KINESIS DATA STREAM
        # ---------------------------------------------------------

        self.transaction_stream = kinesis.Stream(
            self,
            "TransactionStream",
            stream_name="finsecure-transaction-stream",
            stream_mode=kinesis.StreamMode.ON_DEMAND,
        )

        # ---------------------------------------------------------
        # FIREHOSE IAM POLICY
        # ---------------------------------------------------------

        firehose_policy = iam.PolicyDocument(
            statements=[
                # Read transactions from Kinesis
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kinesis:DescribeStream",
                        "kinesis:GetShardIterator",
                        "kinesis:GetRecords",
                        "kinesis:ListShards",
                    ],
                    resources=[
                        self.transaction_stream.stream_arn,
                    ],
                ),

                # Write transaction files into Raw S3
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:AbortMultipartUpload",
                        "s3:GetBucketLocation",
                        "s3:ListBucket",
                        "s3:ListBucketMultipartUploads",
                    ],
                    resources=[
                        raw_bucket.bucket_arn,
                    ],
                ),

                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:PutObject",
                        "s3:GetObject",
                    ],
                    resources=[
                        raw_bucket.arn_for_objects("*"),
                    ],
                ),

                # Use the customer-managed KMS key
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt",
                        "kms:Encrypt",
                        "kms:GenerateDataKey",
                        "kms:ReEncrypt*",
                    ],
                    resources=[
                        lakehouse_key.key_arn,
                    ],
                ),
            ]
        )

        # ---------------------------------------------------------
        # FIREHOSE IAM ROLE
        # ---------------------------------------------------------

        firehose_role = iam.Role(
            self,
            "FirehoseRole",
            assumed_by=iam.ServicePrincipal(
                "firehose.amazonaws.com"
            ),
            inline_policies={
                "FirehoseAccessPolicy": firehose_policy,
            },
        )

        # ---------------------------------------------------------
        # KINESIS SOURCE CONFIGURATION
        # ---------------------------------------------------------

        kinesis_source = (
            firehose.CfnDeliveryStream
            .KinesisStreamSourceConfigurationProperty(
                kinesis_stream_arn=(
                    self.transaction_stream.stream_arn
                ),
                role_arn=firehose_role.role_arn,
            )
        )

        # ---------------------------------------------------------
        # FIREHOSE BUFFERING
        # ---------------------------------------------------------

        buffering = (
            firehose.CfnDeliveryStream
            .BufferingHintsProperty(
                interval_in_seconds=60,
                size_in_m_bs=5,
            )
        )

        # ---------------------------------------------------------
        # FIREHOSE S3 DESTINATION
        # ---------------------------------------------------------

        s3_destination = (
            firehose.CfnDeliveryStream
            .ExtendedS3DestinationConfigurationProperty(
                bucket_arn=raw_bucket.bucket_arn,
                role_arn=firehose_role.role_arn,

                prefix=(
                    "transactions/"
                    "year=!{timestamp:yyyy}/"
                    "month=!{timestamp:MM}/"
                    "day=!{timestamp:dd}/"
                ),

                error_output_prefix=(
                    "errors/"
                    "!{firehose:error-output-type}/"
                ),

                buffering_hints=buffering,

                compression_format="GZIP",
            )
        )

        # ---------------------------------------------------------
        # FIREHOSE DELIVERY STREAM
        # ---------------------------------------------------------

        self.delivery_stream = firehose.CfnDeliveryStream(
            self,
            "TransactionDeliveryStream",

            delivery_stream_name=(
                "finsecure-transaction-firehose"
            ),

            delivery_stream_type=(
                "KinesisStreamAsSource"
            ),

            kinesis_stream_source_configuration=(
                kinesis_source
            ),

            extended_s3_destination_configuration=(
                s3_destination
            ),
        )

        # Ensure IAM role is completely available first
        self.delivery_stream.node.add_dependency(
            firehose_role
        )

        # ---------------------------------------------------------
        # OUTPUTS
        # ---------------------------------------------------------

        CfnOutput(
            self,
            "TransactionStreamName",
            value=self.transaction_stream.stream_name,
        )

        CfnOutput(
            self,
            "DeliveryStreamName",
            value=self.delivery_stream.ref,
        )