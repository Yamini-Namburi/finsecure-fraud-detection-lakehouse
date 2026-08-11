import csv
import json
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).parent
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

CUSTOMERS_FILE = SAMPLE_DATA_DIR / "customers.csv"
ACCOUNTS_FILE = SAMPLE_DATA_DIR / "accounts.csv"
MERCHANTS_FILE = SAMPLE_DATA_DIR / "merchants.csv"
TRANSACTIONS_FILE = SAMPLE_DATA_DIR / "transactions.json"


def load_csv_ids(file_path: Path, id_column: str) -> set[str]:
    with open(
        file_path,
        mode="r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        return {
            row[id_column]
            for row in reader
        }


def load_transactions() -> list[dict]:
    with open(
        TRANSACTIONS_FILE,
        mode="r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def main():
    customer_ids = load_csv_ids(
        CUSTOMERS_FILE,
        "customer_id",
    )

    account_ids = load_csv_ids(
        ACCOUNTS_FILE,
        "account_id",
    )

    merchant_ids = load_csv_ids(
        MERCHANTS_FILE,
        "merchant_id",
    )

    transactions = load_transactions()

    invalid_customer_ids = []
    invalid_account_ids = []
    invalid_merchant_ids = []

    duplicate_transaction_ids = []

    seen_transaction_ids = set()

    fraud_types = Counter()

    geo_anomaly_errors = []
    high_value_errors = []

    for transaction in transactions:

        transaction_id = transaction["transaction_id"]

        if transaction_id in seen_transaction_ids:
            duplicate_transaction_ids.append(
                transaction_id
            )

        seen_transaction_ids.add(
            transaction_id
        )

        if transaction["customer_id"] not in customer_ids:
            invalid_customer_ids.append(
                transaction["customer_id"]
            )

        if transaction["account_id"] not in account_ids:
            invalid_account_ids.append(
                transaction["account_id"]
            )

        if transaction["merchant_id"] not in merchant_ids:
            invalid_merchant_ids.append(
                transaction["merchant_id"]
            )

        if transaction["is_fraud"]:

            fraud_type = transaction["fraud_type"]

            fraud_types[fraud_type] += 1

            if fraud_type == "GEO_ANOMALY":

                if (
                    transaction["country_code"]
                    == transaction["registered_country"]
                ):
                    geo_anomaly_errors.append(
                        transaction_id
                    )

            if fraud_type == "HIGH_VALUE":

                if transaction["amount"] < 1000:
                    high_value_errors.append(
                        transaction_id
                    )

    print("------------------------------------------------")
    print("TRANSACTION DATA QUALITY REPORT")
    print("------------------------------------------------")

    print(
        f"Transactions: {len(transactions)}"
    )

    print(
        f"Unique transaction IDs: "
        f"{len(seen_transaction_ids)}"
    )

    print()

    print(
        f"Invalid customer IDs: "
        f"{len(invalid_customer_ids)}"
    )

    print(
        f"Invalid account IDs: "
        f"{len(invalid_account_ids)}"
    )

    print(
        f"Invalid merchant IDs: "
        f"{len(invalid_merchant_ids)}"
    )

    print(
        f"Duplicate transaction IDs: "
        f"{len(duplicate_transaction_ids)}"
    )

    print()

    print("Fraud distribution:")

    for fraud_type, count in fraud_types.items():
        print(
            f"  {fraud_type}: {count}"
        )

    print()

    print(
        f"Invalid GEO_ANOMALY records: "
        f"{len(geo_anomaly_errors)}"
    )

    print(
        f"Invalid HIGH_VALUE records: "
        f"{len(high_value_errors)}"
    )

    print()

    passed = (
        not invalid_customer_ids
        and not invalid_account_ids
        and not invalid_merchant_ids
        and not duplicate_transaction_ids
        and not geo_anomaly_errors
        and not high_value_errors
    )

    if passed:
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")


if __name__ == "__main__":
    main()