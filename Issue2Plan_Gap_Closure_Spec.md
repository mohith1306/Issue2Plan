# Issue2Plan — Gap Closure & Hackathon Judge Specification

## Purpose

This document is the implementation specification for improving the current Issue2Plan Rote Play.

**Goal:** close the gap between the current proof-of-concept implementation and a reliable, reusable, judge-ready Rote Play.

The coding agent should use this document as the source of truth for implementation work.

---

# 1. Project Definition

## Name

**Issue2Plan**

## One-line pitch

> Turn GitHub issues into evidence-backed, file-level implementation plans by teaching an AI agent a repeatable repository investigation procedure.

## Problem

Developers repeatedly spend significant time converting GitHub issues into actionable implementation plans because they must:

1. Understand the issue.
2. Explore an unfamiliar repository.
3. Locate relevant files.
4. Trace dependencies and execution paths.
5. Find existing implementation patterns.
6. Inspect tests.
7. Determine the exact changes required.
8. Identify risks and edge cases.
9. Validate that conclusions are supported by the repository.

## Solution

Issue2Plan is a reusable Rote Play that takes:

```text
Repository + GitHub Issue
```

and produces:

```text
Evidence-backed implementation plan
```

The Play focuses on **planning and investigation**, not automatically modifying source code.

---

# 2. Current Implementation Problems

The current repository has the correct high-level Play skeleton, but several parts are placeholders or insufficiently intelligent.

The coding agent must address all of the following gaps.

---

## Gap 1 — Issue understanding is not real analysis

### Current problem

The current implementation effectively prints the issue title/body instead of actually extracting requirements.

### Required behavior

Analyze the issue and extract:

- Problem statement
- Requested behavior
- Functional requirements
- Non-functional requirements
- Acceptance criteria
- Constraints
- Explicitly mentioned components
- Important keywords
- Unknowns and ambiguities

The issue analysis must influence all subsequent repository investigation.

### Acceptance criteria

For example:

```text
Issue:
"Add retry support to failed API requests up to
three times using exponential backoff."
```

should produce structured findings such as:

```text
Requirements:
- Retry failed requests
- Maximum attempts: 3
- Use exponential backoff

Keywords:
- retry
- API request
- exponential backoff

Potential areas:
- API client
- error handling
- retry policy
- tests
```

---

# 3. Gap 2 — Repository exploration is too shallow

### Current problem

A generic `ls`/`find` scan is not enough to understand a codebase.

### Required behavior

Identify:

- Programming languages
- Frameworks
- Package manager
- Build system
- Repository structure
- Application entry points
- Major modules
- Configuration
- Test framework
- Test locations
- Documentation
- Relevant architectural boundaries

Do not dump the entire repository. The investigation should progressively narrow the search based on the issue.

---

# 4. Gap 3 — Relevant file discovery is generic

### Current problem

Searching for all files or all functions does not establish relevance to the issue.

### Required behavior

Use issue analysis to drive targeted discovery.

Search for:

- Issue keywords
- Domain concepts
- Classes
- Functions
- Interfaces
- Routes
- Services
- Models
- Configuration
- Similar feature implementations

Each candidate file must include a reason for relevance.

Example:

```text
File:
src/api/ApiClient.ts

Relevant symbol:
ApiClient.request()

Reason:
This method executes outgoing API requests and is directly related
to the requested retry behavior.
```

---

# 5. Gap 4 — Dependency tracing is insufficient

### Current problem

Textual import/require searches do not provide meaningful dependency or execution-path analysis.

### Required behavior

For important components determine:

- Who calls the component?
- What does it call?
- What data flows through it?
- Where are errors handled?
- Where is configuration applied?
- Which downstream components depend on it?
- Which side effects may occur?

Example:

```text
ApiController
    ↓
ApiService
    ↓
ApiClient.request()
    ↓
HTTP transport
    ↓
Error handler
```

Explain how this path relates to the issue.

---

# 6. Gap 5 — Existing pattern discovery is weak

### Current problem

Generic searches such as `function` or TODO/FIXME markers do not identify useful architectural patterns.

