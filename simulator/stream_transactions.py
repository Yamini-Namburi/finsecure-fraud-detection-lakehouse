import json
import time

import boto3

from transaction_generator import generate_transaction


REGION = "eu-north-1"
STREAM_NAME = "finsecure-transaction-stream"


kinesis = boto3.client(
    "kinesis",
    region_name=REGION,
)


def send_transaction(transaction: dict) -> None:
    response = kinesis.put_record(
        StreamName=STREAM_NAME,
        Data=(
            json.dumps(transaction) + "\n"
        ).encode("utf-8"),
        PartitionKey=transaction["customer_id"],
    )

    print(
        f"Sent transaction "
        f"{transaction['transaction_id']} "
        f"to shard {response['ShardId']}"
    )


def main():
    number_of_transactions = 20

    for _ in range(number_of_transactions):
        transaction = generate_transaction(
            fraud_probability=0.10
        )

        send_transaction(transaction)

        time.sleep(1)


if __name__ == "__main__":
    main()