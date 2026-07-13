# Cleanup Report

## Status

This document is the canonical cleanup ledger. Phase 1 inspected 26,598 files (about 5.96 GB), identified 107 duplicate-hash groups, audited 130 Markdown files, statically mapped 904 code/config dependencies, and inspected all 22 slides and 110 embedded media items in the canonical presentation.

## Safety decisions

- Confirmed superseded versions and regenerable environment artifacts may be permanently deleted when a retained successor and deletion log exist.
- Stale or mixed outdated Markdown is permanently deleted only after valid information is consolidated and logged.
- Repository `.git` internals remain protected. Project `.venv` dependencies were removed after retaining requirements and reconstruction instructions.
- `compressed,dataless` files are explicitly flagged where hashing or validation is unavailable.

## Final counts and validation

Final moved, archived, quarantined, deleted, storage, and validation counts are appended after Phases 2-5. Detailed evidence remains in the numbered CSV and Markdown audit artifacts.
