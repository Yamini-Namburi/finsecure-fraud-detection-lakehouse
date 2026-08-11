import json
import random
from pathlib import Path

from transaction_generator import (
    generate_transaction,
    generate_velocity_transactions,
)


OUTPUT_DIR = Path(__file__).parent / "sample_data"
OUTPUT_FILE = OUTPUT_DIR / "transactions.json"


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    transactions = []

    for _ in range(95):
        transaction = generate_transaction(
            fraud_probability=0.10
        )

        transactions.append(transaction)

    velocity_transactions = (
        generate_velocity_transactions(
            count=5
        )
    )

    transactions.extend(
        velocity_transactions
    )

    random.shuffle(transactions)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            transactions,
            file,
            indent=2,
        )

    fraud_count = sum(
        transaction["is_fraud"]
        for transaction in transactions
    )

    print(
        f"Generated {len(transactions)} transactions"
    )

    print(
        f"Fraud transactions: {fraud_count}"
    )

    print(
        f"Normal transactions: "
        f"{len(transactions) - fraud_count}"
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()