### Required behavior

Search for existing patterns relevant to the issue.

Examples:

```text
Existing retry logic
Existing validation
Existing error handling
Existing configuration abstractions
Existing service abstractions
Existing caching
Existing logging
Existing test patterns
```

Prefer extending an established repository pattern over introducing a new architecture unless repository evidence indicates otherwise.

---

# 7. Gap 6 — Test analysis is superficial

### Current problem

Simply locating test files does not establish what should be tested.

### Required behavior

Analyze:

- Unit tests
- Integration tests
- End-to-end tests
- Fixtures
- Mocks
- Test utilities
- Existing related test cases
- Testing conventions

Determine:

1. Tests that should be modified.
2. Tests that should be added.
3. Edge cases.
4. Regression scenarios.

Example:

```text
Existing test:
src/api/__tests__/ApiClient.test.ts

Existing coverage:
- successful request
- failed request

Missing coverage:
- transient failure followed by success
- retry exhaustion
- maximum retry count
- exponential backoff
- permanent error should not retry
```

---

# 8. Gap 7 — Change analysis does not produce real implementation changes

### Required behavior

For every proposed change provide:

- File path
- Class/function/component
- Current behavior
- Required behavior
- Why the component must change
- Dependencies
- Side effects
- Whether a new component is required

Example:

```text
File:
src/api/ApiClient.ts

Symbol:
ApiClient.request()

Current behavior:
Sends one HTTP request and immediately propagates failure.

Required behavior:
Retry transient failures up to three times using the repository's
existing retry policy.

Reason:
This is the central request execution path.

Dependencies:
RetryPolicy
HTTP transport
Error handler
```

---

# 9. Gap 8 — Implementation order is currently just the analysis order

The implementation order must be a real developer execution sequence, not a copy of the investigation workflow.

Example:

```text
1. Extend RetryPolicy configuration.
2. Integrate RetryPolicy with ApiClient.request().
3. Preserve existing error propagation.
4. Add transient-error classification.
5. Add retry exhaustion handling.
6. Update unit tests.
7. Add integration coverage.
```

The order must depend on the actual issue and repository.

---

# 10. Gap 9 — Validation is not real validation

Before finalizing the plan:

### File validation

Check that every referenced file exists.

### Symbol validation

Check that referenced classes, functions, interfaces, methods, and configuration keys exist where possible.

### Pattern validation

Confirm proposed changes are compatible with repository conventions.

### Dependency validation

Confirm described dependency relationships are supported by repository evidence.

### Test validation

Confirm test recommendations match the project's testing framework and conventions.

### Evidence validation

Every important recommendation must have repository evidence.

Do not use code metrics or line counts as a substitute for validation.

---

# 11. Gap 10 — Confidence is currently hard-coded

Confidence must be derived from evidence quality.

### HIGH

- Target files exist
- Target symbols exist
- Relevant code path was inspected
- Existing pattern supports recommendation
- Test structure supports recommendation
- No major unresolved ambiguity

### MEDIUM

- Most evidence exists
- Some architectural uncertainty remains
- One or more assumptions are required

### LOW

- Important files/symbols could not be verified
- Repository evidence is weak
- Issue requirements are ambiguous
- Significant assumptions remain

Always explain the confidence level.

---

# 12. Gap 11 — Issue input must actually drive the workflow

The declared inputs:

```text
repo_path
issue_title
issue_body
```

must meaningfully control the investigation.

Required flow:

```text
Issue
 ↓
Requirements
 ↓
Keywords / concepts
 ↓
Targeted repository search
 ↓
Relevant files
 ↓
Relevant symbols
 ↓
Execution path
 ↓
Impact analysis
 ↓
Tests
 ↓
Changes
 ↓
Validation
 ↓
Plan
```

The same repository with different issues should produce meaningfully different investigations and plans.

---

# 13. Gap 12 — Output should be evidence-backed

Each important recommendation should include:

```text
File
Symbol
Evidence / observation
Reason
Recommended change
Confidence
```

Example:

