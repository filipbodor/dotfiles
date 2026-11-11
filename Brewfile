# Shared command-line dependencies; installs no accounts or credentials.
brew "fnm"
brew "gh"
brew "git-lfs"
# Reuse an existing GCC 15 installation; provision the versioned formula on a new Mac.
brew "gcc@15" unless ["/opt/homebrew/bin/g++-15", "/usr/local/bin/g++-15"].any? { |path| File.executable?(path) }
# The standard-library scripts also work with an existing system Python 3.
brew "python" unless ["/usr/bin/python3", "/opt/homebrew/bin/python3", "/usr/local/bin/python3"].any? { |path| File.executable?(path) }
brew "thefuck"

# Oh My Zsh and its optional autosuggestions plugin are installed separately.
# VS Code is optional and can be installed through its normal distribution.
