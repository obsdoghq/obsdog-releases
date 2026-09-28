# ObsDog downloads

ObsDog is a local-first knowledge tool for people and AI: search Markdown,
preserve revision history, and record which retrieved knowledge was useful.

This repository distributes official binaries and installation documentation.
It does **not** contain the proprietary application source code.

[Send feedback](https://github.com/obsdoghq/obsdog-releases/issues/new/choose) ·
[Feedback privacy guide](FEEDBACK.md) ·
[AI-client setup](https://github.com/obsdoghq/skills/blob/main/docs/SETUP.md)

Installing the [ObsDog plugin](https://github.com/obsdoghq/skills) does **not**
install this CLI. Confirm `obsdog version` in your AI client's environment, then
invoke a plugin skill in a fresh session. Optional global AGENTS.md/CLAUDE.md
instructions are explained in the setup guide; no global files are overwritten.

## CLI free beta — Apple silicon macOS

No account or GitHub login is required for local use. Choose **one** installation
method: Homebrew or the standalone installer.

### Homebrew

```sh
brew install obsdoghq/tap/obsdog
obsdog version
```

The [official tap](https://github.com/obsdoghq/homebrew-tap) installs the exact
checksum-pinned v0.2.4 binary and its license notices. If Homebrew requests trust,
review and approve this formula only; whole-tap trust is unnecessary.

### Standalone installer

Download the installer and checksum manifest from the same immutable release,
inspect them, then install:

```sh
curl -fL --proto '=https' -o obsdog-install.sh https://github.com/obsdoghq/obsdog-releases/releases/download/v0.2.4/install.sh
curl -fL --proto '=https' -o obsdog-checksums.txt https://github.com/obsdoghq/obsdog-releases/releases/download/v0.2.4/checksums.txt
shasum -a 256 obsdog-install.sh
# Compare that hash with the install.sh entry in obsdog-checksums.txt.
less obsdog-install.sh
sh obsdog-install.sh --dry-run
sh obsdog-install.sh
export PATH="$HOME/.local/bin:$PATH"
obsdog version
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
and a public macOS app download are not offered by this release. v0.2.0 removes
project initialization and path-based Space selection. It retains explicit AI authorship, history-preserving Personal
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

v0.2.1 fixes current lexical scoring: retained historical snapshots and incoming
trace chunks no longer distort current scores. Snapshot selection is independent
of timestamp ordering, and equivalent reindexing retains deterministic ordering.
The `lexical/current-v1` baseline preserves source history and recorded evidence;
it does not claim an independently demonstrated hit-rate improvement.

## Start locally

v0.2.4 adds [bounded AI care](guides/ai-care.md): checked updates, splits,
extraction/merge and conditional recovery with exact history and attributable
outcomes. Connected structural care needs server v0.1.29+, compatible active
writers and explicit preparation of the existing connection. It does not enable
sync or run automatic maintenance. See [release notes](releases/v0.2.4.md).

v0.2.3 adds [frozen search pages](guides/search-pages.md), explicit first-page-use
samples, relative document links, separate comment proposals and compact observed
memory summaries. [Release notes](releases/v0.2.3.md) explain the boundaries.

v0.2.2 adds Unicode-normalized, whitespace-insensitive substring search, typed
`care source` checks, `document list` and an [offline dashboard](guides/local-dashboard.md).
The dashboard shows Top 1/3/10 utilization with samples/coverage, activity trends,
useful ratings, edits and restructuring. Unobserved use is unknown, not failure;
updates are activity, not proven improvement. See [release notes](releases/v0.2.2.md).

Use the same Personal knowledge from any directory, with no setup required:

```sh
obsdog document import --file README.md
obsdog document list
obsdog search "installation"
obsdog dashboard serve
```

Knowledge lives under `~/.obsdog`. Commands default to Personal; select another
existing library with `--space <space-id>`. A missing explicit ID fails visibly
rather than writing elsewhere. If multiple existing libraries make the default
ambiguous, use `obsdog space default --set <space-id>`. `init`, `--path` and
`--source-path` are removed, without compatibility aliases. The current directory
and old project bindings do not select a Space. The Wiki uses
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

The actual anonymous v0.2.4 install (including paths with spaces),
v0.1.8-to-v0.2.4 update, retained synthetic Space and attributed agent actions
were verified. Homebrew validation is recorded in the
[official tap](https://github.com/obsdoghq/homebrew-tap#maintainers).
v0.1.7 is a superseded packaging candidate;
its unchanged archive is retained for audit and is not recommended.

Use `command -v obsdog` to confirm which installation owns the command. Do not
install both methods onto your PATH unintentionally. `brew uninstall obsdog`
removes the Homebrew package, not your `~/.obsdog` knowledge or project bindings.

AI callers should use `--actor-type agent --actor your-agent` on `document import`,
`block update`, `search`, `search open` and `search use`, and the separate `--evaluator-type agent
--evaluator your-agent` flags on `feedback add`. JSON output alone does not
identify the caller as an agent. In project instructions, name an exact Space ID
when that project needs a different boundary, and pass it explicitly on every
command; do not infer it from a working directory. Use ObsDog skills/plugin
v0.3.5 or newer for task-entry recall, authorized selective capture and bounded
care guidance. See [v0.2.4 release notes](releases/v0.2.4.md) and
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

Use the [guided feedback forms](https://github.com/obsdoghq/obsdog-releases/issues/new/choose)
for bugs, first-use experiences or ideas. Read [the safety guide](FEEDBACK.md)
before posting; never attach documents, tokens, unredacted logs or personal data.
For a security concern or account-specific support, email
[support](mailto:jh145478@gmail.com) rather than posting publicly.

Hosted use is covered by the [Terms](https://obsdog.ai/terms/) and
[Privacy Policy](https://obsdog.ai/privacy/). Keep recoverable backups during
beta. A public download does not promise a service-level agreement.

## Documentation checks

Before publishing changes, run `python3 -m unittest discover -s tests` and
`python3 scripts/check_public_content.py`. These checks flag common accidental
internal details without printing matched values. They supplement review and
do not certify historical commits, remote release metadata or binary contents.
