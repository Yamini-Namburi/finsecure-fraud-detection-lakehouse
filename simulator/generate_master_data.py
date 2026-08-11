import csv
import random
from pathlib import Path

from faker import Faker


fake = Faker()

OUTPUT_DIR = Path(__file__).parent / "sample_data"


COUNTRIES = ["US", "GB", "CA"]

RISK_TIERS = [
    "LOW",
    "MEDIUM",
    "HIGH",
]

KYC_STATUSES = [
    "VERIFIED",
    "PENDING",
    "REVIEW",
]

MERCHANT_CATEGORIES = [
    "grocery",
    "electronics",
    "travel",
    "restaurant",
    "fuel",
    "fashion",
    "entertainment",
]


def generate_customers(count: int = 100):
    customers = []

    for customer_number in range(1, count + 1):
        customer_id = f"CUST-{customer_number:05d}"

        customer = {
            "customer_id": customer_id,
            "full_name": fake.name(),
            "email": fake.email(),
            "registered_country": random.choice(COUNTRIES),
            "risk_tier": random.choice(RISK_TIERS),
            "kyc_status": random.choice(KYC_STATUSES),
            "account_open_date": fake.date_between(
                start_date="-10y",
                end_date="today",
            ).isoformat(),
        }

        customers.append(customer)

    return customers


def generate_accounts(customers):
    accounts = []

    for customer in customers:
        account = {
            "account_id": f"ACC-{customer['customer_id'].split('-')[1]}",
            "customer_id": customer["customer_id"],
            "account_type": random.choice(
                [
                    "CURRENT",
                    "SAVINGS",
                    "CREDIT_CARD",
                ]
            ),
            "account_status": random.choice(
                [
                    "ACTIVE",
                    "ACTIVE",
                    "ACTIVE",
                    "SUSPENDED",
                ]
            ),
            "balance": round(
                random.uniform(500, 50000),
                2,
            ),
            "currency": {
                "US": "USD",
                "GB": "GBP",
                "CA": "CAD",
            }[customer["registered_country"]],
        }

        accounts.append(account)

    return accounts


def generate_merchants(count: int = 50):
    merchants = []

    for merchant_number in range(1, count + 1):
        merchant = {
            "merchant_id": f"MERCH-{merchant_number:04d}",
            "merchant_name": fake.company(),
            "merchant_category": random.choice(
                MERCHANT_CATEGORIES
            ),
            "country_code": random.choice(COUNTRIES),
        }

        merchants.append(merchant)

    return merchants


def write_csv(filename, rows):
    if not rows:
        return

    output_file = OUTPUT_DIR / filename

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys(),
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {output_file}")


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    customers = generate_customers(100)

    accounts = generate_accounts(
        customers
    )

    merchants = generate_merchants(50)

    write_csv(
        "customers.csv",
        customers,
    )

    write_csv(
        "accounts.csv",
        accounts,
    )

    write_csv(
        "merchants.csv",
        merchants,
    )

    print()
    print(
        f"Customers generated: {len(customers)}"
    )

    print(
        f"Accounts generated: {len(accounts)}"
    )

    print(
        f"Merchants generated: {len(merchants)}"
    )


if __name__ == "__main__":
    main()