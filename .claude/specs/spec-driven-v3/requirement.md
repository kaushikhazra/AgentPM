# Spec-Driven Methodology v3 — Requirement

**Date**: 2026-02-17
**Research**: `.claude/research/spec-driven-development-industry-research.md`

---

## Problem

Taskyn's current spec_driven v2 methodology has 8 node types across 5 mandatory levels with 3 separate verification layers. This is unsustainable:

- Burns excessive context tokens when AI agents traverse the deep hierarchy
- Triggers unnecessary sub-agents for node management
- Applies the same ceremony to bug fixes and major features
- Complex per-type statuses (12+ unique) create cognitive overhead

## Decision

After researching industry SDD approaches (GitHub Spec Kit, Amazon Kiro, Tessl, BMAD, OpenSpec) and reviewing Anthropic's agentic coding best practices, we are implementing a **spec-anchored, 3-level hierarchy** with 5 node types and universal simple statuses.

See `design.md` for the full specification.

## Key Requirements

1. Flatten hierarchy from 5 levels to 3
2. Reduce node types from 8 to 5 (spec, requirement, design, task, todo)
3. Universal simple statuses (draft/active/done/cancelled)
4. Strict gating between phases (requirement → design → task)
5. Time tracking only on todos
6. Tests are todos, not separate verification nodes
7. Scale-adaptive: bugs are todos on existing specs, features get full hierarchy
