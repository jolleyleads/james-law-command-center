# James Law Mobile Command Center

This is a DOE-based command center for James Law outreach.

DOE = Directive → Orchestrate → Execute

## What it does

- Phone-accessible dashboard
- Contact manager
- Draft-only outreach generation
- Media / legislator / attorney / prosecutor / detective workflows
- Timeline notes
- Follow-up tasks
- Error logging
- Make.com webhook support
- OpenAI personalization placeholder
- Twilio / Hunter / Apify placeholders

## Safety

This system does not automatically send emails or SMS.
It creates drafts and logs only.

## Local run

`powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload
`

Then open:

`	ext
http://127.0.0.1:8000
`

## Render

Push to GitHub, connect repo to Render, then deploy.

## James Jolley Case Files Wrapper

This repo now includes a DOE case-file wrapper layer.

Core command:

`Add this to James Jolley Case Files.`

That command routes work through:

- `directives/case_workspace_wrapper.md`
- `orchestration/orchestrator.md`
- `execution/add_case_update.py`

The wrapper is designed to categorize new case information, update timeline records, log evidence, identify contradictions, create follow-up actions, and prepare attorney, prosecutor, media, or legislative packets.

Safety rule: this system creates drafts and structured records only. It does not automatically send emails or SMS.

## MCP Case Files Strategy

This repo now includes an MCP-style strategy directive for James Jolley Case Files.

MCP is treated as the USB-C adapter layer for AI tools and data sources.
DOE remains the discipline layer.

Core rule:

Load the smallest useful tool set for the case task.

Files:

- `directives/mcp_case_files_strategy.md`
- `directives/case_workspace_wrapper.md`
- `orchestration/orchestrator.md`
- `execution/add_case_update.py`
- `data/case_updates.json`

The dashboard supports:

- paste a case update
- save structured case update records
- show recent case updates
- add timeline entries
- add follow-up tasks
