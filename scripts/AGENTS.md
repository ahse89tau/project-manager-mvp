# Scripts Agent Instructions

This folder contains project start/stop scripts for local development.

## Required Script Names

- `start_mac.sh`
- `stop_mac.sh`
- `start_linux.sh`
- `stop_linux.sh`
- `start_windows.bat`
- `stop_windows.bat`

## Scope and Behavior

- Scripts are run from project root.
- Scripts should focus on container lifecycle for the MVP app.
- Output should be short, readable, and explicit about success/failure.
- Stop scripts should only stop services created by this project.

## Safety Rules

- Do not use destructive cleanup outside project context.
- Avoid assumptions about global tooling beyond required project dependencies.
- Keep scripts idempotent where practical (safe to rerun).

## Validation Expectations

- Validate scripts directly on the current platform.
- For non-current platforms, ensure command correctness via static review in PR/change review.
