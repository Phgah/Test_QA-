import requests
import psycopg2
import pytest
import uuid

# Environment configuration
API_URL = "https://api.test-env.com/v1/settlements"
DB_CONFIG = {
    "dbname": "rewards_db",
    "user": "qa_user",
    "password": "qa_password",
    "host": "localhost",
    "port": "5432"
}

@pytest.fixture
def db_cursor():
    """Fixture to automatically open and close the Database connection."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    yield cur
    cur.close()
    conn.close()

def test_tc06_idempotent_retry_prevents_double_payout(db_cursor):
    """
    Test Case 06: Verify the system does not reward twice 
    when the client retries the same request.
    """
    # 1. Setup Test Data
    test_user_id = "USER_AUTO_01"
    test_task_id = f"TASK_{uuid.uuid4()}"
    payload = {
        "user_id": test_user_id,
        "task_id": test_task_id
    }

    # 2. Action 1: Send the initial request (Happy Path)
    response_1 = requests.post(API_URL, json=payload)
    assert response_1.status_code in [200, 201], "The first API call must succeed"

    # 3. Action 2: Simulate client timeout and automatically retry the exact same request
    response_2 = requests.post(API_URL, json=payload)
    
    # Expectation: API must recognize the duplicate (Return HTTP 409 Conflict or 200 Idempotent)
    assert response_2.status_code in [409, 200], "The system failed to handle the idempotent request"
    if response_2.status_code == 200:
        assert response_2.json().get("already_settled") is True

    # 4. Database Assertions: Verify at the data layer
    
    # A. Verify Payouts Table (Exactly 1 record, exactly 10 credits)
    db_cursor.execute("SELECT COUNT(*), SUM(amount) FROM payouts WHERE task_id = %s;", (test_task_id,))
    payout_count, total_amount = db_cursor.fetchone()
    
    assert payout_count == 1, f"ERROR: Found {payout_count} payout records for the same task_id!"
    assert total_amount == 10, f"ERROR: User was credited {total_amount} credits instead of 10!"

    # B. Verify Outbox Table (1 notification event must be created)
    db_cursor.execute("SELECT status FROM outbox_events WHERE aggregate_id = %s;", (test_task_id,))
    outbox_record = db_cursor.fetchone()
    
    assert outbox_record is not None, "ERROR: Event not found in the outbox table!"
    assert outbox_record[0] in ['PENDING', 'PROCESSED'], "Invalid outbox status!"
