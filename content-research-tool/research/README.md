# research/ — fallback only

Reports normally live in the **report output path** you configure on the first run (see the **Output** section of `CLAUDE.md`) — e.g. an Obsidian vault, a Notion export folder, or any local notes directory. That configured path is the single source of truth.

A `DD-MM-YYYY.md` file appears **here only if the write to the configured path failed** for that run (path missing, sync issue, or config not yet set up). If you see one, the run couldn't reach your notes directory — move it over once that's fixed.
