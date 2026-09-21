# Runbook: SSO SAML callback errors

Service: auth-gateway
Owner: Identity
Alarm: `sso-saml-callback-errors`
Last reviewed: 2026-05-11

## What this alarm means

More than 5% of SAML assertions posted to the callback endpoint were rejected
over a 10-minute window. Authentication is a **core customer journey** under
the severity policy.

## Blast radius decides severity here, and it is the exception to the 5% rule

SAML is configured per identity provider. A failure is almost always scoped to
one IdP rather than to all users, so the global error percentage understates
the impact on the affected tenants and overstates it for everyone else.

**Count affected tenants, not the error percentage.**

| Scope | Severity |
|---|---|
| One IdP, password login unaffected | SEV2 |
| More than one IdP | SEV1 |
| All IdPs, or the callback endpoint itself failing | SEV1 |

A single-IdP failure is SEV2 **even though the affected users are completely
blocked**, because an alternative login path exists. If password login is also
unavailable for those users, escalate to SEV1.

## Overwhelmingly the most common cause

**An expired IdP signing certificate.** Certificates are rotated by the
customer, not by us, and we are frequently not told. Check the certificate
expiry on the affected IdP configuration first — it resolves the majority of
these alerts and requires no code change.

## Other causes, in order of frequency

1. **Clock skew.** Assertions carry a validity window, typically 5 minutes.
   More than 3 minutes of skew on either side produces intermittent failures
   that look random.
2. **A changed entity ID or ACS URL** following a customer-side migration.
3. **Assertion size.** Assertions above 64KB are rejected at the proxy before
   reaching auth-gateway, so they will not appear in auth-gateway logs at all.

## Mitigations

- **Ask the customer to re-upload the certificate.** No deploy, no approval.
- **Disable SAML for the affected tenant**, forcing password login. Requires
  Identity team approval — it is visible to the customer and will generate
  support contacts.

## Do not

Do not roll back auth-gateway for a single-tenant SAML failure. The cause is
almost never in our code, and a rollback affects every tenant to fix one.
