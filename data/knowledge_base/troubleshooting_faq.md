# Product Troubleshooting FAQ

_Last updated: 2026-01-15 · Doc ID: FAQ-TROUBLE-001_

## The app won't load / shows a blank screen

1. Hard-refresh the page (Ctrl/Cmd + Shift + R).
2. Clear the browser cache for the site.
3. Try an incognito/private window to rule out extensions.
4. Confirm you are on a supported browser: latest Chrome, Edge, Firefox, or Safari.

If the blank screen persists across browsers, collect the browser console error
and escalate to technical support.

## Sync is not working

- Confirm the device is online.
- Sign out and back in to force a fresh sync token.
- Sync can take up to 5 minutes for large accounts.

Persistent sync failures after these steps should be escalated with the account
ID and approximate time the issue started.

## Exports are failing

Exports over 50,000 rows are queued and delivered by email. If no email arrives
within 1 hour, escalate with the export request time.

## Error codes

- **ERR-402**: billing hold — direct the customer to Settings → Billing.
- **ERR-500**: transient server error — ask the customer to retry in 10 minutes.
- **ERR-403**: permission issue — the workspace admin must grant access.

## What the agent may do

- Provide the numbered self-service steps above.
- Give the meaning of a known error code.
- Escalate reproducible bugs with the details the customer has provided.
