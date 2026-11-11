# Dotfiles

My shared macOS development preferences for Zsh, Git, and VS Code. Account
identities, credentials, machine paths, and private overrides stay outside this
repository.

## What is included

| File | Purpose |
| --- | --- |
| `Brewfile` | Shared command-line dependencies |
| `shell/.zprofile` | Guarded Homebrew setup and local command PATH |
| `shell/.zshrc` | Oh My Zsh, fnm, editor defaults, and `runc` |
| `shell/.profile` | Optional POSIX environment helper |
| `shell/zshrc.local.example` | Optional SDK paths, customized locally |
| `git/gitconfig.example` | Shared Git defaults with a local include |
| `git/gitconfig.local.example` | Identity placeholder |
| `git/ignore` | Global ignore preferences |
| `vscode/settings.json` | Editor preferences and C++/Python runner overrides |
| `npm/npmrc.example` | Registry authentication through an environment variable |

## Shell setup

Review the files and back up the current configuration before copying anything.
These are macOS-oriented preferences; optional tools are loaded only when
available. The restore command below previews every replacement first.

1. Install [Homebrew](https://brew.sh), then install the shared CLI dependencies:

   ```sh
   brew bundle install --file=Brewfile --no-upgrade
   brew bundle check --file=Brewfile --no-upgrade
   ```

   The manifest uses `gcc@15` so `g++-15` remains available even when the unversioned
   GCC formula moves to another major release. It records dependencies, rather
   than locking every package version. Existing GCC 15 installations are reused; the versioned formula is installed
   only when `g++-15` is missing from the standard Homebrew locations. Existing
   Python 3 is reused too. The check verifies availability without requiring
   unrelated package upgrades.
   Oh My Zsh and the optional autosuggestions plugin are installed separately.

   Install Oh My Zsh if you want to use it. The shell remains usable
   without Oh My Zsh. The configured theme is `bureau`.
2. Install fnm and the Node versions your projects require. Initialize fnm with
   `fnm env --use-on-cd --version-file-strategy recursive --shell zsh` as this configuration does. Use `fnm default
   VERSION` to choose a fallback version. Avoid loading nvm alongside fnm; keep its
   installation until any required global tools have been migrated.
3. Optionally install autosuggestions in Oh My Zsh's custom plugin directory:

   ```sh
   git clone https://github.com/zsh-users/zsh-autosuggestions \
     "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-autosuggestions"
   ```

4. Preview and install the shell files using the restore command below, or merge
   them manually into your home directory.
5. Copy `shell/zshrc.local.example` to `~/.zshrc.local` if you need SDK settings.
   The shell also supports `~/.zprofile.local` and `~/.profile.local`.

`~/.local/bin` stays ahead of system tools so local command wrappers take precedence.
The shell uses fnm for project version files and searches parent directories, so
entering `src/` keeps the project root's version. Respect each repository's existing
`.nvmrc` or `.node-version`; do not overwrite work project requirements with the
global default. If fnm reports a missing version, review the version file and run
`fnm install` from that project. No project files are changed by this setup. Oh My Zsh's fnm plugin supplies
completions; the explicit `fnm env` call supplies version switching.
`EDITOR` and `VISUAL` use `code --wait` when available, otherwise `vi`.

### Directory jumping with Pogo

The shell optionally enables [Pogo](https://github.com/filipbodor/pogo) when its
binary is installed and on PATH. Follow Pogo's installation instructions, then
open a new terminal. Use `j project` to jump to a learned directory, `j -` to go
back, or `j` to go home. Existing directories can be opened directly with
`j /path/to/project` and are learned as you visit them.

Pogo's history and any seeded favorites are private local data. They stay outside
this repository. Hop continues to open editor projects; Pogo changes the current
terminal directory.

### Running C++

`runc` lives in `.zshrc` and compiles with `g++-15 -std=c++17`:

```sh
runc solution
runc solution.cpp
runc "solution with spaces"
runc solution sample.txt
: > empty.txt
runc solution empty.txt   # Empty input, even if in.txt exists
```

An explicit input file takes priority over `in.txt`. Without an explicit input,
`in.txt` in the current directory is used when present; otherwise the program reads
from the terminal. Missing explicit input files fail before compilation. Install GCC 15 or change the
compiler in the function to match your setup. Compiler failures stop execution.

## Restore shared preferences

Run from the repository:

```sh
python3 scripts/restore.py                    # Show diffs; change nothing
python3 scripts/restore.py --apply            # Show diffs, then ask before applying
python3 scripts/restore.py --vscode --apply   # Also merge VS Code preferences
```

The default restores only `.zprofile`, `.zshrc`, and `.profile`. Local overrides,
Git identities and account routing, npm credentials, and SDK settings stay in
place. Existing files are copied into a private, timestamped directory under
`~/.local/state/dotfiles-backups/` before any replacement. File permissions are
preserved. Newly created files are recorded in `manifest.json` in that backup.
To undo a restore, copy the originals from that directory to the same relative
paths under your home; remove newly created files listed as `existed: false`.

The command refuses to replace symlinks. VS Code merging preserves unrelated
preferences and unrelated entries inside setting objects. If your settings use
comments or trailing commas (JSONC), merge them manually; the command stops before
writing anything. Review diffs locally because existing settings can contain
private values. `--home PATH` can target a disposable directory for testing.

## Git, editor, and npm

Merge the Git examples with your existing settings. Preserve account-specific
credential helpers, directory-based identity includes, and signing setup in local
configuration. The shared example includes `~/.gitconfig.local` and requires an
explicit identity through `user.useConfigOnly`.

Merge `git/ignore` into `~/.config/git/ignore`. Merge the VS Code settings into your
user settings rather than replacing unrelated preferences. The Code Runner
extension is optional; its C++ override uses GCC 15 and quotes paths. Python uses
`python3`. Other languages use the extension's defaults.

The npm file is an example, not an authentication backup. Replace `@your-scope`
with the package scope you use and supply `GITHUB_PACKAGES_TOKEN` through a secure
local mechanism when using the environment-variable example. Never commit a real
token or a shell file exporting its literal value.

## Repository boundaries

Only explicitly reviewed files are allowed by `.gitignore`. Credentials, account
stores, SSH keys, signing material, histories, caches, generated state, and actual
local override files are excluded. Review each new file before adding it. A
private repository also needs these exclusions.

## References

- [Zsh startup order](https://zsh.sourceforge.io/Doc/Release/Files.html)
- [fnm setup](https://github.com/Schniz/fnm#shell-setup)
- [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions)

- [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile)

## Measure shell startup

```sh
python3 scripts/benchmark-shell.py
python3 scripts/benchmark-shell.py --runs 10
```

This compares the installed interactive login configuration with a minimal Zsh
baseline, using one warm-up and repeated timed runs. It measures from your home
directory with inherited Node-manager paths removed. Local overrides are included;
no timing results or machine details are written to this repository. Startup hooks
run normally, so they may refresh their own caches. The minimal shell still reads
Zsh's unavoidable system `zshenv` file.

Measure before adding plugins and compare the medians on the same machine.
Timing does not cover prompt redraw or terminal rendering. Keep themes and plugins
that you use rather than changing them solely for appearance.

## Checks

```sh
python3 -m unittest discover -s tests -v
```

Restore tests use temporary homes. C++ tests compile real programs and require
Zsh and `g++-15`; they are skipped when these tools are unavailable.
