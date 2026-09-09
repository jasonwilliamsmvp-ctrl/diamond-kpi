# v33 Changelog — Safe Logout UX

- Added a prominent **登出** button to the top-right header on every authenticated page.
- Added a second **安全登出** button in the current-user card in the sidebar.
- Logout clears `diamond_session`, `diamond_preauth`, and `csrf_token` cookies and redirects immediately to `/login`.
- Valid logout events are recorded in Audit Log, including request metadata through the existing security middleware.
- Logout remains usable even if the session is stale or partially invalid.
- No database schema migration is required.