```text
File:
src/auth/AuthService.ts

Symbol:
authenticate()

Evidence:
authenticate() is the entry point for the current authentication flow.

Observation:
JWT validation is performed through validateToken().

Recommendation:
Extend the authentication flow at this integration point.

Confidence:
HIGH
```

---

# 14. Target Architecture

```text
                    +------------------+
                    |   GITHUB ISSUE   |
                    |                  |
                    | Title + Body     |
                    +--------+---------+
                             |
                             v
                  +---------------------+
                  |   ISSUE ANALYZER    |
                  |                     |
                  | Requirements        |
                  | Acceptance criteria |
                  | Keywords            |
                  | Constraints         |
                  | Unknowns            |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |  REPOSITORY SCOUT   |
                  |                     |
                  | Structure           |
                  | Language/framework  |
                  | Entry points        |
                  | Modules             |
                  | Tests               |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |   TARGETED SEARCH   |
                  |                     |
                  | Issue concepts      |
                  | Classes             |
                  | Functions           |
                  | APIs                |
                  | Config              |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |     CODE TRACE      |
                  |                     |
                  | Call paths          |
                  | Dependencies        |
                  | Data flow           |
                  | Side effects        |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |   PATTERN FINDER    |
                  |                     |
                  | Similar features    |
                  | Existing abstractions|
                  | Conventions         |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |    TEST ANALYZER    |
                  |                     |
                  | Existing tests      |
                  | Missing coverage    |
                  | Regression cases    |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |   CHANGE ANALYZER   |
                  |                     |
                  | Files               |
                  | Symbols             |
                  | Components          |
                  | Dependencies        |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  | EVIDENCE VALIDATOR  |
                  |                     |
                  | Files exist?        |
                  | Symbols exist?      |
                  | Evidence supports?  |
                  | Tests consistent?   |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |   PLAN SYNTHESIZER  |
                  |                     |
                  | Implementation      |
                  | order               |
                  | Risks               |
                  | Tests               |
                  | Evidence            |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  | FINAL ISSUE2PLAN    |
                  | IMPLEMENTATION PLAN |
                  +---------------------+
```

---

# 15. Rote-Specific Implementation Model

Do not turn Issue2Plan into a conventional standalone SaaS application.

The core deliverable is a **Rote Play**.

The intended lifecycle is:

```text
First successful execution
        |
        v
   OpenCode Agent
        |
        v
 Repository investigation
        |
        v
 Human guidance / correction
        |
        v
 Correct implementation plan
        |
        v
       Rote
        |
        v
 Reusable Issue2Plan Play
        |
        +----------+----------+
        |          |          |
        v          v          v
      Issue A    Issue B    Issue C
        |          |          |
        v          v          v
      Plan A     Plan B     Plan C
```

The Play should be reusable across different issues and repositories.

---

# 16. MVP Scope

## Input

```text
Local repository
+
GitHub issue title
+
GitHub issue body
```

## Process

```text
Understand
    ↓
Explore
    ↓
Trace
    ↓
Analyze
    ↓
Validate
```

## Output

```text
Evidence-backed implementation plan
```

## Explicitly out of scope

Do NOT automatically:

- Modify source code
- Create commits
- Push changes
- Create pull requests
- Deploy applications
- Change production infrastructure

The MVP is an investigation and planning Play.

---

# 17. Final Output Contract

The final output must contain:

```markdown
# Implementation Plan

## Issue

<issue title>

## 1. Requirement Summary

<requirements>

## 2. Acceptance Criteria

<criteria>

## 3. Repository Understanding

<architecture relevant to issue>

## 4. Relevant Components

| File | Symbol | Reason | Confidence |
|------|--------|--------|------------|

## 5. Execution / Dependency Path

<relevant call/data flow>

## 6. Existing Patterns

<similar implementations and conventions>

## 7. Implementation Changes

### Step 1
<File + symbol + exact change + evidence>

### Step 2
<File + symbol + exact change + evidence>

## 8. Testing Strategy

### Existing Tests

...

### New Tests

...

## 9. Edge Cases

...

## 10. Risks

...

## 11. Implementation Order

1. ...
2. ...
3. ...

## 12. Evidence

- `path/to/file:line`
- `path/to/file:line`

## 13. Validation Results

### Files Verified

...

### Symbols Verified

...

### Assumptions

...

## 14. Confidence

HIGH / MEDIUM / LOW

<reason>
```

