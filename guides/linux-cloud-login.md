# Linux cloud login without a desktop keyring

CLI v0.2.21 adds an explicit encrypted-file credential store for Linux x64.
Local Personal, search, dashboard and stdio MCP still need no account, GUI or
credential store. Only connected cloud operations require authentication.

## Choose the credential store

The default is the OS credential store: an unlocked Secret Service keyring
over D-Bus on Linux. If it is unavailable, authentication stops. There is no
automatic fallback or plaintext credential file.

Linux without that service can explicitly select `encrypted-file`. This stores
the same browser-approved device session; it does not create an unattended
service account or bypass approval. macOS continues to use Keychain.

Before selecting it, independently provision a cryptographically random
32-byte unlock key, encoded as canonical padded standard base64. Use an existing
private key file or trusted secret-manager environment injection. ObsDog does
not generate, print, copy or migrate the key. Do not put its value in command
arguments, shell history, `.env`, source control, agent prompts or support reports.

## Connect an exact Space

Copy the exact Personal Space ID from `app.obsdog.ai/account`. If that ID is not
present locally, `space prepare --id` creates an empty local candidate; it does
not sign in, select a new default, rebind existing knowledge or upload anything.
Pass the chosen ID explicitly. The examples below contain placeholder IDs and
a non-secret path to a key that your operator has already provisioned:

```sh
obsdog version
obsdog space prepare --id spc_from_account
export OBSDOG_CREDENTIAL_STORE=encrypted-file
export OBSDOG_CREDENTIAL_KEY_FILE=/run/user/1000/secrets/obsdog-credential-key
obsdog auth login --space spc_from_account --server https://api.obsdog.ai --no-browser
obsdog auth status --server https://api.obsdog.ai
```

Open the printed verification URL in your browser, sign in and approve the
named device and exact Space. The CLI never asks for a provider password or
prints access/refresh tokens. Login alone does not upload your local library.
Keep the same credential configuration for explicitly requested sync and logout.

The key file must be absolute, owned by your effective user, regular, single-link
and mode `0400` or `0600`, with no symlink path components. One final LF or CRLF
is allowed. It must be outside the ciphertext directory. The default ciphertext
directory is `$XDG_CONFIG_HOME/obsdog/credentials`, or
`$HOME/.config/obsdog/credentials`; it must be owned `0700`. Records must be
owned `0600` regular single-link files. Unsafe objects are refused, not repaired.
`OBSDOG_CREDENTIAL_DIR` can name another absolute, private local directory.

Alternatively let your trusted launcher inject `OBSDOG_CREDENTIAL_KEY` into
each CLI process, with `OBSDOG_CREDENTIAL_KEY_FILE` unset. Exactly one nonempty
key source is required. Do not combine either encrypted-file configuration
with `OBSDOG_SYNC_TOKEN`. Local-only commands ignore credential configuration.

## Logout, errors and recovery

```sh
obsdog auth logout --server https://api.obsdog.ai
```

Ordinary logout revokes the server-side device session before deleting the
local encrypted record. `--local-only` is an explicit offline escape hatch;
it cannot confirm server revocation. Deletion is not a secure-erasure guarantee.

A wrong key, corrupt record or unavailable store stops before new device
authorization and cannot replace or delete the unreadable credential. There
is no keyring/file migration or automatic key rotation. Selecting a different
backend does not revoke the session in the old one. If the key is lost, revoke
the old device from authenticated account settings, provision a new independent
key and approve a fresh login into a new empty credential directory.

Encrypted temporary records are atomically replaced. A failure before rename
preserves the old record; a failure after rename may leave the complete new
record with durability unconfirmed. Stop and inspect status with the same key;
do not blindly restore an older rotating refresh-token backup. Serialize hosted
commands that share one credential directory to avoid refresh-token races.

## What encryption does not protect

Ciphertext is protected at rest only when its key is unavailable to the
attacker. Putting the key beside ciphertext is not independent protection.
Same-user/root access, runtime memory, process environments, debug tools and
captured logs are outside this guarantee. This is not equivalent to the OS
keyring's isolation. Use a private local filesystem and tightly scoped secret
delivery; do not enable shell tracing around authentication.

After updating, restart owned dashboards and reconnect host-owned MCP sessions.
Follow the [agent update checklist](https://github.com/obsdoghq/skills/blob/main/docs/SETUP.md#updating-cli-and-agent-guidance).
Do not include keys, tokens, real Space IDs or private paths in public feedback.
