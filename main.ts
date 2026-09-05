#!/usr/bin/env -S rote play run
/**
 * @rote-frontmatter
 * ---
 * name: issue2plan
 * description: "Turn any GitHub issue into an evidence-backed, file-level implementation plan by investigating the repository"
 * metadata:
 *   rote_version: 0.79.0
 *   version: 0.4.0
 *   status: draft
 *   kind: atomic
 *   flow_type: sequential
 *   execution_model: steps_with_presentation
 *   format: typescript
 *   requires_sessions: false
 *   discoverability:
 *     tags:
 *     - typescript
 *     - github
 *     - issue-analysis
 *     - implementation-plan
 * parameters:
 * - name: repo_path
 *   param_type: string
 *   required: true
 *   description: "Path to the local repository"
 * - name: issue_title
 *   param_type: string
 *   required: true
 *   description: "GitHub issue title"
 * - name: issue_body
 *   param_type: string
 *   required: true
 *   description: "GitHub issue description and body"
 * steps:
 *   analyze_issue:
 *     type: process.exec
 *     argv: [sh, -c, "export CONTEXT_DIR=/tmp/issue2plan_context; mkdir -p $CONTEXT_DIR; export ISSUE_TITLE=\"$issue_title\"; export ISSUE_BODY=\"$issue_body\"; python3 ~/.rote/flows/issue2plan/resources/scripts/analyze_issue.py"]
 *   explore_repository:
 *     type: process.exec
 *     argv: [sh, -c, "export CONTEXT_DIR=/tmp/issue2plan_context; export REPO_PATH=\"$repo_path\"; python3 ~/.rote/flows/issue2plan/resources/scripts/explore_repository.py"]
 *     depends_on: [analyze_issue]
 *   find_relevant_files:
 *     type: process.exec
 *     argv: [sh, -c, "export CONTEXT_DIR=/tmp/issue2plan_context; export REPO_PATH=\"$repo_path\"; python3 ~/.rote/flows/issue2plan/resources/scripts/find_relevant_files.py"]
 *     depends_on: [explore_repository]
 *   trace_dependencies:
 *     type: process.exec
 *     argv: [sh, -c, "export CONTEXT_DIR=/tmp/issue2plan_context; export REPO_PATH=\"$repo_path\"; python3 ~/.rote/flows/issue2plan/resources/scripts/trace_dependencies.py"]
 *     depends_on: [find_relevant_files]
 *   find_patterns:
 *     type: process.exec
 *     argv: [sh, -c, "export CONTEXT_DIR=/tmp/issue2plan_context; export REPO_PATH=\"$repo_path\"; python3 ~/.rote/flows/issue2plan/resources/scripts/find_patterns.py"]
 *     depends_on: [trace_dependencies]
 *   analyze_tests:
 *     type: process.exec
 *     argv: [sh, -c, "export CONTEXT_DIR=/tmp/issue2plan_context; export REPO_PATH=\"$repo_path\"; python3 ~/.rote/flows/issue2plan/resources/scripts/analyze_tests.py"]
 *     depends_on: [find_patterns]
 *   determine_changes:
 *     type: process.exec
 *     argv: [sh, -c, "export CONTEXT_DIR=/tmp/issue2plan_context; export REPO_PATH=\"$repo_path\"; python3 ~/.rote/flows/issue2plan/resources/scripts/determine_changes.py"]
 *     depends_on: [analyze_tests]
 *   validate_findings:
 *     type: process.exec
 *     argv: [sh, -c, "export CONTEXT_DIR=/tmp/issue2plan_context; export REPO_PATH=\"$repo_path\"; python3 ~/.rote/flows/issue2plan/resources/scripts/validate_findings.py"]
 *     depends_on: [determine_changes]
 * ---
 */

const presentationSdk = await import("__ROTE_PRESENTATION_SDK__").catch((cause) => {
  throw new Error(
    "This is a rote steps presentation program. Run it with `rote play run <name>`.",
    { cause },
  );
});
const { FlowOutput, loadPresentationContext, stepName } = presentationSdk;

