# Git Contribution Analyzer

[Русская версия](README.ru.md)

A Python script that runs `git blame` on tracked files and visualizes line attribution by author or group. It describes blame attribution for the current working tree, not the total number of lines an author added throughout history or a measure of individual productivity.

## Requirements

- Python 3 and Git available on `PATH`.
- `pandas` and `matplotlib`.
- A Git checkout whose `.git` is a directory; linked worktrees with a `.git` file are not supported by the current check.

```bash
python -m pip install pandas matplotlib
python git_stat_script.py /path/to/repository
python git_stat_script.py /path/to/repository --grouping-file /path/to/grouping.txt
```

Without `--grouping-file`, the script looks for `grouping.txt` next to the script. Lines beginning with `#` and blank lines are ignored. Each entry maps aliases to a group:

```text
Team A: Alice, Alice Smith
Team B: Bob
```

The program prints a table and displays bar and pie charts. Large repositories can take a long time because it calls `git blame` for each tracked file; files whose blame fails are skipped. Names are matched against Git's `author` field. The commands and graphical output were not tested in the current environment.