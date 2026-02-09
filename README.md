# E-commerce ETL
This project gets information from a SQS queue from AWS, this information is about e-commerce products.
The aim of this project is to create an ETL pipeline to be able to connect with the SQS service, process the date and
save it into a sql table, this is in order to check metrics and help data analyst to get useful information from this data.

## Project Structure
+ Nelo
  + aws
    + config.py
  + db
    + database.py
    + queries.sql
  + models
    + fact_events.py
  + config.py
  + utils.py
  + .env
  + requirements.txt
  + main.py
    
### aws/config.py
Here you will find the aws configuration, this creates an sqs client by using a boto3 instance

### db/database.py
Here it's the database connection, for this project we decided to use a singleton design patter for database connection
and a factory method to create a db session, this is in order to be able to establish a stable connection with the 
database and a scalable project. For this project, the database is postgreSQL.

### db/queries.sql
This file has all the sql queries used to create tables, it contains fact table and object tables definitions, also
contains a couple of EDA queries, to get information such as:
  - Top lists by engagement rate
  - Best performing products by view-to-purchase rate

### models/fact_events.py
Here is the table definition for the table in which the data from the SQS service will be stored,
for this we are using sqlalchemy to create an engine and be able to interact with the database.


### config.py
This file stores the url connection with the database, here we can also save the aws connection information, but for 
scalability purposes we decided to have its own config file.

### utils.py
This file contains all the functions used to process the data, due that the project is small, we decided to just create
the functions and export them to be used in the main file, but if the project starts to grow, the best approach is to 
have a class dedicated to data processing.

### main.py
This file is the principal one that calls the method called: process_batch that interacts with the SQS service in order
to get messages information. BY using a while loop, we are calling the etl pipeline to be able to get the information, 
process the data and save it into the db table.

For database design, we decided to have a star database design, having one fact table and two object tables:
![databse design](assets/db_design.peg)

# Nelo Analytics Data Pipeline – Design Overview

## 1. End-to-End Data Flow

1. **Event Generation**
   - User interactions in the mobile app (iOS / Android) generate e-commerce events such as:
     - `view_item_list`
     - `view_item`
     - `begin_checkout`
     - `purchase`
   - Events are emitted asynchronously and published to an **AWS SQS queue** (`data-engineering-case-analytics-queue`).

2. **Message Ingestion**
   - A Python-based consumer continuously polls the SQS queue using the AWS SDK (`boto3`).
   - Messages are retrieved in small batches to balance throughput and reliability.

3. **Message Normalization**
   - Each message body is decoded from JSON.
   - Some payloads contain nested or string-serialized structures.
   - A normalization layer ensures:
     - The payload is a valid dictionary
     - The `items` field is parsed into structured records

4. **Transformation**
   - Events are transformed into a **fact table format**.
   - Each product interaction is stored as a single row in `fact_events`.
   - Event timestamps are normalized to UTC.

5. **Storage**
   - Transformed rows are written to **PostgreSQL** using SQLAlchemy.
   - A singleton database connection pattern ensures efficient reuse of connections.
   - Messages are deleted from SQS only after successful database commit.

6. **Analytics Consumption**
   - The `fact_events` table can be queried directly by analysts or connected to BI tools.
   - Metrics such as CTR, conversion rate, impressions, and engagement can be computed efficiently.

---

## 2. Data Consistency and Latency Considerations

### Consistency
- The pipeline follows **at-least-once delivery semantics**:
  - Messages are deleted from SQS only after successful persistence.
  - In case of consumer failure, messages may be reprocessed.
- Duplicate events can be handled downstream using:
  - Event IDs (if available)
  - Hash-based deduplication strategies

### Latency
- The system is designed for **near real-time ingestion**:
  - Polling intervals are short (seconds).
  - Typical end-to-end latency is under a few seconds.
- This is sufficient for Growth and product analytics dashboards, where sub-second latency is not critical.

---

## 3. Trade-offs and Design Decisions

### SQS vs Streaming Systems
- **Why SQS**:
  - Managed, reliable, and simple to operate
  - Built-in retry and visibility timeout mechanisms
- **Trade-off**:
  - No strict ordering guarantees
  - Lower throughput compared to Kafka or Kinesis

### Single Fact Table Design
- A denormalized `fact_events` table was chosen to:
  - Simplify analyst queries
  - Avoid complex joins
- Trade-off:
  - Slight data duplication
  - Higher storage usage (acceptable for analytics workloads)

### PostgreSQL as Analytical Store
- Chosen for:
  - Familiarity and ease of local development
  - Strong SQL support
- Trade-off:
  - Not optimal for very high event volumes
  - Would require partitioning or migration for large-scale analytics

### Parsing Non-Standard Payloads
- The `items` field was received in a GA-style serialized format.
- A custom parser was implemented to ensure data usability.
- This improves robustness at the cost of additional transformation logic.

---

## 4. Scalability Considerations

As data volume grows, the design can evolve incrementally:

### Ingestion Scaling
- Run multiple consumer instances in parallel:
  - SQS naturally distributes messages across consumers
- Increase batch size and polling concurrency

### Storage Scaling
- Partition PostgreSQL tables by date
- Add indexes on commonly queried columns (event_time, product_id, list_name)
- Migrate to columnar storage (e.g., Parquet on S3 + Athena) for large-scale analytics

### Processing Scaling
- Move from single-node Python processing to:
  - Spark Structured Streaming
  - AWS Glue or EMR
- Apply schema validation and enrichment at scale

### Architecture Evolution
- Introduce a data lake (raw → processed → analytics layers)
- Add orchestration with Airflow or Step Functions
- Implement monitoring and dead-letter queues (DLQs)

---
