# Latest-Only Cleanup Report

## Result

- Permanently deleted superseded files: 316
- Deleted bytes recorded in the file-level log: 126,874,413
- Deletion failures: 0
- Archived PowerPoint files removed: 9
- Current PowerPoint retained: `07_presentations/current/701_20260712_v02_mdr2_presentation.pptx`
- `90_archive/` and `99_quarantine/` were cleared and removed.

## Retention logic

Files were deleted when they were stored as archived, backup, deprecated, quarantined generated output, or when an explicit later version existed. Unique active raw data, processed data, synthetic data, notebooks, literature records, references, and generation sources were retained.

The following same-topic variants were treated as distinct current deliverables rather than old versions:

- `reported_circuit_width_by_instance_full_revised.*`
- `reported_circuit_width_by_instance_slide_revised.*`

Their unrevised predecessors were deleted. The SRL/QRL evidence-network v1 script was deleted after its remaining command reference was updated to the retained v2 script.

## Validation

- The current PowerPoint passes ZIP integrity validation and retains 22 slides.
- All 35 retained Python sources parse without syntax errors.
- Both retained notebooks parse as valid notebook JSON.
- No archived presentation remains.
- No file-level deletion failed.
- References from the exploratory notebook to the deleted archive script were updated to the active visualization script.

## Audit files

- `latest_only_cleanup_plan.md`
- `latest_only_deletion_log.csv`

The deletion log records every deleted path, SHA-256 where readable, size, modified date, Git status, retained successor, reason, timestamp, and result.
