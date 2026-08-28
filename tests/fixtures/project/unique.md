# Postmortem

The consumer stalled for forty minutes on 3 March because the partition lease
expired while the pod was being evicted from a node under disk pressure.
