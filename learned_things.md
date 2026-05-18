# Things I Learned

---

## Shell & Environment Setup

---

**Q: What is `.zshrc`?**

- A hidden script file that lives at `~/.zshrc` (your home directory)
- Runs automatically every time you open a new terminal window
- Think of it as "startup instructions for your terminal"
- Tools that need to configure your environment (pyenv, nvm, etc.) all add their lines here
- The `.` prefix means it's hidden — `ls -a` shows it, plain `ls` doesn't

---

**Q: What is `PATH`?**

- An environment variable holding a list of directories, separated by colons
- Example: `/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin`
- When you type any command, your shell searches these directories left to right for a matching executable
- First match wins — order matters

```
You type: python3
Shell checks: /opt/homebrew/bin → not here
              /usr/local/bin    → not here
              /usr/bin          → found it → run it → stop
```

- If nothing found anywhere: `command not found: python3`

---

**Q: When does the shell actually search PATH?**

- Every single time you type a command and press Enter
- Not a one-time thing — every `pip install`, `git commit`, `docker run` triggers a fresh PATH search
- PATH is just a variable — it gets read on demand, not cached

---

**Q: Is PATH only used in the terminal?**

- No — PATH exists at the **process** level, not the terminal level
- Every process on your computer has its own copy of environment variables including PATH

| Where | Uses PATH? |
|---|---|
| Terminal commands | Yes |
| Background cron jobs | Yes |
| VS Code running your linter | Yes |
| GitHub Actions CI runner | Yes |
| Docker containers | Yes (their own PATH) |
| FastAPI spawning a subprocess | Yes |

- Common real bug: something works in terminal but breaks in VS Code because VS Code was launched before `.zshrc` ran and has a different PATH

---

**Q: What does `export` do?**

- Sets an environment variable AND makes it visible to child processes
- Without `export`: variable exists only in current shell, disappears when shell exits, child processes can't see it
- With `export`: any process spawned from this shell inherits a copy

```bash
MYVAR="hello"         # private to this shell only
export MYVAR="hello"  # passed down to all child processes
```

---

**Q: What are child processes?**

- Every running program = a process (has its own memory, variables, state)
- When a process starts another program → that new program is a **child process**
- The child gets a **copy** of the parent's environment at the moment it's spawned

```
Terminal (parent)
    └── python3 script.py (child)
            └── subprocess.run("git ...") (grandchild)
```

- Key point: copy, not a reference — changes in the child don't affect the parent, and vice versa after spawn
- This is why `export` exists: without it, the variable never gets packed into the copy the child receives
- This is also why `.env` files, `docker-compose.yml` environment sections, and GitHub Actions secrets all exist — they're all solving the same problem: getting the right variables into the right process

---

**Q: In line 1 of the pyenv setup, you set `PYENV_ROOT` but don't include `$PATH` — does that overwrite PATH?**

- No. Line 1 creates a **brand new variable** called `PYENV_ROOT` — it never touches PATH
- Only line 2 touches PATH
- Analogy: declaring `x = 5` in Python doesn't overwrite any other variable

```bash
# Line 1 — creates new variable, PATH untouched
export PYENV_ROOT="$HOME/.pyenv"

# Line 2 — only line that modifies PATH
export PATH="$PYENV_ROOT/bin:$PATH"
#                            ^^^^^ old PATH fully preserved here
```

---

**Q: Line 2 uses `$PYENV_ROOT` — but that was set in line 1. Is it still available?**

- Yes — `.zshrc` runs line by line, top to bottom, at terminal startup
- By the time line 2 runs, `PYENV_ROOT` is already defined from line 1
- After line 2, PATH looks like:

```
/Users/dionfernandes/.pyenv/bin : /opt/homebrew/bin : /usr/local/bin : ...
          (new, first)                    (old PATH, fully preserved)
```

- pyenv's directory is first → it intercepts `python3` before system Python gets a chance

---

**Q: Why did `python3 --version` still show 3.9.6 right after adding the pyenv lines?**

- `echo >> ~/.zshrc` only **writes text to a file** — it does not execute anything
- The current terminal session already read `.zshrc` when it first opened (before those lines existed)
- From that session's perspective, those lines never existed

