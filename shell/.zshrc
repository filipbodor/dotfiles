# Keep local command wrappers ahead of system tools, without duplicate entries.
typeset -U path PATH
path=("$HOME/.local/bin" $path)

export ZSH="${ZSH:-$HOME/.oh-my-zsh}"
ZSH_THEME="bureau"
plugins=(git gh vscode xcode brew)
(( ! $+commands[thefuck] )) || plugins+=(thefuck)
(( ! $+commands[fnm] )) || plugins+=(fnm)
if [[ -r "${ZSH_CUSTOM:-$ZSH/custom}/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]]; then
    plugins+=(zsh-autosuggestions)
fi
[[ ! -r "$ZSH/oh-my-zsh.sh" ]] || source "$ZSH/oh-my-zsh.sh"

# One Node manager; follow each project's .nvmrc or .node-version.
if (( $+commands[fnm] )); then
    eval "$(fnm env --use-on-cd --version-file-strategy recursive --shell zsh)"
fi

if (( $+commands[code] )); then
    export EDITOR='code --wait'
else
    export EDITOR=vi
fi
export VISUAL="$EDITOR"

alias g++='g++ -std=c++17'

# Compile a C++ file; optional input overrides the in.txt fallback.
runc() {
    if (( $# < 1 || $# > 2 )); then
        print -u2 'Usage: runc <filename with or without .cpp> [input-file]'
        return 1
    fi
    local name="${1%.cpp}"
    if [[ -z "$name" || ! -f "$name.cpp" ]]; then
        print -u2 "C++ source not found: $name.cpp"
        return 1
    fi
    local input="${2-}"
    if (( $# == 2 )); then
        if [[ ! -f "$input" || ! -r "$input" ]]; then
            print -u2 "Input file not found or unreadable: $input"
            return 1
        fi
    elif [[ -f in.txt ]]; then
        input=in.txt
    fi
    if (( ! $+commands[g++-15] )); then
        print -u2 'runc requires g++-15; install GCC 15 or update the compiler in runc.'
        return 1
    fi
    local executable="$name"
    [[ "$executable" = /* ]] || executable="./$executable"
    # Make relative source paths unambiguous even when names begin with '-'.
    local source="$name.cpp"
    [[ "$source" = /* ]] || source="./$source"
    command g++-15 -std=c++17 "$source" -o "$executable" || return $?
    if [[ -n "$input" ]]; then
        "$executable" < "$input"
    else
        "$executable"
    fi
}

# Identities, optional SDK paths, and private aliases belong here.
[[ ! -r "$HOME/.zshrc.local" ]] || source "$HOME/.zshrc.local"
