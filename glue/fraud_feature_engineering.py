import sys

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F


# =========================================================
# 1. READ GLUE JOB PARAMETERS
# =========================================================

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "SOURCE_DATABASE",
        "SOURCE_TABLE",
        "TARGET_S3_PATH",
    ],
)


# =========================================================
# 2. CREATE SPARK AND GLUE CONTEXT
# =========================================================

sc = SparkContext.getOrCreate()

glue_context = GlueContext(sc)

spark = glue_context.spark_session


# =========================================================
# 3. INITIALIZE GLUE JOB
# =========================================================

job = Job(glue_context)

job.init(
    args["JOB_NAME"],
    args,
)


# =========================================================
# 4. READ PROCESSED TRANSACTIONS FROM GLUE DATA CATALOG
# =========================================================

source_dynamic_frame = (
    glue_context.create_dynamic_frame.from_catalog(
        database=args["SOURCE_DATABASE"],
        table_name=args["SOURCE_TABLE"],
    )
)

df = source_dynamic_frame.toDF()


print("Source schema:")
df.printSchema()

print(
    f"Source record count: {df.count()}"
)


# =========================================================
# 5. BASIC DATA VALIDATION
# =========================================================

df = df.filter(
    F.col("transaction_id").isNotNull()
    & F.col("customer_id").isNotNull()
    & F.col("amount").isNotNull()
    & F.col("transaction_ts").isNotNull()
)


# =========================================================
# 6. FRAUD FEATURE ENGINEERING
# =========================================================


# ---------------------------------------------------------
# FEATURE 1: TRANSACTION HOUR
# ---------------------------------------------------------
#
# Extract the hour from the transaction timestamp.
#
# Example:
#
# 2026-08-14 02:30:00
#
# becomes:
#
# transaction_hour = 2
#

df = df.withColumn(
    "transaction_hour",
    F.hour(
        F.col("transaction_ts")
    ),
)


# ---------------------------------------------------------
# FEATURE 2: NIGHT TRANSACTION FLAG
# ---------------------------------------------------------
#
# Transactions occurring between
# 00:00 and 05:59 are flagged.
#
# 1 = night transaction
# 0 = normal daytime transaction
#

df = df.withColumn(
    "night_transaction_flag",
    F.when(
        F.col("transaction_hour")
        .between(0, 5),
        F.lit(1),
    ).otherwise(
        F.lit(0)
    ),
)


# ---------------------------------------------------------
# FEATURE 3: FOREIGN TRANSACTION FLAG
# ---------------------------------------------------------
#
# Compare:
#
# country_code
#
# against:
#
# registered_country
#
# Example:
#
# registered_country = IN
# country_code       = US
#
# foreign_transaction_flag = 1
#

df = df.withColumn(
    "foreign_transaction_flag",
    F.when(
        F.col("country_code")
        != F.col("registered_country"),
        F.lit(1),
    ).otherwise(
        F.lit(0)
    ),
)


# ---------------------------------------------------------
# FEATURE 4: HIGH AMOUNT FLAG
# ---------------------------------------------------------
#
# Initial project threshold:
#
# amount > 1000
#
# Later we can replace this static rule with
# customer-specific statistical thresholds.
#

df = df.withColumn(
    "high_amount_flag",
    F.when(
        F.col("amount") > 1000,
        F.lit(1),
    ).otherwise(
        F.lit(0)
    ),
)


# ---------------------------------------------------------
# FEATURE 5: HIGH RISK CUSTOMER FLAG
# ---------------------------------------------------------
#
# customer_risk_tier values might contain:
#
# LOW
# MEDIUM
# HIGH
#
# We create a numeric feature:
#
# HIGH -> 1
# everything else -> 0
#

df = df.withColumn(
    "high_risk_customer_flag",
    F.when(
        F.upper(
            F.col("customer_risk_tier")
        ) == "HIGH",
        F.lit(1),
    ).otherwise(
        F.lit(0)
    ),
)


# ---------------------------------------------------------
# FEATURE 6: ONLINE TRANSACTION FLAG
# ---------------------------------------------------------
#
# Convert the existing boolean field
# into a model-friendly integer.
#

df = df.withColumn(
    "online_transaction_flag",
    F.when(
        F.col("is_online") == True,
        F.lit(1),
    ).otherwise(
        F.lit(0)
    ),
)


# =========================================================
# 7. SIMPLE FRAUD RISK SCORE
# =========================================================
#
# This is NOT the ML model.
#
# It is only a simple engineered score that helps us
# validate whether the features are behaving correctly.
#
# Maximum current score = 5
#

df = df.withColumn(
    "fraud_risk_score",
    (
        F.col("night_transaction_flag")
        + F.col("foreign_transaction_flag")
        + F.col("high_amount_flag")
        + F.col("high_risk_customer_flag")
        + F.col("online_transaction_flag")
    ),
)


# =========================================================
# 8. CREATE HUMAN-READABLE RISK BAND
# =========================================================
#
# 0-1 -> LOW
# 2-3 -> MEDIUM
# 4-5 -> HIGH
#

df = df.withColumn(
    "fraud_risk_band",
    F.when(
        F.col("fraud_risk_score") >= 4,
        F.lit("HIGH"),
    )
    .when(
        F.col("fraud_risk_score") >= 2,
        F.lit("MEDIUM"),
    )
    .otherwise(
        F.lit("LOW")
    ),
)


# =========================================================
# 9. PRINT RESULT INFORMATION
# =========================================================

print(
    "Feature-engineered schema:"
)

df.printSchema()


print(
    f"Feature-engineered record count: "
    f"{df.count()}"
)


print(
    "Sample fraud features:"
)

df.select(
    "transaction_id",
    "customer_id",
    "amount",
    "transaction_hour",
    "night_transaction_flag",
    "foreign_transaction_flag",
    "high_amount_flag",
    "high_risk_customer_flag",
    "online_transaction_flag",
    "fraud_risk_score",
    "fraud_risk_band",
    "is_fraud",
).show(
    20,
    truncate=False,
)


# =========================================================
# 10. WRITE FEATURE DATASET TO S3
# =========================================================
#
# We deliberately use a DIFFERENT S3 location from the
# processed transaction dataset.
#
# Example:
#
# processed bucket/
#
# transactions/
#
# fraud_features/
#

(
    df.write
    .mode("overwrite")
    .partitionBy(
        "year",
        "month",
        "day",
    )
    .parquet(
        args["TARGET_S3_PATH"]
    )
)


# =========================================================
# 11. COMMIT GLUE JOB
# =========================================================

job.commit()


print(
    "Fraud feature engineering "
    "job completed successfully."
)