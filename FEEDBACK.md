# Share product feedback safely

[Open a guided issue](https://github.com/obsdoghq/obsdog-releases/issues/new/choose)
for CLI, plugins, installation or dashboard feedback. A GitHub account is required
to submit; reading existing feedback is public. Search existing issues first.
This repository is the product-feedback home even though application source is
private. Plugin implementation contributions belong in the skills repository.

## What helps

- CLI version (`obsdog version`), plugin version, AI-client version and OS.
- The exact installation route (Homebrew, standalone, Codex or Claude plugin).
- Expected versus actual behavior and a **tiny invented** reproduction example.
- What you tested, what worked, and what you have **not** tested yet. In
  particular, plugin installation is not proof of next-session skill invocation.
- A redacted screenshot if useful; inspect the whole image before posting.

## What must stay private

Do not upload `.obsdog`, SQLite files, backups, real documents or search traces.
Omit tokens, credentials, email addresses, personal paths, private repository
URLs, document/Space identifiers and screenshots containing that information.
Logs/diagnostic bundles are not automatically safe: reduce them to a reviewed
error message and invented input. Maintainers do not need access to your Space
for initial triage. Never grant account or vault access in an issue.

For a security or privacy vulnerability, **do not include exploit details or
affected user data in a public issue**. Use the existing
[support email](mailto:jh145478@gmail.com) for initial private coordination.
Do not send secrets or a full Space by email either. These ordinary feedback
forms do not imply a response SLA.

Product feedback is not a knowledge judgment. `obsdog feedback add` records a
usefulness/relevance evaluation within a Space; it does not file a GitHub issue.
ObsDog never posts product feedback automatically.
