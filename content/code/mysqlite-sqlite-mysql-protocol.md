---
title: "MySQLite: MySQL Protocol Over SQLite"
date: 2026-04-10
comments: true
---

**MySQLite**: A MySQL wire protocol server backed by SQLite — your application connects on port 3306 as usual, MySQL queries get translated to SQLite SQL on the fly, and all data lives in a single `.sqlite` file.

## The Development Database Problem

Every application that talks to MySQL needs a MySQL server for development. The standard solutions:

- **Docker**: `docker run -e MYSQL_ROOT_PASSWORD=... mysql` works, but adds Docker to your dependency chain, uses significant RAM, and requires managing container lifecycle.
- **System MySQL**: Install MySQL or MariaDB as a system service. It runs at startup, consumes resources, and the data directory is scattered across `/var/lib/mysql`.
- **sqltool**: Isolated instances without containers (covered in a previous article). Better, but still runs a real MySQL daemon.

MySQLite takes a different approach: speak MySQL's protocol, store in SQLite. Your application code doesn't change. No client-side modifications. No driver updates. The `mysql://` connection string works as-is.

## How It Works

MySQL uses a client/server protocol called the MySQL Binary Protocol. When your application connects to port 3306, it performs a handshake, authenticates, and then sends SQL queries as binary packets. The server parses, executes, and returns results in a defined binary format.

MySQLite speaks this protocol. It listens on 3306, performs the handshake, authenticates with configured credentials, and then intercepts the query:

```
Application → MySQL Protocol → MySQLite → SQL Translation → SQLite
```

The translation layer rewrites MySQL SQL to SQLite SQL. Most translation is straightforward — the core SQL subset that applications actually use is nearly identical between the two. The interesting cases are MySQL-specific functions and behaviors:

```sql
-- MySQL                            → SQLite equivalent
NOW()                               datetime('now')
UNIX_TIMESTAMP()                    strftime('%s', 'now')
IFNULL(x, y)                        IFNULL(x, y)           (same)
GROUP_CONCAT(x SEPARATOR ',')       group_concat(x, ',')
AUTO_INCREMENT                      AUTOINCREMENT
```

The translation is not complete MySQL compatibility — it's practical development compatibility. It covers the queries that real applications send.

## Configuration

```ini
[server]
host = 127.0.0.1
port = 3306

[database]
path = data.sqlite

[auth]
user = root
password =
```

```bash
./mysqlite --config config.ini
```

Then connect with any MySQL client or ORM:

```bash
mysql -h 127.0.0.1 -u root -P 3306

# Laravel
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=myapp
DB_USERNAME=root
DB_PASSWORD=

# WordPress wp-config.php — no changes needed
```

The project has been tested with WordPress — including a full install and wp-admin — which involves complex queries, transactions, and schema management. If WordPress works, most applications do.

## Build

```bash
# Requires Nim >= 2.0
nimble build
./mysqlite --config config.ini
```

Or with make:
```bash
make      # build
make run  # build + run with local config.ini
```

Dependencies (including a bundled SQLite 3.52.0 amalgamation) are fetched automatically by nimble. The bundled SQLite means there's no system SQLite version dependency.

## Tradeoffs

MySQLite is a development tool, not a production database. The tradeoffs are deliberate:

**What works**: Standard CRUD, transactions, indexes, most schema operations, any ORM that generates standard SQL.

**What doesn't**: MySQL-specific storage engines, replication, binary logging, stored procedures with MySQL extensions, and full text search.

The goal is to run your development and test suites against something that starts instantly, uses minimal resources, and stores its data in a single file you can copy, commit, or throw away.

## Why Nim

The MySQL Binary Protocol is a stateful, binary protocol with specific framing requirements. Implementing it correctly requires careful byte manipulation, length-prefixed strings, and proper handling of multi-packet responses.

Nim's low-level capabilities make this natural. The protocol implementation is readable — you can see exactly which bytes are being written and why. Nim's performance characteristics mean MySQLite handles connection overhead and query translation without measurable latency for development workloads.

## Links

- **GitHub**: [lucianofedericopereira/mysqlite](https://github.com/lucianofedericopereira/mysqlite)

## License

MIT
