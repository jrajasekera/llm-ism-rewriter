---
title: Deploy runbook
owner: platform
---

# Deploy runbook

In today's fast-paced world, deploys have become increasingly important.

## Steps

1. Drain the node with `kubectl drain --ignore-daemonsets`.
2. Wait for the pod count to reach 0.
3. Apply the manifest: `kubectl apply -f deploy.yaml`.

The rollout takes about 4 minutes and may fail if the image pull exceeds 90 s.

| Flag | Effect |
|------|--------|
| `--force` | Skips the drain |

## Rollback

Run `kubectl rollout undo deployment/api`. Hope this helps!
