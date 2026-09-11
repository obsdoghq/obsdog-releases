# ObsDog downloads

ObsDog is a local-first knowledge tool for people and AI: search Markdown,
preserve revision history, and record which retrieved knowledge was useful.

This repository distributes official binaries and installation documentation.
It does **not** contain the proprietary application source code.

## CLI free beta — Apple silicon macOS

No account or GitHub login is required for local use. Download the installer and
checksum manifest from the same immutable release, inspect them, then install:

```sh
curl -fL --proto '=https' -o obsdog-install.sh https://github.com/obsdoghq/obsdog-releases/releases/download/v0.1.8/install.sh
curl -fL --proto '=https' -o obsdog-checksums.txt https://github.com/obsdoghq/obsdog-releases/releases/download/v0.1.8/checksums.txt
shasum -a 256 obsdog-install.sh
# Compare that hash with the install.sh entry in obsdog-checksums.txt.
less obsdog-install.sh
sh obsdog-install.sh --version v0.1.8 --dry-run
sh obsdog-install.sh --version v0.1.8
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
are not the notarized macOS desktop application. Intel/macOS, Windows, Linux,
Homebrew packages and a public macOS app download are not offered by this
initial release.

## Start locally

From the project whose Markdown you want to manage:

```sh
obsdog init
obsdog document import --file README.md
obsdog search "installation"
obsdog wiki serve
```

Knowledge lives under `~/.obsdog`; a project's `AGENTS.md` records its Space
connection. Review the managed section created by `init`. The Wiki uses
`http://127.0.0.1:47777` by default. Use `obsdog <command> --help` for options.
Local usage is not metered and does not require network access.

```sh
obsdog update --check
obsdog update
```

The public binary uses this repository's releases for updates without a token.
Development (`odev`) and package-manager installations are not overwritten.
Users of the earlier private CLI should run this installer once to adopt the
public update channel. Installation does not migrate or discard Space data.

The actual anonymous v0.1.6-to-v0.1.8 update and preservation of an isolated
synthetic Space were verified. v0.1.7 is a superseded packaging candidate;
its unchanged archive is retained for audit and is not recommended.

AI callers should use `--actor-type agent --actor your-agent` on `search`,
`search open` and `search use`, and the separate `--evaluator-type agent
--evaluator your-agent` flags on `feedback add`. JSON output alone does not
identify the caller as an agent. New or repaired project guidance includes these
options; review `obsdog init --dry-run` before refreshing existing guidance with
`obsdog init --repair`. See [v0.1.8 release notes](releases/v0.1.8.md).

## Optional hosted Personal beta

Guarded cloud signup is open for controlled beta testing at
[ObsDog App](https://app.obsdog.ai). Limits are one Personal Space,
three active device sessions, 100 MiB retained cloud data and 10,000 new sync
operations per UTC month, initially up to 100 hosted accounts. History and sync
copies count toward cloud storage; these are not quotas on local files.
There is no checkout, hosted AI credit, or automatic paid conversion.

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
