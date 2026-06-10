# Plan - Maintenance Doctor And Alerting

## Tasks
- [x] Confirm `.github/workflows/doctor.yml` exists.
- [x] Confirm local non-network doctor runs without mutating corpus data.
- [x] Review Dependabot configuration and security workflows.
- [x] Use GitHub Actions default notifications initially.
- [ ] Confirm notification delivery or operator routine from future live failure
  evidence.

## Current blocker

- Live repository secrets and variables exist.
- Continuing evidence should be recorded through future weekly doctor runs.
- Webhook or issue creation remains deferred until a live failure pattern
  justifies more alerting machinery.
