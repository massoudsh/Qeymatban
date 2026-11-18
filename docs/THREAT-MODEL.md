# Threat model

Scope: the Qeymatban API, dashboard and data pipeline as deployed with
`compose.yaml`. One page, focused on what actually applies to a data-heavy
valuation product.

## Assets

| Asset | Where | Impact if exposed |
|---|---|---|
| Property and transaction data | PostgreSQL | Competitive harm to partners, privacy of sellers |
| Model artifacts | `models/` volume | Copying the pricing engine |
| API keys | `QEYMATBAN_API_KEYS`, `QEYMATBAN_API_KEY` env | Free use of the B2B API |
| Database credentials | `DATABASE_URL`, `.env` | Full data access |

## Threats and mitigations

| Threat | Mitigation |
|---|---|
| API key leaked to the browser | Key lives only in server-side Next.js routes, never `NEXT_PUBLIC_*` |
| Secrets committed to git | `.gitignore` covers `.env*` and `*.joblib`; `gitleaks` runs in CI |
| Unauthenticated API abuse | Set `QEYMATBAN_API_KEYS`; all `/v1/valuations*` routes then require `X-API-Key` |
| Cross-origin abuse | `QEYMATBAN_CORS_ORIGINS` is an explicit allow-list |
| SQL injection | All queries go through SQLAlchemy parameter binding; no string-built SQL |
| Malicious CSV import | Strict type, range and uniqueness validation before any write |
| Silent model regression | `retrain` rejects worse candidates; `evaluate` enforces thresholds |
| Container escape / root process | API runs as uid 10001 after the entrypoint drops privileges |
| Log-based data leak | Logs carry request id, path, status and duration only — no payloads |
| Dependency compromise | Dependabot updates, CodeQL analysis, CycloneDX SBOM artifact |

## Known gaps

- Authentication is a shared API key, not per-tenant identity. Multi-tenant
  roles and quotas are not implemented.
- No rate limiting. Put the API behind a gateway or reverse proxy for public
  exposure.
- `POST /v1/valuations` stores the submitted property attributes indefinitely;
  a retention policy is not implemented yet.
- TLS termination is out of scope for the compose stack; run it behind a proxy
  that terminates HTTPS.

## Reporting

Security issues should go to the maintainers privately rather than a public issue.
