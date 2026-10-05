# PyMFEM on Windows with WSL2 + VS Code + GitHub

Setup guide and reference notes for running [PyMFEM](https://github.com/mfem/PyMFEM) on Windows through WSL2 (Ubuntu 24.04), developing in VS Code, and versioning the work on GitHub.

- **Author:** Adilton Pereira ([@AdtPereira](https://github.com/AdtPereira))
- **Project repo:** [github.com/AdtPereira/pymfem-work](https://github.com/AdtPereira/pymfem-work)
- **Date:** 1 October 2026 (updated 2 October 2026: virtual environment procedure §4.3, WSL checks §3, plot windows §6, using PyMFEM examples §10, viewing `.mesh`/`.gf` files with matplotlib and GLVis §11, setting up a second computer and SSH key status §12; Example 1 figure and `ex1` details §10.8, GLVis 3D cutting-plane keys §11.5)
- **Tested with:** Windows + WSL2, Ubuntu 24.04, Python 3.12.3, mfem 4.10.0, numpy 2.5.3, matplotlib 3.11.2, numba 0.68.0

---

## Contents

1. [What is PyMFEM](#1-what-is-pymfem)
2. [Install WSL2 and Ubuntu](#2-install-wsl2-and-ubuntu)
3. [The Ubuntu terminal](#3-the-ubuntu-terminal)
4. [Install system packages, create the virtual environment, install PyMFEM](#4-install-system-packages-create-the-virtual-environment-install-pymfem)
5. [Configure VS Code for WSL](#5-configure-vs-code-for-wsl)
6. [Run the first example (Poisson)](#6-run-the-first-example-poisson)
7. [Project organization (own repo vs. fork)](#7-project-organization-own-repo-vs-fork)
8. [Git and SSH setup in WSL](#8-git-and-ssh-setup-in-wsl)
9. [Publish the project on GitHub](#9-publish-the-project-on-github)
10. [Using PyMFEM's examples and data in your project](#10-using-pymfems-examples-and-data-in-your-project)
11. [Viewing .mesh and .gf files (matplotlib, GLVis)](#11-viewing-mesh-and-gf-files-matplotlib-glvis)
12. [Setting up a second computer](#12-setting-up-a-second-computer)
13. [Optional: parallel (MPI) build from source](#13-optional-parallel-mpi-build-from-source)
14. [Troubleshooting](#14-troubleshooting)
15. [Quick reference](#15-quick-reference)

---

## 1. What is PyMFEM

PyMFEM is the Python binding for [MFEM](https://mfem.org), a high-performance parallel finite element (FEM) library written in C++. Its installer builds MFEM and the Python wrapper together.

Two ways to install it (from the PyMFEM README):

| Method | Command | Notes |
|---|---|---|
| Prebuilt (serial) | `pip install mfem` | Binary wheels on **Linux** only. Fast. Import as `mfem.ser`. |
| From source | `pip install ./ -C"with-parallel=Yes" --verbose` | Inside a clone of the repo. Enables MPI (`mfem.par`), GPU, GSLIB, SuiteSparse, libCEED, LAPACK. Slow (compiles everything). See `INSTALL.md`. |

> **Key point:** pip only installs quickly when a prebuilt wheel exists for your Python version; otherwise it tries a long build from source. The README says Python 3.8–3.12, but that is out of date: **mfem 4.10.0 has Linux wheels for Python 3.11, 3.12, 3.13 and 3.14** (checked on PyPI, 2 Oct 2026). Ubuntu 24.04's Python 3.12 is used here.

---

## 2. Install WSL2 and Ubuntu

On **Windows**:

1. Open PowerShell **as administrator** and run:
   ```powershell
   wsl --install -d Ubuntu-24.04
   ```
2. Reboot.
3. Open Ubuntu (see next section). On first launch, create a Linux **username** and **password**. This password is used for `sudo`.
4. Install **VS Code on Windows** (not inside WSL).
5. In VS Code, install the **WSL** extension (by Microsoft).

---

## 3. The Ubuntu terminal

### How to open it

- **Start menu:** press the Windows key, type `Ubuntu`, click it.
- **Windows Terminal** (recommended): open *Terminal*, click the **⌄** arrow next to **+** and choose *Ubuntu*. It can be set as default under *Settings → Startup → Default profile*.
- **From PowerShell/CMD:** type `wsl` (or `wsl -d Ubuntu-24.04`).
- **Inside VS Code:** when connected to WSL (bottom-left shows `WSL: Ubuntu-24.04`), open *Terminal → New Terminal* (`` Ctrl+` ``).

### Reading the prompt

```
(.venv) adilt@adilton:~/projects/pymfem-work$
```

| Part | Meaning |
|---|---|
| `(.venv)` | A Python virtual environment is active (appears after `source .venv/bin/activate`) |
| `(base)` | Instead of `(.venv)`: a **conda** environment is active. Run `conda deactivate` before working on this project (see §4.3) |
| `adilt` | Linux username |
| `@adilton` | Computer name (hostname) |
| `~/projects/pymfem-work` | Current folder. `~` = home folder `/home/adilt` |
| `$` | Normal user (`#` would mean root/admin) |

Only type the command **after** the `$`; the prompt itself is printed by the terminal.

When `sudo` asks for the password, **nothing is shown while typing**. That is normal.

### Windows commands from Ubuntu, and checking WSL

`wsl` is a **Windows** command. Inside Ubuntu it gives `Command 'wsl' not found` (do **not** run the suggested `sudo apt install wsl`; that is an unrelated Linux package). Add `.exe` and WSL runs the Windows program:

```bash
wsl.exe --status        # default distro and WSL version
wsl.exe --version       # WSL, kernel and WSLg versions
wsl.exe -l -v           # installed distros; VERSION column must be 2
```

The same commands work in PowerShell without `.exe`.

Network setup (matters for live GLVis streaming, §11.7):

```bash
ip addr show eth0               # WSL's own IP address (often 172.x.x.x)
wslinfo --networking-mode       # "nat" (default) or "mirrored"
cat /mnt/c/Users/adilt/.wslconfig 2>/dev/null   # WSL settings file, if any
```

- **nat** (default): WSL has its own IP; `localhost` in Ubuntu is **not** Windows.
- **mirrored**: WSL shares Windows' network; `localhost` works both ways.
- `wslinfo` not found → older WSL; update with `wsl --update` in PowerShell.

Windows drives are visible in Ubuntu under `/mnt/` (`C:\glvis` = `/mnt/c/glvis`), and the Linux files are visible in Windows Explorer at `\\wsl.localhost\Ubuntu-24.04\home\adilt\...`. Convert between the two forms with `wslpath`:

```bash
wslpath -w ~/projects/pymfem-work     # → \\wsl.localhost\Ubuntu-24.04\home\adilt\projects\pymfem-work
wslpath -u 'C:\glvis'                 # → /mnt/c/glvis
```

---

## 4. Install system packages, create the virtual environment, install PyMFEM

All commands in this section run in the **Ubuntu terminal**. Do the steps in order: 4.1 → 4.2 → 4.3 → 4.4.

### 4.1 Install the system packages (one time)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip python3-tk git build-essential
```

| Command | Purpose |
|---|---|
| `sudo` | Run as administrator (asks for the Linux password) |
| `apt update` | Refresh Ubuntu's list of available packages |
| `&&` | Run the next command only if the previous one succeeded |
| `apt upgrade -y` | Install updates; `-y` answers "yes" automatically |
| `python3` | Python interpreter |
| `python3-venv` | Ability to create virtual environments (**required for 4.3**) |
| `python3-pip` | pip, the Python package installer |
| `python3-tk` | GUI toolkit used by matplotlib to open plot windows |
| `git` | Version control; downloads repositories |
| `build-essential` | C/C++ compiler and tools (needed if something must be compiled) |

### 4.2 Create the project folder

```bash
mkdir -p ~/projects/pymfem-work
cd ~/projects/pymfem-work
```

- `mkdir -p` creates the folder (and `projects` if missing); no error if it already exists.
- `cd` enters it. The prompt changes to `...:~/projects/pymfem-work$`.

> Keep projects inside the Linux home (`~/...`), **not** under `/mnt/c/...`. Access across the Windows/Linux boundary is much slower and can cause permission problems.

### 4.3 Create and activate the virtual environment (`.venv`)

A **virtual environment** is a private copy of Python inside the project folder. Packages installed while it is active go into it, not into Ubuntu's system Python.

Why it is needed:
- Ubuntu 24.04 **blocks** `pip install` into the system Python (`error: externally-managed-environment`).
- Each project keeps its own package versions, without conflicts.
- If something breaks, the environment can be deleted and recreated in a minute.

#### Step 1: Make sure the system Python 3.12 will be used

```bash
which python3        # must print /usr/bin/python3
python3 --version    # must print Python 3.12.x
```

If the prompt starts with **`(base)`**, a **conda** (Anaconda/Miniconda) environment is active and `python3` may point to conda's Python instead of Ubuntu's. The `.venv` would then be built on conda's Python, mixing the two setups. Turn it off first:

```bash
conda deactivate                              # for this terminal
conda config --set auto_activate_base false   # optional: stop it starting in every new terminal
```

#### Step 2: Create the environment

```bash
cd ~/projects/pymfem-work
/usr/bin/python3 -m venv .venv
```

- `-m venv` runs Python's built-in *venv* module.
- `.venv` is the folder it creates (a dot at the start makes it hidden).
- Using the full path `/usr/bin/python3` guarantees Ubuntu's Python 3.12 is used, even if conda or another Python is on the PATH.
- It takes a few seconds and prints nothing when it succeeds.

Check it exists:
```bash
ls -a                   # .venv appears in the list
ls .venv/bin            # activate, pip, python, python3, ...
```

#### Step 3: Activate it

```bash
source .venv/bin/activate
```

The prompt now starts with **`(.venv)`**:
```
(.venv) adilt@adilton:~/projects/pymfem-work$
```

Confirm that `python` and `pip` now come from the environment:
```bash
which python         # /home/adilt/projects/pymfem-work/.venv/bin/python
python --version     # Python 3.12.x
which pip            # /home/adilt/projects/pymfem-work/.venv/bin/pip
```

Inside an active environment, `python` and `pip` (without the `3`) refer to the environment's copies.

#### Step 4: Upgrade pip inside the environment

```bash
pip install --upgrade pip
```

#### Everyday use

| Action | Command |
|---|---|
| Activate (each new terminal) | `cd ~/projects/pymfem-work && source .venv/bin/activate` |
| Leave the environment | `deactivate` |
| See what is installed | `pip list` |
| Check which Python is used | `which python` |
| Save the installed packages | `pip freeze > requirements.txt` (or keep a hand-written list, see §7) |

VS Code activates the environment automatically in new terminals once `.venv/bin/python` is selected as the interpreter (§5.3).

#### Delete and recreate the environment

`.venv` can always be rebuilt; it is **not** committed to Git (see `.gitignore` in §7).

```bash
cd ~/projects/pymfem-work
deactivate 2>/dev/null           # leave it if active
rm -rf .venv                     # delete
/usr/bin/python3 -m venv .venv   # create again
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt  # reinstall the project's packages
```

Do this if the folder was moved or renamed (a venv stores its absolute path), or if packages got into a bad state.

### 4.4 Install PyMFEM and test

With `(.venv)` showing in the prompt:

```bash
pip install mfem numpy matplotlib numba
python -c "import mfem.ser as mfem; print('MFEM OK')"
```

| Package | Purpose |
|---|---|
| `mfem` | PyMFEM, serial version (prebuilt wheel for Python 3.12) |
| `numpy` | Arrays; PyMFEM returns data as numpy arrays |
| `matplotlib` | Plotting |
| `numba` | JIT compiler, used for custom coefficient functions (`@mfem.jit.scalar`) |

`python -c "..."` runs a one-line Python program. **`MFEM OK`** means the installation works.

### 4.5 Summary: the whole sequence

```bash
# 4.1 system packages (one time)
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip python3-tk git build-essential

# 4.2 project folder
mkdir -p ~/projects/pymfem-work && cd ~/projects/pymfem-work

# 4.3 virtual environment
conda deactivate 2>/dev/null      # only matters if "(base)" is shown
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
which python                      # .../pymfem-work/.venv/bin/python
pip install --upgrade pip

# 4.4 PyMFEM
pip install mfem numpy matplotlib numba
python -c "import mfem.ser as mfem; print('MFEM OK')"
```

---

## 5. Configure VS Code for WSL

### 5.1 Open the project from WSL

```bash
cd ~/projects/pymfem-work
code .
```

The bottom-left corner must show **`WSL: Ubuntu-24.04`**.

Alternatively: *File → Open Folder* → `/home/adilt/projects/pymfem-work`.

> Opening the folder as the workspace matters: it is what lets VS Code detect the `.venv` automatically.

### 5.2 Extensions (install **in WSL**)

Extensions installed on Windows appear greyed out with a ⚠ and the button **"Install in WSL: Ubuntu-24.04"**. They must be installed on the WSL side to see the Linux Python.

| Extension | Needed? |
|---|---|
| **Python** (Microsoft) | **Yes**. Automatically brings Pylance, Python Debugger and Python Environments |
| **Jupyter** (Microsoft) | Recommended (notebooks with inline plots) |
| autopep8 | Optional (auto-formatting) |
| Pylint | Optional (linting, can be noisy) |
| Python Indent, Python for VSCode (deprecated), Python Extension Pack, autoDocstring | Not needed |

### 5.3 Select the interpreter

`Ctrl+Shift+P` → **Python: Select Interpreter** → choose `./.venv/bin/python`.

If the venv is not listed (only `/usr/bin/python3` appears):

- **Do not** pick `/usr/bin/python3`; that is the system Python and `mfem` is not installed there.
- Choose **Enter interpreter path...** and type:
  ```
  /home/adilt/projects/pymfem-work/.venv/bin/python
  ```
- The status bar should then show something like `3.12.3 ('.venv': venv)`.

A `C:\Users\...\python3.12.exe` entry is the Windows Python; ignore it.

### 5.4 Workspace settings

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

Create it with:
```bash
mkdir -p .vscode && code .vscode/settings.json
```

### 5.5 The `code` command

`code` opens things in VS Code:

| Command | Effect |
|---|---|
| `code .` | Open the current folder |
| `code ex1.py` | Open `ex1.py`; if it doesn't exist, an empty tab opens and the file is created on save (`Ctrl+S`) |

Other ways to create a file: the **New File** icon in the Explorer, *File → New File*, or `touch ex1.py` in the terminal.

### 5.6 Seeing PyMFEM and your project side by side

Opening the parent folder `~/projects` shows both `PyMFEM/` and `pymfem-work/`, but then VS Code ignores `pymfem-work/.vscode/settings.json` (settings are read only from the workspace root) and interpreter detection is less reliable.

Better: a **multi-root workspace**:

1. *File → Open Folder* → `/home/adilt/projects/pymfem-work`.
2. *File → Add Folder to Workspace...* → `/home/adilt/projects/PyMFEM`.
3. *File → Save Workspace As...* → `~/projects/pymfem.code-workspace` (outside both repos, so it is not committed).

Reopen it with *File → Open Workspace from File* or `code ~/projects/pymfem.code-workspace`. Both folders appear in the Explorer, the project's settings and interpreter work, and Source Control shows the two repositories separately.

Benefits: PyMFEM's examples, `data/` meshes and source are one click away, and `Ctrl+Shift+F` searches both. Do **not** edit files inside `PyMFEM/` (that makes `git pull` there conflict); copy what you need into `pymfem-work` (§10).

**Restricted Mode:** when VS Code opens a folder for the first time it may show *Restricted Mode* in the status bar, which disables running and debugging. Click it (or the blue banner) and choose **Trust** for folders whose code you trust.

---

## 6. Run the first example (Poisson)

Solves $\nabla \cdot (\alpha \nabla u) = f$ on a unit square with $u = 0$ on the boundary, and plots the result with matplotlib. Adapted from the PyMFEM README (BSD-3 license).

`examples/ex1.py` (renamed to `examples/ex1_readme.py` in §10.4, when PyMFEM's own `ex1.py` is copied in):

```python
import numpy as np
import mfem.ser as mfem

# Create a square mesh
mesh = mfem.Mesh(10, 10, "TRIANGLE")

# Define the finite element function space
fec = mfem.H1_FECollection(1, mesh.Dimension())   # H1 order=1
fespace = mfem.FiniteElementSpace(mesh, fec)

# Define the essential dofs
ess_tdof_list = mfem.intArray()
ess_bdr = mfem.intArray([1]*mesh.bdr_attributes.Size())
fespace.GetEssentialTrueDofs(ess_bdr, ess_tdof_list)

# Define constants for alpha (diffusion coefficient) and f (RHS)
alpha = mfem.ConstantCoefficient(1.0)
rhs = mfem.ConstantCoefficient(1.0)

# For a variable coefficient, use a numba-JIT compiled function:
# @mfem.jit.scalar
# def alpha(x):
#     return x + 1.0

# Define the bilinear and linear operators
a = mfem.BilinearForm(fespace)
a.AddDomainIntegrator(mfem.DiffusionIntegrator(alpha))
a.Assemble()
b = mfem.LinearForm(fespace)
b.AddDomainIntegrator(mfem.DomainLFIntegrator(rhs))
b.Assemble()

# Initialize a gridfunction to store the solution vector
x = mfem.GridFunction(fespace)
x.Assign(0.0)

# Form the linear system of equations (AX=B)
A = mfem.OperatorPtr()
B = mfem.Vector()
X = mfem.Vector()
a.FormLinearSystem(ess_tdof_list, x, b, A, X, B)
print("Size of linear system: " + str(A.Height()))

# Solve the linear system using PCG and store the solution in x
AA = mfem.OperatorHandle2SparseMatrix(A)
M = mfem.GSSmoother(AA)
mfem.PCG(AA, M, B, X, 1, 200, 1e-12, 0.0)
a.RecoverFEMSolution(X, b, x)

# Extract vertices and solution as numpy arrays
# FIX: in mfem 4.10 GetVertexArray() returns a tuple -> convert to numpy
verts = np.array(mesh.GetVertexArray())
sol = x.GetDataArray()

# Plot the solution using matplotlib
import matplotlib.pyplot as plt
import matplotlib.tri as tri

triang = tri.Triangulation(verts[:, 0], verts[:, 1])

fig, ax = plt.subplots()
ax.set_aspect('equal')
tpc = ax.tripcolor(triang, sol, shading='gouraud')
fig.colorbar(tpc)
plt.show()            # or: plt.savefig("ex1.png")
```

Run:
```bash
python examples/ex1.py
```
or the ▶ **Run** button / `F5` in VS Code.

### Expected output

```
Size of linear system: 121
   Iteration :   0  (B r, r) = 0.00663539
   ...
   Iteration :  10  (B r, r) = 3.54358e-16
Average reduction factor = 0.21696
```

121 unknowns = 11 × 11 nodes. PCG converges in about 10 iterations. A window then shows a smooth bump, maximum at the centre and zero on the edges.

### The README bug (and fix)

The original README code does `verts = mesh.GetVertexArray()` and fails with:

```
TypeError: tuple indices must be integers or slices, not tuple
```

In mfem 4.10, `GetVertexArray()` returns a Python **tuple**, which does not support numpy-style indexing (`verts[:,0]`). Wrapping it in `np.array(...)` fixes it.

### Plot windows in WSL

- **Windows 11:** WSLg (WSL's graphics support) opens matplotlib windows automatically. They appear on the Windows **taskbar with a penguin icon**; click it if the window opens behind VS Code.
- **The terminal seems stuck after the solver output:** `plt.show()` **waits until the plot window is closed**. Close the window (or press `Ctrl+C` in the terminal) and the prompt returns. This is normal matplotlib behaviour.
- **`[WARN:COPY MODE]` in the window title:** WSLg could not use its fast shared-memory drawing and copies the image instead. It is a performance warning, not an error; the window works. To try to clear it, in PowerShell: `wsl --update`, then `wsl --shutdown`, and reopen Ubuntu/VS Code. Updating the graphics driver can also help. Otherwise ignore it.
- **No window appears** (e.g. Windows 10), or to avoid waiting: replace `plt.show()` with `plt.savefig("ex1.png", dpi=150)` and click the PNG in the VS Code Explorer, or run the code in a Jupyter notebook (`.ipynb`) for inline plots.

### Inspecting variables (debugging)

| Tool | Gives |
|---|---|
| `type(x)` | The type, e.g. `<class 'tuple'>` or `<class 'numpy.ndarray'>` |
| `isinstance(x, tuple)` | `True`/`False` |
| `len(x)` | Number of elements |
| `x.shape` | Dimensions (numpy only), e.g. `(121, 2)` |
| `x.dtype` | Element type (numpy only), e.g. `float64` |
| `dir(x)` | All methods/attributes; useful to explore PyMFEM objects |

In VS Code: hover over a variable, or debug with `F5` + a breakpoint and look at the **Variables** panel.

---

## 7. Project organization (own repo vs. fork)

| | Option A: own repo, PyMFEM as dependency | Option B: fork PyMFEM |
|---|---|---|
| Use when | Writing your own simulations/tools | Changing PyMFEM itself (bug fixes, new wrappers, pull requests) |
| Install | `pip install mfem` (prebuilt) | Build from source (needs `cmake`, `swig`, compiler; slow) |
| Repo content | Only your code | The whole PyMFEM codebase |
| Updating PyMFEM | `pip install --upgrade mfem` | `git fetch upstream && git merge upstream/master` |

**Chosen: Option A.** Forking is always possible later if a limitation in PyMFEM itself is found.

### Project layout

Final layout after §10 and §11:

```
~/projects/
├── pymfem.code-workspace     ← multi-root workspace (§5.6), not committed
├── pymfem-work/              ← own project (on GitHub)
│   ├── .venv/                ← virtual env, NOT committed
│   ├── .vscode/settings.json
│   ├── .gitignore
│   ├── requirements.txt
│   ├── README.md
│   ├── LICENSE-PyMFEM        ← PyMFEM's BSD-3 licence (needed for copied files)
│   ├── data/                 ← meshes copied from PyMFEM (§10)
│   ├── examples/             ← PyMFEM examples (§10) + ex1_readme.py (own)
│   └── tools/
│       └── view_gf.py        ← viewer for .mesh/.gf (§11)
└── PyMFEM/                   ← clone of upstream, reference only (not in own repo)
```

### Files

Created with:
```bash
cd ~/projects/pymfem-work
mkdir -p examples
mv ex1.py examples/
```

**`.gitignore`**
```
.venv/
__pycache__/
*.pyc
*.png
*.mesh
*.gf
!data/**
```

`*.mesh` and `*.gf` ignore **output** files written by the examples; the last line, `!data/**`, is an exception so the **input** meshes in `data/` are committed (added in §10).

**`requirements.txt`**
```
mfem==4.10.0
numpy
matplotlib
numba
```

Recreate the environment anywhere with:
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

**`README.md`** — short description, setup and run instructions.

The `cat > file << 'EOF' ... EOF` pattern in the terminal writes everything between the markers into `file`.

---

## 8. Git and SSH setup in WSL

WSL has its **own** home folder, separate from Windows, so Git config and SSH keys must be set up on the Linux side.

### 8.1 Git identity (one time)

```bash
git config --global user.name "Adilton Pereira"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global --list        # check
```

| Setting | Meaning |
|---|---|
| `--global` | Applies to all repositories of this user (stored in `~/.gitconfig`) |
| `user.name` | Author name written in commits. Free text, need not be the GitHub username. Quotes required if it has spaces. |
| `user.email` | **Links commits to the GitHub account.** Use an email registered on GitHub (or GitHub's no-reply address from *Settings → Emails*). |
| `init.defaultBranch main` | Name of the first branch created by `git init`. GitHub uses `main`; Git's old default was `master`. Avoids `src refspec main does not match any` on push. |

Notes:
- `fatal: unable to read config file '/home/adilt/.gitconfig'` before the first `git config --global` is normal: the file doesn't exist yet.
- Git lists the setting as `init.defaultbranch` (lowercase); that's fine.
- Rename an existing `master` branch with `git branch -m master main`.

### 8.2 Branch vs. repository name

- **Repository name**: the project's name on GitHub, chosen when creating it, part of the URL (`github.com/AdtPereira/pymfem-work`). Can be renamed in the repo's *Settings*; then update the local link with `git remote set-url origin git@github.com:AdtPereira/new-name.git`.
- **Branch name** (`main`): a line of development inside the repository.

### 8.3 SSH key

#### Reusing an existing key from Windows (what was done)

```bash
ls -l /mnt/c/Users/adilt/.ssh              # find the key on Windows
mkdir -p ~/.ssh
cp /mnt/c/Users/adilt/.ssh/id_ed25519 /mnt/c/Users/adilt/.ssh/id_ed25519.pub ~/.ssh/
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
ls -l ~/.ssh                                # check permissions
```

Expected:
```
-rw------- 1 adilt adilt 464 ... id_ed25519
-rw-r--r-- 1 adilt adilt 100 ... id_ed25519.pub
```

- `id_ed25519` = **private** key. Never share it.
- `id_ed25519.pub` = **public** key, the one registered on GitHub.
- The `chmod` steps are required: SSH refuses a private key that other users can read, and files copied from Windows get loose permissions.

#### Creating a new key (alternative)

```bash
ssh-keygen -t ed25519 -C "you@example.com"    # Enter to accept defaults
cat ~/.ssh/id_ed25519.pub                       # copy this line
```
Add it at GitHub → *Settings → SSH and GPG keys → New SSH key*.

#### Test the connection

```bash
ssh -T git@github.com
```

First time only, SSH asks to confirm GitHub's identity. Type the full word **`yes`** (a plain `y` is not accepted). GitHub's ED25519 fingerprint is:
```
SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU
```
It is then saved in `~/.ssh/known_hosts`.

Success message:
```
Hi AdtPereira! You've successfully authenticated, but GitHub does not provide shell access.
```
("no shell access" is normal.)

If `Permission denied (publickey)`: the key isn't on the GitHub account. Add the `.pub` content to GitHub. To compare which key GitHub has:
```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub     # compare SHA256 with GitHub's SSH keys page
```

#### Key with a non-standard name

SSH tries `id_ed25519`, `id_rsa`, etc. automatically. For another name (e.g. `github_key`):
```bash
cat >> ~/.ssh/config << 'EOF'
Host github.com
    User git
    IdentityFile ~/.ssh/github_key
EOF
chmod 600 ~/.ssh/config
```

---

## 9. Publish the project on GitHub

### 9.1 First commit

```bash
cd ~/projects/pymfem-work
git init
git add .
git status        # .venv/ must NOT appear
git commit -m "Initial PyMFEM setup with Poisson example"
```

### 9.2 Create the GitHub repository

1. GitHub → **+** → **New repository**.
2. Name: `pymfem-work`.
3. Leave *README*, *.gitignore* and *license* **unticked** (the files already exist locally).
4. **Create repository**.

### 9.3 Push

```bash
git remote add origin git@github.com:AdtPereira/pymfem-work.git
git push -u origin main
```

`-u` links the local `main` to `origin/main`, so later a plain `git push` is enough.

Result: [github.com/AdtPereira/pymfem-work](https://github.com/AdtPereira/pymfem-work), with `.vscode/`, `examples/`, `.gitignore`, `README.md`, `requirements.txt`, and no `.venv`.

### 9.4 Day-to-day workflow

```bash
git add .
git commit -m "Describe what changed"
git push
```

Or in VS Code: **Source Control** panel (branch icon) → message → **Commit** → **Sync Changes**.

Optional: add a description and topics (`fem`, `pymfem`) via the ⚙ next to **About** on the repo page.

---

## 10. Using PyMFEM's examples and data in your project

### 10.1 Clone PyMFEM next to the project (reference only)

```bash
cd ~/projects
git clone https://github.com/mfem/PyMFEM.git     # next to, not inside, pymfem-work
git -C PyMFEM pull                                 # later: update it
```

### 10.2 Run an example inside the PyMFEM clone

```bash
source ~/projects/pymfem-work/.venv/bin/activate   # reuse the project's venv
cd ~/projects/PyMFEM/examples                       # examples load meshes from ../data
python ex1.py -h                                    # list options
python ex1.py
```

- Files ending in `p.py` (e.g. `ex1p.py`) are parallel and need the MPI build (§13).
- If an example tries to connect to GLVis and complains, check `-h` for a flag to turn visualization off (usually `-no-vis`). Results are still saved as `.mesh` / `.gf` files (§11).

### 10.3 How examples find their meshes

At the end of each example (e.g. `ex0.py`) the mesh path is built relative to the script itself:

```python
meshfile = expanduser(join(os.path.dirname(__file__), '..', 'data', args.mesh))
```

So `examples/ex0.py` looks for `../data/star.mesh`. Any copy keeps working as long as `examples/` and `data/` sit side by side. An absolute path in `-m` also works (`os.path.join` discards the earlier parts): `python examples/ex0.py -m ~/projects/PyMFEM/data/star.mesh`.

### 10.4 Copy the examples and meshes into your project

```bash
cd ~/projects/pymfem-work

# 1. Protect your own ex1.py (PyMFEM has an examples/ex1.py that would overwrite it)
git mv examples/ex1.py examples/ex1_readme.py
sed -i 's#examples/ex1.py#examples/ex1_readme.py#' README.md

# 2. Check sizes (GitHub rejects single files > 100 MB)
du -sh ../PyMFEM/data ../PyMFEM/examples

# 3. Copy contents (the trailing /. copies the contents, not the folder itself)
mkdir -p data
cp -r ../PyMFEM/examples/. examples/
cp -r ../PyMFEM/data/. data/
cp ../PyMFEM/LICENSE LICENSE-PyMFEM        # BSD-3 requires keeping the notice

# 4. Let Git track input meshes in data/
echo '!data/**' >> .gitignore

# 5. Test and commit
python examples/ex0.py
git add .
git status        # no .venv, no __pycache__; data/ files listed
git commit -m "Add PyMFEM examples and data (BSD-3, see LICENSE-PyMFEM)"
git push
```

Add a note to `README.md`, e.g. *"`examples/` and `data/` are copied from [PyMFEM](https://github.com/mfem/PyMFEM) (BSD-3, see `LICENSE-PyMFEM`); `ex1_readme.py` is my own."* The copies don't update by themselves: `git -C ../PyMFEM pull` and repeat step 3 when needed.

### 10.5 README example vs. `ex0.py` vs. `ex1.py`

All three solve the Poisson problem $-\Delta u = 1$ with $u = 0$ on the boundary, using PCG with a Gauss–Seidel preconditioner.

| | README example (`ex1_readme.py`) | `examples/ex0.py` | `examples/ex1.py` |
|---|---|---|---|
| Origin | PyMFEM README (modified from `ex1.cpp`) | Port of MFEM `ex0.cpp`, the simplest example | Port of MFEM `ex1.cpp` |
| Mesh | Generated: `Mesh(10, 10, "TRIANGLE")` | Read from file (`star.mesh` default), refined once | Read from file (`star.mesh` default), refined uniformly up to ≤ 50,000 elements (§10.8) |
| Dimension | 2D only | 2D or 3D (e.g. `fichera.mesh`) | 2D or 3D |
| Order | Fixed 1 | `-o` option | `-o` option; `-o -1` = isoparametric (uses the mesh's own curved/NURBS space) |
| Boundary DOFs | `GetEssentialTrueDofs` with boundary attributes | `GetBoundaryTrueDofs` (all boundary) | All boundary attributes marked essential → `GetEssentialTrueDofs` |
| Extra options | — | — | `-sc` static condensation, `-pa` partial assembly, `-d` device, `-vis` GLVis |
| Output | matplotlib plot on screen | `sol.gf` + `mesh.mesh` for GLVis | `sol.gf` + **`refined.mesh`**; optional live stream to GLVis (port 19916) |
| Structure | Flat script | `run()` + `if __name__ == "__main__":` | Same |

### 10.6 The mfem.org Example 0 figure

The picture for Example 0 on <https://mfem.org/examples/> (four peaks around a central crater) is the **same equation on a different domain**: it matches the solution on `square-disc.mesh`, a square with a circular hole. The hole edge is also boundary ($u = 0$), which pulls the surface down in the middle; the solution peaks along the diagonals, farthest from both boundaries. (Inferred by solving on several meshes; the site doesn't name the mesh.)

```bash
python examples/ex0.py -m square-disc.mesh
```

Changing only `-m` shows how much the geometry alone shapes the solution.

### 10.7 `test/run_examples.py` is not a normal test suite

It runs the **C++** MFEM examples and the **Python** examples and compares the numbers in their output, so it needs the compiled C++ examples (looked for in the package's `external/ser` folder). They exist after a **source build**, but not with the prebuilt `pip install mfem`, where it fails with:

```
data file (under ser dir) does not exist in the package directory
```

That does not mean the install is broken; the script is meant for PyMFEM developers. Options: `-serial`, `-parallel`, `-np N`, `-ex exN`, `-verbose`, `-clean`, `-mfemsdir`, `-mfempdir`, `-sandbox`.

### 10.8 The mfem.org Example 1 figure, and what `ex1` adds

**The figure is `fichera.mesh` with a cutting plane.** The Example 1 picture on <https://mfem.org/examples/> (an L-shaped block, blue sides, coloured top) does not name its mesh. It was identified as follows (2 Oct 2026):

- `l-shape.mesh` in MFEM's [`data/`](https://github.com/mfem/mfem/tree/master/data) is **2D** (3 quads), so it cannot give a 3D block.
- `fichera.mesh` is the cube $[-1,1]^3$ minus one corner octant (7 hexahedra). The missing octant is $x, y, z < 0$, so the **lower half** ($-1 \le z \le 0$) is an **L-shaped prism**, half as tall as it is wide.
- All outer faces are boundary ($u = 0$), so they are blue. The coloured top face is therefore **not** a real face: it is a GLVis **cutting plane at $z = 0$**, showing the solution inside the domain.
- Solving `ex1` on `fichera.mesh` and plotting the $z = 0$ slice gives the same picture: zero on the edges and a long peak bending around the inner corner of the L (slice maximum ≈ 0.147).
- `fichera.mesh` is one of the official sample runs in the header of `ex1.cpp`.

**Refinement rule.** `ex1` refines uniformly as many times as possible while keeping ≤ 50,000 elements:

```python
ref_levels = int(np.floor(np.log(50000. / mesh.GetNE()) / np.log(2.) / dim))
```

For `fichera.mesh` (7 elements, dim 3): $\lfloor 4.27 \rfloor = 4$ levels → $7 \times 8^4 = 28{,}672$ hexahedra (16 cells per unit length), which matches the fine grid on the sides of the picture. For `star.mesh` (20 quads, dim 2): $\lfloor 5.64 \rfloor = 5$ levels → 20,480 quads.

**Reproduce the figure:**

```bash
cd ~/projects/pymfem-work
python examples/ex1.py -m fichera.mesh        # check -h for the visualization flag (-vis)
glvis -m refined.mesh -g sol.gf               # note: refined.mesh, not mesh.mesh
```

Then set a horizontal cutting plane at mid-height with the 3D keys in §11.5 (`i`, `x`/`y`, `z`).

---

## 11. Viewing .mesh and .gf files (matplotlib, GLVis)

### 11.1 What these files are

They are **text data files**, not images:

- **`.mesh`**: the geometry, i.e. vertex coordinates and which vertices form each element.
- **`.gf`** (grid function): the solution values (one per degree of freedom) **on that mesh**. A `.gf` is meaningless without its `.mesh`, so they are always loaded together.

Output file names differ between examples: `ex0` writes `mesh.mesh` + `sol.gf`; `ex1` writes **`refined.mesh`** + `sol.gf`.

Example: the start of `data/star.mesh`:

```
MFEM mesh v1.0

#
# MFEM Geometry Types (see mesh/geom.hpp):
#
# POINT       = 0
# SEGMENT     = 1
# TRIANGLE    = 2
# SQUARE      = 3
# TETRAHEDRON = 4
# CUBE        = 5
#

dimension
2

elements
20
1 3 0 11 26 14
...
```

- Lines starting with `#` are a **comment**, a legend of geometry codes present in every MFEM mesh file. They do **not** mean the mesh contains tetrahedra or cubes.
- Each element line is `attribute  geometry  vertex numbers`: `1 3 0 11 26 14` = attribute 1, geometry 3 (quadrilateral), vertices 0, 11, 26, 14.
- `star.mesh` is a flat 2D mesh of **20 quadrilaterals** (31 vertices, coordinates x ∈ [−1.618, 1.309], y ∈ [−1.539, 1.539]). After one `UniformRefinement()` it has 80.

Quick inspection in Python:

```python
import mfem.ser as mfem
mesh = mfem.Mesh("data/star.mesh", 1, 1)
print("dimension:", mesh.Dimension())
print("vertices:", mesh.GetNV())
print("elements:", mesh.GetNE())
print("boundary elements:", mesh.GetNBE())
print("element types:", {mesh.GetElementType(i) for i in range(mesh.GetNE())})  # 3 = quadrilateral
```

### 11.2 Option 1: matplotlib script `tools/view_gf.py` (no installs)

Save as `~/projects/pymfem-work/tools/view_gf.py`:

```python
"""
Plot MFEM output files (.mesh + .gf) with matplotlib.

Usage:
    python view_gf.py                          # mesh.mesh + sol.gf, 2D colour map
    python view_gf.py -m mesh.mesh -g sol.gf --3d
    python view_gf.py -m mesh.mesh             # mesh only (no solution)
    python view_gf.py --save result.png        # save instead of opening a window

Works for 2D meshes (triangles and quads). Curved/high-order meshes are
drawn using their vertices only.
"""
import argparse
import numpy as np
import mfem.ser as mfem
import matplotlib.pyplot as plt
import matplotlib.tri as tri

parser = argparse.ArgumentParser(description="View MFEM .mesh/.gf files")
parser.add_argument("-m", "--mesh", default="mesh.mesh", help="mesh file")
parser.add_argument("-g", "--gf", default="sol.gf", help="grid function file ('' = mesh only)")
parser.add_argument("--3d", dest="three_d", action="store_true", help="3D surface plot")
parser.add_argument("--save", default="", help="save to this image file instead of showing")
args = parser.parse_args()

# 1. Read the mesh (generate_edges=1, refine=1, same as the examples)
mesh = mfem.Mesh(args.mesh, 1, 1)
if mesh.Dimension() != 2:
    raise SystemExit(f"This viewer handles 2D meshes; {args.mesh} is {mesh.Dimension()}D.")

# 2. Vertex coordinates and element connectivity (quads split into 2 triangles)
verts = np.array(mesh.GetVertexArray())
triangles = []
for e in range(mesh.GetNE()):
    v = list(mesh.GetElementVertices(e))
    if len(v) == 3:
        triangles.append(v)
    else:
        triangles += [[v[0], v[1], v[2]], [v[0], v[2], v[3]]]
triang = tri.Triangulation(verts[:, 0], verts[:, 1], triangles)

# 3. Read the grid function and get its value at each mesh vertex
values = None
if args.gf:
    gf = mfem.GridFunction(mesh, args.gf)
    vals = mfem.Vector()
    gf.GetNodalValues(vals, 1)       # value at each vertex (component 1)
    values = vals.GetDataArray().copy()
    print(f"{args.gf}: min = {values.min():.6g}, max = {values.max():.6g}")
print(f"{args.mesh}: {mesh.GetNV()} vertices, {mesh.GetNE()} elements")

# 4. Plot
fig = plt.figure(figsize=(7, 6))
if values is None:
    # Draw each element as its real polygon (quads are not split here)
    from matplotlib.collections import PolyCollection
    polys = [verts[list(mesh.GetElementVertices(e))] for e in range(mesh.GetNE())]
    ax = fig.add_subplot()
    ax.add_collection(PolyCollection(polys, facecolor="lightsteelblue",
                                     edgecolor="k", linewidth=0.6))
    ax.autoscale()
    ax.set_aspect("equal")
    ax.set_title(f"{args.mesh}  ({mesh.GetNE()} elements)")
elif args.three_d:
    ax = fig.add_subplot(projection="3d")
    surf = ax.plot_trisurf(triang, values, cmap="jet", linewidth=0.1, edgecolor="k")
    fig.colorbar(surf, shrink=0.6)
    ax.set_title(f"{args.gf} on {args.mesh}")
else:
    ax = fig.add_subplot()
    tpc = ax.tripcolor(triang, values, shading="gouraud", cmap="jet")
    ax.triplot(triang, lw=0.2, color="k", alpha=0.3)
    fig.colorbar(tpc)
    ax.set_aspect("equal")
    ax.set_title(f"{args.gf} on {args.mesh}")

if args.save:
    plt.savefig(args.save, dpi=120, bbox_inches="tight")
    print("saved", args.save)
else:
    plt.show()
```

Usage, from the folder where the example wrote its output:

```bash
python ~/projects/pymfem-work/tools/view_gf.py                 # 2D colour map of sol.gf on mesh.mesh
python ~/projects/pymfem-work/tools/view_gf.py --3d            # 3D surface
python ~/projects/pymfem-work/tools/view_gf.py -g ""           # mesh only
python ~/projects/pymfem-work/tools/view_gf.py -m data/star.mesh -g ""
python ~/projects/pymfem-work/tools/view_gf.py -m refined.mesh # output of ex1 (2D meshes only)
python ~/projects/pymfem-work/tools/view_gf.py --save out.png  # PNG instead of a window
```

How it works: `mfem.Mesh(file, 1, 1)` reads the mesh, `mfem.GridFunction(mesh, file)` reads the solution, `GetNodalValues(vals, 1)` gives one value per vertex, and matplotlib draws it. **2D meshes only**; for 3D use GLVis or ParaView.

### 11.3 Option 2: GLVis Windows app

GLVis is MFEM's own interactive viewer (rotate, zoom, mesh lines, 3D and high-order elements).

1. Download the **Windows** version from <https://glvis.org/download/> (no Linux binary is listed there) and put it in a fixed folder, e.g. `C:\glvis`.
2. In Ubuntu, check the exact file name and create a shortcut command:

   ```bash
   ls /mnt/c/glvis
   echo "alias glvis='/mnt/c/glvis/glvis.exe'" >> ~/.bashrc
   source ~/.bashrc
   ```

   `>>` appends to `~/.bashrc` (a single `>` would overwrite it); `source` reloads it in the current terminal. To fix a wrong path: `code ~/.bashrc`, edit the last line, `source ~/.bashrc`.

3. Open files **with arguments**, `-m` for the mesh and `-g` for the solution:

   ```bash
   cd ~/projects/pymfem-work
   glvis -m data/star.mesh              # mesh only
   glvis -m mesh.mesh -g sol.gf         # mesh + solution (ex0)
   glvis -m refined.mesh -g sol.gf      # mesh + solution (ex1)
   ```

   If GLVis can't read the files, pass Windows-style full paths:

   ```bash
   glvis -m "$(wslpath -w mesh.mesh)" -g "$(wslpath -w sol.gf)"
   ```

   From PowerShell instead (not CMD, which handles `\\wsl.localhost` paths badly):

   ```powershell
   C:\glvis\glvis.exe -m \\wsl.localhost\Ubuntu-24.04\home\adilt\projects\pymfem-work\mesh.mesh -g \\wsl.localhost\Ubuntu-24.04\home\adilt\projects\pymfem-work\sol.gf
   ```

**"Waiting for data on port 19916..."**: GLVis was started **without** files and is in *server mode*, waiting for a running program to stream data to it. Close it and start it with `-m`/`-g` as above.

### 11.4 Option 3: GLVis inside a Jupyter notebook in VS Code

Independent of the Windows app; use one or the other.

1. Install, with the venv active:

   ```bash
   cd ~/projects/pymfem-work
   source .venv/bin/activate
   pip install glvis ipykernel requests
   ```

   `ipykernel` lets VS Code use the venv as the notebook's Python. `requests` is listed because **glvis 1.1.1 needs it but does not install it** (`ModuleNotFoundError: No module named 'requests'` otherwise).

2. Create e.g. `viewer.ipynb`; top right **Select Kernel → Python Environments → `.venv`**.

3. Mesh + solution (every line must start at the left margin, with no indentation):

   ```python
   import mfem.ser as mfem
   from glvis import glvis

   mesh = mfem.Mesh("mesh.mesh", 1, 1)
   sol = mfem.GridFunction(mesh, "sol.gf")
   glvis((mesh, sol))
   ```

   Mesh only:

   ```python
   mesh = mfem.Mesh("data/star.mesh", 1, 1)
   glvis(mesh)
   ```

   - Paths are relative to the notebook's folder; otherwise use full paths (`/home/adilt/projects/pymfem-work/sol.gf`).
   - `glvis(...)` must be the **last line of the cell** (a notebook only displays what the last line returns).
   - Keys can be preset: `glvis(mesh, keys="ma")`.

### 11.5 GLVis keys and what the view shows

Source: GLVis key bindings in the [GLVis README](https://github.com/GLVis/glvis/blob/master/README.md). Click on the GLVis window first so it receives the keys.

**Mouse**

| Action | Effect |
|---|---|
| Left button drag | Rotate |
| Left button + `Shift` | Start spinning |
| Right button drag up / down | **Zoom in / out** |
| Middle button (wheel click) drag | Translate (pan) the view |

**View keys**

| Key | Effect |
|---|---|
| `*` / `/` | **Zoom in / out**. Easiest on the numeric keypad. Spanish keyboard: `*` = `Shift` + the `+` key (right of `P`), `/` = `Shift+7`. US keyboard: `*` = `Shift+8`, `/` = its own key |
| `+` / `-` | Stretch / compress in the **z direction** (height of the solution surface), *not* zoom |
| `Ctrl` + arrow keys | Translate (pan) the view |
| Arrow keys | Rotate |
| `1`–`9` | Rotate about the coordinate axes |
| `r` | Reset to the default 3D view |
| `R` | Cycle through the six 2D projections (use it for a flat top view of a 2D mesh) |

**Display keys**

| Key | Effect |
|---|---|
| `m` | Toggle mesh: none / element edges / level lines |
| `e` | Toggle elements state |
| `a` | Toggle bounding box / axes (none, with or without coordinates, RGB axes) |
| `c` | Toggle colour bar and caption |
| `F3` / `F4` | Shrink / grow each element towards its centre |

GLVis always draws inside a 3D box, even for a 2D mesh: the x/y limits are the mesh's coordinates, the z range is just viewer space. Elements may appear slightly shrunk so they can be told apart. A 2D mesh seen this way is still 2D.

**3D scalar data: cutting plane and level surfaces**

These work only for a **3D mesh** (e.g. `fichera.mesh`); on a 2D mesh they do nothing visible. There is **no single "horizontal cut" key**: `i` turns the plane on, then it is rotated and moved into place.

| Key | Effect |
|---|---|
| `i` | Cycle the cutting (clipping) plane: none → cut through the elements → show only the elements behind the plane |
| `I` | Switch the algorithm used in "cut through the elements" mode |
| `x` / `X` | **Rotate** the plane (angle φ) |
| `y` / `Y` | **Rotate** the plane (angle θ) |
| `z` / `Z` | **Translate** (move) the plane along its normal |
| `E` | Show / hide the elements in the cutting plane |
| `M` | Show / hide the mesh lines in the cutting plane |
| `o` / `O` | Refine / de-refine the elements used for drawing (smoother picture) |
| `u` / `U` | Move the level-surface value up / down |
| `v` / `V` | Add / delete a level surface |
| `w` / `W` | Move boundary elements in / out along their normal (exploded view) |

**Recipe for the Example 1 picture** (`glvis -m refined.mesh -g sol.gf` after `ex1 -m fichera.mesh`, §10.8):

1. Click the GLVis window.
2. `i` once → cut through the elements.
3. `x`/`X` and `y`/`Y` until the plane is horizontal (`M` shows the mesh on the plane, which makes its orientation easy to see).
4. `z`/`Z` to move it to mid-height; the L-shaped section appears where Fichera's corner is missing.
5. `i` again → only the elements behind the plane are drawn: the L-shaped block with the coloured cut on top, as on mfem.org.
6. Choose the viewing angle with the mouse, `r` or `R`.

### 11.6 Option 4: ParaView (later, for 3D and vector fields)

For larger or 3D problems (e.g. the electromagnetics examples), write ParaView files from the script with `mfem.ParaViewDataCollection` (see PyMFEM's `ex5.py` / `ex9.py`) and open the `.pvd` in ParaView for Windows.

### 11.7 Live streaming to GLVis from WSL (not set up)

Examples with visualization on send data to GLVis over a socket (`localhost`, port 19916). With WSL's default **nat** networking, `localhost` inside Ubuntu is not Windows, so this does not work out of the box (check with `wslinfo --networking-mode`, §3). Saving files and opening them (§11.3) avoids the problem.

---

## 12. Setting up a second computer

Sections 4–11 were done on the **work computer** (1 October 2026). This section is for any other computer (e.g. the **home computer**, 2 October 2026) that should work on the same GitHub repository.

### 12.1 What travels with the repository and what doesn't

| Comes with `git clone` | Must be redone on each computer |
|---|---|
| Code (`examples/`, `tools/`), `data/` meshes | WSL2 + Ubuntu, VS Code + extensions (§2, §5.2) |
| `requirements.txt` | System packages (§4.1) |
| `.vscode/settings.json` | The `.venv` (never committed; §4.3) |
| `.gitignore`, `README.md`, `LICENSE-PyMFEM` | Git identity: `~/.gitconfig` (§8.1) |
| | SSH key registered on GitHub (§8.3) |
| | GLVis download + `glvis` alias in `~/.bashrc` (§11.3) |
| | Reference clone of PyMFEM (§10.1), workspace file (§5.6) |

### 12.2 Procedure

All commands in the Ubuntu terminal of the new computer.

**1. Basics (§4.1)**

```bash
conda deactivate 2>/dev/null        # if the prompt shows (base)
which python3 && python3 --version  # /usr/bin/python3, Python 3.12.x
git --version
# if something is missing:
sudo apt update && sudo apt install -y python3 python3-venv python3-pip python3-tk git build-essential
```

**2. Git identity, once per computer (§8.1)**

```bash
git config --global --list
git config --global user.name "Adilton Pereira"
git config --global user.email "adilton@ugr.es"
git config --global init.defaultBranch main
```

Use the **same email on every computer**, and make sure it is listed (and verified) under **GitHub → Settings → Emails**. That email, not the SSH key, is what links commits to the GitHub account.

**3. SSH key for this computer (§8.3)**

```bash
ssh -T git@github.com
```

If it already says `Hi AdtPereira!`, go to step 4. Otherwise, either reuse a key that already exists on this Windows PC:

```bash
ls -l /mnt/c/Users/adilt/.ssh
mkdir -p ~/.ssh
cp /mnt/c/Users/adilt/.ssh/id_ed25519 /mnt/c/Users/adilt/.ssh/id_ed25519.pub ~/.ssh/
chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_ed25519 && chmod 644 ~/.ssh/id_ed25519.pub
```

or create a new one (recommended: **one key per computer**):

```bash
ssh-keygen -t ed25519 -C "adilton@ugr.es home PC"
```

Then register the public key on GitHub (**Settings → SSH and GPG keys → New SSH key**, title e.g. `Home PC`):

```bash
cat ~/.ssh/id_ed25519.pub        # copy the whole line
ssh -T git@github.com            # → Hi AdtPereira! ...
```

A copied key that was never registered on GitHub fails exactly like a missing key; see §12.4.

**4. Move any old, non-cloned project folder out of the way**

`git clone` refuses to write into an existing, non-empty folder (`fatal: destination path 'pymfem-work' already exists and is not an empty directory`).

```bash
deactivate 2>/dev/null
cd ~/projects
mv pymfem-work pymfem-work-old       # nothing is deleted
```

Copy anything worth keeping from `pymfem-work-old` into the clone afterwards. Its `.venv` cannot be reused (a venv stores its absolute path).

**5. Clone**

```bash
cd ~/projects
git clone git@github.com:AdtPereira/pymfem-work.git
cd pymfem-work
git log --oneline       # commits made on the other computer
ls -a
```

**6. Recreate the virtual environment (§4.3)**

```bash
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
which python                        # .../pymfem-work/.venv/bin/python
pip install --upgrade pip
pip install -r requirements.txt     # same versions as on the other computer
python -c "import mfem.ser as mfem; print('MFEM OK')"
```

For the GLVis notebook (§11.4) also `pip install glvis ipykernel requests`, or better, add these three lines to `requirements.txt` and commit, so every computer gets them.

**7. VS Code (§5)**

```bash
code .
```

Check `WSL: Ubuntu-24.04` in the bottom-left corner; **Trust** the folder if asked; install the **Python** and **Jupyter** extensions *in WSL* if this PC doesn't have them; check the interpreter is `./.venv/bin/python` (it is usually picked up from the cloned `.vscode/settings.json`).

**8. Extras, if used on this computer**

```bash
cd ~/projects && git clone https://github.com/mfem/PyMFEM.git        # reference copy (§10.1)
echo "alias glvis='/mnt/c/glvis/glvis.exe'" >> ~/.bashrc && source ~/.bashrc   # after downloading GLVis to C:\glvis (§11.3)
```

### 12.3 Working on two computers

GitHub is the meeting point between the computers.

| When | Command |
|---|---|
| **Start** of every session, on either computer | `git pull` |
| **End** of every session | `git add .` → `git commit -m "..."` → `git push` |
| Any time | `git status` shows whether you are ahead of / behind GitHub |

- Forgetting to **push** at the end means the other computer cannot get the changes.
- Forgetting to **pull** at the start means editing an old version, which can lead to a merge conflict on the next push.

### 12.4 SSH keys: checking and diagnosing

```bash
ls -l ~/.ssh                                   # which key files exist
ssh-keygen -lf ~/.ssh/id_ed25519.pub           # fingerprint (SHA256:...) and label
ssh -vT git@github.com 2>&1 | grep -E "Offering|Authentications"   # which key SSH offers
```

How to read the results:

| Output | Meaning |
|---|---|
| `Hi AdtPereira! You've successfully authenticated...` | Key registered on this account ✅ |
| `Offering public key: ... SHA256:XXXX` followed by `Permission denied (publickey)` | SSH found and offered the key, but **GitHub doesn't know it**: add the `.pub` to GitHub |
| No `Offering public key` line | No key file found, or a `~/.ssh/config` points elsewhere (`cat ~/.ssh/config`) |
| `Hi otheruser!` | Key is registered on a **different** GitHub account |
| `UNPROTECTED PRIVATE KEY FILE!` | Permissions too open (typical after copying from Windows): `chmod 600 ~/.ssh/id_ed25519` |

Compare the `SHA256:...` fingerprint with the ones listed under **GitHub → Settings → SSH and GPG keys** to see whether a key is registered.

**The label (comment) at the end of a key** (e.g. `adilton@cefetmg.br`) is only text written at creation time with `-C`. GitHub ignores it; an old email there does no harm. To change it (the key and fingerprint stay the same; asks for the passphrase if the key has one):

```bash
ssh-keygen -c -C "adilton@ugr.es home PC" -f ~/.ssh/id_ed25519
```

### 12.5 Status of the keys (2 October 2026)

| | Work computer | Home computer |
|---|---|---|
| Key file | `~/.ssh/id_ed25519`, copied from its Windows `C:\Users\adilt\.ssh` | `~/.ssh/id_ed25519`, copied from its Windows `C:\Users\adilt\.ssh` (created July 2025) |
| Fingerprint | (see GitHub → Settings → SSH and GPG keys) | `SHA256:39An8v9aCWvIkOiNkJ9Jmk/WV7Y3CJM7HforhNP0u9I` |
| Label | — | `adilton@cefetmg.br` (old email; label only) |
| Permissions in WSL | OK | OK (`chmod 700/600/644` done) |
| Offered by SSH | Yes | Yes |
| Registered on GitHub | **Yes** (repo pushed on 1 Oct) | **No** → `Permission denied (publickey)` |

They are **two different keys** (if they were the same, the home computer would have been accepted).

**Pending on the home computer:**

1. *(Optional)* relabel: `ssh-keygen -c -C "adilton@ugr.es home PC" -f ~/.ssh/id_ed25519`.
2. `cat ~/.ssh/id_ed25519.pub` → GitHub → **Settings → SSH and GPG keys → New SSH key**, title `Home PC`.
3. `ssh -T git@github.com` → `Hi AdtPereira!`.
4. `git config --global user.email` → an email listed under GitHub → Settings → Emails (e.g. `adilton@ugr.es`); same check on the work computer.
5. Continue with §12.2 step 4 (move the old folder, clone, recreate `.venv`).

When done, GitHub's SSH keys page should list **two keys**, one per computer, each with its own fingerprint. A key for a computer that is no longer used can be deleted there at any time.

---

## 13. Optional: parallel (MPI) build from source

Only needed for `mfem.par` or extra features. Use a **separate venv** so it doesn't replace the prebuilt `mfem` used by the project.

```bash
sudo apt install -y cmake swig libopenmpi-dev openmpi-bin
cd ~/projects/PyMFEM
python3 -m venv .venv && source .venv/bin/activate
pip install mpi4py
pip install ./ -C"with-parallel=Yes" --verbose
```

Full comparison test after a source build:
```bash
cd test
python run_examples.py -serial -ex ex1
```

Cleaning a source build (from the README):
```bash
rm -rf build      # build directory
rm -rf external   # external dependencies + wrapper code
git clean -f      # files under mfem/_ser and mfem/_par
```

Other options (CUDA, GSLIB, libCEED, ...): see [INSTALL.md](https://github.com/mfem/PyMFEM/blob/master/INSTALL.md).

---

## 14. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Ubuntu not in Start menu | WSL not installed | `wsl --install -d Ubuntu-24.04` as admin, reboot |
| Nothing shows when typing `sudo` password | Normal behaviour | Just type and press Enter |
| `pip install mfem` starts compiling for ages | No wheel for that Python version (mfem 4.10.0 has wheels for 3.11–3.14) | Use Ubuntu's Python 3.12 (`/usr/bin/python3`) |
| `error: externally-managed-environment` | pip into system Python | Create/activate `.venv` |
| `The virtual environment was not created successfully because ensurepip is not available` | `python3-venv` not installed | `sudo apt install -y python3-venv`, then delete `.venv` and create it again (§4.3) |
| Prompt shows `(base)` | conda's base environment is active | `conda deactivate`; `conda config --set auto_activate_base false` |
| `which python` is not `.../pymfem-work/.venv/bin/python` | venv not active, or conda active | `conda deactivate`, then `source .venv/bin/activate` |
| `.venv` stops working after moving/renaming the folder | venv stores its absolute path | Delete and recreate it (§4.3) |
| Extensions greyed out with ⚠ | Installed only on Windows | Click **Install in WSL: Ubuntu-24.04** |
| `.venv` not offered as interpreter | Folder not opened as workspace | *File → Open Folder*, or *Enter interpreter path...* → `.../.venv/bin/python` |
| `ModuleNotFoundError: No module named 'mfem'` | Wrong interpreter (system Python) | Select `.venv/bin/python` / `source .venv/bin/activate` |
| Prompt lacks `(.venv)` in VS Code terminal | Terminal opened before interpreter selection | Open a new terminal |
| `TypeError: tuple indices must be integers or slices, not tuple` | `GetVertexArray()` returns tuple | `verts = np.array(mesh.GetVertexArray())` |
| No plot window | No WSLg (e.g. Windows 10) | `plt.savefig(...)` or Jupyter notebook |
| `fatal: unable to read config file '~/.gitconfig'` | No global config yet | Run the `git config --global` commands |
| `Please type 'yes', 'no' or the fingerprint` | Typed `y` | Type `yes` |
| `Permission denied (publickey)` | Key not on GitHub, or wrong key | Add `.pub` to GitHub; compare fingerprints (§12.4) |
| `fatal: destination path 'pymfem-work' already exists and is not an empty directory` | A non-cloned folder with that name exists | `mv pymfem-work pymfem-work-old`, then clone (§12.2) |
| Commits from one computer don't show the GitHub profile picture | `user.email` on that computer isn't listed on GitHub | Set it to a verified GitHub email (§12.2 step 2) |
| Changes from the other computer are missing | Not pushed there, or not pulled here | `git push` on the other one, `git pull` here (§12.3) |
| `UNPROTECTED PRIVATE KEY FILE!` | Loose permissions (copied from Windows) | `chmod 600 ~/.ssh/id_ed25519`, `chmod 700 ~/.ssh` |
| `src refspec main does not match any` | Branch is `master` or no commit yet | `git branch -m master main`; make a commit first |
| `run_examples.py`: data file does not exist | Prebuilt wheel lacks C++ examples | Run Python examples directly (§10.2) or build from source |
| `Command 'wsl' not found` inside Ubuntu | `wsl` is a Windows command | Use `wsl.exe ...` or PowerShell (§3) |
| Terminal stuck after solver output, no prompt | `plt.show()` waits for the plot window | Close the window (penguin icon on the taskbar) or `Ctrl+C` (§6) |
| `[WARN:COPY MODE]` in a WSLg window title | WSLg fallback drawing mode | Harmless; `wsl --update` + `wsl --shutdown` may clear it (§6) |
| *Restricted Mode* in VS Code; can't run/debug | Folder not trusted yet | Click *Restricted Mode* → **Trust** (§5.6) |
| Copied example: mesh file not found | `data/` not next to `examples/` | Copy `data/` too, or pass a full path with `-m` (§10.3) |
| Meshes in `data/` not committed | `*.mesh` in `.gitignore` | Add `!data/**` to `.gitignore` (§10.4) |
| GLVis: "Waiting for data on port 19916" | Started without files (server mode) | `glvis -m mesh.mesh -g sol.gf` (§11.3) |
| GLVis can't open the file | Linux path given to a Windows program | `glvis -m "$(wslpath -w mesh.mesh)" ...` (§11.3) |
| GLVis: `mesh.mesh` not found after running `ex1` | `ex1` writes `refined.mesh`, not `mesh.mesh` | `glvis -m refined.mesh -g sol.gf` (§10.8) |
| `ModuleNotFoundError: No module named 'requests'` on `from glvis import glvis` | glvis 1.1.1 missing dependency | `pip install requests` (§11.4) |
| `IndentationError: unexpected indent` in a notebook cell | Pasted lines start with spaces | Remove the indentation (`Shift+Tab`) (§11.4) |
| GLVis: `+`/`-` don't zoom | They stretch the z direction | Zoom with `*` / `/` or right mouse button drag (§11.5) |
| GLVis: `i`, `x`, `y`, `z` do nothing | Cutting-plane keys work only on 3D meshes | Use a 3D mesh, e.g. `fichera.mesh` (§11.5) |
| GLVis: `x`/`X` turns the cutting plane instead of moving it | `x`/`y` rotate, `z` translates | Move the plane with `z`/`Z` (§11.5) |
| Notebook shows nothing after `glvis(...)` | Not the last line of the cell, or wrong kernel | Make it the last line; kernel = `.venv` (§11.4) |
| `TypeError: Wrong number or type of arguments for ... GetNodalValues` | Missing component argument | `gf.GetNodalValues(vals, 1)` |
| mesh file lists TETRAHEDRON/CUBE but looks 2D | That list is a comment legend | Check `dimension` and element lines (§11.1) |

---

## 15. Quick reference

```bash
# --- Start working ---
cd ~/projects/pymfem-work
source .venv/bin/activate
code .

# --- Run ---
python examples/ex1_readme.py
python examples/ex0.py -m square-disc.mesh     # mfem.org Example 0 figure (§10.6)
python examples/ex1.py -m fichera.mesh         # mfem.org Example 1 figure (§10.8)

# --- View results ---
python tools/view_gf.py                 # sol.gf on mesh.mesh (matplotlib)
python tools/view_gf.py -g "" -m data/star.mesh
glvis -m mesh.mesh -g sol.gf            # GLVis Windows app (alias, §11.3), ex0 output
glvis -m refined.mesh -g sol.gf         # ex1 output; 3D cut: i, x/y rotate, z move (§11.5)

# --- Packages ---
pip install <package>
pip install -r requirements.txt
pip install --upgrade mfem
pip list
deactivate

# --- Git ---
git pull                          # start of every session (two computers, §12.3)
git status
git add .
git commit -m "message"
git push
git pull
git log --oneline

# --- Checks ---
wsl.exe -l -v                     # WSL version 2?
python --version
python -c "import mfem.ser as mfem; print('MFEM OK')"
which python                      # must be .../pymfem-work/.venv/bin/python
git config --global --list
ssh -T git@github.com
ssh-keygen -lf ~/.ssh/id_ed25519.pub   # key fingerprint
```

### Links

- PyMFEM: https://github.com/mfem/PyMFEM
- PyMFEM install options: https://github.com/mfem/PyMFEM/blob/master/INSTALL.md
- MFEM: https://mfem.org
- MFEM example descriptions: https://mfem.org/examples/
- MFEM `ex1.cpp`: https://github.com/mfem/mfem/blob/master/examples/ex1.cpp
- MFEM mesh files: https://github.com/mfem/mfem/tree/master/data
- GLVis: https://glvis.org (download: https://glvis.org/download/)
- GLVis key bindings: https://github.com/GLVis/glvis/blob/master/README.md
- pyglvis (notebook widget): https://github.com/GLVis/pyglvis
- Project repo: https://github.com/AdtPereira/pymfem-work
