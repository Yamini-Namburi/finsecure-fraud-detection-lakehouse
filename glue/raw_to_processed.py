import sys

from awsglue.transforms import *
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

sc = SparkContext()

glueContext = GlueContext(sc)

spark = glueContext.spark_session


# =========================================================
# 3. INITIALIZE GLUE JOB
# =========================================================

job = Job(glueContext)

job.init(args["JOB_NAME"], args)


# =========================================================
# 4. READ DATA FROM GLUE DATA CATALOG
# =========================================================

source_dynamic_frame = glueContext.create_dynamic_frame.from_catalog(
    database=args["SOURCE_DATABASE"],
    table_name=args["SOURCE_TABLE"],
)

df = source_dynamic_frame.toDF()

print("Source schema:")
df.printSchema()

print(f"Source record count: {df.count()}")


# =========================================================
# 5. CLEAN / TRANSFORM DATA
# =========================================================

# Convert transaction timestamp from string to timestamp
df = df.withColumn(
    "transaction_ts",
    F.to_timestamp(F.col("transaction_ts")),
)


# Remove duplicate transactions
df = df.dropDuplicates(["transaction_id"])


# Remove invalid transactions
df = df.filter(
    F.col("transaction_id").isNotNull()
    & F.col("customer_id").isNotNull()
    & F.col("amount").isNotNull()
)


print("Processed schema:")
df.printSchema()

print(f"Processed record count: {df.count()}")


# =========================================================
# 6. WRITE PROCESSED DATA TO S3 AS PARQUET
# =========================================================

(
    df.write
    .mode("overwrite")
    .partitionBy("year", "month", "day")
    .parquet(args["TARGET_S3_PATH"])
)


# =========================================================
# 7. COMMIT GLUE JOB
# =========================================================

job.commit()

print("Glue ETL job completed successfully.")