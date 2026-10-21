# BA3073 deployment verification, 2026-10-21

This is a verification ledger, not the assignment report. The report must be
generated through the application's production console using the prepared
evidence and instructions.

## Implemented and tested

- Local Linux/amd64 image built using a pinned ACR runtime layer after matching
  both requirements-file hashes; no embedded keys, database or master key found.
- Current source image pushed to ACR and deployed on ECS with persistent mounts.
  Digest: `sha256:e6ba2f65ddf7073f9ecf5bcb931442c1f67b2241783ad68a55833cc44bbbd9d4`.
- Local and ECS health, UI, application authentication, model call, tiny code
  generation, artifact download and manifests passed actual smoke checks.
- Thirty focused/regression tests passed: 12 evidence/essay tests and 18
  context/upload tests. Evidence bundles validate image type, size, checksum,
  identifiers and ownership; image bytes are embedded after model generation.
- Task 2 direct-IP UI and health requests passed from the student's computer.
  A temporary screenshot window was rechecked at 08:06 UTC. Its host Docker
  firewall permits only the SSH-observed client IP and schedules automatic
  restoration of loopback binding after twenty minutes. This is a temporary
  collection stage, distinct from the final Task 3 network configuration.
- Domain HTTPS uses a trusted certificate and a separate Nginx access gate.
  Missing/wrong gateway credentials and Bearer-only requests returned 401;
  correct credentials, application login and subsequent Bearer API requests
  returned 200. The current origin test at 08:08 UTC passed all these checks.
- User-supplied Edge screenshot shows the actual HTTPS domain address bar and
  application login page. This proves that browser path can load the interface;
  the screenshot alone does not prove application sign-in or AI generation.

## Limits and remaining collection

- Public HTTP returned an upstream Alibaba Cloud ICP message (403), although
  origin HTTP returns the configured 308 redirect. The certificate renewal
  dry-run failed on its HTTP challenge. The timer exists; successful automatic
  renewal has not been established.
- Command-line public TLS probes later failed while user Edge HTTPS succeeded.
  Do not infer a universal HTTPS outage from that client-specific failure.
- Task 2 server self-requests can time out because its security group allows
  the student IP rather than the server's own public source. Preserve the
  genuine failed self-check and the separate successful client check.
- Final configuration binds the backend to `127.0.0.1:14242`; remove the cloud
  security group's temporary 14242 inbound rule after screenshot collection.
- Address-bar screenshots must be original browser images. No reconstructed
  address bars or fabricated success pages are accepted.
- The gateway uses a shared deployment cookie, with no per-user revocation.
  This documented teaching limitation is separate from application ownership.

## Submission source

Student-specified repository: https://github.com/SSSylviaaa1201/AI_Learning_Assistant.
The teaching repository remains the upstream reference. Credentials, `.env`,
runtime data, generated artifacts and dependency directories are excluded.

The user subsequently supplied all three original address-bar screenshots,
showing signed-in production consoles for local, direct-IP and HTTPS access.
After Task 2 collection, loopback-only binding was restored at 08:24 UTC;
origin gateway and application Bearer checks passed again at 08:25 UTC. The
cloud security-group rule deletion still requires confirmation. Idle preview
screenshots must not be described as completed report generation.