const out = new FlowOutput();
const ctx = await loadPresentationContext();

const extractText = (output: any): string => {
  if (output.body?.stdout?.text) return output.body.stdout.text;
  return "";
};

const parseJson = (text: string): any => {
  try {
    const trimmed = text.trim();
    const jsonStart = trimmed.indexOf("{");
    const jsonEnd = trimmed.lastIndexOf("}");
    if (jsonStart >= 0 && jsonEnd > jsonStart) {
      return JSON.parse(trimmed.substring(jsonStart, jsonEnd + 1));
    }
    return JSON.parse(trimmed);
  } catch {
    return null;
  }
};

const step0 = ctx.requireAvailable(stepName("analyze_issue"));
const step1 = ctx.requireAvailable(stepName("explore_repository"));
const step2 = ctx.requireAvailable(stepName("find_relevant_files"));
const step3 = ctx.requireAvailable(stepName("trace_dependencies"));
const step4 = ctx.requireAvailable(stepName("find_patterns"));
const step5 = ctx.requireAvailable(stepName("analyze_tests"));
const step6 = ctx.requireAvailable(stepName("determine_changes"));
const step7 = ctx.requireAvailable(stepName("validate_findings"));

const issueData = parseJson(extractText(step0)) || {};
const repoData = parseJson(extractText(step1)) || {};
const filesData = parseJson(extractText(step2)) || {};
const depsData = parseJson(extractText(step3)) || {};
const patternsData = parseJson(extractText(step4)) || {};
const testsData = parseJson(extractText(step5)) || {};
const changesData = parseJson(extractText(step6)) || {};
const validationData = parseJson(extractText(step7)) || {};

// Issue data
const problem: string = issueData.problem || ctx.params.issue_title;
const expectedBehavior: string = issueData.expected_behavior || "";
const domainConcepts: string[] = issueData.domain_concepts || [];
const technicalKeywords: string[] = issueData.technical_keywords || [];
const likelyComponents: string[] = issueData.likely_components || [];
const keywords: string[] = issueData.keywords || [];
const requirements: string[] = issueData.requirements || [];
const acceptanceCriteria: string[] = issueData.acceptance_criteria || [];
const constraints: string[] = issueData.constraints || [];
const unknowns: string[] = issueData.unknowns || [];

// Repo data
const languages: Record<string, number> = repoData.language || {};
const frameworks: string[] = repoData.framework || [];
const packageManagers: string[] = repoData.package_manager || [];
const sourceDirectories: string[] = repoData.source_directories || [];
const testDirectories: string[] = repoData.test_directories || [];
const entryPoints: string[] = repoData.entry_points || [];
const buildSystem: string[] = repoData.build_system || [];
const repoStructure: string[] = repoData.repository_structure || [];
const testFramework: string = repoData.test_framework || "unknown";

// Files data
const relevantFiles: Array<{path: string; reasons: string[]; matched_concept: string; relevant_lines: any[]; confidence: number}> = filesData.files || [];

// Dependencies data
const callPaths: Array<{entry_symbol: string; file: string; line: number; called_symbols: any[]; callers: any[]; files: string[]; relationship: string; error_handling: string[]; evidence: any[]}> = depsData.call_paths || [];

// Patterns data
const relevantPatterns: Array<{existing_pattern: string; locations: any[]; evidence: string; how_it_applies: string; confidence: number}> = patternsData.relevant_patterns || [];
const conventions: any[] = patternsData.conventions || [];

// Tests data
const existingTestFiles: string[] = testsData.existing_test_files || [];
const relevantExistingTests: Array<{file: string; relevance: number; reasons: string[]; confidence: string}> = testsData.relevant_existing_tests || [];
const proposedModifications: Array<{file: string; what_to_add: string; confidence: string; reason: string}> = testsData.proposed_modifications || [];
const proposedNewTests: Array<{source_file: string; proposed_test_file: string; test_directory_exists: boolean; what_to_test: string; test_scenarios: string[]; confidence: string; status: string}> = testsData.proposed_new_tests || [];
const missingCoverage: string[] = testsData.missing_coverage || [];

