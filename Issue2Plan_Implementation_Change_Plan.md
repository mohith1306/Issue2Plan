# Issue2Plan — Implementation Change Plan

## Objective

Improve the existing Issue2Plan Rote Play so that its current 8-step workflow performs **real repository-aware investigation** and produces a trustworthy, evidence-backed, file/symbol-level implementation plan.

The product definition, scope, and 8-step structure remain unchanged.

---

## 1. Keep the Original Product Definition

### Input
- Repository path
- GitHub issue title
- GitHub issue body

### Output
An evidence-backed, file-level implementation plan.

### Scope
Issue2Plan is a **read-only repository investigation and planning workflow**.

It must NOT:
- modify source code
- create commits
- push changes
- create pull requests
- deploy anything
- make production changes

---

## 2. Keep Exactly 8 Investigation Stages

Keep these eight stages:

1. Analyze Issue
2. Explore Repository
3. Find Relevant Files
4. Trace Dependencies
5. Find Patterns
6. Analyze Tests
7. Determine Changes
8. Validate Findings

The key change is to make each stage produce meaningful evidence that becomes context for the next stage.

---

## 3. New Internal Data Flow

```text
Issue Input
    |
    v
1. Issue Analysis
    |
    | issue_context
    v
2. Repository Exploration
    |
    | repository_context
    v
3. Relevant File Discovery
    |
    | candidate_files
    v
4. Dependency / Code Trace
    |
    | code_paths
    v
5. Existing Pattern Discovery
    |
    | patterns
    v
6. Test Analysis
    |
    | test_evidence
    v
7. Change Analysis
    |
    | change_plan
    v
8. Evidence Validation
    |
    | validated_findings
    v
Final Plan Synthesis
```

The critical architectural change is that the stages must **exchange structured findings** instead of operating as isolated shell commands.

---

## 4. Step 1 — Analyze Issue

### Current Problem

The current implementation effectively echoes the issue and extracts weak keyword information.

### Required Change

Produce a structured `IssueContext` containing:

```text
problem
expected_behavior
acceptance_criteria
domain_concepts
technical_keywords
likely_components
constraints
unknowns
```

For the ArrayBuffer issue, the analysis should conceptually identify:
- Problem: `res.send(ArrayBuffer)` results in `{}` being sent.
- Expected behavior: ArrayBuffer contents should be sent correctly.
- Domain concepts: HTTP response, response body, ArrayBuffer, serialization, `res.send`.
- Technical keywords: `res.send`, `ArrayBuffer`, response, JSON, body.
- Unknowns: where `res.send` is implemented, how body types are classified, and whether binary handling already exists.

Do not hard-code Express-specific files or symbols. Those must be discovered later.

---

## 5. Step 2 — Explore Repository

### Current Problem

The current step performs shallow `ls`/`find` operations and does not establish repository context.

### Required Change

Build a `RepositoryContext` containing:

```text
language
framework
package_manager
source_directories
test_directories
entry_points
config_files
build_system
repository_structure
```

These values must be discovered from the repository, not hard-coded.

---

## 6. Step 3 — Find Relevant Files

### Current Problem

The current implementation performs generic file discovery rather than issue-driven repository search.

### Required Change

Use:

```text
IssueContext
+
RepositoryContext
```

to generate issue-specific search concepts.

For an ArrayBuffer response issue, the investigation might search for:

```text
res.send
ArrayBuffer
response body
serialization
send
```

Produce:

```text
CandidateFile

file
reason
matched_concept
relevant_lines
confidence
```

Do not provide expected file names to the Play.

---

## 7. Step 4 — Trace Dependencies

### Current Problem

Generic import searching does not establish the execution path related to the issue.

### Required Change

For important candidate files:

```text
Find relevant symbols
        |
        v
Inspect surrounding code
        |
        v
Find calls
        |
        v
Find called functions
        |
        v
Build execution path
```

Produce:

```text
CodePath

entry_symbol
called_symbols
files
relationship
evidence
```

The actual symbols and files must be discovered from the repository.

---

## 8. Step 5 — Find Existing Patterns

### Current Problem

The current pattern search is generic and does not identify repository conventions or analogous implementations.

### Required Change

Search for existing solutions to similar behavior.

For a binary-response issue, investigate concepts such as:

```text
ArrayBuffer
Buffer
Uint8Array
Stream
binary responses
```

The goal is:

> Prefer existing repository patterns over inventing new architecture.

Produce:

```text
Pattern

existing_pattern
location
similarity
how_it_applies
evidence
confidence
```

---

## 9. Step 6 — Analyze Tests

### Current Problem

The current Play incorrectly reports no tests for mature repositories.

### Required Change

Identify:

```text
test_framework
relevant_test_files
relevant_test_cases
fixtures
helpers
regression_patterns
```

Produce:

```text
TestEvidence

framework
existing_tests
relevant_test_files
missing_coverage
recommended_tests
```

The exact test files and framework must be discovered from the repository.

---

## 10. Step 7 — Determine Changes

### Current Problem

The current output uses:

```text
File: (to be determined)
Symbol: (to be determined)
```

and therefore is not an implementation plan.

### Required Change

Generate change recommendations only after the earlier investigation stages have produced evidence.

Each change should contain:

```text
file
symbol
current_behavior
required_behavior
reason
evidence
dependencies
confidence
```

Do not invent files or symbols.

---

## 11. Step 8 — Validate Findings

### Current Problem

Validation exists structurally but receives no meaningful findings.

### Required Change

For every proposed file:

