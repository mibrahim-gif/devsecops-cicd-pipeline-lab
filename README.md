
# DevSecOps Security CI/CD Pipeline Lab

A small CI/CD pipeline that automatically checks every code change for exposed secrets, insecure code, and broken functionality before it is trusted.

Built and tested from **Kali Linux**, hosted on **GitHub**, automated with **GitHub Actions**.

## Pipeline overview

```
Kali Linux
    ↓
Python application
    ↓
GitHub
    ↓
GitHub Actions
    ↓
┌──────────────────┐
│ Gitleaks         │ → Detect exposed secrets
│ Semgrep          │ → Detect insecure code
│ Pytest           │ → Make sure app works
└────────┬─────────┘
         ↓
   Security Gate
      ↓       ↓
   FAIL ❌   PASS ✅
```

The pipeline runs on every push to `main` and on every pull request.

## What each tool does

| Tool | Question it answers | What it reads |
|---|---|---|
| Gitleaks | Did I accidentally commit a password or key? | The full git history |
| Semgrep | Is any code written in a dangerous way? | Python source files |
| Pytest | Does the app still behave correctly? | `test_app.py`, which runs `app.py` |

A program can pass one check and fail another. Insecure code can work perfectly (passes pytest, fails Semgrep), and safe code can be broken (passes Semgrep, fails pytest). That is why the pipeline uses all three.

## Repository structure

```
devsecops-security-lab/
├── .github/
│   └── workflows/
│       └── security.yml    # The pipeline definition
├── app.py                  # The application
├── test_app.py             # Automated test for the application
├── vulnerable.py           # Intentionally insecure code (lab bait for Semgrep)
├── .gitignore
└── README.md
```

### Files

- **app.py** prints `Corporate Security Application`.
- **test_app.py** runs `app.py` and checks that the expected text is printed.
- **vulnerable.py** contains `subprocess.call(user_input, shell=True)`. This is **deliberately insecure** (command injection risk) to prove Semgrep catches it. Never use this pattern in real code.
- **security.yml** defines the GitHub Actions workflow.

## How the workflow works

The workflow has one job (`security`) with these steps:

1. **Checkout** with `fetch-depth: 0` (full history, required by Gitleaks).
2. **Gitleaks** scans for secrets.
3. **Set up Python 3.12.**
4. **Install tools** (`pip install semgrep pytest`).
5. **Semgrep** runs `semgrep scan --config p/python --error`.
6. **Pytest** runs `pytest -v`.

Key settings:

- `--error` makes Semgrep exit with a failure when it finds anything, so the job turns red.
- `if: always()` on the later steps means every check runs even if an earlier one fails, so one run shows all results.
- If **any** step fails, the whole job fails. The job result is the security gate.

## Running locally (Kali Linux)

Test before pushing to avoid waiting on GitHub.

```bash
cd ~/devsecops-security-lab

python3 -m venv .venv
source .venv/bin/activate
pip install pytest semgrep

pytest -v
semgrep scan --config p/python --error
gitleaks detect          # if gitleaks is installed
```

Run the app itself:

```bash
python3 app.py
```

## Running the pipeline on GitHub

```bash
git add <files>
git commit -m "Describe your change"
git push
```

Then open the repo on GitHub → **Actions** → click the newest run → expand each step to read its log.

## Expected results

| State of the repo | Gitleaks | Semgrep | Pytest | Gate |
|---|---|---|---|---|
| `vulnerable.py` present | ✅ | ❌ | ✅ | **FAIL** |
| `vulnerable.py` removed | ✅ | ✅ | ✅ | **PASS** |

### Demo: PASS and FAIL paths

Remove the bait to see PASS:

```bash
git rm vulnerable.py
git commit -m "Remove vulnerable.py"
git push
```

Restore it to see FAIL again:

```bash
git revert HEAD --no-edit
git push
```

## Making the gate enforce

By default a failed check is only a warning. To block bad code from reaching `main`:

1. GitHub → **Settings** → **Branches** → **Add branch protection rule**
2. Branch name pattern: `main`
3. Enable **Require status checks to pass before merging**
4. Select the `security` check
5. Save

Now open a pull request from a branch containing bad code and the merge button stays blocked until the checks pass.

## Screenshots



## Lessons learned / troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Gitleaks fails with "unknown revision" and exit code 1 | GitHub's default checkout is shallow (1 commit), so the commit range is missing | Add `fetch-depth: 0` to the checkout step |
| Pytest fails with exit code 5 | No test files found (pytest looks for `test_*.py`) | Create `test_app.py` |
| `NameError: name 'runypy' is not defined` | Typo in the module name | Spell it `runpy` |
| `AssertionError` showing `Coporate` vs `Corporate` | Typo in the expected text | Match the text exactly |
| Later steps skipped after a failure | Steps stop after the first failure by default | Add `if: always()` |
| Terminal shows `dquote>` or `heredoc>` | Unclosed quote, or the closing `EOF` is missing | Press Ctrl+C and retype, or use `nano` |
| Job stuck on "Waiting for a runner" | GitHub is assigning a hosted runner | Wait a few minutes, or cancel and re-run |
| Semgrep reports a finding on `vulnerable.py` | Working as intended | Remove or fix the file |

### Pytest exit codes

| Code | Meaning |
|---|---|
| 0 | All tests passed |
| 1 | One or more tests failed |
| 5 | No tests were found |



## Disclaimer

`vulnerable.py` exists only for education. It demonstrates a command injection flaw and should never be run with untrusted input or deployed.
