---
description: Pick up the next unblocked ticket and work it per the project protocol
---
Follow `tickets/README.md`.

1. Run `python scripts/tickets.py next`. If $ARGUMENTS names a ticket ID, use that one instead (verify its dependencies are done).
2. Read the ticket file and every doc it references. Re-read the hard rules in `CLAUDE.md`.
3. Set it `in_progress`, implement it, and verify EVERY acceptance criterion by running something. Tick each with `python scripts/tickets.py check <ID> <n>`.
4. Record any metric with `record_metric` (target vs achieved). Never invent numbers or citations; mark unknowns `UNVERIFIED`.
5. Set `done` only when the tool allows it, append to the ticket's Agent log, and summarize: what was done, what passed, what is left, and the next ticket.
