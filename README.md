# ObsDog downloads

ObsDog is a local-first knowledge tool for people and AI: search Markdown,
preserve revision history, and record which retrieved knowledge was useful.

This repository distributes official binaries and installation documentation.
It does **not** contain the proprietary application source code.

## CLI free beta — Apple silicon macOS

No account or GitHub login is required for local use. Choose **one** installation
method: Homebrew or the standalone installer.

### Homebrew

```sh
brew install obsdoghq/tap/obsdog
obsdog version
```

The [official tap](https://github.com/obsdoghq/homebrew-tap) installs the exact
checksum-pinned v0.1.16 binary and its license notices. If Homebrew requests trust,
review and approve this formula only; whole-tap trust is unnecessary.

### Standalone installer

Download the installer and checksum manifest from the same immutable release,
inspect them, then install:

```sh
curl -fL --proto '=https' -o obsdog-install.sh https://github.com/obsdoghq/obsdog-releases/releases/download/v0.1.16/install.sh
curl -fL --proto '=https' -o obsdog-checksums.txt https://github.com/obsdoghq/obsdog-releases/releases/download/v0.1.16/checksums.txt
shasum -a 256 obsdog-install.sh
# Compare that hash with the install.sh entry in obsdog-checksums.txt.
less obsdog-install.sh
sh obsdog-install.sh --dry-run
sh obsdog-install.sh
export PATH="$HOME/.local/bin:$PATH"
obsdog --help
obsdog --licenses
```

The installer verifies the binary archive checksum and version before replacing
only `~/.local/bin/obsdog`. It does not modify project files or knowledge data.
An optional `--install-dir /absolute/path` selects another standalone location.
SHA-256 verifies integrity against the release manifest; it is not an Apple
notarization ticket or an independent publisher signature.

The release includes the binary license, third-party notices, SPDX inventory,
source revision identifier, and checksum manifest. These terminal CLI archives
are not the notarized macOS desktop application. Intel macOS, Windows, Linux
and a public macOS app download are not offered by this release. v0.1.16 retains
no-init Personal selection, explicit AI authorship, history-preserving Personal
adoption and current hosted OAuth compatibility. It adds revision-bound source
declarations, authoring reviews and source/temporal filters. Connected care writes
require server v0.1.26 and compatible active clients; keep recoverable backups.
v0.1.15 corrects v0.1.14's rejection of normal newline-terminated block replacement
files without weakening the single-block or current-revision guards. v0.1.16
derives fading, revision-bound usage activation from real observations and adds
bounded same-query adaptive ranking, with `--ranking lexical` as the baseline.
No source or history is deleted; no unobserved note is rated bad. Use
`obsdog memory show --format json` to inspect the evidence and policy.
Installing it does not upload data or merge libraries automatically.

## Start locally

Use the same Personal knowledge from any directory, with no setup required:

```sh
obsdog document import --file README.md
obsdog search "installation"
obsdog wiki serve
```

Knowledge lives under `~/.obsdog`. Commands default to Personal; select another
existing library with `--space <space-id>`. An explicit broken binding fails
visibly rather than writing elsewhere. If multiple existing libraries make the
default ambiguous, use `obsdog space default --set <space-id>`. Optional
`obsdog init --dry-run` previews project guidance without creating a separate
library for every repository. The Wiki uses
`http://127.0.0.1:47777` by default. Use `obsdog <command> --help` for options.
Local usage is not metered and does not require network access.

For Homebrew installations, use `brew update` then
`brew upgrade obsdoghq/tap/obsdog`. For standalone installations:

```sh
obsdog update --check
obsdog update
```

The public binary uses this repository's releases for updates without a token.
Development (`odev`) and package-manager installations are not overwritten.
Users of the earlier private CLI should run this installer once to adopt the
public update channel. Installation does not migrate or discard Space data.

The actual anonymous default v0.1.16 install (including paths with spaces),
v0.1.8-to-v0.1.16 update, retained synthetic Space and attributed agent actions
were verified. Homebrew style, strict audit, upgrade and formula tests also pass.
v0.1.7 is a superseded packaging candidate;
its unchanged archive is retained for audit and is not recommended.

Use `command -v obsdog` to confirm which installation owns the command. Do not
install both methods onto your PATH unintentionally. `brew uninstall obsdog`
removes the Homebrew package, not your `~/.obsdog` knowledge or project bindings.

AI callers should use `--actor-type agent --actor your-agent` on `document import`,
`block update`, `search`, `search open` and `search use`, and the separate `--evaluator-type agent
--evaluator your-agent` flags on `feedback add`. JSON output alone does not
identify the caller as an agent. New or repaired project guidance includes these
options; review `obsdog init --dry-run` before refreshing existing guidance with
`obsdog init --repair`. See [v0.1.16 release notes](releases/v0.1.16.md) and
[the source-aware care guide](guides/knowledge-care.md) for the exact JSON and
safe AI workflow. Source checks are not task usefulness; unknown notes are not
silently verified. [Living memory](guides/living-memory.md) explains observed
connections, decay and the bounded ranking adjustment. No background worker,
automatic factual inference or deletion is enabled. Performance improvement is
an evaluation question, not a claim established by shipping this policy.

## Optional hosted Personal beta

Guarded cloud signup is open for controlled beta testing at
[ObsDog App](https://app.obsdog.ai). Limits are one Personal Space,
three active device sessions, 100 MiB retained cloud data and 10,000 new sync
operations per UTC month, initially up to 100 hosted accounts. History and sync
copies count toward cloud storage; these are not quotas on local files.
There is no checkout, hosted AI credit, or automatic paid conversion.

Local and hosted libraries must have the same Space identity to synchronize.
Signing in does not backfill an older offline library. If both Personal libraries
already contain data, use the advanced `sync adopt-preview` / `sync adopt`
workflow only after reviewing whole-Space upload, private backups and the plan.
It preserves historical evidence and keeps the original read-only; verify
readback before `space activate-adopted`. This is private managed sync, not
end-to-end encryption. See `obsdog sync --help` for the exact available commands.

Fresh-account and independent-network acceptance are still in progress; this
is not a general-availability announcement. Existing users can continue even
when new signup capacity is paused. New organizations, a public TestFlight
link and an App Store release are not part of this download. The current status
is documented at [ObsDog](https://obsdog.ai) and [Docs](https://docs.obsdog.ai).

## Feedback and security

Use this repository's issues for reproducible CLI feedback, but do not attach
documents, tokens, unredacted logs or personal data. For a security concern or
account-specific support, email [support](mailto:jh145478@gmail.com).

Hosted use is covered by the [Terms](https://obsdog.ai/terms/) and
[Privacy Policy](https://obsdog.ai/privacy/). Keep recoverable backups during
beta. A public download does not promise a service-level agreement.

## Documentation checks

Before publishing changes, run `python3 -m unittest discover -s tests` and
`python3 scripts/check_public_content.py`. These checks flag common accidental
internal details without printing matched values. They supplement review and
do not certify historical commits, remote release metadata or binary contents.
