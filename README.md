# NZ Student Opportunity OS

An automated opportunity discovery, validation, lifecycle management, ranking, and monitoring system designed for computer science students in Auckland, New Zealand.

NZ Student Opportunity OS uses OpenClaw to discover opportunities, validates and filters the results, maintains a production opportunity dataset, removes expired entries, ranks current opportunities, and exposes system health through a local web dashboard.

![NZ Student Opportunity OS Dashboard](docs/dashboard.png)

## Overview

Finding internships, student programmes, workshops, hackathons, networking events, and research opportunities often requires manually checking many different websites.

NZ Student Opportunity OS turns that process into a repeatable automated pipeline.

The system can:

- discover new opportunities through OpenClaw
- clean and normalize AI-generated results
- validate opportunity quality
- reject generic search and listing pages
- remove tracking parameters
- detect duplicate source URLs
- detect exact and near-duplicate opportunities
- separate approved and review-required results
- classify opportunities by lifecycle
- archive expired opportunities
- maintain an active production batch
- rank opportunities using multiple suitability factors
- generate JSON, CSV, and Markdown outputs
- preserve historical snapshots between runs
- roll back production data after automation failures
- monitor automation health
- display current system status through a local dashboard

## Current Status

The project currently operates as a recurring local automation system and includes:

- automated weekly opportunity discovery
- validation and duplicate detection
- lifecycle management
- production rollback protection
- automated health monitoring
- regression testing
- release privacy checks
- local dashboard observability

The current automated test suite contains **38 passing tests**.

## Architecture

```text
OpenClaw
   |
   v
Raw Opportunity Output
   |
   v
Cleaning / Normalization
   |
   v
Validation
   |
   +----> Rejected
   |
   +----> Needs Review
   |
   v
Approved Opportunities
   |
   v
Production Batch
   |
   v
Lifecycle Classification
   |
   +----> Expired / Archive
   |
   +----> Uncertain / Review
   |
   v
Active Opportunities
   |
   v
Ranking + Export
   |
   +----> JSON
   +----> CSV
   +----> Markdown
   |
   v
Dashboard + Health Monitoring
```

## Opportunity Scoring

Each opportunity can be scored across five dimensions:

| Dimension | Maximum Score |
| --- | ---: |
| Relevance | 5 |
| Beginner Fit | 5 |
| Career Value | 5 |
| Practicality | 5 |
| University Fit | 5 |
| **Total** | **25** |

The ranking layer sorts opportunities by total score so that higher-value opportunities appear first.

## Validation

The validation layer checks for issues such as:

- generic search or listing pages
- tracking parameters
- duplicate source URLs
- exact duplicate titles
- near-duplicate titles
- suspicious or uncertain wording
- malformed opportunity records
- direct opportunity pages versus generic search pages

Entries are classified into three groups:

```text
Approved
Needs Review
Rejected
```

Only approved entries are automatically eligible for production publishing.

Entries that require human judgement remain available for review instead of being silently discarded.

## Lifecycle Management

Production opportunities are classified into:

```text
Active
Uncertain
Expired
```

### Active

Opportunities with valid future dates, ongoing applications, or other indicators that they are still usable.

### Uncertain

Opportunities whose lifecycle cannot be determined confidently.

These entries are kept for manual review.

### Expired

Opportunities whose relevant dates have already passed.

Expired opportunities are removed from the active production dataset and can be archived for historical reference.

## Ranking

After validation and lifecycle processing, active opportunities are ranked according to their total score.

The ranking system also includes duplicate handling so that stronger versions of the same opportunity can be retained.

Core ranking functionality is implemented in:

```text
src/ranking.py
```

## Automation Safety

The weekly automation uses transaction-style protection for production data.

Before production data is modified, the system creates a backup.

If a later stage fails, the automation can restore:

```text
Production Batch
Live Opportunity Data
Batch Status
```

The automation status records:

- whether the run succeeded
- the stage where a failure occurred
- whether production data had already been modified
- whether rollback was performed
- the transaction backup location
- validation counts
- lifecycle counts
- total execution time

This allows failures to be visible without leaving the production dataset in a partially updated state.

## System Health

The dashboard monitors the health of major components:

```text
Weekly Automation
Validation
Lifecycle
Refresh
Production Batch
```

The dashboard also displays:

- latest weekly run
- latest successful run
- run duration
- production entry count
- validation counts
- lifecycle counts
- rollback status
- current automation stage
- component health
- current health issues

A healthy run can be displayed as:

```text
System Health: HEALTHY
Run Stage: completed
Rollback Performed: No
```

## Dashboard

The local web dashboard provides a simple monitoring interface for the system.

It includes:

- live backend data status
- system health
- validation statistics
- lifecycle statistics
- component health
- refresh status
- production batch status
- ranked opportunity cards
- filtering
- searching
- score filtering
- local favorites

The dashboard is implemented with:

```text
HTML
CSS
JavaScript
```

No front-end framework is required.

## Project Structure

