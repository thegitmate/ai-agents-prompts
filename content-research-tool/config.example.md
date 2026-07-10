# Config (example)

Copy this file to `config.local.md` and fill in your own values. `config.local.md` is
gitignored, so your personal paths never get committed. On the first run, Claude will ask
you for the report output path and create `config.local.md` for you automatically.

## Report output path
The absolute path to the folder where finished reports get written. Point this at whatever
notes system you use — an Obsidian vault, a Notion export folder, or any local directory.

```
REPORT_OUTPUT_PATH = /absolute/path/to/your/notes/MARKET-RESEARCH
```

Reports are written as `<REPORT_OUTPUT_PATH>/DD-MM-YYYY.md`. If the path is missing or
unwritable, the run falls back to `research/DD-MM-YYYY.md` inside this repo.
