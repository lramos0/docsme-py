# docsme-py

> Generate a yearly work summary from your git commits — with optional AI-powered elaboration.

---

## ✨ Features

* 🐍 Python-based CLI
* ⚡ Fast and lightweight
* 🔍 Scans all git repos under a directory
* 📊 Builds structured commit data using pandas
* 🧠 Optional AI elaboration (Cursor / Claude / manual)
* 🛠️ First-time interactive setup for easy onboarding

---

## 🚀 Installation

### Install from PyPI

```bash
pip install docsme
```

### Install from source

```bash
git clone https://github.com/yourname/docsme-py.git
cd docsme-py
python -m venv venv
source venv/bin/activate
pip install -e .
```

---

## 🧪 First-Time Setup (New)

Simply run:

```bash
docsme
```

If no configuration is found, docsme will guide you through an interactive setup:

```
Thank you for using docsme, proceed with this interactive setup.

what is your github user_name?
> your-username

want me to find where your projects are stored? [y/n]
> y

I found these directories named "projects":
1. ~/projects
2. ~/code/projects

Select one by number:
> 1

please let me know your preferences for AI elaboration:
a. do not elaborate unless I pass --use-agent
b. elaborate with cursor by default
c. elaborate with claude by default
> c
```

Your configuration will be saved locally and reused automatically.

---

## 📦 Usage

### Default (after setup)

```bash
docsme
```

Generates a report using:

* your configured projects directory
* your GitHub username
* the current year

---

### Specify a directory manually

```bash
docsme ~/projects
```

---

### Filter commits

```bash
docsme ~/projects --since "2024-01-01" --until "2024-12-31"
```

```bash
docsme ~/projects --author "your-email@example.com"
```

---

### Output results

```bash
docsme ~/projects --output report.csv
docsme ~/projects --output report.json
docsme ~/projects --output report.parquet
```

---

### Preview output

```bash
docsme ~/projects --preview 10
```

---

### Enable AI elaboration

```bash
docsme --use-agent
```

Behavior depends on your setup preference:

* `manual` → only runs when `--use-agent` is passed
* `cursor` → enabled by default
* `claude` → enabled by default

---

### Re-run setup

```bash
docsme --setup
```

---

## ⚙️ Configuration

Docsme stores your preferences in:

```bash
~/.config/docsme/config.json
```

Example:

```json
{
  "github_username": "your-username",
  "projects_root": "/Users/you/projects",
  "ai_elaboration": "claude"
}
```

These values are also exposed as runtime environment variables:

* `DOCSME_GITHUB_USERNAME`
* `DOCSME_PROJECTS_ROOT`
* `DOCSME_AI_ELABORATION`

---

## 🧠 How it works

Docsme:

1. Recursively finds git repositories under your projects directory
2. Runs `git log` across each repo
3. Builds a pandas DataFrame of commits
4. Sorts and filters commit history
5. Outputs structured data or feeds it into AI workflows

---

## 🔄 Update

```bash
pip install --upgrade docsme
```

---

## ❌ Uninstall

```bash
pip uninstall docsme
```

---

## 🛠️ Development

```bash
git clone https://github.com/yourname/docsme-py.git
cd docsme-py
python -m venv venv
source venv/bin/activate
pip install -e .
```

---

## 🚨 Notes

* Requires Python 3.9+
* Requires `git` installed and available in PATH
* Only repositories with a `.git` folder will be detected

---

## 📄 License

MIT © lramos0