---

# 18. Judge Criteria

The project must be evaluated as a Rote Play, not merely as a code repository.

## Criterion 1 — Does it actually run?

The Play must:

- Install/load correctly through Rote.
- Accept its declared inputs.
- Execute successfully.
- Produce a meaningful implementation plan.
- Handle missing/invalid inputs gracefully.
- Avoid destructive repository modifications.

**Target: 9/10+**

---

## Criterion 2 — Can a stranger understand and trust it?

A judge who did not build the project should be able to understand:

- What problem it solves
- What inputs it needs
- What procedure it performs
- What output it generates
- Why its recommendations are trustworthy
- Where the evidence came from
- What confidence means

The output should make this immediately clear:

```text
Issue
 ↓
Requirement
 ↓
Repository evidence
 ↓
Affected files
 ↓
Recommended changes
 ↓
Tests
 ↓
Risks
 ↓
Implementation order
```

**Target: 9/10+**

---

## Criterion 3 — Do people actually want to reuse it?

A stranger should be able to take:

```text
Their repository
+
Their GitHub issue
```

and obtain:

```text
A useful implementation plan
```

without understanding Issue2Plan internals.

**Target: 9/10+**

---

# 19. Additional Judge Criteria

## Reusability

The procedure must work across:

```text
Repository A + Issue A
Repository B + Issue B
Repository C + Issue C
```

Do not hard-code one repository or one issue.

## Evidence quality

Recommendations must be grounded in actual repository evidence.

Prefer:

```text
AuthService.authenticate() is the current authentication
entry point, and validateToken() is called from this method.
The issue changes authentication behavior, so this is the
primary integration point.
```

over:

```text
Probably modify AuthService.
```

## Reliability

Avoid hallucinating:

- Files
- Classes
- Functions
- Dependencies
- Tests
- Architecture

When something cannot be verified, explicitly state:

```text
Unable to verify.
```

## Safety

The MVP should remain read-only.

---

# 20. Current vs Target

| Area | Current State | Required State |
|------|---------------|----------------|
| Issue understanding | Prints issue | Extracts requirements |
| Repository exploration | Basic file scan | Architectural discovery |
| File discovery | Generic search | Issue-driven search |
| Dependency analysis | Textual imports | Relevant execution paths |
| Pattern discovery | Generic grep | Issue-relevant patterns |
| Test analysis | Finds tests | Determines missing coverage |
| Change analysis | Generic output | File/symbol-level changes |
| Implementation order | Workflow order | Developer execution order |
| Validation | Metrics/line counts | Evidence verification |
| Confidence | Hard-coded | Evidence-based |
| Output | Generic report | Evidence-backed plan |
| Reusability | Limited | Cross-repository |
| Rote integration | Basic Play | Reusable procedure |

---

# 21. Example of Desired Behavior

Given:

```text
Issue:

Add retry support to failed API requests up to three times
using exponential backoff.
```

The Play should discover something like:

```text
Issue Understanding
-------------------

Requirements:
- Retry transient API failures.
- Maximum attempts: 3.
- Use exponential backoff.
- Preserve current behavior for permanent failures.


Relevant Components
-------------------

src/api/ApiClient.ts
  ApiClient.request()

src/api/RetryPolicy.ts
  RetryPolicy

src/api/__tests__/ApiClient.test.ts


Execution Path
--------------

Controller
    ↓
ApiService
    ↓
ApiClient.request()
    ↓
HTTP transport
    ↓
Error handler


Existing Pattern
----------------

RetryPolicy already exists in src/api/RetryPolicy.ts.

Recommendation:
Extend the existing abstraction rather than creating a new
retry implementation.


Implementation Changes
----------------------

1. Extend RetryPolicy configuration.
2. Integrate RetryPolicy with ApiClient.request().
3. Preserve permanent-error behavior.
4. Add retry exhaustion handling.
5. Update ApiClient unit tests.
6. Add transient-failure regression tests.


Risks
-----

- Retrying non-idempotent requests may duplicate side effects.
- Backoff configuration must not block request handling indefinitely.


Confidence
----------

HIGH

Reason:
All referenced files and symbols were verified and the repository
already contains a compatible retry abstraction.
```

