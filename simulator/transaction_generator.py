import csv
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).parent
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

CUSTOMERS_FILE = SAMPLE_DATA_DIR / "customers.csv"
ACCOUNTS_FILE = SAMPLE_DATA_DIR / "accounts.csv"
MERCHANTS_FILE = SAMPLE_DATA_DIR / "merchants.csv"


FRAUD_TYPES = [
    "HIGH_VALUE",
    "GEO_ANOMALY",
    "VELOCITY",
]

FOREIGN_COUNTRIES = [
    "US",
    "GB",
    "CA",
    "DE",
    "FR",
    "SG",
    "AE",
]

DEVICE_TYPES = [
    "MOBILE",
    "WEB",
    "POS",
]

CURRENCY_BY_COUNTRY = {
    "US": "USD",
    "GB": "GBP",
    "CA": "CAD",
    "DE": "EUR",
    "FR": "EUR",
    "SG": "SGD",
    "AE": "AED",
}


def load_csv(file_path: Path) -> list[dict]:
    with open(
        file_path,
        mode="r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        return list(reader)


CUSTOMERS = load_csv(CUSTOMERS_FILE)
ACCOUNTS = load_csv(ACCOUNTS_FILE)
MERCHANTS = load_csv(MERCHANTS_FILE)


def find_customer_accounts(customer_id: str) -> list[dict]:
    return [
        account
        for account in ACCOUNTS
        if account["customer_id"] == customer_id
    ]


def get_random_customer() -> dict:
    return random.choice(CUSTOMERS)


def get_random_merchant() -> dict:
    return random.choice(MERCHANTS)


def create_base_transaction() -> dict:
    customer = get_random_customer()

    customer_accounts = find_customer_accounts(
        customer["customer_id"]
    )

    if not customer_accounts:
        raise ValueError(
            f"No account found for customer {customer['customer_id']}"
        )

    account = random.choice(customer_accounts)
    merchant = get_random_merchant()

    country = customer["registered_country"]

    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "customer_id": customer["customer_id"],
        "account_id": account["account_id"],
        "merchant_id": merchant["merchant_id"],
        "merchant_category": merchant["merchant_category"],
        "amount": round(random.uniform(5.0, 200.0), 2),
        "currency": CURRENCY_BY_COUNTRY.get(
            country,
            account["currency"],
        ),
        "transaction_ts": datetime.now(
            timezone.utc
        ).isoformat(),
        "country_code": country,
        "registered_country": customer["registered_country"],
        "is_online": random.choice([True, False]),
        "device_type": random.choice(DEVICE_TYPES),
        "device_fingerprint": str(uuid.uuid4()),
        "customer_risk_tier": customer["risk_tier"],
        "fraud_type": None,
        "is_fraud": False,
    }

    return transaction


def inject_high_value_fraud(
    transaction: dict,
) -> dict:
    transaction["amount"] = round(
        random.uniform(1000.0, 5000.0),
        2,
    )

    transaction["fraud_type"] = "HIGH_VALUE"
    transaction["is_fraud"] = True

    return transaction


def inject_geo_anomaly(
    transaction: dict,
) -> dict:
    registered_country = transaction["registered_country"]

    candidate_countries = [
        country
        for country in FOREIGN_COUNTRIES
        if country != registered_country
    ]

    foreign_country = random.choice(candidate_countries)

    transaction["country_code"] = foreign_country

    transaction["currency"] = CURRENCY_BY_COUNTRY.get(
        foreign_country,
        transaction["currency"],
    )

    transaction["fraud_type"] = "GEO_ANOMALY"
    transaction["is_fraud"] = True

    return transaction


def inject_velocity_fraud(
    transaction: dict,
) -> dict:
    transaction["amount"] = round(
        random.uniform(50.0, 500.0),
        2,
    )

    transaction["fraud_type"] = "VELOCITY"
    transaction["is_fraud"] = True

    return transaction


def generate_transaction(
    fraud_probability: float = 0.10,
) -> dict:
    transaction = create_base_transaction()

    should_inject_fraud = (
        random.random() < fraud_probability
    )

    if not should_inject_fraud:
        return transaction

    fraud_type = random.choice(FRAUD_TYPES)

    if fraud_type == "HIGH_VALUE":
        return inject_high_value_fraud(transaction)

    if fraud_type == "GEO_ANOMALY":
        return inject_geo_anomaly(transaction)

    if fraud_type == "VELOCITY":
        return inject_velocity_fraud(transaction)

    return transaction


def generate_velocity_transactions(
    count: int = 5,
) -> list[dict]:
    base_transaction = create_base_transaction()

    transactions = []

    for _ in range(count):
        transaction = base_transaction.copy()

        transaction["transaction_id"] = str(uuid.uuid4())

        transaction["transaction_ts"] = datetime.now(
            timezone.utc
        ).isoformat()

        transaction["device_fingerprint"] = str(uuid.uuid4())

        transaction = inject_velocity_fraud(transaction)

        transactions.append(transaction)

    return transactions