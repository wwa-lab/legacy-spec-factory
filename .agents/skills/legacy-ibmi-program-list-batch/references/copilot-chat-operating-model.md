# Copilot Chat Operating Model

Use this reference when the runtime is limited to GitHub Copilot Chat or an
equivalent chat UI.

## Core Constraint

Copilot Chat should not be treated as a reliable concurrent batch runner. A
single chat shares context, source excerpts, plans, and file state across all
requested work. For evidence-heavy IBM i program analysis, that causes context
contamination and status drift.

## Required Pattern

```text
One program = one Copilot Chat session
One session prompt = one generated prompt file
Progress tracking = durable state files
```

The model usually cannot:

- Clear its own chat context.
- Open a new chat by prompt alone.
- Create isolated workers inside one chat.
- Safely run many programs concurrently in one conversation.

## Safe Parallelism

Parallel work is allowed only across separate chats:

```text
Operator A / Chat A -> @CC080
Operator B / Chat B -> @CC081
Operator C / Chat C -> @CC138T
```

Rules:

- One Copilot Chat handles one program at a time.
- Each chat uses a different prompt file.
- Each chat writes to a unique output directory.
- Claim the row as `in_progress` before starting.
- Record `owner` and `session_id` when available.
- Do not let two chats edit the same row or output folder.
- Merge results into the manifest only after validation passes or a blocker is
  recorded.

If the team cannot coordinate row claiming safely, run programs serially.

## Context-Budget Continuation

Add this rule to long-running prompts:

```text
If validation passes and the current session can still safely process the next
bounded batch, continue directly to the next batch. Do not stop early only
because the context budget is approaching a soft limit. If the session cannot
safely continue, write an explicit checkpoint and stop.
```

Bounded means:

- One program at a time.
- At most five routine bodies or source windows per program-analysis turn.
- No full prior artifacts or long source excerpts carried in chat.
- Durable files updated before reading the next source window.

## New Session Handoff

When a chat must stop, write `batch-session-handoff.md` with:

- Batch manifest path.
- Program list/status path.
- Last completed program.
- Last validator status.
- Current blocker, if any.
- Next program.
- Next routines/windows or source ranges.
- Required artifact updates.
- Copy-ready resume prompt.

The next session should resume from files, not from a narrative summary of the
previous chat.
