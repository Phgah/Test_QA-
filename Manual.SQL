SELECT task_id, COUNT(*) as payout_count, SUM(amount) as total_awarded
FROM payouts
WHERE task_id = 'T-DUP-123' 
GROUP BY task_id;
-- Expectation :
-- payout_count = 1
-- total_awarded = 10

SELECT user_id, SUM(amount) AS total_wallet_balance
FROM payouts
WHERE user_id = 'USER_001'
GROUP BY user_id;
-- Expectation: total_wallet_balance = 30 

SELECT event_id, aggregate_type, aggregate_id, status, created_at
FROM outbox_events
WHERE aggregate_id = 'T-DUP-123';
-- Expectation: 
-- status = 'PENDING' (if worker not run or API notification return with 500)
-- status = 'PROCESSED' (if notification success)

SELECT task_id, completed_at_utc, status
FROM tasks
WHERE completed_at_utc >= '2026-10-26 00:00:00' 
  AND settlement_cycle_id = 'CURRENT_WEEK_ID';
-- Expectation: Return 0 (0 rows). If any data return as result that being Cut-off Boundary (Bug).
