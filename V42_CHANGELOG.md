# v42 Practical Security Edition

- MFA remains optional; FORCE_PRIVILEGED_MFA defaults to false.
- Login lockout: 5 failed attempts / 15 minutes by default.
- Signed HttpOnly SameSite=Strict session cookies; production Secure flag.
- 30-minute sliding idle timeout plus 8-hour absolute session limit.
- Server-side role/region/employee/clinic authorization retained and reviewed on sales/CRM mutation routes.
- Sensitive admin account operations require admin password re-authentication and invalidate old sessions.
- Audit logs retain username, action, entity, detail, IP, HTTP method and path for sensitive mutations.
- Production startup refuses weak/default SECRET_KEY, SQLite, or demo-data seeding.
- Render keeps DATABASE_URL/SECRET_KEY/ADMIN_PASSWORD out of source; PostgreSQL has no public IP allow list.

MFA code remains available for later opt-in/IPO-stage hardening but is not forced in this release.
