# CLAUDE.md - lacasetitadelascamisetas

## Inheritance

**Do not redefine the global Reflection or Decision Frameworks here — only extend or customize them.**

READ `~/.claude/CLAUDE.md` first to understand the system architecture.

## Project
DuocUC group coursework (second semester, Analista Programador): sales, inventory and user management app for the store of Marisol Mena, using OOP, Python, Tkinter and JSON files. Delivery on 2026-11-06. The teacher will use the GUI and force edge cases; students must explain every line.

## Knowledge Base
`$HOME/.claude/knowledge/Projects/lacasetitadelascamisetas/`
- `overview.md` — stack, commands, project structure
- `decisions.md` — architectural patterns, conventions
- `progress.md` — full session archive
- `progress-current.md` — last 2 sessions (frontmatter: status, next, blockers)
- `blockers.md` — active blockers

**At session start:** READ `progress-current.md` + `decisions.md`
**During work:** UPDATE knowledge/ when finding new patterns or blockers
**At session end:** UPDATE `progress-current.md` + `MASTER_CONTEXT.md`

## Stack
- Python 3.10 or newer, standard library (tkinter, abc, hashlib, unittest) plus one approved dependency: mysql-connector-python (approved 2026-11-17 for the Parcial 3 MySQL migration, HU14 / SCRUM-24)
- Database: MySQL (Homebrew on the Mac) and MariaDB 10.4 (XAMPP on teammates' Windows machines); SQL must run on both
- Test runner: unittest
- Homebrew `python3` on the Mac has no Tkinter: run the GUI with `/opt/homebrew/opt/python@3.13/bin/python3.13`

## Key Commands
```bash
python3.13 main.py             # start the GUI
python3 -m unittest -v         # run the tests
```

## Code Conventions
- Code identifiers, UI strings and comments in Spanish, matching the rest of the project
- Keep the code simple enough for second-semester students to explain: no extra frameworks or clever patterns

## What NOT to do
- Do not add dependencies beyond the standard library and mysql-connector-python
- Do not copy from LaSoaMarisol until the user confirms whose project it is

---
Updated: 2026-11-03
