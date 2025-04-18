# Command Toolkit

A collection of useful command-line utilities for code management and productivity.

## Installation

### Requirements

- Python 3.6+
- Git (to download this repository)

### Windows

1. Clone the repository

    ```powershell
    git clone https://github.com/OK-Diamond/PS-Utils.git
    ```

2. Run the setup script

    ```powershell
    cd PS-Utils
    ./setup_win.ps1
    ```

This will automatically register all commands in your PowerShell profile.

### Linux

To be added

### macOS

To be added

## Available Commands

### combine-files

Combines multiple files into one for ease of sharing/export.

#### Requirements

- Python
  - Libraries: argparse, fnmatch

**Usage:**

```powershell
combine-files /path/to/folder output.txt
```

Run `combine-files -h` for info on args.

**Example:**

```powershell
# Combine all Python files from a project into a single file
combine-files /path/to/project output.txt --include "*.py"

# Combine all code files except specific directories
combine-files /path/to/project output.txt --exclude-dirs "node_modules" "venv" "tmp"
```

## Uninstallation

Running the setup script will create an uninstall script in the same folder.

### Windows

Run the uninstall script to remove all commands:

```powershell
cd <path of this folder>
./uninstall_win.ps1
```

### Linux & MacOS

To be added.
