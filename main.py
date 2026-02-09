import os
import time
from dotenv import load_dotenv

from models.fact_events import Base
from db.database import Database
from utils import process_batch

# db setup
engine = Database.get_engine()
Base.metadata.create_all(bind=engine)
SessionLocal = Database.get_session_factory()

print("Database connected")
load_dotenv()
queue_url = os.getenv('aws_queue_url')


# Main loop
def main():
    print("Starting SQS consumer...")
    print(f"Queue: {queue_url}")
    print("=" * 60)

    while True:
        # Process all available messages in the queue
        batch_count = 0
        total_inserted = 0

        while True:
            rows_inserted = process_batch()

            if rows_inserted == 0:
                # No more messages in queue
                break

            batch_count += 1
            total_inserted += rows_inserted

        if total_inserted > 0:
            print(f"\n{'=' * 60}")
            print(f"COMPLETED: {total_inserted} total rows from {batch_count} batches")
            print(f"{'=' * 60}\n")

        # Wait before checking queue again
        time.sleep(5)


if __name__ == "__main__":
    main()
