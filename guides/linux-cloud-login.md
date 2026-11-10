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

## Connect your account, then authorize Spaces

CLI v0.2.42 connects a device to your account without copying a Space ID first.
Keep your existing credential backend and key configuration. The example key
path below is a placeholder for a key your operator has already provisioned:

```sh
obsdog version
export OBSDOG_CREDENTIAL_STORE=encrypted-file
export OBSDOG_CREDENTIAL_KEY_FILE=/run/user/1000/secrets/obsdog-credential-key
obsdog auth login --server https://api.obsdog.ai --no-browser
obsdog auth status --server https://api.obsdog.ai
```

Open the exact verification URL printed by this command. The new account flow
uses `https://app.obsdog.ai/device/v3`; old explicit-Space login uses a different
page. Sign in, review the account and requesting device, and approve either
account connection only or one eligible Space. Account connection alone grants
no knowledge access. The displayed hyphen is accepted; it is not an expiry fix.
Never approve a code you did not just request.

Add another Space to the same connection with:

```sh
obsdog auth grant --server https://api.obsdog.ai --no-browser
obsdog auth status --server https://api.obsdog.ai
```

Choose and approve that exact Space in the browser. Switching among approved
Spaces does not require another account pairing. Login and grant do not upload
knowledge, start sync, or change your default local Space.

To explicitly download an approved Space, replace `SPACE_ID` below with its exact
ID shown by `auth status`. If it already exists locally, inspect it and preserve
pending edits. If absent, `space prepare` creates an empty candidate with that
identity. Never relabel an unrelated existing library to make it match.

```sh
obsdog space prepare --id SPACE_ID
obsdog sync connect --space SPACE_ID --server https://api.obsdog.ai
obsdog --timeout 180s sync pull --space SPACE_ID --server https://api.obsdog.ai
```

First pull is separate from successful login. For `activity_detail_expired`,
`client_upgrade_required` or `snapshot_required`, preserve the local profile and
follow [full-history recovery](history-retention.md). Re-pairing does not rebuild
a server checkpoint. Do not delete a library, force a cursor or upload an empty
replacement to bypass recovery.

## Select and disconnect accounts

```sh
obsdog auth accounts --server https://api.obsdog.ai
obsdog auth login --add-account --server https://api.obsdog.ai --no-browser
obsdog auth use --account ACCOUNT_ID --server https://api.obsdog.ai
obsdog auth revoke-space --space SPACE_ID --server https://api.obsdog.ai
obsdog auth logout --server https://api.obsdog.ai
```

`auth use` selects an already connected account. `revoke-space` removes only that
Space grant; `logout` revokes the selected account's device connection and all
its grants. Neither deletes local knowledge. Website sign-out is separate from
CLI disconnection. A failed or uncertain revocation keeps the local credential
so you can inspect and retry deliberately.

Existing explicit `auth login --space SPACE_ID` remains a legacy exact-Space
flow. It preserves its old credential records and must not be combined with
`--account` or `--add-account`. Once account connections exist, sync uses the
selected account and never silently falls back to another account or old token.
The hosted MCP plugin has its own connection; CLI pairing does not reconnect it.

## Credential file requirements

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
do not blindly restore an older rotating refresh-token backup. The account flow coordinates refresh and local record updates across processes.
After an interrupted operation, inspect status using the same configuration;
never delete the index or restore an old token to force a retry.

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