// Changes data
const changes: any[] = changesData.changes || [];
const implOrder: any[] = changesData.implementation_order || [];

// Validation data
const perChangeValidation: any[] = validationData.per_change_validation || [];
const testValidation: any[] = validationData.test_validation || [];
const validationScore: number = validationData.validation_score || 0;
const verifiedCount: number = validationData.verified_count || 0;
const contradictedCount: number = validationData.contradicted_count || 0;
const inferredCount: number = validationData.inferred_count || 0;
const unknownCount: number = validationData.unknown_count || 0;
const totalChecks: number = validationData.total_checks || 0;
const repositoryFactScore: number = validationData.repository_fact_score || 0;
const behavioralClaimScore: number = validationData.behavioral_claim_score || 0;
const relationshipScore: number = validationData.relationship_score || 0;
const testScore: number = validationData.test_score || 0;
const confidenceModel: any = validationData.confidence_model || {};

// Compute overall confidence from granular model
const overallConfidence = validationScore >= 80 ? "HIGH" : validationScore >= 50 ? "MEDIUM" : "LOW";

// --- OUTPUT ---
out.human("# Implementation Plan");
out.human("");
out.human("## Issue");
out.human(ctx.params.issue_title);
out.human("");

// 1. Requirement Summary
out.human("## 1. Requirement Summary");
out.human("");
out.human(`**Problem:** ${problem}`);
out.human("");
if (expectedBehavior) {
  out.human(`**Expected Behavior:** ${expectedBehavior}`);
  out.human("");
}
if (requirements.length > 0) {
  out.human("**Requirements:**");
  requirements.forEach((r: string) => out.human(`- ${r}`));
  out.human("");
}
if (domainConcepts.length > 0) {
  out.human(`**Domain Concepts:** ${domainConcepts.join(", ")}`);
  out.human("");
}
if (likelyComponents.length > 0) {
  out.human(`**Likely Components:** ${likelyComponents.join(", ")}`);
  out.human("");
}

// 2. Acceptance Criteria
out.human("## 2. Acceptance Criteria");
out.human("");
if (acceptanceCriteria.length > 0) {
  acceptanceCriteria.forEach((ac: string, i: number) => out.human(`${i + 1}. ${ac}`));
} else {
  out.human(`1. The implementation described in the issue works correctly`);
}
if (constraints.length > 0) {
  out.human("");
  out.human("**Constraints:**");
  constraints.forEach((c: string) => out.human(`- ${c}`));
}
if (unknowns.length > 0) {
  out.human("");
  out.human("**Open Questions:**");
  unknowns.forEach((u: string) => out.human(`- ${u}`));
}
out.human("");

// 3. Repository Understanding
out.human("## 3. Repository Understanding");
out.human("");
if (Object.keys(languages).length > 0) {
  out.human("**Languages:** " + Object.entries(languages).map(([l, c]) => `${l} (${c} files)`).join(", "));
}
if (frameworks.length > 0) out.human("**Frameworks:** " + frameworks.join(", "));
if (packageManagers.length > 0) out.human("**Package Managers:** " + packageManagers.join(", "));
if (buildSystem.length > 0) out.human("**Build System:** " + buildSystem.join(", "));
if (sourceDirectories.length > 0) out.human("**Source Directories:** " + sourceDirectories.join(", "));
if (testDirectories.length > 0) out.human("**Test Directories:** " + testDirectories.join(", "));
if (entryPoints.length > 0) out.human("**Entry Points:** " + entryPoints.join(", "));
out.human("");
if (repoStructure.length > 0) {
  out.human("**Repository Structure:**");
  out.human("```");
  repoStructure.forEach((entry: string) => out.human(entry));
  out.human("```");
}
out.human("");