```text
Does the file exist?
```

For every proposed symbol:

```text
Does the symbol exist?
```

For every evidence claim:

```text
Does the source actually support the claim?
```

For every proposed change:

```text
Does the change address the issue?
```

For proposed tests:

```text
Does the test location/framework actually exist?
```

Validation must produce measurable results and dynamic confidence.

---

## 12. Fix Acceptance Criteria Generation

The current Play treats the issue title itself as an acceptance criterion.

Instead, acceptance criteria must represent observable behavior.

Conceptually:

```text
## 2. Acceptance Criteria

1. ArrayBuffer passed to res.send() is handled
   as response data rather than serialized as {}.

2. The resulting HTTP response contains the
   expected ArrayBuffer contents.

3. Existing supported response-body behavior
   remains unchanged.

4. Regression coverage exists for the issue.

5. Tests pass after the change.
```

The actual criteria should be derived from the issue semantics and repository conventions.

---

## 13. Fix Implementation Order

Implementation order should follow actual dependencies.

Conceptually:

```text
1. Modify <verified implementation symbol>
   to support the required behavior.

2. Preserve existing behavior for
   other supported response types.

3. Add regression coverage in
   <verified test file>.

4. Add edge-case coverage.

5. Run the repository's existing test suite.
```

The exact order must be generated from the discovered implementation path and dependencies.

---

## 14. Make Evidence a First-Class Internal Object

Every important finding should internally have a structure similar to:

```text
Finding {
    claim
    file
    symbol
    lines
    observation
    reason
    confidence
}
```

The final plan should be generated from **validated findings**, not solely from the LLM's interpretation of the issue.

---

## 15. Confidence Model

### HIGH

```text
- file verified
- symbol verified
- source inspected
- behavior directly supports conclusion
```

### MEDIUM

```text
- file verified
- relevant code found
- behavior partially inferred
```

### LOW

```text
- recommendation based mainly on issue text
- source evidence insufficient
```

The Play must never claim HIGH confidence for an unverified file or symbol.

---

## 16. Preserve the Final Output Structure

Keep the current 14-section output:

```text
# Implementation Plan

## Issue

## 1. Requirement Summary

## 2. Acceptance Criteria

## 3. Repository Understanding

## 4. Relevant Components

## 5. Execution / Dependency Path

## 6. Existing Patterns

## 7. Implementation Changes

## 8. Testing Strategy

## 9. Edge Cases

## 10. Risks

## 11. Implementation Order

## 12. Evidence

## 13. Validation Results

## 14. Confidence
```

The improvement is that every section must be **evidence-derived**.

---

## 17. Preserve the Product Boundary

Issue2Plan is NOT becoming:

- an autonomous coding agent
- a GitHub Copilot competitor
- a PR generation system
- a commit/push automation system
- a deployment agent
- a general-purpose repository agent

The product remains:

```text
GitHub Issue
      |
      v
Repository Investigation
      |
      v
Evidence
      |
      v
File/Symbol Identification
      |
      v
Implementation Reasoning
      |
      v
Implementation Plan
```

---

## 18. Implementation Sequence

### Phase 1 — Foundation
- Fix Issue Analyzer
- Fix Repository Scout
- Establish structured context between stages

### Phase 2 — Repository Investigation
- Fix Relevant File Discovery
- Add Symbol Discovery
- Make searches issue-driven

### Phase 3 — Code Understanding
- Fix Dependency Tracing
- Fix Pattern Discovery

### Phase 4 — Planning
- Fix Test Analysis
- Fix Change Analysis
- Generate real implementation order

### Phase 5 — Trust
- Build real Evidence Validator
- Verify files
- Verify symbols
- Verify source claims
- Calculate confidence dynamically

### Phase 6 — Presentation
- Improve the final 14-section implementation plan
- Clearly expose evidence and validation results

### Phase 7 — Real-Repository Testing
Test against:
1. Express issue
2. Deno issue
3. Another unfamiliar repository/issue

Measure:
- issue understanding
- relevant files
- symbol accuracy
- dependency tracing
- existing patterns
- test analysis
- evidence quality
- final plan quality
- hallucination rate
- validation score

### Phase 8 — Rote Capture

Once the workflow consistently produces a successful result:

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
Human guidance/correction
        |
        v
Correct result
        |
        v
Rote captures procedure
        |
        v
Reusable Issue2Plan Play
```

Then publish the Play.

---

## 19. Definition of Done

Issue2Plan is ready for hackathon submission when a fresh issue from an unfamiliar repository can produce:

```text
✓ Correct issue interpretation
✓ Behavioral acceptance criteria
✓ Repository understanding
✓ Relevant files
✓ Relevant symbols
✓ Execution/dependency path
✓ Existing implementation patterns
✓ Existing tests
✓ Missing test coverage
✓ Concrete implementation changes
✓ Edge cases
✓ Risks
✓ Developer-oriented implementation order
✓ Source-backed evidence
✓ Verified files
✓ Verified symbols
✓ Dynamic confidence
```

And most importantly:

```text
No invented files
No invented symbols
No unsupported implementation claims
No hard-coded confidence
```

The Play should be reusable across repositories rather than tuned to a single test repository.

---

## 20. Core Principle

Every change to Issue2Plan should answer at least one of these questions:

1. Does it improve repository understanding?
2. Does it improve issue-specific investigation?
3. Does it improve evidence quality?
4. Does it improve validation and trust?
5. Does it improve reuse across repositories?

If a proposed feature does not improve one of these, it should not be added to the MVP.
