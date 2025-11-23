# Installation Guide

## Install from GitHub without PyPI

There are several ways to install `latex-tools` directly from GitHub without publishing to PyPI:

### Option 1: Install from GitHub Release (Recommended)

When a release is created, GitHub Actions automatically builds wheel and source distribution files attached to the release.

```bash
# Install the latest release
pip install https://github.com/iheitlager/latex-tools/releases/latest/download/latex_tools-0.2.0-py3-none-any.whl

# Or install a specific version
pip install https://github.com/iheitlager/latex-tools/releases/download/v0.2.0/latex_tools-0.2.0-py3-none-any.whl
```

**Find the correct wheel URL:**
1. Go to https://github.com/iheitlager/latex-tools/releases
2. Click on the latest release
3. Right-click on the `.whl` file and copy the link
4. Use that URL with `pip install`

### Option 2: Install directly from git repository

```bash
# Install from main branch
pip install git+https://github.com/iheitlager/latex-tools.git

# Install from a specific branch
pip install git+https://github.com/iheitlager/latex-tools.git@develop

# Install from a specific tag
pip install git+https://github.com/iheitlager/latex-tools.git@v0.2.0

# Install from a specific commit
pip install git+https://github.com/iheitlager/latex-tools.git@abc1234
```

### Option 3: Install from downloaded release artifacts

If you download the build artifacts from GitHub Actions:

```bash
# Download the .whl file from the workflow run
pip install latex_tools-0.2.0-py3-none-any.whl
```

### Option 4: Install in development mode

For contributors or if you want to modify the code:

```bash
# Clone the repository
git clone https://github.com/iheitlager/latex-tools.git
cd latex-tools

# Install in editable mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Option 5: Using uv (modern Python package manager)

```bash
# Install from GitHub
uv pip install git+https://github.com/iheitlager/latex-tools.git

# Or clone and install locally
git clone https://github.com/iheitlager/latex-tools.git
cd latex-tools
uv sync
```

## Verify Installation

After installation, verify the tools are available:

```bash
# Check installed version
pip show latex-tools

# Try the command-line tools
latex-processor --help
doi-validator --help
latex-diff --help
```

## Creating a Release

To trigger the build-and-release workflow:

### Method 1: Using git tags (Recommended)

```bash
# Create and push a version tag
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

This automatically:
1. Triggers the GitHub Actions workflow
2. Builds wheel and source distributions
3. Creates a GitHub Release with the packages attached

### Method 2: Manual workflow dispatch

1. Go to: https://github.com/iheitlager/latex-tools/actions
2. Click on "Build and Release Package"
3. Click "Run workflow"
4. Enter version (optional) and click "Run workflow"

This builds the package and uploads artifacts (but doesn't create a release).

## Updating the Package

When you install from git, the package is pinned to that commit. To update:

```bash
# Upgrade to latest from git
pip install --upgrade git+https://github.com/iheitlager/latex-tools.git

# Or if installed from a wheel, download and install the new version
pip install --upgrade https://github.com/iheitlager/latex-tools/releases/latest/download/latex_tools-0.2.0-py3-none-any.whl
```

## Uninstall

```bash
pip uninstall latex-tools
```

## Distributing Privately

### Option A: GitHub as a package repository

You can add GitHub as a package source in `requirements.txt`:

```txt
# requirements.txt
latex-tools @ git+https://github.com/iheitlager/latex-tools.git@v0.2.0
```

Then users can install with:
```bash
pip install -r requirements.txt
```

### Option B: Share the wheel file directly

1. Download the `.whl` file from a GitHub Release
2. Share it via email, cloud storage, or internal file server
3. Users install with: `pip install latex_tools-0.2.0-py3-none-any.whl`

### Option C: Use GitHub Packages (advanced)

You can publish to GitHub Packages (GitHub's package registry) which provides a pip-compatible index.

## Troubleshooting

### "ERROR: Could not find a version that satisfies the requirement"

Make sure you're using the full GitHub URL with `git+https://`:
```bash
pip install git+https://github.com/iheitlager/latex-tools.git
```

### SSL Certificate errors

If you get SSL errors, try:
```bash
pip install --trusted-host github.com git+https://github.com/iheitlager/latex-tools.git
```

### Authentication required for private repos

For private repositories:
```bash
# Using GitHub personal access token
pip install git+https://YOUR_TOKEN@github.com/iheitlager/latex-tools.git

# Or using SSH
pip install git+ssh://git@github.com/iheitlager/latex-tools.git
```
