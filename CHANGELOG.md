# Changelog

All notable changes to `mcp-server-doctor` will be documented in this file.

The format is based on Keep a Changelog, and this project uses semantic versioning.

## [Unreleased]

- Added a 10 MiB default input limit for file and stdin reports, with the configurable `--max-input-bytes` option.
- Oversized input is rejected before JSON parsing, using bounded reads for both files and stdin.
- Documented and tested duplicate tool, resource, and prompt identifiers as blocking integrity errors.
- Added a null-capabilities edge-case guard and the July 2026 security review.

## [0.1.2] - 2026-07-06

- Updated GitHub Actions workflow dependencies to current major versions.
- Modernized package license metadata to avoid current Setuptools deprecation warnings.
- Added `--strict` mode to treat warnings as validation failures.
- Included strict-mode state in rendered JSON summaries.

## [0.1.1] - 2026-06-17

- Added `resourceTemplates` validation and capability presence checks.
- Detected missing and duplicate `uriTemplate` values.
- Fixed GitHub Actions workflow pins to supported action versions.

## [0.1.0] - 2026-06-03

- Initial open-source release with CLI, examples, tests, GitHub workflows, security policy, and contributor docs.
