# qdiff

`qdiff` compares two SQL query plans and prints the differences that change cost.

## Install

```bash
pip install qdiff
```

## Usage

```bash
qdiff plan-a.json plan-b.json --threshold 0.05
```

`--threshold` is the fraction of total cost a node must move before it is
reported. The default is 0.05. Passing `--all` reports every node.

Plans must come from `EXPLAIN (FORMAT JSON)` on PostgreSQL 13 or later. Plans
from other engines are rejected with exit code 2.

## Known limits

Parallel workers are counted once, not per worker, so a plan that changes its
worker count will under-report. There is no fix planned for 1.x.
