# Incident 2291: checkout latency

At 14:02 UTC on 3 June, p99 latency on the checkout API rose from 180 ms to 4 s. The on-call engineer rolled back release 412 at 14:19, and latency returned to baseline by 14:23.

Release 412 raised the connection pool ceiling. We saw the pool exhaust within ten minutes of the deploy, which points to a connection leak, but we have not identified the leaking code path.

The rollback restored service. We have not identified the cause of the connection leak. Release 412 stays blocked until we do.
