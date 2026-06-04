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
