# Issue2Plan

## Repository-Aware GitHub Issue Investigation

> Turn any GitHub issue into an evidence-backed, file-level
> implementation plan by teaching an agent a repeatable repository
> investigation procedure.

------------------------------------------------------------------------

## 1. Problem Statement

Developers spend significant time turning GitHub issues into actionable
implementation plans because they repeatedly need to:

-   Understand the issue and its requirements
-   Explore an unfamiliar repository
-   Locate relevant files and components
-   Trace dependencies and execution paths
-   Find existing implementation patterns
-   Inspect existing tests
-   Determine exactly what needs to change
-   Identify risks and edge cases

### Proposed Solution

**Issue2Plan** is a reusable Rote Play that takes a GitHub issue and a
repository, investigates the codebase, validates its findings, and
produces an evidence-backed, file-level implementation plan.

The Play focuses on **planning, not code modification**.

------------------------------------------------------------------------

# 2. Core Concept

The Play should transform:

``` text
GitHub Issue
     +
Repository
     |
     v
Issue Understanding
     |
     v
Repository Exploration
     |
     v
Impact / Dependency Analysis
     |
     v
Test Analysis
     |
     v
Validation
     |
     v
Evidence-Backed Implementation Plan
```

The procedure should remain stable while the issue and repository can
change between executions.

------------------------------------------------------------------------

# 3. High-Level Architecture

``` text
                    +----------------------+
                    |      USER INPUT      |
                    |                      |
                    |  GitHub Repository   |
                    |  GitHub Issue        |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   ISSUE UNDERSTANDING|
                    |                      |
                    | Extract:             |
                    | - requirements       |
                    | - constraints        |
                    | - acceptance criteria|
                    | - unknowns           |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |  REPOSITORY EXPLORER |
                    |                      |
                    | - repository structure|
                    | - entry points       |
                    | - relevant modules   |
                    | - existing patterns  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |    IMPACT ANALYZER   |
                    |                      |
                    | - dependencies       |
                    | - call paths         |
                    | - affected files     |
                    | - side effects       |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |     TEST ANALYZER    |
                    |                      |
                    | - existing tests     |
                    | - missing coverage   |
                    | - regression cases   |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |    PLAN GENERATOR    |
                    |                      |
                    | - file-level changes |
                    | - implementation order|
                    | - risks              |
                    | - tests              |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |      VALIDATION       |
                    |                      |
                    | - referenced files   |
                    |   actually exist     |
                    | - referenced symbols |
                    |   exist              |
                    | - recommendations    |
                    |   fit repository     |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | FINAL IMPLEMENTATION |
                    |        PLAN          |
                    +----------------------+
```

------------------------------------------------------------------------

# 4. Input

## Required Inputs

### Repository

The repository to investigate.

For the MVP, the preferred approach is to operate on a **locally cloned
repository**. This avoids making GitHub authentication a hard dependency
for the core analysis.

Example:

``` text
current working directory
```

### GitHub Issue

The issue title and description, supplied as input to the Play.

Example:

``` text
Issue:
Add retry support to failed API requests.
```

------------------------------------------------------------------------

# 5. Execution Workflow

The Play should follow a consistent investigation procedure.

## Step 1 --- Understand the Issue

Extract:

-   Problem being reported
-   Requested behavior
-   Functional requirements
-   Non-functional requirements
-   Acceptance criteria
-   Constraints
-   Explicitly mentioned components
-   Unknown information

Do not start proposing code changes before understanding the request.

------------------------------------------------------------------------

## Step 2 --- Explore the Repository

Inspect the repository systematically.

Identify:

-   Project type
-   Programming languages
-   Frameworks
-   Repository structure
-   Application entry points
-   Major modules
-   Configuration
-   Build system
-   Test structure
-   Documentation
-   Relevant directories

The objective is to establish a high-level architectural model before
making recommendations.

------------------------------------------------------------------------

## Step 3 --- Identify Relevant Files

Search for code related to the issue.

Look for:

-   Classes
-   Functions
-   Interfaces
-   Services
-   Controllers
-   Routes
-   Models
-   Configuration
-   Utilities
-   Existing implementations
-   Similar features

Create a list of candidate files and explain why each one is relevant.

------------------------------------------------------------------------

## Step 4 --- Trace Dependencies and Execution Paths

For important components, determine:

-   Who calls them?
-   What do they call?
-   What data flows through them?
-   Where are errors handled?
-   Where is configuration applied?
-   Which downstream components depend on them?

The goal is to understand the impact of the requested change.

------------------------------------------------------------------------