// 4. Relevant Components
out.human("## 4. Relevant Components");
out.human("");
out.human("| File | Matched Concept | Confidence | Relevance |");
out.human("|------|-----------------|------------|-----------|");
if (relevantFiles.length > 0) {
  relevantFiles.slice(0, 15).forEach((f: any) => {
    const conf = typeof f.confidence === 'number' ? `${Math.round(f.confidence * 100)}%` : "N/A";
    out.human(`| \`${f.path}\` | ${f.matched_concept || "general"} | ${conf} | ${(f.reasons || []).slice(0, 2).join("; ")} |`);
  });
} else {
  out.human("| (none found) | - | - | No relevant files identified |");
}
out.human("");

// 5. Execution / Dependency Path
out.human("## 5. Execution / Dependency Path");
out.human("");
if (callPaths.length > 0) {
  callPaths.slice(0, 8).forEach((cp: any) => {
    out.human(`**\`${cp.entry_symbol}\`** in \`${cp.file}:${cp.line}\` — ${cp.relationship}`);
    if (cp.called_symbols && cp.called_symbols.length > 0) {
      out.human(`  - Calls: ${cp.called_symbols.map((c: any) => `\`${c.symbol}\` (${c.relationship})`).join(", ")}`);
    }
    if (cp.callers && cp.callers.length > 0) {
      out.human(`  - Called by: ${cp.callers.map((c: any) => `\`${c.symbol}\` in \`${c.file}:${c.line}\``).join(", ")}`);
    }
    if (cp.error_handling && cp.error_handling.length > 0) {
      out.human(`  - Error handling: ${cp.error_handling.join(", ")}`);
    }
    out.human("");
  });
} else {
  out.human("No dependency paths traced.");
  out.human("");
}

// 6. Existing Patterns
out.human("## 6. Existing Patterns");
out.human("");
if (relevantPatterns.length > 0) {
  relevantPatterns.slice(0, 8).forEach((p: any) => {
    out.human(`**${p.existing_pattern}** (confidence: ${Math.round((p.confidence || 0) * 100)}%)`);
    if (p.locations) {
      p.locations.slice(0, 2).forEach((loc: any) => {
        out.human(`- \`${loc.file}:${loc.line}\`: ${loc.snippet}`);
        if (loc.context_type) out.human(`  - Context: ${loc.context_type}`);
        if (loc.how_it_applies) out.human(`  - How it applies: ${loc.how_it_applies}`);
        if (loc.reusability && loc.reusability.length > 0) out.human(`  - Reusability: ${loc.reusability.join(", ")}`);
      });
    }
    out.human("");
  });
} else {
  out.human("No issue-relevant patterns found.");
  out.human("");
}
if (conventions.length > 0) {
  out.human("**Code Conventions:**");
  conventions.slice(0, 5).forEach((c: any) => out.human(`- ${c.pattern} (${c.file}, ${c.count} occurrences)`));
  out.human("");
}

