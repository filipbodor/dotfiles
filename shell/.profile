# Optional environment helper installed by local tooling.
if [ -r "$HOME/.local/bin/env" ]; then
    . "$HOME/.local/bin/env"
fi
if [ -r "$HOME/.profile.local" ]; then
    . "$HOME/.profile.local"
fi
