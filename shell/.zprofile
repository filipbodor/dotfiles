# Homebrew for Apple Silicon and Intel Macs.
if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi

typeset -U path PATH
path=("$HOME/.local/bin" $path)

# Machine-specific additions stay outside the repository.
[[ ! -r "$HOME/.zprofile.local" ]] || source "$HOME/.zprofile.local"
