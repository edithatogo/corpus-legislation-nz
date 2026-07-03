# NZLII Gazette Redundancy Archive

Date: 2026-07-03.

Track 45 treats NZLII as a secondary Gazette source. The archive path is
intentionally separate from the official, DigitalNZ, and Victoria/LexisNexis
layers.

## Current Access State

Live probes of the historical Gazette entry points currently return a managed
content challenge for automated clients. The repository records this as a
blocked source-state archive instead of attempting to bypass access controls.

Relevant evidence sources:

- `https://www.nzlii.org/robots.txt`
- `https://www.nzlii.org/nz/legis/hist_act/`
- `https://www.nzlii.org/nz/legis/num_reg/`

## Commands

Probe and record the source state:

```powershell
uv run nzlc nzlii-gazette-probe `
  --output-dir data/nzlii-gazette
```

Bundle the recorded source-state tree into an archive:

```powershell
uv run nzlc nzlii-gazette-archive `
  --source-dir data/nzlii-gazette `
  --output-dir dist/nzlii-gazette `
  --year 2026
```

## Outputs

The probe writes:

- `data/nzlii-gazette/records.jsonl`
- `data/nzlii-gazette/source_records.jsonl`
- `data/nzlii-gazette/raw/probe/source_state.json`
- `data/nzlii-gazette/manifests/latest_manifest.json`
- `data/nzlii-gazette/manifests/validation_report.json`
- `data/nzlii-gazette/manifests/coverage_report.json`
- `data/nzlii-gazette/_state/source_state.json`

The archive bundle writes:

- `dist/nzlii-gazette/corpus-legislation-nz-gazette-nzlii-2026.tar.*`
- `dist/nzlii-gazette/corpus-legislation-nz-gazette-nzlii-2026.manifest.json`
- `dist/nzlii-gazette/corpus-legislation-nz-gazette-nzlii-2026.release-evidence.json`
- `dist/nzlii-gazette/corpus-legislation-nz-gazette-nzlii-2026.SHA256SUMS.txt`

## Canonical Policy

NZLII remains a redundancy source only. It does not replace the official
Gazette, DigitalNZ, or Victoria/LexisNexis archives. Any future usability
change should be rerun through Track 45 and, if access becomes valid, through
Track 46 canonical comparison.
