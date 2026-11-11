# Worker settings

## Retry count

The retry count limits the number of attempts for a failed job. The default is five attempts.

## Queue order

The worker processes jobs in arrival order. Jobs with the same timestamp keep their insertion order.

## Log directory

The worker writes one log file for each run. The operator selects the directory before starting the worker.
