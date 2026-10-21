# Deployment operations — current state, 2026-10-21

This is an operations record, not the assignment report. The report must be
generated in the production console; only its prompt and sanitized references
have been prepared in the workspace's report-inputs directory.

## Runtime

- Local: http://127.0.0.1:14242/ui/ (healthy).
- ECS: Ubuntu 22.04 x86_64, 8.138.216.5, /opt/ai-learning-assistant.
- ACR tag: crpi-nhsrlij77120ulh1.cn-guangzhou.personal.cr.aliyuncs.com/sunyinluo/sunyinluo:assignment-20261021-report-ready.
- Digest: sha256:e6ba2f65ddf7073f9ecf5bcb931442c1f67b2241783ad68a55833cc44bbbd9d4.
- DNS: sunyinluo.asia A 8.138.216.5.
- Configured HTTPS: https://sunyinluo.asia/ui/.
- Trusted Let's Encrypt certificate issued, expiring 2027-01-19.
- Final ECS backend is bound only to 127.0.0.1:14242; direct public access is closed.
- data/ and workspace/ are persistent bind mounts; restart policy is unless-stopped.

## Observed access paths

The user supplied original Edge screenshots on 2026-10-21 showing the actual
address bars and signed-in production consoles for local, direct-IP and HTTPS
access. The final domain is https://sunyinluo.asia/ui/. The gateway password
prompt was reported separately by the user and authentication was independently
checked on the origin. Idle artifact previews are not generated reports.

Earlier command-line probes encountered TLS closure, while public HTTP returned
Alibaba Cloud's Non-compliance ICP Filing page (403). These observations must be
kept separate: command-line failure does not establish a browser-wide HTTPS
outage. Nginx origin checks and earlier automated authentication/API tests passed.
See edge-https-observation.json and its original screenshot in deployment evidence.

Certbot timer and a Nginx reload deploy hook are installed. The actual renewal
dry-run failed: the CA's HTTP challenge request was intercepted with 403. Do not
claim that renewal has been validated until the blocker is resolved and retested.

## Local build

Dockerfile is the complete fresh-runtime path. The tested cached-runtime path
reuses this account's pinned ACR runtime with identical dependency-file hashes:

    docker build --platform linux/amd64 --provenance=false --sbom=false -f Dockerfile.cached-runtime -t ai-learning-assistant-backend:local .
    docker compose -p ai-learning-assistant up -d --no-build --wait
    powershell -File scripts/check-local-ui.ps1

The cached Dockerfile fails if either dependency manifest changes. The base was
checked for embedded API keys, secret files, databases and master keys; none were
present. Disable provenance/SBOM attachments for this ACR personal registry because
it rejects Docker's empty OCI attestation. Secrets stay in ignored .env and
data/model-secrets.env, never in images or source.

## Temporary Task 2 access versus final state

Task 2 used 0.0.0.0:14242 with the cloud security-group rule restricted to the
student's observed IP 112.96.87.60/32. Independent client UI and health checks
returned 200 before closure. ECS self-requests timed out because the ECS source
was not the allowed client; preserve that difference in the evidence.
The backend is now loopback-only. The user confirmed removal of the cloud
security group's temporary 14242 inbound rule after screenshot collection.
This cloud-console action is user-confirmed, not independently queried via API.
All three original workbench address-bar screenshots have been collected.

## HTTPS access control

Nginx terminates TLS and proxies to 127.0.0.1:14242. HTTP is configured to redirect
to HTTPS except ACME, but the upstream filing block prevents public HTTP from
reaching that configuration. scripts/configure-https.py documents the installed
configuration and receives credentials through stdin. Actual credentials and
Nginx password hashes stay outside the repository.

Basic authentication and app Bearer tokens both use Authorization. After a valid
proxy sign-in, Nginx issues a Secure/HttpOnly/SameSite=Strict cookie, allowing the
app's Bearer header through the separate proxy gate. Missing/wrong credentials
and Bearer-without-gateway tests returned 401; authorized UI and app Bearer API
returned 200. Origin tests passed again after final loopback restoration.
The gate is separate from BNBU
login. Its deployment-wide shared token lacks per-user revocation; stronger
session management or an identity-aware proxy remains a future improvement.

## Report instructions and checks

essay_html.py now specifies BA3073 structure, maximum 20 A4 pages, actual evidence,
all three tasks, truthful failed-test treatment, security/cost discussion and no
invented citations. Owner-scoped evidence text bundles embed original screenshots
after generation without sending Base64 to the text model. See uploads.md.

Thirty tests passed: 12 evidence/essay tests plus 18 context/upload regressions.
Local and ECS live model, generation, download and manifest checks passed; existing
accounts and artifacts survived replacements. Chromium HTML-to-PDF was verified.
No assignment report has been authored outside the production console.

Complete modified source was pushed to the user-selected repository:
https://github.com/SSSylviaaa1201/AI_Learning_Assistant.
Report prompt, sanitized references and three original screenshot assets are
prepared locally. Report prose still must be generated in the production console.
Public HTTP/ACME challenge reachability and the failed renewal dry-run remain
documented operational limitations; do not claim these checks passed.

Never submit the preparation note, private credentials, .env files, data/,
workspace/, dependency directories, runtime archives or private keys.
