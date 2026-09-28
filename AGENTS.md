# Distribution repository

- Keep this repository limited to public download documentation and metadata.
- Never copy proprietary source, deployment configuration, credentials or user data here.
- Release artifacts are built and tested in the private source repository.
- Never overwrite a published tag or release asset; issue a new version.
- Keep operator access and deployment instructions in private documentation.
- Run `python3 scripts/check_public_content.py` and its tests before publishing
  documentation. Inspect release descriptions and assets separately; the checker
  does not prove remote metadata, Git history or binaries free of sensitive data.
- Commit messages use `{type}: {imperative specific summary}`.
