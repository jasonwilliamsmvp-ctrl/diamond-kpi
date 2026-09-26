# v44 deployment checklist

## Render
- [ ] Deploy to a staging service/database first.
- [ ] `APP_ENV=production` on production.
- [ ] `SEED_DEMO_DATA=false`.
- [ ] Strong generated `SECRET_KEY`; never copy it into GitHub.
- [ ] `ADMIN_PASSWORD` is a Render secret and is not the default.
- [ ] `FORCE_PRIVILEGED_MFA=false` for the current practical-security policy.
- [ ] PostgreSQL is used in production and public database access is disabled/restricted.
- [ ] Decide RPO/RTO and enable a database backup/PITR plan that meets it.
- [ ] Configure off-service backup storage and perform a restore test.
- [ ] Optional: set `SECURITY_ALERT_WEBHOOK_URL` to an approved internal webhook.

## GitHub
- [ ] Require pull request review for the production branch.
- [ ] Prevent force pushes/deletion of the production branch.
- [ ] Require the `Security checks` workflow to pass.
- [ ] Enable secret scanning / push protection if available.
- [ ] GitHub owners/admins use MFA.
- [ ] No `.env`, database URL, passwords or production dumps are committed.

## Functional security test
- [ ] Sales cannot access another salesperson's customer, sales, visit or employee record by changing IDs/URLs.
- [ ] Manager cannot access another region by changing IDs/URLs/API parameters.
- [ ] Five failed logins cause temporary lockout.
- [ ] Idle session expires after configured timeout.
- [ ] Admin sensitive operations require re-authentication where implemented.
- [ ] KPI and sales exports appear in Audit Log.
- [ ] `/security-status` reports a valid v44 audit hash chain.
- [ ] Backup file can actually be restored to a separate database.