// 7. Implementation Changes
out.human("## 7. Implementation Changes");
out.human("");
if (changes.length > 0) {
  changes.slice(0, 10).forEach((ch: any, i: number) => {
    const confLevel = ch.confidence?.level || "UNKNOWN";
    const confReason = ch.confidence?.reason || "";
    out.human(`### Step ${i + 1} — ${confLevel} Confidence`);
    out.human("");
    out.human(`**File:** \`${ch.file}:${ch.line}\``);
    out.human(`**Symbol:** \`${ch.symbol}\``);
    out.human(`**Current Behavior:** ${ch.current_behavior}`);
    out.human(`**Required Behavior:** ${ch.required_behavior}`);
    if (ch.why_this_location && ch.why_this_location.length > 0) {
      out.human("**Why This Location:**");
      ch.why_this_location.forEach((reason: string) => out.human(`- ${reason}`));
    }
    if (ch.reuse && ch.reuse.length > 0) {
      out.human(`**Reuse:** ${ch.reuse.join(", ")}`);
    }
    if (ch.affected_callers && ch.affected_callers.length > 0) {
      out.human("**Affected Callers:**");
      ch.affected_callers.forEach((c: any) => out.human(`- \`${c.symbol}\` in \`${c.file}\` (breakage risk: ${c.breakage_risk})`));
    }
    if (ch.evidence && ch.evidence.length > 0) {
      out.human("**Evidence:**");
      ch.evidence.slice(0, 3).forEach((e: any) => out.human(`- \`${ch.file}:${e.line}\` — ${e.text}`));
    }
    if (ch.test_guidance && ch.test_guidance.length > 0) {
      out.human("**Test Guidance:**");
      ch.test_guidance.forEach((t: string) => out.human(`- ${t}`));
    }
    if (ch.risks && ch.risks.length > 0) {
      out.human(`**Risks:** ${ch.risks.join("; ")}`);
    }
    if (confReason) {
      out.human(`**Confidence Reason:** ${confReason}`);
    }
    out.human("");
  });
} else {
  out.human("No specific changes determined.");
  out.human("");
}

// 8. Testing Strategy
out.human("## 8. Testing Strategy");
out.human("");
out.human(`**Test Framework:** ${testFramework}`);
out.human("");

if (relevantExistingTests.length > 0) {
  out.human("**Existing Relevant Tests:**");
  relevantExistingTests.forEach((t: any) => {
    out.human(`- \`${t.file}\` (relevance: ${t.relevance}) — ${t.reasons.join(", ")}`);
  });
  out.human("");
}

if (proposedModifications.length > 0) {
  out.human("**Proposed Test Modifications:**");
  proposedModifications.forEach((m: any) => {
    out.human(`- \`${m.file}\` — ${m.what_to_add}`);
    out.human(`  - Reason: ${m.reason}`);
  });
  out.human("");
}

if (proposedNewTests.length > 0) {
  out.human("**Proposed New Tests:**");
  proposedNewTests.forEach((t: any) => {
    out.human(`- \`${t.proposed_test_file}\` (status: ${t.status}, confidence: ${t.confidence})`);
    out.human(`  - What to test: ${t.what_to_test}`);
    if (t.test_scenarios && t.test_scenarios.length > 0) {
      out.human(`  - Scenarios:`);
      t.test_scenarios.forEach((s: string) => out.human(`    - ${s}`));
    }
    if (!t.test_directory_exists) {
      out.human(`  - Note: test directory does not exist yet`);
    }
  });
  out.human("");
}

if (missingCoverage.length > 0) {
  out.human("**Missing Coverage:**");
  missingCoverage.forEach((m: string) => out.human(`- No tests for '${m}'`));
  out.human("");
}

if (existingTestFiles.length > 0 && relevantExistingTests.length === 0 && proposedModifications.length === 0 && proposedNewTests.length === 0) {
  out.human(`**All Test Files (${existingTestFiles.length}):**`);
  existingTestFiles.slice(0, 10).forEach((t: string) => out.human(`- \`${t}\``));
  out.human("");
}

// 9. Edge Cases
out.human("## 9. Edge Cases");
out.human("");
if (unknowns.length > 0) unknowns.forEach((u: string) => out.human(`- ${u}`));
if (constraints.length > 0) constraints.forEach((c: string) => out.human(`- ${c}`));
if (unknowns.length === 0 && constraints.length === 0) out.human("- No specific edge cases identified");
out.human("");

// 10. Risks
out.human("## 10. Risks");
out.human("");
const allRisks: string[] = [];
changes.slice(0, 5).forEach((ch: any) => {
  if (ch.risks) ch.risks.forEach((r: string) => allRisks.push(`[${ch.symbol}] ${r}`));
});
if (contradictedCount > 0) allRisks.push(`${contradictedCount} claim(s) contradicted by source code`);
if (unknownCount > 0) allRisks.push(`${unknownCount} check(s) could not be verified`);
if (allRisks.length > 0) {
  allRisks.forEach((r: string) => out.human(`- ${r}`));
} else {
  out.human("No significant risks identified.");
}
out.human("");

