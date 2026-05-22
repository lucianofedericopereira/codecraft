---
title: "NimBase: xBase Programming for the Modern Linux Terminal"
date: 2026-04-17
comments: true
---

**NimBase**: A terminal database programming environment written in Nim — xBase syntax, SQLite storage, full-screen TUI forms, and a REPL. The productive simplicity of dBase and Clipper, running on GNU+Linux today.

## What xBase Was

In the 1980s and early 1990s, dBase was how small businesses built data applications. A `.prg` file with `USE`, `APPEND`, `REPLACE`, and `@ SAY GET` commands. Full-screen forms. Table browsing. Procedures and functions. No framework, no ORM, no web layer. Just a programming environment and a data file.

Clipper compiled dBase applications to fast executables. FoxPro added SQL and a better IDE. The whole family — called xBase — gave a generation of programmers the fastest path from "I need to track inventory" to "here is a working application."

That world mostly disappeared. Windows and web UIs replaced the terminal. SQL replaced the navigational model. The productivity of xBase — where a skilled programmer could build a real application in a day — went with it.

NimBase brings it back, on a modern Linux terminal, with SQLite as the storage layer.

## A Taste of the Language

```xbase
PROCEDURE Main
  USE customers
  GO TOP
  DO WHILE .NOT. EOF()
    ? TRIM(customers->last_name) + ", " + customers->first_name
    SKIP
  END
CLOSE
```

```xbase
PROCEDURE AddCustomer
  USE customers
  APPEND BLANK
  @ 5, 10 SAY "Last Name: " GET customers->last_name
  @ 6, 10 SAY "First Name: " GET customers->first_name
  @ 7, 10 SAY "Email: " GET customers->email
  READ
  IF UPDATED()
    ? "Customer added."
  ELSE
    DELETE
    ? "Cancelled."
  END
CLOSE
```

The `@ row, col SAY ... GET ... READ` pattern creates full-screen interactive forms. `GET VALID` adds validation. `GET WHEN` makes fields conditional. The TUI handles input, tab navigation, and confirmation — you describe the form; NimBase renders and drives it.

## Features

- **xBase syntax**: procedures, functions, codeblocks, macro expansion (`&var`)
- **Full-screen TUI**: `@ SAY/GET/READ` forms, boxes, PROMPT menus, TBROWSE browser
- **SQLite storage**: one `.sqlite` file per table, portable, single-file backup
- **Memo fields**: type M opens `$VISUAL`/`$EDITOR` for long-form text
- **Structure editor**: interactive `CREATE` / `MODIFY STRUCTURE`
- **100+ built-ins**: strings, dates, arrays, math, file I/O, database navigation
- **Interactive REPL**: dot-command prompt for ad-hoc queries
- **Export**: `COPY TO ... DELIMITED` (CSV) and `COPY TO ... SDF` (fixed-width)

## Usage

```bash
# Run a program file
nimbase myapp.prg

# Interactive REPL
nimbase
. USE customers
. LIST
. ? RECCOUNT()
. QUIT

# With a specific data directory
nimbase -d ~/mydata/ myapp.prg
```

## Build

```bash
nimble install illwill db_connector
nim c -o:nimbase src/nimbase.nim
# or
make
```

Requires Nim ≥ 2.0.

## Why This Exists

Certain classes of applications — data entry, reporting, local databases, administrative tools — don't need a web interface. They need a fast, keyboard-driven interface with forms, tables, and menus. This is exactly what terminal UIs do well.

Modern developers building these applications reach for Python with curses, or Go with bubbletea, or Rust with ratatui. All fine choices. None of them are as expressive as xBase for data-centric applications, because xBase was designed specifically for this problem.

`USE customers` opens a table. `APPEND BLANK` creates a new record. `@ 5, 10 SAY "Name:" GET customers->name READ` creates a form field. Three lines to add a data entry screen. The expressiveness comes from the domain-specific nature of the language.

NimBase is for developers who know what terminal UIs can do and want a language designed around building them — or for anyone curious about how programming felt before the web became the default interface for everything.

## Links

- **GitHub**: [lucianofedericopereira/nimbase](https://github.com/lucianofedericopereira/nimbase)

## License

MIT
