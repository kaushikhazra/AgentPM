# Spec-Driven Development: Industry Research

**Date**: 2026-02-17
**Purpose**: Comprehensive research on spec-driven development methodologies, frameworks, tools, and approaches across the software industry. This research informs the methodology redesign for Taskyn PM.

---

## Table of Contents

1. [What is Spec-Driven Development?](#1-what-is-spec-driven-development)
2. [Historical Roots and Related Methodologies](#2-historical-roots-and-related-methodologies)
3. [Existing Frameworks and Methodologies](#3-existing-frameworks-and-methodologies)
4. [Hierarchy and Structure of Work Items](#4-hierarchy-and-structure-of-work-items)
5. [AI-First / AI-Assisted Spec-Driven Development](#5-ai-first--ai-assisted-spec-driven-development)
6. [Tools and Implementations](#6-tools-and-implementations)
7. [Verification and Validation Patterns](#7-verification-and-validation-patterns)
8. [Lightweight vs Heavyweight Approaches](#8-lightweight-vs-heavyweight-approaches)
9. [Criticisms and Limitations](#9-criticisms-and-limitations)
10. [Real-World Adoption](#10-real-world-adoption)
11. [Three Levels of Specification Rigor](#11-three-levels-of-specification-rigor)
12. [Comparative Analysis of Tools](#12-comparative-analysis-of-tools)
13. [Key Takeaways for Taskyn](#13-key-takeaways-for-taskyn)

---

## 1. What is Spec-Driven Development?

### Definition

Spec-Driven Development (SDD) is a development paradigm that inverts the traditional relationship between specifications and code. Instead of specifications serving code, **code serves specifications**. The specification becomes the source of truth, and implementation (whether human-written or AI-generated) is a derived artifact.

The term was academically formalized in 2004 as a synergy between Test-Driven Development (TDD) and Design by Contract (DbC), but it experienced a major renaissance in 2025 driven by LLM-powered agentic workflows.

### Core Principle

> "The Product Requirements Document isn't a guide for implementation; it's the source that generates implementation. Technical plans aren't documents that inform coding; they're precise definitions that produce code."
> -- GitHub Spec Kit documentation

### The Power Inversion

| Aspect | Traditional Development | Spec-Driven Development |
|--------|------------------------|------------------------|
| Source of truth | Code | Specification |
| Architecture | Advisory | Enforceable |
| Drift | Discovered post-facto | Prevented pre-runtime |
| Specs role | Scaffolding, discarded | Living, executable |
| Code role | Primary artifact | Generated/derived artifact |

### Multiple Interpretations

The industry uses "spec-driven development" to mean different things depending on context:

1. **API-First / Contract-First**: Writing OpenAPI/GraphQL specs before implementation (Atlassian, Stripe)
2. **BDD/SBE Style**: Executable specifications using Given/When/Then scenarios (Cucumber, SpecFlow)
3. **Design Doc / RFC Driven**: Writing design documents for review before coding (Google, Uber, Airbnb)
4. **AI-Assisted SDD**: Using structured specs as prompts for AI code generation (Kiro, Spec Kit, 2025+)
5. **Formal Specification**: Mathematical specification with proof systems (TLA+, Alloy, Z notation)

---

## 2. Historical Roots and Related Methodologies

### Design by Contract (DbC) — Bertrand Meyer, 1986

The grandfather of spec-driven thinking. DbC defines software component interfaces using three formal elements:

- **Preconditions**: What must be true before a method is called
- **Postconditions**: What must be true after a method completes
- **Class Invariants**: What must always be true for an object

First implemented in Eiffel. The key insight: contracts are not documentation -- they are executable, verifiable constraints. DbC proved that specifications can be machine-checked, not just human-read.

### Test-Driven Development (TDD) — Kent Beck, 2003

TDD inverted the code-then-test pattern by writing tests first. The Red-Green-Refactor cycle:
1. Write a failing test (the specification of behavior)
2. Write minimal code to pass
3. Refactor

TDD made specs executable at the unit level but didn't address higher-level system specifications.

### Behavior-Driven Development (BDD) — Dan North, 2006

BDD extended TDD upward to the behavior level using natural-language-like syntax:

```gherkin
Given a user is logged in
When they add an item to cart
Then the cart count should increase by 1
```

Key tools: Cucumber, SpecFlow, JBehave, RSpec. BDD emphasized **shared understanding** between business and technical teams, not just testing.

### Acceptance Test-Driven Development (ATDD)

ATDD focuses on defining acceptance criteria before implementation, with automated acceptance tests. ATDD emphasizes testing; BDD emphasizes behavior and shared understanding. The key difference is audience and intent rather than mechanism.

### Specification by Example (SBE) — Gojko Adzic, 2011

SBE formalized the practice of using concrete examples to specify requirements. Adzic chose the name over BDD because it emphasizes the nature of requirements ("examples") rather than the process ("behavior").

Key insight from Adzic: many teams confuse BDD with test automation using Given/When/Then. True SBE is a **collaborative requirements discovery** approach, not a testing technique.

Four main benefits:
1. Produces living, reliable documentation
2. Defines expectations clearly and makes validation efficient
3. Reduces rework
4. Assures that software built is right for its purpose

### RFC-Driven Development

Requests for Comments (RFCs) are design documents that engineering teams use to communicate intent and get feedback before implementation. Major companies use variations:

- **Google**: "Design Docs"
- **Uber**: "RFCs"
- **Airbnb**: "Specs and Design Docs for both Product and Engineering"
- **Facebook/Meta**: Design review process
- **Amazon**: 6-page narratives (not exactly RFCs but same philosophy)

RFC structure typically includes: Context, Problem Statement, Proposed Solution, Alternatives Considered, Open Questions.

Benefits: Engineers who write design docs and ask for reviews ship more maintainable architecture, just as engineers who write tests and ask for code reviews ship more maintainable code.

### Architecture Decision Records (ADRs) — Michael Nygard

ADRs capture a single architectural decision and its rationale. They differ from RFCs in scope (one decision vs. one feature) and lifecycle (immutable record vs. living document).

Standard ADR template: Title, Status, Context, Decision, Consequences.

ADRs create a living documentation system for architectural consistency. They are used as reference during code and architectural reviews.

### Model-Driven Development (MDD)

MDD uses visual or formal models to generate code. Tools like Simulink (automotive), SCADE (avionics), and Enterprise Architect generate production code from models. MDD is the direct ancestor of AI-assisted SDD -- both generate code from higher-level abstractions. The key difference: LLMs remove the constraint of predefined, parseable spec languages.

---

## 3. Existing Frameworks and Methodologies

### The Modern SDD Landscape (2025-2026)

The 2025 renaissance of SDD was triggered by the convergence of:
- LLM coding agents becoming capable enough for production code
- "Vibe coding" (unstructured prompting) producing unmaintainable results
- Need for repeatable, auditable AI-assisted development workflows

### Named Frameworks

| Framework | Creator | Approach | Key Innovation |
|-----------|---------|----------|----------------|
| **GitHub Spec Kit** | GitHub | CLI + slash commands | Constitution-based governance, 3-phase gated workflow |
| **Amazon Kiro** | AWS | Full IDE | EARS notation for requirements, integrated design phase |
| **Tessl Framework** | Tessl | Platform | Spec Registry (10K+ pre-built specs), spec-as-source aspiration |
| **BMAD Method** | BMad Code | Multi-agent | 21 specialized AI agents, scale-adaptive intelligence |
| **OpenSpec** | Fission-AI | Lightweight CLI | No phase gates, works with 20+ assistants, vendor-neutral |
| **SpecPulse** | SpecPulse | Python framework | CLI creates foundation, AI enhances content |

### Traditional/Established Frameworks

| Framework | Origin | Focus |
|-----------|--------|-------|
| **Cucumber/Gherkin** | BDD community | Executable plain-language specs |
| **OpenAPI/Swagger** | API community | Contract-driven API development |
| **Pact** | SEEK/DiUS | Consumer-driven contract testing |
| **Specmatic** | Specmatic | API contract as executable spec |
| **Simulink** | MathWorks | Model-based code generation (automotive) |
| **TLA+** | Leslie Lamport | Formal specification of concurrent systems |
| **Alloy** | MIT | Lightweight formal methods |

---

## 4. Hierarchy and Structure of Work Items

### Traditional Agile Hierarchy

```
Theme / Initiative
  └── Epic
        └── Feature
              └── User Story
                    └── Task / Sub-task
```

Typically 4-5 levels. Epics span multiple sprints; stories fit within a sprint; tasks are assignable units.

### GitHub Spec Kit Hierarchy (3-phase, gated)

```
Specification (spec.md)
  ├── Business requirements
  ├── User stories
  ├── Acceptance criteria
  └── Edge cases
        ↓ [Gate: Human Review]
Implementation Plan (plan.md)
  ├── Technical architecture
  ├── Technology choices
  ├── Phase breakdown
  └── Rationale for decisions
        ↓ [Gate: Human Review]
Tasks (tasks.md)
  ├── Discrete, reviewable units
  ├── Parallelization markers [P]
  └── Verification criteria per task
```

Additional supporting artifacts:
- `data-model.md` (schemas)
- `research.md` (technical investigation)
- `contracts/` (API specifications)
- `quickstart.md` (validation scenarios)

### Amazon Kiro Hierarchy (3-phase, EARS-based)

```
Requirements (requirements.md)
  ├── User Stories in EARS notation
  ├── Acceptance Criteria (structured)
  └── Format: WHEN [condition] THE SYSTEM SHALL [behavior]
        ↓ [Gate: Human Review]
Design (design.md)
  ├── Technical architecture
  ├── Sequence diagrams
  └── Implementation considerations
        ↓ [Gate: Human Review]
Tasks (tasks.md)
  ├── Sequenced by dependencies
  ├── Trackable completion status
  └── Optional comprehensive tests
```

EARS (Easy Approach to Requirements Syntax) format: `While <precondition>, when <trigger>, the <system name> shall <system response>.`

### BMAD Method Hierarchy (Multi-agent, deep)

```
Product Vision (via Analyst Agent)
  └── PRD (via PM Agent)
        └── Architecture Design (via Architect Agent)
              └── Development Stories (via Scrum Master Agent)
                    └── Implementation Tasks (via Dev Agent)
                          └── Validation (via QA Agent)
```

Key distinction: each level is owned by a specialized AI agent persona. The Scrum Master agent transforms plans into "hyper-detailed development stories."

### OpenSpec Hierarchy (Lightweight, no gates)

```
Change Proposal (.openspec/changes/<id>/proposal.md)
  └── Specification (spec.md)
        └── Design (design.md)
              └── Tasks (tasks.md)
```

Key distinction: no rigid phase gates. Any artifact can be updated at any time. Each change gets its own folder.

### InfoQ/Academic 5-Layer Execution Model

```
Specification Layer (declarative intent)
  └── Generation Layer (multi-target compilation)
        └── Artifact Layer (disposable outputs)
              └── Validation Layer (continuous enforcement)
                    └── Runtime Layer (constrained operations)
```

This represents SDD as an architectural pattern, not just a development workflow.

### Comparison: Depth and Granularity

| Approach | Levels | Smallest Unit | Gate Type |
|----------|--------|---------------|-----------|
| Agile (Jira) | 4-5 | Sub-task | Sprint boundary |
| Spec Kit | 3 | Task in tasks.md | Human review |
| Kiro | 3 | Task in tasks.md | Human review |
| BMAD | 5-6 | Implementation task | Agent handoff |
| OpenSpec | 3-4 | Task | None (flexible) |
| Formal (TLA+) | 2 | Property/invariant | Proof verification |

---

## 5. AI-First / AI-Assisted Spec-Driven Development

### Why SDD Rose in the AI Era

The problems with "vibe coding" (unstructured AI prompting) made SDD relevant again:

1. **No institutional memory**: Chat-based prompts disappear; specs persist
2. **Inconsistent quality**: Different prompts produce wildly different results; specs standardize intent
3. **No verification**: Vibe coding has no built-in quality gates; SDD has explicit validation
4. **Context loss**: Long conversations lose context; specs maintain bounded context
5. **Unrepeatable**: Can't reproduce the same result; specs are deterministic inputs

### The Spec as AI Prompt

In AI-assisted SDD, the spec serves dual purpose:
1. **Human communication**: Describes intent to stakeholders
2. **Machine instruction**: Provides structured input that reduces LLM hallucination

Research shows that providing LLMs with semi-structured input significantly improves reasoning performance and reduces hallucinations, making machine-readable specs essential.

### Addy Osmani's Spec Framework for AI Agents

Six core areas for effective AI specs:
1. **Commands**: Full executable commands with flags
2. **Testing**: Framework details, locations, coverage expectations
3. **Project Structure**: Where code, tests, docs belong
4. **Code Style**: Real code snippets over paragraphs of description
5. **Git Workflow**: Branch naming, commit format, PR requirements
6. **Boundaries**: What agents should never touch

Three-tier boundary system:
- **Always do**: Safe actions without asking
- **Ask first**: High-impact changes requiring approval
- **Never do**: Hard stops (never commit secrets)

### Workflow Pattern for AI-Assisted SDD

The emerging consensus workflow:

```
1. SPECIFY  →  Define behavior, requirements, acceptance criteria
                (human-led, AI-assisted drafting)

2. PLAN     →  Generate technical architecture, data models
                (AI-led, human-reviewed)

3. TASKS    →  Break into small, reviewable units
                (AI-generated, human-approved)

4. IMPLEMENT →  Execute individual tasks
                (AI-executed, human-verified)

5. VALIDATE  →  Verify code matches specifications
                (automated tests + human review)
```

### Key Insight: Minimum Viable Specification

Not every change needs a full spec. The golden rule: **use the minimum level of specification rigor that removes ambiguity for your context.** A bug fix might need one sentence; a new feature might need a full spec.

Kiro was criticized for applying its full workflow even to small bugs -- "like using a sledgehammer to crack a nut."

---

## 6. Tools and Implementations

### GitHub Spec Kit

- **Type**: Open-source CLI toolkit
- **Released**: 2025
- **Approach**: 3-phase gated workflow (Specify, Plan, Tasks)
- **Key Innovation**: "Constitution" -- immutable principles that AI must always follow
- **Integration**: Works with GitHub Copilot, Claude Code, Gemini CLI
- **Commands**: `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`
- **Structure**: Creates `specs/[branch-name]/` directories with spec.md, plan.md, tasks.md
- **Gates**: Pre-implementation gates (Simplicity, Anti-Abstraction, Integration-First)
- **Limitation**: Creates a branch per spec (spec-first only, not spec-anchored over time)

### Amazon Kiro

- **Type**: Full IDE (fork of VS Code)
- **Released**: 2025
- **Approach**: 3-phase (Requirements, Design, Tasks) using EARS notation
- **Key Innovation**: Integrated IDE experience, structured requirements format
- **Files Generated**: requirements.md, design.md, tasks.md
- **EARS Format**: `WHEN [condition/event] THE SYSTEM SHALL [expected behavior]`
- **Limitation**: Heavyweight for small changes; doesn't scale down well

### Tessl Framework

- **Type**: Platform with CLI and registry
- **Released**: 2025
- **Approach**: Spec-anchored to spec-as-source
- **Key Innovation**: Spec Registry with 10,000+ pre-built specs for open-source libraries
- **Unique**: Only major tool aspiring to spec-as-source level
- **Generated code marked**: `// GENERATED FROM SPEC - DO NOT EDIT`
- **Philosophy**: Specs as long-term memory that persists across agent sessions

### BMAD Method

- **Type**: Open-source multi-agent framework
- **Approach**: 21 specialized agents with 50+ guided workflows
- **Key Innovation**: Scale-adaptive intelligence (adjusts from bug fixes to enterprise systems)
- **Agent Roles**: Analyst, PM, Architect, Scrum Master, Dev, QA, and more
- **Philosophy**: Source code is no longer the sole source of truth; documentation (PRDs, architecture, stories) is
- **Unique**: Human-in-the-loop governance structure with specialized agent personas

### OpenSpec

- **Type**: Lightweight open-source framework
- **Released**: 2025
- **Approach**: No phase gates, flexible iteration
- **Key Innovation**: Vendor-neutral (works with 20+ AI assistants), no API keys needed
- **Philosophy**: Iterate freely, adapt as you go. No rigid phase gates.
- **Structure**: `.openspec/changes/<id>/` with proposal, specs, design, tasks
- **Unique**: Most lightweight of the modern SDD tools

### SpecPulse

- **Type**: Python CLI framework
- **Approach**: Two-step (CLI creates structure, AI enhances content)
- **Key Innovation**: Safe operations -- AI only works on files the CLI has created
- **Install**: `pip install specpulse`
- **Platform**: Cross-platform (Windows, macOS, Linux)

### Traditional Specification Tools

| Tool | Domain | Spec Type |
|------|--------|-----------|
| OpenAPI/Swagger | REST APIs | Schema-based contract |
| GraphQL SDL | GraphQL APIs | Type-based schema |
| Protocol Buffers | RPC/Data | Binary schema |
| Cucumber | BDD | Gherkin scenarios |
| Pact | Microservices | Consumer-driven contracts |
| Specmatic | APIs | Contract-as-test |
| TLA+ | Distributed systems | Formal temporal logic |
| Simulink | Control systems | Visual model |

---

## 7. Verification and Validation Patterns

### Verification Approaches in SDD

The arxiv paper identifies three complementary verification approaches:

1. **Automated Testing** (unit, integration, acceptance)
   - Each acceptance criterion in the spec becomes a test case
   - Tests fail if implementation deviates from spec
   - CI/CD pipeline embedding of spec validators

2. **BDD Scenario Execution**
   - Given/When/Then scenarios serve as executable verification
   - Living documentation that stays in sync with code
   - Tools: Cucumber, SpecFlow, Behave

3. **Contract Testing**
   - API contracts verified against implementations
   - Consumer-driven contracts (Pact)
   - Schema validation, payload inspection
   - Tools: Pact, Specmatic

### Gated Workflow Patterns

**GitHub Spec Kit gates:**
- Simplicity Gate: "Using 3 or fewer projects? No future-proofing?"
- Anti-Abstraction Gate: "Using framework directly? Single model representation?"
- Integration-First Gate: "Contracts defined? Contract tests written?"
- `/speckit.analyze` acts as quality gate for consistency

**Kiro gates:**
- Each phase (Requirements, Design, Tasks) requires human review
- Implementation tasks are sequenced by dependencies
- Tests can be generated alongside tasks

### Drift Detection (InfoQ Architecture Model)

In mature SDD systems, drift detection becomes continuous:

- **Schema validation**: Does implementation match declared schemas?
- **Backward compatibility analysis**: Do changes break existing contracts?
- **Specification differentials**: Has spec diverged from implementation?
- **Contract verification**: Do runtime messages match declared interfaces?

Drift types: structural, behavioral, semantic, security-related, evolutionary.

### Test-First in SDD Context

The strictest SDD implementations require:
1. Write specification (acceptance criteria)
2. Generate tests FROM specification (tests must fail - Red phase)
3. Get tests approved by human
4. Generate implementation to make tests pass (Green phase)
5. Verify implementation matches spec (not just tests)

### LLM-as-a-Judge

Addy Osmani recommends using a second AI agent to review the first agent's output against quality guidelines. This is a form of automated peer review where:
- Agent A generates code from spec
- Agent B reviews code against spec for compliance
- Discrepancies flagged for human review

---

## 8. Lightweight vs Heavyweight Approaches

### The Spectrum

```
Lightweight                                              Heavyweight
|                                                              |
Vibe     OpenSpec   Kiro/     BMAD      Formal     Waterfall
Coding              Spec Kit  Method    Methods    BDUF
                                       (TLA+)
|         |          |         |          |           |
No spec   Flexible   Gated    Multi-    Proof-     Exhaustive
          iteration  phases   agent     based      documentation
                              deep      verification before any code
```

### Lightweight Approaches

**Characteristics:**
- Minimal documentation overhead
- Flexible iteration (update any artifact anytime)
- No rigid phase gates
- Focus on removing ambiguity, not exhaustive completeness
- Practical for small-medium features

**Examples:**
- OpenSpec: No gates, any artifact updatable anytime
- Addy Osmani's workflow: Minimal but focused specs
- Natural Language Development (Marmelab): Iterative prompting with simple instructions

**When to use:**
- Small to medium features
- Exploratory work
- Solo developers
- Rapid prototyping that needs to become production

### Heavyweight Approaches

**Characteristics:**
- Comprehensive documentation
- Strict phase gates with human approval
- Multi-level artifact generation
- Formal verification possible
- Audit trails

**Examples:**
- BMAD Method: 21 agents, 50+ workflows
- GitHub Spec Kit: Constitutional governance, 3 gates
- Formal methods (TLA+): Mathematical proofs
- Waterfall BDUF: Complete spec before any code

**When to use:**
- Large cross-team systems
- Compliance-heavy domains (financial, medical, automotive)
- Systems requiring formal verification
- When multiple AI agents need coordination

### The Sweet Spot

The emerging consensus is that **spec-anchored** (maintaining specs over time, with automated alignment checks) represents the practical sweet spot for most production systems. It provides enough structure to prevent drift without the overhead of spec-as-source or the fragility of spec-first-then-forget.

### Critical Insight: Scale Matters

SDD tools need to scale both up AND down:
- A bug fix should not require a 3-phase gated workflow
- A new microservice should not be vibe-coded
- The methodology should adapt to problem size

BMAD Method addresses this with "scale-adaptive intelligence." OpenSpec addresses it by having no gates. Most other tools do not address it well.

---

## 9. Criticisms and Limitations

### The Waterfall Accusation

The most common criticism: SDD is "Waterfall reborn." Several voices make this case:

**Marmelab ("The Waterfall Strikes Back"):**
- SDD revives Big Design Up Front principles
- Software development is fundamentally non-deterministic
- Specs pile up hypotheses that may not match reality
- Over-engineering: specs contain "imaginary corner cases and overkill refinements"
- Doubled review burden (review specs + review code)

**Scott Logic ("Radical Idea or Reinvented Waterfall?"):**
- The fastest path is still iterative prompting and review
- AI's superpower is making code cheap; SDD slows that down
- SDD "drags you right back into the past"
- Tested Spec Kit on real product increment; found it slower than iterative approach

### Seven Practical Problems (Marmelab)

1. **Context Blindness**: Agents miss existing functions that need updates
2. **Excessive Documentation**: Too much text, especially in design phase
3. **Over-Engineering**: Repetitions, imaginary corner cases, overkill
4. **Misapplied Terminology**: Generated "User Stories" often aren't real user needs
5. **Doubled Review Burden**: Review specs, then review code
6. **False Confidence**: Agents don't always follow the spec
7. **Diminishing Returns**: Benefits decrease as applications grow

### Spec Rot / Spec Drift

Maintaining parity between spec and code invites "spec rot" -- specs that are out of date. This increases governance and review burden. Only spec-as-source (where code is generated from spec) truly solves this, but the tooling isn't mature enough for most domains.

### Role Problem

A valid criticism: SDD requires the spec writer to be both:
- A business analyst (to catch requirement errors)
- A developer (to catch design errors)

This is a rare combination. SDD doesn't eliminate the need for skilled developers; it shifts where their skills are applied.

### Brownfield Limitations

SDD works best for greenfield (new) projects. For brownfield (existing) codebases:
- Agents struggle with existing code context
- Specs miss existing patterns and conventions
- The larger the codebase, the less useful pure SDD becomes

### Counter-Arguments

1. **Not waterfall**: SDD iterations are much shorter than waterfall cycles. The spec-plan-implement loop can happen in hours, not months.
2. **Not all-or-nothing**: Use minimum viable specification for the context.
3. **Spec drift is solvable**: Automated tests anchored to specs catch drift early.
4. **The alternative is worse**: Vibe coding produces unmaintainable code at scale.

---

## 10. Real-World Adoption

### Enterprise Adoption

- **Google**: Design Docs are mandatory for significant changes
- **Uber**: RFC process for cross-team changes
- **Airbnb**: Specs and Design Docs for both Product and Engineering
- **Stripe**: API-first development with OpenAPI specs
- **GitHub**: Public GraphQL schema as living contract; published breaking-change policy

### Domain-Specific Adoption

**Financial Services:**
- Enterprise teams report 75% reduction in cycle time for API changes
- Incompatibilities caught at spec review rather than production
- Spec-anchored approach using OpenAPI + Specmatic

**Open Source Projects:**
- Apache Kafka uses Kafka Improvement Proposals (KIPs)
- KIP structure: problem/motivation, proposed change, public interfaces, compatibility impact, test plan, alternatives
- Changes discussed on mailing lists, adopted by formal vote

**Automotive / Embedded:**
- Spec-as-source is already standard
- Simulink models generate certified production code
- Regulatory requirements mandate formal specification

### Current Adoption Rates

SDD adoption remains under 20% despite proven benefits. Barriers include:
- Difficult mindset shift (implementation-first to spec-first thinking)
- Tooling immaturity (especially for brownfield codebases)
- Perception as waterfall/BDUF
- Lack of consensus on "correct" SDD workflow

### Academic Research

The paper "Spec-Driven Development: From Code to Contract in the Age of AI Coding Assistants" (Deepak Babu Piskala, 2025, arXiv:2602.00180) provides the most comprehensive academic treatment, analyzing SDD across three rigor levels with case studies from API development, enterprise systems, and embedded software.

---

## 11. Three Levels of Specification Rigor

The arxiv paper defines a crucial spectrum of how authoritative specifications are:

### Level 1: Spec-First

- **Definition**: Write specification before coding; may drift post-implementation
- **Spec lifecycle**: Created before implementation, possibly abandoned after
- **Code relationship**: Code is influenced by spec but not continuously verified against it
- **Best for**: Prototypes, AI-assisted initial development, features where upfront clarity prevents assumption-making
- **Tools**: All SDD tools support this level
- **Risk**: Spec rot after implementation

### Level 2: Spec-Anchored

- **Definition**: Specifications evolve alongside code throughout system lifecycle
- **Spec lifecycle**: Living document, maintained as code changes
- **Code relationship**: Automated tests enforce alignment between spec and code
- **Best for**: Production systems with multiple maintainers, long-lived services
- **Verification**: BDD scenarios, contract tests, CI/CD integration
- **Tools**: Tessl aspires to this; most tools support it with discipline
- **Risk**: Maintenance overhead; requires process discipline

### Level 3: Spec-as-Source

- **Definition**: Humans edit only specifications; machines generate code entirely from specs
- **Spec lifecycle**: THE source code; traditional code is a generated artifact
- **Code relationship**: Code is 100% generated, marked as `// DO NOT EDIT`
- **Best for**: Domains with mature generation tooling (automotive, embedded)
- **Verification**: Formal verification possible; generated code is deterministic
- **Tools**: Simulink, SCADE; Tessl exploring for general software
- **Risk**: Requires mature, trusted generation tooling; not viable for most domains yet

### Decision Framework

```
Does AI assistance or complex requirements apply?
  → Spec-First (minimum rigor)

Long-lived system with multiple maintainers?
  → Spec-Anchored (enforce alignment)

Viable code generation tooling exists for your domain?
  → Spec-as-Source (maximize automation)
```

**Golden Rule**: Use the minimum level of specification rigor that removes ambiguity for your context.

---

## 12. Comparative Analysis of Tools

### Feature Comparison Matrix

| Feature | Spec Kit | Kiro | Tessl | BMAD | OpenSpec |
|---------|----------|------|-------|------|---------|
| **Phase gates** | 3 strict | 3 strict | Flexible | Agent-based | None |
| **Spec format** | Markdown | EARS notation | Flexible | PRD-style | Markdown |
| **Smallest unit** | Task | Task | Spec | Story/Task | Task |
| **AI integration** | Multi-tool | Built-in IDE | Platform | Multi-agent | Multi-tool |
| **Scale-adaptive** | No | No | Partially | Yes | Yes |
| **Brownfield support** | Limited | Limited | Better | Better | Better |
| **Spec-anchored** | No (branch-per-spec) | No | Yes | Partially | No |
| **Open source** | Yes | No | Partially | Yes | Yes |
| **Vendor lock-in** | Low | High (IDE) | Medium | Low | None |
| **Constitution/Rules** | Yes | No | Via registry | Via agent personas | No |
| **Team collaboration** | Good | Good | Good | Good | Basic |

### Workflow Comparison

**Spec Kit**: Specify → Plan → Tasks → (Implement) — Branch per spec, constitutional governance
**Kiro**: Requirements → Design → Tasks → (Implement) — EARS notation, IDE-integrated
**Tessl**: Spec → (optional Plan) → Implement — Registry-enhanced, spec-anchored aspiration
**BMAD**: Vision → PRD → Architecture → Stories → Tasks → Implementation → Validation — Deep multi-agent
**OpenSpec**: Proposal → Spec → Design → Tasks — No gates, flexible iteration

### Strengths and Weaknesses

**Spec Kit**
- Strengths: Well-structured, constitutional governance, open source
- Weaknesses: Branch-per-spec limits long-term spec maintenance, heavyweight for small changes

**Kiro**
- Strengths: Integrated IDE experience, structured EARS notation
- Weaknesses: Vendor lock-in to IDE, doesn't scale down for small tasks

**Tessl**
- Strengths: Spec Registry solves library hallucination, spec-anchored vision
- Weaknesses: Newer/less mature, platform dependency

**BMAD**
- Strengths: Scale-adaptive, comprehensive agent coverage, handles complexity well
- Weaknesses: Complex setup, 21 agents may be overkill, heavy framework

**OpenSpec**
- Strengths: Lightweight, vendor-neutral, no lock-in, flexible
- Weaknesses: Less structure may lead to inconsistency, no built-in verification

---

## 13. Key Takeaways for Taskyn

### What the Industry Tells Us

1. **The 3-file pattern is emerging as standard**: `requirements.md`, `design.md`, `tasks.md` (used by Kiro, our Taskyn, and increasingly by the community). This pattern works because it separates concerns cleanly: what (requirements), how (design), and do (tasks).

2. **Gated workflows have value but must scale down**: The biggest criticism of SDD is that it's too heavyweight for small changes. Any methodology in Taskyn must support both a 5-minute bug fix and a multi-week feature without ceremony overhead.

3. **Spec-anchored is the sweet spot**: Specs that are written once and forgotten (spec-first) rot. Specs that generate all code (spec-as-source) require tooling that doesn't exist yet. Spec-anchored -- maintaining specs alongside code -- is the practical middle ground.

4. **Verification must be built into the workflow, not bolted on**: Every spec should produce testable acceptance criteria. The best SDD workflows generate tests before implementation, not after.

5. **AI agents need bounded context**: LLMs work best on one focused task at a time. Task decomposition into small, reviewable units is not just project management -- it's prompt engineering.

6. **Scale-adaptive methodology is rare but needed**: BMAD and OpenSpec address this; most tools don't. Taskyn's methodology should automatically adapt to problem size.

7. **The spec is the PM dashboard's backing store**: Taskyn's current approach of having PM nodes point to spec files (not duplicate them) is aligned with industry best practice. The spec files are the source of truth; the PM system is the dashboard.

### Hierarchy Design Considerations

The industry shows a range of 3-6 levels in work item hierarchies:

| Level | Spec Kit | Kiro | BMAD | Agile/Jira | Our Current |
|-------|----------|------|------|------------|-------------|
| 1 | Spec | Requirements | Vision/PRD | Epic | Spec |
| 2 | Plan | Design | Architecture | Feature | Design |
| 3 | Tasks | Tasks | Stories | Story | Implementation |
| 4 | — | — | Tasks | Task | Validation |
| 5 | — | — | Subtasks | Subtask | — |

Our current 4-level hierarchy (spec → design → implementation → validation) is within the sweet spot. The question is whether those levels represent the right concepts and whether the gating between them is appropriate.

### Anti-Patterns to Avoid

1. **Over-specification**: Generating comprehensive specs for trivial changes
2. **Spec rot**: Specs that are never updated after initial creation
3. **False confidence**: Assuming agents followed the spec without verification
4. **Doubled review burden**: Reviewing both spec and code without automation
5. **Context blindness**: Ignoring existing codebase when generating specs
6. **Bulk node creation**: Creating all PM nodes upfront rather than as work happens (we already learned this lesson)

### What Competitors Do That We Don't (Yet)

1. **Constitutional governance** (Spec Kit): Immutable principles that constrain AI behavior
2. **Spec Registry** (Tessl): Pre-built specs for common libraries to prevent hallucination
3. **EARS notation** (Kiro): Structured, testable requirements format
4. **Scale-adaptive intelligence** (BMAD): Adjusting process weight to problem size
5. **LLM-as-a-Judge** (Osmani): Automated AI review of AI output
6. **Drift detection** (InfoQ model): Continuous spec-code alignment checking

---

## Sources

- [Spec-Driven Development - Wikipedia](https://en.wikipedia.org/wiki/Spec-driven_development)
- [GitHub Spec Kit - spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md)
- [Diving Into Spec-Driven Development With GitHub Spec Kit - Microsoft](https://developer.microsoft.com/blog/spec-driven-development-spec-kit)
- [Spec Driven Development: When Architecture Becomes Executable - InfoQ](https://www.infoq.com/articles/spec-driven-development/)
- [Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl - Martin Fowler](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- [Spec-driven development: Unpacking 2025's key practices - Thoughtworks](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices)
- [How to write a good spec for AI agents - Addy Osmani](https://addyosmani.com/blog/good-spec/)
- [My LLM coding workflow going into 2026 - Addy Osmani](https://addyosmani.com/blog/ai-coding-workflow/)
- [Spec-Driven Development: From Code to Contract - arXiv](https://arxiv.org/html/2602.00180v1)
- [Spec-Driven Development: The Waterfall Strikes Back - Marmelab](https://marmelab.com/blog/2025/11/12/spec-driven-development-waterfall-strikes-back.html)
- [Putting Spec Kit Through Its Paces - Scott Logic](https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html)
- [How spec-driven development improves AI coding quality - Red Hat](https://developers.redhat.com/articles/2025/10/22/how-spec-driven-development-improves-ai-coding-quality)
- [Amazon Kiro Specs Documentation](https://kiro.dev/docs/specs/)
- [Kiro Concepts Documentation](https://kiro.dev/docs/specs/concepts/)
- [BMAD Method - GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
- [OpenSpec - GitHub](https://github.com/Fission-AI/OpenSpec)
- [OpenSpec Framework](https://openspec.dev/)
- [SpecPulse - GitHub](https://github.com/specpulse/specpulse)
- [Tessl Platform](https://tessl.io/)
- [Tessl launches spec-driven development tools](https://tessl.io/blog/tessl-launches-spec-driven-framework-and-registry/)
- [Design by Contract - Wikipedia](https://en.wikipedia.org/wiki/Design_by_contract)
- [Specification by Example - Wikipedia](https://en.wikipedia.org/wiki/Specification_by_example)
- [Behavior-driven development - Wikipedia](https://en.wikipedia.org/wiki/Behavior-driven_development)
- [Specification by Example, 10 years later - Gojko Adzic](https://gojko.net/2020/03/17/sbe-10-years.html)
- [RFC Driven Development - Engineering Management](https://engineering-management.space/post/rfc-driven-development/)
- [RFCs and Design Docs - Pragmatic Engineer](https://blog.pragmaticengineer.com/rfcs-and-design-docs/)
- [Architecture Decision Records - ADR GitHub](https://adr.github.io/)
- [ADR Process - AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html)
- [A Practical Guide to Spec-Driven Development - Zencoder](https://docs.zencoder.ai/user-guides/tutorials/spec-driven-development-guide)
- [Awesome Specification Driven Development - GitHub](https://github.com/aabs/awesome-specification-driven-development)
- [Beyond TDD: Why Spec-Driven Development is the Next Step - Kinde](https://www.kinde.com/learn/ai-for-software-engineering/best-practice/beyond-tdd-why-spec-driven-development-is-the-next-step/)
- [Spec-First API Development - Atlassian](https://www.atlassian.com/blog/atlassian-engineering/spec-first-api-development)
- [EARS Notation - Alistair Mavin](https://alistairmavin.com/ears/)
- [Comprehensive Guide: Kiro, Spec Kit, BMAD - Medium](https://medium.com/@visrow/comprehensive-guide-to-spec-driven-development-kiro-github-spec-kit-and-bmad-method-5d28ff61b9b1)
- [The Limits of Spec-Driven Development - Isoform](https://isoform.ai/blog/the-limits-of-spec-driven-development)
- [Spec-Driven Development: Hot New Waterfall? - The Stack](https://www.thestack.technology/spec-driven-development-is-all-the-rage-but/)