## Step 5 --- Search for Existing Patterns

Before proposing new code, search the repository for similar
functionality.

Examples:

``` text
Existing retry mechanisms
Existing validation patterns
Existing error handling
Existing configuration patterns
Existing service abstractions
Existing test patterns
```

Prefer extending an established repository pattern over introducing a
new architecture.

------------------------------------------------------------------------

## Step 6 --- Analyze Tests

Inspect:

-   Existing unit tests
-   Integration tests
-   End-to-end tests
-   Test utilities
-   Fixtures
-   Mocks
-   Related test cases

Determine:

1.  Which existing tests should change?
2.  Which new tests should be added?
3.  Which edge cases should be covered?
4.  Which regression scenarios are important?

------------------------------------------------------------------------

## Step 7 --- Determine Required Changes

For each affected component, determine:

-   File path
-   Class/function/component
-   Current behavior
-   Required behavior
-   Why it must change
-   Dependencies
-   Potential side effects

The output should be concrete enough that another developer can
implement the issue without repeating the entire investigation.

------------------------------------------------------------------------

## Step 8 --- Validate Findings

Before producing the final plan, verify:

### File validation

Every referenced file should actually exist.

### Symbol validation

Referenced classes, functions, interfaces, methods, and configuration
keys should exist where possible.

### Pattern validation

Proposed changes should be consistent with existing repository patterns.

### Dependency validation

Affected components and dependencies should be supported by repository
evidence.

### Test validation

Recommended tests should align with the project's existing testing
conventions.

------------------------------------------------------------------------

# 6. Evidence-Backed Recommendations

Every important recommendation should have evidence.

Instead of:

``` text
Modify AuthService.
```

The Play should produce:

``` text
File:
src/auth/AuthService.ts

Component:
AuthService.authenticate()

Evidence:
- authenticate() is the entry point for the current authentication flow.
- JWT validation is currently performed through validateToken().
- OAuth-related logic is already centralized in TokenValidator.

Reason:
This is the narrowest integration point for the requested change.

Required change:
Extend the authentication flow to support OAuth tokens without
changing downstream authorization behavior.
```

The objective is to make the final plan **auditable** rather than purely
AI-generated.

------------------------------------------------------------------------

# 7. Validation and Confidence

Each major recommendation should receive a confidence level.

``` text
HIGH
MEDIUM
LOW
```

Example:

``` text
Confidence: HIGH

Reason:
The target file exists, the referenced function exists, and the
repository already contains a similar implementation pattern.
```

If the agent cannot verify a recommendation, it should explicitly state
the uncertainty rather than inventing repository details.

------------------------------------------------------------------------

# 8. Final Output Format

The Play should produce a standardized implementation plan.

``` markdown
# Implementation Plan

## Issue

<issue title>

## 1. Requirement Summary

<summary of the issue and acceptance criteria>

## 2. Repository Understanding

<high-level architecture relevant to the issue>

## 3. Affected Components

| File | Component | Reason |
|------|-----------|--------|
| ...  | ...       | ...    |

## 4. Implementation Changes

### Step 1

<file-level implementation change>

### Step 2

<file-level implementation change>

### Step 3

<file-level implementation change>

## 5. Dependencies

<affected dependencies and execution paths>

## 6. Testing Strategy

### Existing Tests

<tests that should be modified>

### New Tests

<tests that should be added>

## 7. Edge Cases

<important edge cases>

## 8. Risks

<potential regressions or architectural risks>

## 9. Implementation Order

1. ...
2. ...
3. ...

## 10. Evidence

- `path/to/file:line`
- `path/to/file:line`

## Confidence

HIGH / MEDIUM / LOW

<explanation>
```

------------------------------------------------------------------------

# 9. MVP Scope

The first version should intentionally remain focused.

## MVP Input

``` text
Local Repository
+
GitHub Issue
```

## MVP Process

``` text
Understand
    ->
Explore
    ->
Trace
    ->
Analyze
    ->
Validate
```

## MVP Output

``` text
Evidence-backed implementation plan
```

## Explicitly Out of Scope

The MVP should **not** modify source code.

It should not:

-   Implement the issue
-   Create a pull request
-   Push commits
-   Modify repository files
-   Automatically change configuration
-   Execute production operations

This keeps the first Play focused, inspectable, and reliable.

------------------------------------------------------------------------

# 10. Rote Play Model

The project should be built according to Rote's core model:

``` text
                 FIRST SUCCESSFUL RUN
                         |
                         v
                  +-------------+
                  |   OpenCode  |
                  |    Agent    |
                  +------+------+
                         |
                    Investigation
                         |
                         v
                 Human Guidance
                         |
                         v
                 Correct Result
                         |
                         v
                       Rote
                         |
                         v
                 +---------------+
                 |  Issue2Plan   |
                 |      Play     |
                 +-------+-------+
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
          Issue A     Issue B     Issue C
             |           |           |
             v           v           v
           Plan A      Plan B      Plan C
```

The objective is not to manually build a large automation framework
first.

Instead:

1.  Perform the workflow once.
2.  Guide the agent toward a successful result.
3.  Let Rote capture the successful procedure.
4.  Re-run the resulting Play with different issues and repositories.
5.  Refine the procedure based on failures.

------------------------------------------------------------------------

# 11. First Practice Run

The first practice run should use a real repository and a realistic
issue.

The agent should be instructed to:

``` text
Investigate the supplied GitHub issue against the current repository.

Do not modify any files.

Produce an evidence-backed implementation plan containing:
- issue requirements
- relevant architecture
- affected files
- affected functions/classes
- dependencies
- existing implementation patterns
- existing tests
- new tests required
- risks
- implementation order

Validate that referenced files and symbols exist before finalizing.
```

During the first run, human guidance should correct:

-   Incorrect repository assumptions
-   Irrelevant files
-   Missing dependencies
-   Weak evidence
-   Hallucinated symbols
-   Missing test coverage
-   Incorrect implementation order

The successful workflow becomes the basis for the Issue2Plan Play.

------------------------------------------------------------------------

# 12. Success Criteria

The Play is successful if it can take different issues and produce
useful plans without requiring the user to manually repeat the
repository investigation.

### Functional Success

Given:

``` text
Repository A + Issue A
```

produce:

``` text
Plan A
```

Given:

``` text
Repository B + Issue B
```

produce:

``` text
Plan B
```

using the same reusable procedure.

### Quality Success

The resulting plan should:

-   Reference real files
-   Reference real symbols where possible
-   Explain why each file is relevant
-   Identify affected components
-   Identify tests
-   Identify risks
-   Provide implementation order
-   Include repository evidence
-   Clearly state uncertainty

### Reusability Success

A stranger should be able to understand the Play from its description
and execute it with their own repository and issue.

------------------------------------------------------------------------

# 13. Future Enhancements

After the MVP works, potential extensions include:

``` text
GitHub Issue URL
      |
      v
Automatic Issue Fetching
      |
      v
Repository Analysis
      |
      v
Implementation Plan
      |
      +--> Create implementation branch
      |
      +--> Generate task checklist
      |
      +--> Generate test plan
      |
      +--> Create GitHub comment
```

Other possible enhancements:

-   GitHub API integration
-   Pull Request generation
-   Issue-to-task decomposition
-   Automatic codebase diagrams
-   Change-impact graphs
-   Plan comparison
-   Historical issue pattern detection
-   Confidence scoring
-   Human approval checkpoints

These should be considered only after the core Play is reliable.

------------------------------------------------------------------------

# 14. Project Pitch

### Short Pitch

> **Issue2Plan turns GitHub issues into evidence-backed, file-level
> implementation plans by teaching an AI agent a reusable repository
> investigation procedure.**

### Problem

Developers repeatedly spend time understanding codebases before they can
implement GitHub issues.

### Solution

A reusable Rote Play that performs the investigation once as a
structured procedure and can then repeat it across different issues and
repositories.

### Key Differentiator

The output is not generic AI advice.

It is:

``` text
Repository-aware
+
File-level
+
Evidence-backed
+
Validated
+
Reusable
```

------------------------------------------------------------------------

# 15. Project Flow

``` text
                    GITHUB ISSUE
                         +
                    REPOSITORY
                         |
                         v
                +----------------+
                | Issue Analysis |
                +-------+--------+
                        |
                        v
                +----------------+
                | Repo Discovery |
                +-------+--------+
                        |
                        v
                +----------------+
                | Code Tracing   |
                +-------+--------+
                        |
                        v
                +----------------+
                | Impact Analysis|
                +-------+--------+
                        |
                        v
                +----------------+
                | Test Analysis  |
                +-------+--------+
                        |
                        v
                +----------------+
                |   Validation   |
                +-------+--------+
                        |
                        v
              +----------------------+
              | Evidence-Backed Plan |
              +----------------------+
                        |
                        v
                  DEVELOPER
                        |
                        v
                IMPLEMENTS ISSUE
```

------------------------------------------------------------------------

## Guiding Principle

> **Do the investigation once. Capture the method. Reuse it for every
> similar issue.**
