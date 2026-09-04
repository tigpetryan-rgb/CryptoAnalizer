# CryptoAnalizer

CI/test layer for the FUTURES_INTELLIGENCE multi-chat futures analysis protocol.

## Source-of-truth boundary

- Google Drive remains the authoritative operational state and queue.
- This repository stores versioned protocol rules, synthetic fixtures, and regression tests only.
- CI must never mutate live trades, Drive workflow state, or dispatch helpers.

## Initial automated checks

- canonical 5-chat role/capability mapping
- H04 mutual exclusion: W07 and W08 may never execute in one invocation
- helper capability isolation
- stale revision rejection
- duplicate assignment rejection
- receipt capability consistency

Run locally:

```bash
python -m unittest discover -s tests -v
```
