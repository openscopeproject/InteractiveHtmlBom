# Agent Guidelines for Interactive html BOM

This document provides essential information for AI coding agents working on the Interactive html BOM application.

# Team workflow rules

All agents participate in one workflow.

Shared handoff file:
- Read `WORKFLOW_STATE.md` before starting work
- Update `WORKFLOW_STATE.md` before finishing work
- Never overwrite another section unnecessarily
- Preserve decisions, assumptions, blockers, and next steps

Workflow order:
1. Planner clarifies the request with the user
2. Planner writes clarified scope and acceptance criteria
3. Debater critiques the plan
4. Implementor makes the change
5. Reviewer reviews the result
8. Linter checks formatting/linting
9. Commit-message writes the final commit message

Writing rules:
- Keep entries short and structured
- Prefer bullets over long paragraphs
- Record file paths when discussing code changes
- Record exact test commands and results
- Record unresolved questions under "Open Questions"

# Shared workflow rules

All agents must use WORKFLOW_STATE.md as the shared handoff file.

Before starting:
- Read WORKFLOW_STATE.md

After finishing:
- Update only the sections relevant to your role
- Preserve existing content unless it is outdated or clearly incorrect
- Add a short handoff note for the next agent

When working on code, dependencies, libraries, frameworks, or APIs:
- Record important findings in WORKFLOW_STATE.md

Do not use chat history as the only source of truth.
WORKFLOW_STATE.md is the canonical workflow record.


## Development Principles

The objective is to create software that is:

* Easy to use
* Resource-efficient whenever possible
* Maintainable and extensible
* Open-source friendly
* Do not modify already existing and functioning code, keep the changes minimal.
* It is a community project, do not brake other peoples code

Since the project will be released as open source, special attention must be paid to:

* Clean Code principles
* Readability
* Consistent architecture
* Clear and easily understandable codebase organization

The resulting codebase should be approachable, easy to navigate, and simple for contributors to understand and extend.
