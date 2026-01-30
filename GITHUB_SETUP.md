# GitHub Repository Setup Guide

This guide will help you set up the session-ctl repository on GitHub.

## Initial Steps

### 1. Initialize a New Git Repository

```bash
# Navigate to the session_controller directory
cd tools/session_controller

# Initialize git (if not already initialized)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Session Controller v1.0.0"
```

### 2. Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `session-ctl`
3. **Important**: Don't initialize with README, .gitignore, or license (we already have them)
4. Copy the repository URL

### 3. Push to GitHub

```bash
# Add the remote repository (replace with your URL)
git remote add origin https://github.com/YOUR_USERNAME/session-ctl.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Repository Settings

### Configure Repository

After creating the repository, update these settings:

1. **About section**:
   - Description: "Python CLI tool and library for programmatic control of Session Desktop"
   - Website: `https://getsession.org/`
   - Topics: `session`, `messenger`, `desktop`, `cli`, `python`, `cdp`, `sqlcipher`

2. **Features**:
   - Enable: Issues, Pull requests, Discussions, Actions, Projects, Wiki

3. **Branch protection** (optional):
   - Protect `main` branch
   - Require PR reviews before merging

## Update Repository URLs

Before pushing, update these URLs in the repository files:

### 1. Update README.md

Replace all instances of:
```
https://github.com/your-username/session-ctl
```

With your actual repository URL, e.g.:
```
https://github.com/johndoe/session-ctl
```

### 2. Update setup.py

Replace:
```python
url="https://github.com/your-username/session-ctl",
author="Session Controller Contributors",
```

With:
```python
url="https://github.com/johndoe/session-ctl",
author="John Doe",
```

### 3. Update pyproject.toml

Replace:
```toml
[project.urls]
Homepage = "https://github.com/your-username/session-ctl"
Documentation = "https://github.com/your-username/session-ctl#readme"
Repository = "https://github.com/your-username/session-ctl"
"Bug Reports" = "https://github.com/your-username/session-ctl/issues"
```

With your actual URLs.

## Create a Release

Once pushed to GitHub:

1. Go to **Releases** → **Create a new release**
2. Tag: `v1.0.0`
3. Release title: `v1.0.0 - Initial Release`
4. Description:
   ```markdown
   ## What's New

   Initial release of Session Controller!

   ### Features
   - Database mode for read-only access to Session's SQLCipher database
   - CDP mode for full control when Session is running with remote debugging
   - CLI tool with commands: list, messages, send, watch, search, media, info
   - Full-text search across messages using FTS5
   - Attachment decryption and download
   - Real-time message watching with polling
   - Support for multiple Session profiles
   - Python API for programmatic access

   ### Installation

   ```bash
   pip install git+https://github.com/johndoe/session-ctl.git
   ```

   Or:
   ```bash
   git clone https://github.com/johndoe/session-ctl.git
   cd session-ctl
   pip install -e .
   ```

   See [README.md](https://github.com/johndoe/session-ctl#readme) for full documentation.
   ```
5. Click **Publish release**

## Next Steps

### Add GitHub Topics

Go to repository settings and add topics:
- `session`
- `messenger`
- `desktop`
- `cli`
- `python`
- `cdp`
- `sqlcipher`
- `privacy`

### Set Up GitHub Actions (Optional)

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
        pip install -e .
    - name: Run tests
      run: |
        pytest
    - name: Lint
      run: |
        flake8 session_controller
        mypy session_controller
```

### Create a Badge for README.md

Add this badge to the top of your README.md:

```markdown
![PyPI version](https://img.shields.io/badge/version-1.0.0-blue)
```

## Testing the Installation

After pushing to GitHub, test that others can install it:

```bash
# Test installation from GitHub
pip install git+https://github.com/johndoe/session-ctl.git

# Test CLI
session-ctl --version  # or session-ctl info

# Test Python API
python -c "from session_controller import SessionDatabase; print('Success!')"
```

## Share Your Repository

Once everything is set up:

1. Tweet about it (if you use X/Twitter)
2. Share in Session community channels
3. Submit to [Awesome Python](https://github.com/vinta/awesome-python)
4. Mention in relevant issues/PRs in the Session Desktop repo

## Checklist

- [ ] Initialize git repository
- [ ] Update all URLs in README.md, setup.py, and pyproject.toml
- [ ] Create GitHub repository
- [ ] Push code to GitHub
- [ ] Create v1.0.0 release
- [ ] Add repository topics
- [ ] Test installation from GitHub
- [ ] Share with the community

---

Need help? Check the [GitHub documentation](https://docs.github.com/en).