---

# 22. Testing Requirements

Before declaring the project complete, run the Play against multiple real scenarios.

Minimum:

```text
Test 1 — Simple feature issue
Test 2 — Bug fix issue
Test 3 — Refactoring / architectural issue
```

Prefer different repositories if possible.

For every run verify:

- Issue-specific analysis
- Correct relevant files
- Correct symbols
- Evidence
- Dependency reasoning
- Test recommendations
- Implementation order
- Confidence
- No hallucinated paths
- No source modifications

---

# 23. Failure Handling

### Invalid repository

Return:

```text
Repository does not exist or is not accessible.
```

### Empty issue

Return:

```text
Issue title/body is insufficient to perform a reliable analysis.
```

### Ambiguous issue

Return:

```text
Unresolved ambiguities:
- ...
```

and reduce confidence.

### Missing evidence

Do not fabricate.

Return:

```text
Evidence unavailable for this recommendation.
```

### Unsupported repository

State the limitation and continue with whatever evidence can be verified.

---

# 24. Engineering Constraints

When modifying the implementation:

1. Preserve Rote Play compatibility.
2. Preserve the existing declared inputs unless there is a strong reason to change them.
3. Keep the Play read-only.
4. Avoid unnecessary dependencies.
5. Prefer repository-native tools and commands.
6. Make outputs deterministic and structured where possible.
7. Never hard-code results for a demonstration repository.
8. Never hard-code confidence.
9. Do not make the Play dependent on a single repository.
10. Keep the MVP focused on investigation and planning.

---

# 25. Definition of Done

Issue2Plan is ready for hackathon submission only when:

- [ ] Rote Play runs successfully.
- [ ] OpenCode can execute it end-to-end.
- [ ] Issue requirements are actually analyzed.
- [ ] Issue concepts drive repository exploration.
- [ ] Relevant files are identified with reasons.
- [ ] Relevant symbols are identified.
- [ ] Dependencies/execution paths are traced.
- [ ] Existing patterns are discovered.
- [ ] Existing tests are analyzed.
- [ ] Missing tests are identified.
- [ ] Implementation changes are concrete.
- [ ] Implementation order is issue-specific.
- [ ] Every major recommendation has evidence.
- [ ] Files are validated.
- [ ] Symbols are validated where possible.
- [ ] Confidence is evidence-based.
- [ ] No source files are modified automatically.
- [ ] At least three different real scenarios have been tested.
- [ ] The Play works with fresh repositories/issues.
- [ ] The final output is understandable to a stranger.
- [ ] The public Play description clearly explains inputs, process, and output.
- [ ] The Play is published for judges/users to run.

---

# 26. Target Judge Score

| Criterion | Target |
|-----------|--------|
| Actually runs | 9/10 |
| Stranger understands it | 9/10 |
| Reusability / adoption | 9/10 |
| Evidence quality | 9/10 |
| Issue-specific reasoning | 9/10 |
| Validation | 9/10 |
| Scope discipline | 9/10 |
| Rote integration | 10/10 |

The current implementation is a proof of concept.

The target implementation should feel like a **real, reusable developer workflow captured as a Rote Play**.

---

# 27. Instruction to the Coding Agent

Implement the missing functionality described in this document.

**Do not merely update the README.**

First inspect the existing repository and implementation. Then modify the actual Rote Play so that it satisfies the architecture, behavior, output contract, validation requirements, and definition of done above.

Do not expand the product into a general-purpose coding agent.

The core objective is:

```text
GitHub Issue
+
Repository
        ↓
Issue-aware investigation
        ↓
Evidence-backed findings
        ↓
Validated implementation plan
```

The implementation should be robust enough that a judge can run the Play against a fresh repository and issue and receive a genuinely useful implementation plan.
