import json
import os
import re
from datetime import datetime, timezone
from models.fact_events import FactEvent, Base
from aws.config import sqs
from db.database import Database
from dotenv import load_dotenv

load_dotenv()
queue_url = os.getenv('aws_queue_url')

engine = Database.get_engine()
Base.metadata.create_all(bind=engine)
SessionLocal = Database.get_session_factory()


def poll_messages():
    """Poll SQS for messages"""
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=5
    )
    return response.get("Messages", [])


def parse_ga_items(items_str: str):
    """
    Returns list of dicts with item_id, item_name, price, item_list_name.
    """
    items = []

    # Remove outer brackets
    items_str = items_str.strip().strip('[]')

    # Extract item blocks using brace counting
    item_blocks = []
    depth = 0
    start = -1

    for i, char in enumerate(items_str):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                item_blocks.append(items_str[start:i + 1])

    # Extract fields from each block
    for block in item_blocks:
        # Helper to extract field value
        def get_value(key):
            match = re.search(rf"{key}=([^,}}]+)", block)
            if match:
                val = match.group(1).strip()
                return None if val in ["(not set)", "null"] else val
            return None

        # Parse price
        price = None
        if price_str := get_value("price"):
            try:
                price = float(price_str)
            except ValueError:
                pass

        items.append({
            "item_id": get_value("item_id"),
            "item_name": get_value("item_name"),
            "price": price,
            "item_list_name": get_value("item_list_name"),
        })

    return items


def normalize_event(body):
    """
    ensures the event payload is a dict
    """
    parsed = body

    # Unwrap JSON strings
    for _ in range(5):
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except json.JSONDecodeError:
                return None
        else:
            break

    # Handle SNS wrapper
    if isinstance(parsed, dict) and "Message" in parsed:
        try:
            return json.loads(parsed["Message"])
        except json.JSONDecodeError:
            return None

    if not isinstance(parsed, dict):
        return None

    return parsed


def parse_event(event: dict):
    """Parse a single event into FactEvent rows"""
    rows = []

    ts = event.get("event_timestamp")
    if ts is None:
        return rows

    if ts > 1e14:
        event_time = datetime.fromtimestamp(ts / 1_000_000, tz=timezone.utc)
    elif ts > 1e11:
        event_time = datetime.fromtimestamp(ts / 1_000, tz=timezone.utc)
    else:
        event_time = datetime.fromtimestamp(ts, tz=timezone.utc)

    items = event.get("items")

    # Handle items as a string representation
    if isinstance(items, str):
        items = parse_ga_items(items)
    elif not isinstance(items, list):
        return rows

    for item in items:
        if not isinstance(item, dict):
            continue

        rows.append(
            FactEvent(
                event_time=event_time,
                user_id=event.get("user_id"),
                event_name=event.get("event_name"),
                platform=event.get("platform"),
                list_name=item.get("item_list_name"),
                product_id=item.get("item_id"),
                product_name=item.get("item_name"),
                price=item.get("price")
            )
        )

    return rows


def delete_message(receipt_handle):
    """Delete a message from SQS"""
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )


def process_batch():
    """
    Process one batch of messages.
    Returns the number of rows inserted.
    """
    messages = poll_messages()
    if not messages:
        return 0

    # Start db session
    session = SessionLocal()
    total_rows = 0
    receipts_to_delete = []

    try:
        for msg in messages:
            raw_body = msg["Body"]
            event = normalize_event(raw_body)

            if not event:
                continue

            rows = parse_event(event)

            if rows:
                session.add_all(rows)
                total_rows += len(rows)
                receipts_to_delete.append(msg["ReceiptHandle"])

        # Commit first
        if total_rows > 0:
            session.commit()

            # Only delete messages after successful commit
            for receipt in receipts_to_delete:
                delete_message(receipt)

            print(f"✓ Processed batch: {total_rows} rows from {len(messages)} messages")

        return total_rows

    except Exception as e:
        session.rollback()
        print(f"✗ ERROR in batch: {e}")
        import traceback
        traceback.print_exc()
        return 0

    finally:
        session.close()
