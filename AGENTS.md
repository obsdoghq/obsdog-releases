# Distribution repository

- Use Project draft tickets for internal work and verification, not duplicate
  repository Issues or TODO.md checklists. Public Issues remain feedback intake.
  Never copy private task bodies, access details or deployment
  evidence into this public repository. Source CI is not binary publication.

- Keep this repository limited to public download documentation, metadata and
  narrowly scoped public installation helpers; no application implementation.
- Never copy proprietary source, deployment configuration, credentials or user data here.
- Release artifacts are built and tested in the private source repository.
- Never overwrite a published tag or release asset; issue a new version.
- Keep operator access and deployment instructions in private documentation.
- Run `python3 scripts/check_public_content.py` and its tests before publishing
  documentation. Inspect release descriptions and assets separately; the checker
  does not prove remote metadata, Git history or binaries free of sensitive data.
- Commit messages use `{type}: {imperative specific summary}`.
