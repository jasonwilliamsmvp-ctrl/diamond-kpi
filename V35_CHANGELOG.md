# v35 — Sales CRM navigation and customer management

- Sales sidebar now has separate entry points for overview, customer management, daily performance and visit calendar. These use the existing `/sales-portal` endpoint with a `tab` query parameter and enforce the same backend employee ownership checks.
- Added customer list and a scoped customer edit page for sales users. Sales cannot change ownership or region.
- Daily performance and calendar retain the existing product master and scheduling logic.
- IMPORTANT: Accounts marked `must_change_password` must first change password under Account Security and log in again. Until then the backend intentionally blocks all business pages; adding navigation cannot bypass this protection.
- No schema migration; no database reset.