Two ways to fix:
1. `source ~/.zshrc` — re-reads and executes the file inside the **current** shell
2. Open a new terminal — fresh shell reads `.zshrc` from scratch on startup

---

**Q: What does `source` do vs running a script normally?**

```bash
bash ~/.zshrc    # spawns NEW child process → runs script there → exits
                 # current shell is completely unchanged

source ~/.zshrc  # runs script directly inside current shell process
                 # PATH changes, exports, etc. actually stick
```

- `source` is the only way to modify the environment of an already-running shell from within it
- This principle applies everywhere: servers restart after config changes for the same reason — you can't reach into a running process and change its memory just by editing a file

---

## Project Structure

---

**Q: What are `__init__.py` files?**

- Empty files that tell Python "this directory is a importable package"
- Without them, cross-file imports fail:

```python
# This fails if backend/app/schemas/ has no __init__.py
from app.schemas.financial import FilingCitation
```

- Every Python directory in this project has one
- You never put code in them (for this project) — their existence is the signal

---

**Q: Why is `.env` in `.gitignore` but `.env.example` is committed?**

- `.env` = real API keys → **never commit** → anyone with your git history can steal them
- `.env.example` = template with placeholder values → safe to commit → tells collaborators what variables to set up
- Workflow: clone repo → copy `.env.example` to `.env` → fill in real values → `.env` stays local forever

---

**Q: Why are `data/` and `.venv/` in `.gitignore`?**

| Folder | Why ignored |
|---|---|
| `data/` | Raw SEC filings = hundreds of MB. Git is for source code, not downloaded data. Regenerate by running the pipeline. |
| `.venv/` | Thousands of installed library files. Regenerate anytime with `pip install -r requirements.txt`. Committing it would bloat the repo massively. |

---

## Pyenv & Version Management

---

**Q: What do these three pyenv setup lines do?**

```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

- **Line 1:** Creates a variable pointing to where pyenv stores everything (`~/.pyenv`)
- **Line 2:** Adds pyenv's bin directory to the front of PATH so system finds pyenv before system Python
- **Line 3:** The critical line — runs pyenv's initialization script, which **adds `~/.pyenv/shims` to the front of PATH**

After these run, PATH looks like:
```
~/.pyenv/shims : ~/.pyenv/bin : /usr/local/bin : /usr/bin : ...
(shims added by   (bin added by  (old PATH preserved)
 line 3)          line 2)
```

---

**Q: What are shims and why do we need them?**

- **Shims** = lightweight wrapper scripts in `~/.pyenv/shims/` that intercept commands like `python3`, `pip`, etc.
- When you run `python3`, the system finds the shim first (because shims are first in PATH)
- The shim's job: decide **which actual Python version to use** based on:
  1. `.python-version` file in current directory (set by `pyenv local`)
  2. `.python-version` file in parent directories
  3. Global default (set by `pyenv global`)

```
You type: python3
  ↓
System searches PATH, finds ~/.pyenv/shims/python3 first
  ↓
Shim checks: is there a .python-version file here? → check parent dirs
  ↓
If found: run that version. If not found: run global default
  ↓
Actual Python runs
```

- Without shims, you'd have to manually switch Python versions or use long paths like `/Users/.../.pyenv/versions/3.11.0/bin/python3`

---

**Q: What happens if I don't use `pyenv local` and just have the three setup lines?**

Every terminal will use your **global default version** (set by `pyenv global 3.11.x` once):
- No `.python-version` file in current directory → shim skips step 1 & 2
- Falls back to global default → same version in every terminal

This is perfect for projects where everyone uses the same Python version. Only use `pyenv local` when *this specific directory* needs a different version.

---

**Q: Is shims folder explicitly added to PATH in those lines?**

- No, not explicitly written out
- `eval "$(pyenv init -)"` (line 3) does it automatically behind the scenes
- It runs a pyenv script that adds `~/.pyenv/shims` to the front of PATH
- You don't see it written out, but it happens

---

**Q: Are shims the only folder in pyenv?**

No. The pyenv directory structure:
```
~/.pyenv/
├── bin/          (pyenv command itself)
├── shims/        (wrapper scripts for python, pip, etc.)
├── versions/     (where actual Python versions are installed)
└── ...other files
```

---