```text
nz-opportunity-os/
│
├── automation/
│   ├── run_weekly_automation.ps1
│   └── weekly_prompt.txt
│
├── src/
│   ├── parser.py
│   ├── ranking.py
│   ├── exporter.py
│   ├── cli.py
│   ├── validate_opportunities.py
│   ├── archive_expired_opportunities.py
│   ├── migrate_legacy_batch.py
│   ├── refresh_from_openclaw.py
│   ├── refresh_from_batch.py
│   ├── append_openclaw_batch.py
│   ├── remove_from_batch.py
│   ├── prune_published_batch.py
│   ├── write_batch_status.py
│   ├── write_automation_health.py
│   ├── release_preflight.py
│   └── ...
│
├── tests/
│   ├── test_cli.py
│   ├── test_exporter.py
│   ├── test_health.py
│   ├── test_lifecycle.py
│   ├── test_migration.py
│   ├── test_parser.py
│   ├── test_ranking.py
│   └── test_validator.py
│
├── web/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── sample_data/
│   └── sample_opportunities.txt
│
├── docs/
│   └── dashboard.png
│
├── .gitignore
├── README.md
├── requirements.txt
├── run_weekly_automation.bat
└── start_local_server.bat
```

Runtime logs, production opportunity data, backups, generated history files, and machine-specific files are excluded from the public repository.

## Requirements

### Python

Python 3.11 or newer is recommended.

Install the development dependencies with:

```bash
python -m pip install -r requirements.txt
```

Current Python development dependency:

```text
pytest
```

### OpenClaw

OpenClaw is required for automated opportunity discovery.

The rest of the Python pipeline can still be developed and tested independently using sample or manually supplied opportunity data.

## Running the Tests

From the project root:

```bash
python -m pytest -v
```

The current test suite covers areas including:

- parsing
- exporting
- ranking
- duplicate handling
- validation
- direct opportunity page detection
- generic search page rejection
- lifecycle classification
- date handling
- migration behaviour
- automation health

A successful run currently reports:

```text
38 passed
```

## Running the Dashboard

From the project root:

```bash
python -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/web/index.html
```

On Windows, you can also run:

```text
start_local_server.bat
```

## Running the Weekly Automation

On Windows:

```text
run_weekly_automation.bat
```

Or run the PowerShell automation directly:

```powershell
powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File ".\automation\run_weekly_automation.ps1"
```

The weekly pipeline performs:

```text
OpenClaw Discovery
        ↓
Output Normalization
        ↓
Cleaning
        ↓
Validation
        ↓
Approved-Only Publishing
        ↓
Lifecycle Classification
        ↓
Production Batch Update
        ↓
Live Data Refresh
        ↓
Batch Status Generation
        ↓
Automation Health Check
```

## Failure Testing

The automation supports controlled failure injection for testing rollback behaviour.

Supported failure stages include:

```text
openclaw_search
clean
validation
append
lifecycle
refresh
batch_status
health
```

This makes it possible to verify that production rollback works correctly when a pipeline stage fails.

## Sample Data

Safe demonstration data is available at:

```text
sample_data/sample_opportunities.txt
```

The sample file can be used for development and demonstrations without exposing production opportunity data.

Production runtime data is intentionally excluded from the public repository.

## Generated Outputs

During normal local operation, the system can generate outputs such as:

```text
JSON
CSV
Markdown summaries
Historical snapshots
Batch status files
Automation status files
Health reports
Lifecycle archives
```

Most generated runtime files are intentionally excluded through `.gitignore`.

## Release Safety

Before publishing changes, run:

```bash
python src/release_preflight.py
```

The release preflight checks public project files for common release risks such as:

- local Windows user paths
- possible API keys
- possible tokens
- secret files
- machine-specific information

A clean release should report:

```text
Potential content issues: 0
Sensitive files found: 0

Release preflight PASSED.
```

## Privacy and Runtime Data

The public repository excludes runtime files including:

```text
logs/
production batch data
raw OpenClaw responses
cleaned production data
transaction backups
lifecycle backups
migration backups
historical runtime snapshots
```

This keeps local operating data separate from the public source code.

## Engineering Goals

The project focuses on four engineering goals:

1. **Automation reliability**
2. **Data quality**
3. **Safe production updates**
4. **Operational observability**

The project started as a simple student opportunity ranking tool and evolved into a small production-style data pipeline with:

- modular Python components
- automated testing
- AI-assisted discovery
- validation gates
- lifecycle management
- historical snapshots
- rollback protection
- system health monitoring
- release safety checks
- a local operational dashboard

## Key Engineering Concepts Demonstrated

This project demonstrates practical experience with:

- Python application structure
- parsing and normalization
- data validation
- ranking algorithms
- duplicate detection
- file-based persistence
- defensive programming
- regression testing
- automation scripting
- PowerShell orchestration
- transaction-style rollback
- lifecycle management
- observability
- front-end dashboard development
- Git release hygiene
- privacy-aware repository publishing

## Future Work

Potential future improvements include:

- configurable student profiles
- support for multiple New Zealand cities
- richer source verification
- application tracking
- email or messaging notifications
- historical opportunity analytics
- cloud deployment
- scheduled remote execution
- recommendation models
- personalized ranking weights
- richer source credibility scoring
- automated review workflows

## Disclaimer

Opportunity information can change after discovery.

Always verify:

- dates
- deadlines
- eligibility requirements
- application status
- event details
- programme requirements

using the original source before applying or attending.

## Project Purpose

NZ Student Opportunity OS is a personal software engineering project built to explore how automation, validation, lifecycle management, testing, and monitoring can be combined into a practical student-focused workflow.

It is intended as both a useful local tool and a software engineering portfolio project.