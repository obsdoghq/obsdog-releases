# ObsDog downloads

ObsDog is a local-first knowledge tool for people and AI: search Markdown,
preserve revision history, and record which retrieved knowledge was useful.

This repository distributes official binaries and installation documentation.
It does **not** contain the proprietary application source code.

[Send feedback](https://github.com/obsdoghq/obsdog-releases/issues/new/choose) ·
[Feedback privacy guide](FEEDBACK.md) ·
[AI-client setup](https://github.com/obsdoghq/skills/blob/main/docs/SETUP.md)

## Quick Start — CLI + AI plugin

On Apple silicon macOS with Codex or Claude Code already installed (and Homebrew
if the CLI is not yet installed),
run the first-party installer at `https://obsdog.ai/install.sh`. It pins and
checksum-verifies the public [agent setup helper](scripts/setup-agent.sh),
which installs/reuses the CLI and then installs the plugin for **one** chosen
client. For Codex:

```sh
curl -fsSL https://obsdog.ai/install.sh | sh -s -- --client codex
obsdog version
obsdog document list
```

For Claude Code, change the final flag to `--client claude`. To inspect the
entry before execution, download and read it first:

```sh
curl -fsSLo obsdog-agent-install.sh https://obsdog.ai/install.sh
less obsdog-agent-install.sh
sh obsdog-agent-install.sh --client codex
```

The entry pins the immutable
[helper source](https://github.com/obsdoghq/obsdog-releases/blob/d64550e384c3ed7c577c26d707f062e847c5985a/scripts/setup-agent.sh)
and its SHA-256; append `--dry-run` to preview actions. It needs network access to
Homebrew/the plugin marketplace during installation, but local Personal use
needs no account or connection. An empty list is normal. In a **fresh agent
session**, invoke ObsDog `find` to check that the skill loads. The helper does
not create sample knowledge, sign in, sync, upload, or edit global instructions.
If either half fails, it reports the failed stage; rerun after fixing that stage.
The installer sends no success telemetry. Public website command-copy counts
require diagnostics consent and represent interest, not completed installs.

CLI-only use needs no plugin; use either method below. Installing the
[plugin](https://github.com/obsdoghq/skills) by itself does **not** install the
CLI. The [setup guide](https://github.com/obsdoghq/skills/blob/main/docs/SETUP.md)
covers optional proactive agent instructions without overwriting global files.

## CLI free beta — Apple silicon macOS

No account or GitHub login is required for local use. Choose **one** installation
method: Homebrew or the standalone installer.

### Homebrew

```sh
brew install obsdoghq/tap/obsdog
obsdog version
```

The [official tap](https://github.com/obsdoghq/homebrew-tap) installs the exact
checksum-pinned v0.2.18 binary and its license notices. If Homebrew requests trust,
review and approve this formula only; whole-tap trust is unnecessary.

### Standalone installer

Download the installer and checksum manifest from the same immutable release,
inspect them, then install:

```sh
curl -fL --proto '=https' -o obsdog-install.sh https://github.com/obsdoghq/obsdog-releases/releases/download/v0.2.18/install.sh
curl -fL --proto '=https' -o obsdog-checksums.txt https://github.com/obsdoghq/obsdog-releases/releases/download/v0.2.18/checksums.txt
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

## What to do after installation

v0.2.18 [adapts Graph scale to the map and viewport](releases/v0.2.18.md):
bounded node/click sizes, representative titles and reversible zoom/Fit retain
every loaded document, including dense and independent maps.

v0.2.17 [shows all loaded documents together](releases/v0.2.17.md), including
independent notes, in the shared hosted/offline Graph. Circular focus emphasizes
direct neighbors without hiding the rest of the map. Explicitly opened dashboard
deep links work while cross-site API access remains blocked. Restart running
dashboard and MCP processes after updating.

v0.2.16 [introduced the shared visual system](releases/v0.2.16.md); v0.2.17
replaces its component-at-a-time navigation with the full map.

v0.2.15 [adds a one-time local Graph reveal and optional read-only search,
recovery and Git-source diagnostics](releases/v0.2.15.md). It does not change
the graph layout or default search ranking.

v0.2.14 [shows whether old labels apply to the current revision, lists
recorded source checks for follow-up, and adds a guarded section append to
existing documents](releases/v0.2.14.md). Connected append requires the
server's exact-Space capability; installing this CLI does not enable sync.

v0.2.13 [distinguishes legacy newline normalization from structural damage,
clarifies retired duplicate groups and adds bounded Korean no-hit
hints](releases/v0.2.13.md). New zero-hit traces record an explicit frozen
candidate count; older missing counts remain unknown.

v0.2.12 [guards structural edits, separates diagnostic search from observed
retrieval and organizes dense local Graphs](releases/v0.2.12.md). `doctor`
detects old Markdown layout mismatches but does not repair them.

v0.2.11 [adds retrieval-run listing, same-query re-hit checks and bounded
adjacent-topic hints](releases/v0.2.11.md). A hint is navigation, not proof of
an exact answer or a recorded use.

v0.2.10 [adds conditional document correction and duplicate supersession](releases/v0.2.10.md).
For a connected Space, use a compatible server and recheck exact-Space care
capability before these actions. After upgrading, restart running `obsdog mcp`
and `obsdog dashboard serve` processes; reconnect agent sessions as needed.

v0.2.8 [prevents accidental duplicate imports and hides deprecated knowledge in
new searches by default](releases/v0.2.8.md). `document import` is create-only;
`--fork` is an explicit separate copy, not an update. Use `obsdog doctor` to
inspect exact duplicate candidates and `--include-deprecated` when auditing
retired search material.

v0.2.7 [detects an old dashboard left running after a CLI upgrade](releases/v0.2.7.md).
Stop and rerun `obsdog dashboard serve` after upgrading, then refresh the
browser; refreshing alone cannot replace the server. The dashboard shows this
instruction if it sees that its executable was replaced. It does not terminate
another process automatically.

v0.2.6 adds [recent activity, device-local time display and quiet update
notices](releases/v0.2.6.md). Daily trend buckets remain UTC. The update check
never uploads knowledge and can be disabled. Read [dashboard details](guides/local-dashboard.md).

v0.2.5 keeps returned-only searches in the event history but excludes them from
the bounded Living-memory scoring input. A library with many unopened results
can still project its observed opens and evaluations; overflow from potentially
scoring events still falls back explicitly to lexical search. This patch does
not delete knowledge, change the scoring weights or prove a retrieval gain.
See [release notes](releases/v0.2.5.md).

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

The v0.2.8 source package passed local race/vet, installer integrity, archive
decoder, SPDX and checksum checks. Anonymous published installation (including
paths with spaces), v0.1.8-to-v0.2.8 update, retained synthetic knowledge and
agent attribution also passed. Homebrew validation is recorded in the
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
