# Quick Reference: GitHub Package Distribution

## Project Evaluation Summary

✅ **Well-structured Python package:**
- Modern `pyproject.toml` with hatchling backend
- Proper `src/` layout
- Version management via `__init__.py`
- 3 CLI tools defined: `latex-processor`, `doi-validator`, `latex-diff`
- Test suite with pytest
- Using `uv` for dependency management

## Files Created

### 1. `.github/workflows/build-package.yml`
**Purpose:** Automatically builds and releases packages when you create a git tag

**What it does:**
- Builds wheel (`.whl`) and source distribution (`.tar.gz`)
- Uploads artifacts for 90 days
- Creates GitHub Release with packages attached

**Trigger:** Push a tag like `v0.2.0`

### 2. `.github/workflows/test.yml`
**Purpose:** Runs tests on every push/PR

**What it does:**
- Tests on Ubuntu and macOS
- Runs pytest with coverage
- Tests that the package builds correctly

### 3. `INSTALL.md`
**Purpose:** Complete installation guide for users

**Covers:**
- 5 different installation methods
- Installing from releases
- Installing from git
- Development installation
- Troubleshooting

### 4. `MANIFEST.in`
**Purpose:** Ensures correct files are included in distributions

### 5. `bin/release`
**Purpose:** Helper script to create releases easily

---

## How to Use

### Creating a Release

**Option 1: Using the helper script (easiest)**
```bash
# Create and push a release tag
./bin/release 0.3.0

# Dry run to preview
./bin/release 0.3.0 --dry-run

# With custom message
./bin/release 0.3.0 -m "Added new features and bug fixes"
```

**Option 2: Manually**
```bash
# 1. Update version in code
# Edit src/latex_tools/__init__.py: __version__ = "0.3.0"

# 2. Commit the version change
git add src/latex_tools/__init__.py
git commit -m "Bump version to 0.3.0"

# 3. Create and push tag
git tag -a v0.3.0 -m "Release version 0.3.0"
git push origin v0.3.0
```

### What Happens Next

1. **GitHub Actions triggers** (takes ~2-3 minutes)
   - Builds wheel and source distribution
   - Creates GitHub Release
   - Attaches packages to release

2. **Users can install** with:
   ```bash
   # From git
   pip install git+https://github.com/iheitlager/latex-tools.git@v0.3.0
   
   # From release wheel
   pip install https://github.com/iheitlager/latex-tools/releases/download/v0.3.0/latex_tools-0.3.0-py3-none-any.whl
   ```

### Monitoring

- **View builds:** https://github.com/iheitlager/latex-tools/actions
- **View releases:** https://github.com/iheitlager/latex-tools/releases
- **Download artifacts:** Available in Actions tab or Releases page

---

## Installation Methods (for end users)

### 1. From Git (always latest)
```bash
pip install git+https://github.com/iheitlager/latex-tools.git
```

### 2. From Specific Version
```bash
pip install git+https://github.com/iheitlager/latex-tools.git@v0.2.0
```

### 3. From Release Wheel (fastest)
```bash
pip install https://github.com/iheitlager/latex-tools/releases/latest/download/latex_tools-0.2.0-py3-none-any.whl
```

### 4. In requirements.txt
```txt
# requirements.txt
latex-tools @ git+https://github.com/iheitlager/latex-tools.git@v0.2.0
```

### 5. For Development
```bash
git clone https://github.com/iheitlager/latex-tools.git
cd latex-tools
pip install -e .
```

---

## Advantages Over PyPI

✅ **No PyPI account needed**
✅ **No package name conflicts**
✅ **Full control over distribution**
✅ **Automatic builds on release**
✅ **Free hosting on GitHub**
✅ **Easy to test pre-releases**
✅ **Works with private repos** (with authentication)

---

## Testing the Workflow

Before creating a real release, you can test:

```bash
# 1. Manually trigger the workflow
# Go to: https://github.com/iheitlager/latex-tools/actions
# Click: "Build and Release Package" → "Run workflow"

# 2. Test local build
uv build
# or
python -m build

# Check dist/ folder for .whl and .tar.gz files
ls -lh dist/

# 3. Test local install
pip install dist/*.whl
latex-processor --help
```

---

## Sharing With Others

### Public Repository
Simply share the installation command:
```bash
pip install git+https://github.com/iheitlager/latex-tools.git
```

### Private Repository
Users need authentication:
```bash
# Using GitHub token
pip install git+https://TOKEN@github.com/iheitlager/latex-tools.git

# Using SSH (if SSH keys configured)
pip install git+ssh://git@github.com/iheitlager/latex-tools.git
```

### Offline/Internal Distribution
1. Download `.whl` from GitHub Releases
2. Share file via internal network/email
3. Users install: `pip install latex_tools-0.2.0-py3-none-any.whl`

---

## Troubleshooting

### Build fails in GitHub Actions
- Check Python version compatibility (set to 3.14 in workflow)
- Ensure all dependencies in `pyproject.toml`
- Check build logs in Actions tab

### Can't find the release
- Releases only created when pushing tags starting with `v`
- Check: https://github.com/iheitlager/latex-tools/releases
- Verify tag was pushed: `git ls-remote --tags origin`

### Installation fails for users
- Ensure they're using `git+https://` prefix
- For private repos, they need repo access
- Check network/firewall isn't blocking GitHub

---

## Next Steps

1. **Test the workflow:**
   ```bash
   ./bin/release 0.2.1 --dry-run
   ```

2. **Create first automated release:**
   ```bash
   ./bin/release 0.2.1
   ```

3. **Monitor the build:**
   - Visit: https://github.com/iheitlager/latex-tools/actions

4. **Share installation instructions:**
   - Point users to `INSTALL.md`
   - Share the pip install command

5. **Optional: Add badges to README:**
   ```markdown
   ![Build](https://github.com/iheitlager/latex-tools/workflows/Build%20and%20Release%20Package/badge.svg)
   ![Tests](https://github.com/iheitlager/latex-tools/workflows/Test%20Package/badge.svg)
   ```
