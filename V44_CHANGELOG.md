# Diamond KPI v44 — Business Continuity & Security Edition

Built on v42 Practical Security Edition. MFA remains optional by default.

## Implemented in application/repository
- Login lockout, secure session expiry, CSRF/security headers and backend role/region scoping retained from v42.
- Audit records now use a SHA-256 hash chain for newly created records. Legacy pre-v44 records remain readable but are not retroactively trusted.
- `/security-status` (Admin only) verifies the hash chain and reports security configuration state without exposing secrets.
- KPI and sales CSV exports create audit records with row count and authorization scope.
- Optional `SECURITY_ALERT_WEBHOOK_URL` sends a generic JSON alert when an account is locked after repeated login failures. No password or secret is included.
- PostgreSQL backup, restore and backup-integrity verification scripts included.
- GitHub Actions security workflow compiles Python and runs `pip-audit` on dependencies for pushes/PRs.
- Separate `render.staging.yaml` retained for staging isolation.

## Requires account/platform configuration
- Configure an external scheduler/storage for backups. Do not store production backups only on the web service filesystem.
- Configure `SECURITY_ALERT_WEBHOOK_URL` only if an approved internal webhook endpoint exists.
- Enable GitHub branch protection, required PR review, MFA for GitHub owners, and secret scanning where available.
- Use separate Render services/databases/secrets for staging and production.
- Confirm the Render PostgreSQL plan provides the required retention/PITR for the company's RPO/RTO; the repository cannot enable plan-level backups by itself.

## Verification before production
1. Deploy to staging.
2. Test sales/manager/admin authorization, including direct URL/ID tampering.
3. Trigger five failed logins and confirm temporary lockout and audit record.
4. Export KPI/sales and confirm audit records.
5. Visit `/security-status` as Admin and confirm `audit_chain_ok=true` after new v44 audit records exist.
6. Run `scripts/verify_backup.sh` against a non-production or approved database and perform a restore drill.
