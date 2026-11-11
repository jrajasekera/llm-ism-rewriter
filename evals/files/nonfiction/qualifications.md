Here's the thing: the scheduler selects the shortest queue. The cache refreshes only if the client asks. The two nodes commit simultaneously.

The retry limit applies to each job separately. An operator can inspect a failed job before resubmitting it.
