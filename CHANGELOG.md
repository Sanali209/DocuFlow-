# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with FastAPI backend and Svelte 5 frontend.
- `build_dist.py` for automated one-folder deployment.
- `GncParser` module for parsing Rexroth/Hans Laser 801 files.
- `SyncService` for watching `Z:` drive directories (Mihtav/Sidra).
- Documentation (README, CONTRIBUTING, ARCHITECTURE, DEPLOYMENT).

### Changed
- Refactored frontend to use generic styles.
- Updated database schema to support Order/Task hierarchy.