// 11. Implementation Order
out.human("## 11. Implementation Order");
out.human("");
if (implOrder.length > 0) {
  implOrder.forEach((o: any) => {
    const typeLabel = o.type === "testing" ? "[test]" : o.type === "validation" ? "[validate]" : o.type === "review" ? "[review]" : "[impl]";
    out.human(`${o.step}. ${typeLabel} ${o.description}`);
    if (o.details) out.human(`   ${o.details}`);
  });
} else {
  out.human("1. Analyze requirements");
  out.human("2. Identify affected files");
  out.human("3. Implement changes");
  out.human("4. Add tests");
  out.human("5. Validate");
}
out.human("");

// 12. Evidence
out.human("## 12. Evidence");
out.human("");
out.human(`- Verified: ${verifiedCount} check(s)`);
out.human(`- Inferred: ${inferredCount} check(s)`);
out.human(`- Contradicted: ${contradictedCount} check(s)`);
out.human(`- Unknown: ${unknownCount} check(s)`);
out.human("");
if (perChangeValidation.length > 0) {
  out.human("**Per-Change Validation:**");
  perChangeValidation.slice(0, 5).forEach((cv: any) => {
    const status = cv.overall_status || "unknown";
    out.human(`- \`${cv.symbol}\` in \`${cv.file}\`: ${status} (${cv.verified_count}/${cv.total_checks} checks passed)`);
  });
  out.human("");
}

// 13. Validation Results
out.human("## 13. Validation Results");
out.human("");
out.human(`**Overall Validation Score:** ${validationScore}%`);
out.human("");
out.human(`| Metric | Score |`);
out.human(`|--------|-------|`);
out.human(`| Repository Facts (files/symbols) | ${repositoryFactScore}% |`);
out.human(`| Behavioral Claims | ${behavioralClaimScore}% |`);
out.human(`| Relationships | ${relationshipScore}% |`);
out.human(`| Test Recommendations | ${testScore}% |`);
out.human("");

// 14. Confidence
out.human("## 14. Confidence");
out.human("");
out.human(`**Overall: ${overallConfidence}**`);
out.human("");
if (confidenceModel && Object.keys(confidenceModel).length > 0) {
  out.human("**Granular Confidence:**");
  Object.entries(confidenceModel).forEach(([key, val]: [string, any]) => {
    const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
    out.human(`- **${label}:** ${val.level} — ${val.reason}`);
  });
  out.human("");
}
if (overallConfidence === "HIGH") {
  out.human("All referenced files and symbols verified. Source claims supported by code evidence. Repository evidence strongly supports the recommendations.");
} else if (overallConfidence === "MEDIUM") {
  out.human("Most evidence verified. Some behavioral claims could not be fully confirmed. Manual review recommended for complex areas.");
} else {
  out.human("Limited evidence available. Significant manual analysis required before implementation.");
}

out.summary(`Issue2Plan: ${overallConfidence} confidence plan for "${ctx.params.issue_title}" (${validationScore}% validation)`);
out.result({
  run_id: ctx.run.run_id,
  issue_title: ctx.params.issue_title,
  repo_path: ctx.params.repo_path,
  confidence: overallConfidence,
  validation_score: validationScore,
  repository_fact_score: repositoryFactScore,
  behavioral_claim_score: behavioralClaimScore,
  relationship_score: relationshipScore,
  test_score: testScore,
  verified_count: verifiedCount,
  contradicted_count: contradictedCount,
  inferred_count: inferredCount,
  problem,
  keywords,
  requirements,
  languages: Object.keys(languages),
  frameworks,
  relevant_files: relevantFiles.length,
  changes: changes.length,
  existing_test_files: existingTestFiles.length,
  proposed_modifications: proposedModifications.length,
  proposed_new_tests: proposedNewTests.length,
});
