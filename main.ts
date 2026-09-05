#!/usr/bin/env -S rote play run
/**
 * @rote-frontmatter
 * ---
 * name: issue2plan
 * description: "Turn any GitHub issue into an evidence-backed, file-level implementation plan by investigating the repository"
 * metadata:
 *   rote_version: 0.79.0
 *   version: 0.3.0
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

// Extract all data
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

const languages: Record<string, number> = repoData.language || {};
const frameworks: string[] = repoData.framework || [];
const packageManagers: string[] = repoData.package_manager || [];
const sourceDirectories: string[] = repoData.source_directories || [];
const testDirectories: string[] = repoData.test_directories || [];
const entryPoints: string[] = repoData.entry_points || [];
const configFiles: Record<string, string> = repoData.config_files || {};
const buildSystem: string[] = repoData.build_system || [];
const repoStructure: string[] = repoData.repository_structure || [];
const testFramework: string = repoData.test_framework || "unknown";

const relevantFiles: Array<{path: string; reasons: string[]; matched_concept: string; relevant_lines: any[]; confidence: number}> = filesData.files || [];

const callPaths: Array<{entry_symbol: string; file: string; line: number; called_symbols: any[]; callers: any[]; files: string[]; relationship: string; error_handling: string[]; evidence: any[]}> = depsData.call_paths || [];

const relevantPatterns: Array<{existing_pattern: string; locations: any[]; evidence: string}> = patternsData.relevant_patterns || [];
const conventions: any[] = patternsData.conventions || [];

const relevantTestFiles: Array<{file: string; relevance: number; reasons: string[]}> = testsData.relevant_test_files || [];
const testFiles: string[] = testsData.test_files || [];
const missingCoverage: string[] = testsData.missing_coverage || [];
const recommendedTests: any[] = testsData.recommended_tests || [];

const changes: any[] = changesData.changes || [];
const implOrder: any[] = changesData.implementation_order || [];

const filesVerified: any[] = validationData.files_verified || [];
const filesMissing: any[] = validationData.files_missing || [];
const symbolsVerified: any[] = validationData.symbols_verified || [];
const symbolsMissing: any[] = validationData.symbols_missing || [];
const sourceClaims: any[] = validationData.source_claims || [];
const changeRelevance: any[] = validationData.change_relevance || [];
const testLocationValidation: any[] = validationData.test_location_validation || [];
const assumptions: string[] = validationData.assumptions || [];
const validationScore: number = validationData.validation_score || 0;
const fileSymbolScore: number = validationData.file_symbol_score || 0;
const claimsScore: number = validationData.claims_score || 0;
const relevanceScore: number = validationData.relevance_score || 0;

// Compute dynamic confidence
const confidence = validationScore >= 80 ? "HIGH" : validationScore >= 50 ? "MEDIUM" : "LOW";

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

// 2. Acceptance Criteria (behavioral)
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
if (frameworks.length > 0) {
  out.human("**Frameworks:** " + frameworks.join(", "));
}
if (packageManagers.length > 0) {
  out.human("**Package Managers:** " + packageManagers.join(", "));
}
if (buildSystem.length > 0) {
  out.human("**Build System:** " + buildSystem.join(", "));
}
if (sourceDirectories.length > 0) {
  out.human("**Source Directories:** " + sourceDirectories.join(", "));
}
if (testDirectories.length > 0) {
  out.human("**Test Directories:** " + testDirectories.join(", "));
}
if (entryPoints.length > 0) {
  out.human("**Entry Points:** " + entryPoints.join(", "));
}
if (Object.keys(configFiles).length > 0) {
  out.human("**Config Files:** " + Object.entries(configFiles).map(([k, v]) => `${k} (${v})`).join(", "));
}
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
    const confidence = typeof f.confidence === 'number' ? `${Math.round(f.confidence * 100)}%` : "N/A";
    out.human(`| \`${f.path}\` | ${f.matched_concept || "general"} | ${confidence} | ${(f.reasons || []).slice(0, 2).join("; ")} |`);
  });
} else {
  out.human("| (none found) | - | - | No relevant files identified |");
}
out.human("");
if (relevantFiles.length > 0 && relevantFiles[0].relevant_lines?.length > 0) {
  out.human("**Key Code Locations:**");
  relevantFiles.slice(0, 3).forEach((f: any) => {
    if (f.relevant_lines && f.relevant_lines.length > 0) {
      out.human(`- \`${f.path}:${f.relevant_lines[0].line}\` — ${f.relevant_lines[0].text}`);
    }
  });
  out.human("");
}

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
    if (cp.evidence && cp.evidence.length > 0) {
      out.human(`  - Evidence: \`${cp.file}:${cp.evidence[0].line}\` — ${cp.evidence[0].text}`);
    }
    out.human("");
  });
} else {
  out.human("No dependency paths traced. Manual analysis recommended.");
  out.human("");
}

// 6. Existing Patterns
out.human("## 6. Existing Patterns");
out.human("");
if (relevantPatterns.length > 0) {
  relevantPatterns.slice(0, 8).forEach((p: any) => {
    out.human(`**${p.existing_pattern}:**`);
    if (p.locations) {
      p.locations.slice(0, 2).forEach((loc: any) => {
        out.human(`- \`${loc.file}:${loc.line}\`: ${loc.snippet}`);
        if (loc.how_it_applies) {
          out.human(`  - How it applies: ${loc.how_it_applies}`);
        }
        if (loc.similarity) {
          out.human(`  - Similarity: ${Math.round(loc.similarity * 100)}%`);
        }
      });
    }
    out.human("");
  });
} else {
  out.human("No issue-relevant patterns found in the codebase.");
  out.human("");
}
if (conventions.length > 0) {
  out.human("**Code Conventions:**");
  conventions.slice(0, 5).forEach((c: any) => {
    out.human(`- ${c.pattern} (${c.file}, ${c.count} occurrences)`);
  });
  out.human("");
}

// 7. Implementation Changes
out.human("## 7. Implementation Changes");
out.human("");
if (changes.length > 0) {
  changes.slice(0, 10).forEach((ch: any, i: number) => {
    out.human(`### Step ${i + 1} — ${ch.confidence} Confidence`);
    out.human("");
    out.human(`**File:** \`${ch.file}:${ch.line}\``);
    out.human(`**Symbol:** \`${ch.symbol}\``);
    out.human(`**Current Behavior:** ${ch.current_behavior}`);
    out.human(`**Required Behavior:** ${ch.required_behavior}`);
    out.human(`**Reason:** ${ch.reason}`);
    if (ch.evidence && ch.evidence.length > 0) {
      out.human("**Evidence:**");
      ch.evidence.slice(0, 3).forEach((e: any) => {
        out.human(`- \`${ch.file}:${e.line}\` — ${e.text}`);
      });
    }
    if (ch.dependencies && ch.dependencies.length > 0) {
      out.human(`**Dependencies:** ${ch.dependencies.map((d: any) => `\`${d.symbol}\` (${d.relationship})`).join(", ")}`);
    }
    if (ch.depended_by && ch.depended_by.length > 0) {
      out.human(`**Depended By:** ${ch.depended_by.map((d: any) => `\`${d.symbol}\` in \`${d.file}\``).join(", ")}`);
    }
    out.human("");
  });
} else {
  out.human("No specific changes determined. Manual analysis required.");
  out.human("");
}

// 8. Testing Strategy
out.human("## 8. Testing Strategy");
out.human("");
out.human(`**Test Framework:** ${testFramework}`);
out.human("");
if (relevantTestFiles.length > 0) {
  out.human("**Relevant Test Files:**");
  relevantTestFiles.forEach((t: any) => {
    out.human(`- \`${t.file}\` (relevance: ${t.relevance}) — ${t.reasons.join(", ")}`);
  });
  out.human("");
}
if (testFiles.length > 0) {
  out.human("**All Test Files:**");
  testFiles.slice(0, 10).forEach((t: string) => out.human(`- \`${t}\``));
  out.human("");
}
if (missingCoverage.length > 0) {
  out.human("**Missing Coverage:**");
  missingCoverage.forEach((m: string) => out.human(`- No tests for '${m}'`));
  out.human("");
}
if (recommendedTests.length > 0) {
  out.human("**Recommended Tests:**");
  recommendedTests.forEach((r: any) => {
    out.human(`- \`${r.suggested_test_file}\` — ${r.what_to_test}`);
    out.human(`  - Reason: ${r.reason}`);
  });
  out.human("");
}

// 9. Edge Cases
out.human("## 9. Edge Cases");
out.human("");
if (unknowns.length > 0) {
  unknowns.forEach((u: string) => out.human(`- ${u}`));
}
if (constraints.length > 0) {
  constraints.forEach((c: string) => out.human(`- ${c}`));
}
if (unknowns.length === 0 && constraints.length === 0) {
  out.human("- No specific edge cases identified from issue analysis");
}
out.human("");

// 10. Risks
out.human("## 10. Risks");
out.human("");
if (filesMissing.length > 0) {
  out.human("**Missing Files:**");
  filesMissing.forEach((f: any) => out.human(`- \`${f.file}\` not found`));
  out.human("");
}
if (symbolsMissing.length > 0) {
  out.human("**Missing Symbols:**");
  symbolsMissing.forEach((s: any) => out.human(`- \`${s.symbol}\` not found in \`${s.file}\``));
  out.human("");
}
if (assumptions.length > 0) {
  out.human("**Assumptions:**");
  assumptions.forEach((a: string) => out.human(`- ${a}`));
  out.human("");
}
if (filesMissing.length === 0 && symbolsMissing.length === 0 && assumptions.length === 0) {
  out.human("No significant risks identified.");
}
out.human("");

// 11. Implementation Order
out.human("## 11. Implementation Order");
out.human("");
if (implOrder.length > 0) {
  implOrder.forEach((o: any) => {
    const typeEmoji = o.type === "testing" ? "[test]" : o.type === "validation" ? "[validate]" : o.type === "review" ? "[review]" : "[impl]";
    out.human(`${o.step}. ${typeEmoji} ${o.description}`);
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
const allEvidence: any[] = [];
filesVerified.slice(0, 10).forEach((f: any) => allEvidence.push({ type: "file", text: `\`${f.file}\` exists` }));
symbolsVerified.slice(0, 10).forEach((s: any) => allEvidence.push({ type: "symbol", text: `\`${s.symbol}\` in \`${s.file}\` — ${s.status}` }));
sourceClaims.filter((c: any) => c.supported).slice(0, 5).forEach((c: any) => allEvidence.push({ type: "claim", text: `\`${c.symbol}\`: ${c.observation}` }));
if (allEvidence.length > 0) {
  allEvidence.forEach((e: any) => out.human(`- [${e.type}] ${e.text}`));
} else {
  out.human("- Limited evidence available");
}
out.human("");

// 13. Validation Results
out.human("## 13. Validation Results");
out.human("");
out.human(`**Overall Validation Score:** ${validationScore}%`);
out.human("");
out.human(`| Metric | Score |`);
out.human(`|--------|-------|`);
out.human(`| File/Symbol Verification | ${fileSymbolScore}% |`);
out.human(`| Source Claims Verification | ${claimsScore}% |`);
out.human(`| Change Relevance | ${relevanceScore}% |`);
out.human("");
out.human(`- Files verified: ${filesVerified.length}`);
out.human(`- Files missing: ${filesMissing.length}`);
out.human(`- Symbols verified: ${symbolsVerified.length}`);
out.human(`- Symbols missing: ${symbolsMissing.length}`);
out.human(`- Source claims verified: ${sourceClaims.filter((c: any) => c.supported).length}/${sourceClaims.length}`);
out.human(`- Relevant changes: ${changeRelevance.filter((r: any) => r.relevant).length}/${changeRelevance.length}`);
if (testLocationValidation.length > 0) {
  out.human(`- Test locations valid: ${testLocationValidation.filter((t: any) => t.valid).length}/${testLocationValidation.length}`);
}
if (assumptions.length > 0) {
  out.human(`- Assumptions: ${assumptions.length}`);
}
out.human("");

// 14. Confidence
out.human("## 14. Confidence");
out.human("");
out.human(`**${confidence}**`);
out.human("");
if (confidence === "HIGH") {
  out.human("All referenced files and symbols were verified. Source claims are supported by code evidence. Repository evidence strongly supports the recommendations.");
} else if (confidence === "MEDIUM") {
  out.human("Most evidence exists but some uncertainty remains. Some source claims could not be fully verified. Manual review recommended for complex areas.");
} else {
  out.human("Limited evidence available. Significant manual analysis required before implementation. Some files or symbols could not be verified.");
}

out.summary(`Issue2Plan: ${confidence} confidence plan for "${ctx.params.issue_title}" (${validationScore}% validation)`);
out.result({
  run_id: ctx.run.run_id,
  issue_title: ctx.params.issue_title,
  repo_path: ctx.params.repo_path,
  confidence,
  validation_score: validationScore,
  file_symbol_score: fileSymbolScore,
  claims_score: claimsScore,
  relevance_score: relevanceScore,
  problem,
  keywords,
  requirements,
  languages: Object.keys(languages),
  frameworks,
  relevant_files: relevantFiles.length,
  changes: changes.length,
  test_files: testFiles.length,
  files_verified: filesVerified.length,
  files_missing: filesMissing.length,
  symbols_verified: symbolsVerified.length,
  symbols_missing: symbolsMissing.length,
});
