# Incident 2026-10-04: checkout latency

On 4 October, p99 latency on the checkout service rose from 300 ms to 2.1 s for 47 minutes. The first report, filed during the incident, attributed the rise to a traffic spike from the partner promotion.

The second review found the cause was not the traffic spike but a cache misconfiguration: the deploy at 14:02 set the session cache TTL to zero, so every request went to the database. Traffic during the window was within the normal weekly range.

To prevent a repeat, there are three steps. First, add a lower bound for the TTL to the config schema. Second, alert when the cache hit rate stays below 80 percent for five minutes. Third, add the cache settings to the deploy checklist.

The owners for each step are listed in the tracker.
