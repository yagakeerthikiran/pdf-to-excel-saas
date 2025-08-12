# Monitoring

This directory contains scripts and configurations related to monitoring, alerting, and the automated issue-resolution workflow.

## Key Technologies
- Sentry (Error Tracking)
- PostHog (Product Analytics)
- AWS CloudWatch (Logging & Alarms)

## Purpose
The components in this directory are responsible for:
- Aggregating logs and errors from the frontend and backend.
- Providing insights into user behavior via session replays and analytics.
- Triggering alerts based on predefined conditions (e.g., error spikes, performance degradation).
- Powering the "auto-fix" workflow, which programmatically responds to alerts to enable rapid bug fixes.

Refer to `docs/auto-fix-workflow.md` (to be created) for a detailed explanation of this process.
