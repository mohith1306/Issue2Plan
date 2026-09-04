#!/usr/bin/env -S rote play run
/**
 * @rote-frontmatter
 * ---
 * name: issue2plan
 * description: "Turn any GitHub issue into an evidence-backed, file-level implementation plan by investigating the repository"
 * metadata:
 *   rote_version: 0.79.0
 *   version: 0.2.0
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

const keywords: string[] = issueData.keywords || [];
const requirements: string[] = issueData.requirements || [];
const acceptanceCriteria: string[] = issueData.acceptance_criteria || [];
const constraints: string[] = issueData.constraints || [];
const unknowns: string[] = issueData.unknowns || [];
const languages: Record<string, number> = repoData.languages || {};
const frameworks: string[] = repoData.frameworks || [];
const entryPoints: string[] = repoData.entry_points || [];
const relevantFiles: Array<{path: string; reasons: string[]}> = filesData.files || [];
const callPaths: Array<{file: string; symbol: string; callers: any[]}> = depsData.call_paths || [];
const patterns: Record<string, any[]> = patternsData.relevant_patterns || {};
const conventions: any[] = patternsData.conventions || [];
const testFiles: string[] = testsData.test_files || [];
const testFramework: string = testsData.test_framework || "unknown";
const missingCoverage: string[] = testsData.missing_coverage || [];
const changes: any[] = changesData.changes || [];
const implOrder: any[] = changesData.implementation_order || [];
const filesVerified: any[] = validationData.files_verified || [];
const filesMissing: any[] = validationData.files_missing || [];
const symbolsVerified: any[] = validationData.symbols_verified || [];
const symbolsMissing: any[] = validationData.symbols_missing || [];
const assumptions: string[] = validationData.assumptions || [];
const validationScore: number = validationData.validation_score || 0;

const confidence = validationScore >= 80 ? "HIGH" : validationScore >= 50 ? "MEDIUM" : "LOW";

out.human("# Implementation Plan");
out.human("");
out.human("## Issue");
out.human(ctx.params.issue_title);
out.human("");
out.human("## 1. Requirement Summary");
if (requirements.length > 0) {
  requirements.forEach((r: string) => out.human(`- ${r}`));
} else {
  out.human(ctx.params.issue_body || "No requirements extracted");
}
out.human("");
out.human("## 2. Acceptance Criteria");
if (acceptanceCriteria.length > 0) {
  acceptanceCriteria.forEach((a: string) => out.human(`- ${a}`));
} else {
  out.human("- Requirements must be implemented as described");
}
if (constraints.length > 0) {
  out.human("");
  out.human("**Constraints:**");
  constraints.forEach((c: string) => out.human(`- ${c}`));
}
if (unknowns.length > 0) {
  out.human("");
  out.human("**Unknowns:**");
  unknowns.forEach((u: string) => out.human(`- ${u}`));
}
out.human("");
out.human("## 3. Repository Understanding");
out.human("");
if (Object.keys(languages).length > 0) {
  out.human("**Languages:** " + Object.entries(languages).map(([l, c]) => `${l} (${c} files)`).join(", "));
}
if (frameworks.length > 0) {
  out.human("**Frameworks:** " + frameworks.join(", "));
}
if (entryPoints.length > 0) {
  out.human("**Entry points:** " + entryPoints.join(", "));
}
if (repoData.test_framework) {
  out.human("**Test framework:** " + repoData.test_framework);
}
if (repoData.package_managers && repoData.package_managers.length > 0) {
  out.human("**Package managers:** " + repoData.package_managers.join(", "));
}
out.human("");
out.human("## 4. Relevant Components");
out.human("");
out.human("| File | Relevance |");
out.human("|------|-----------|");
if (relevantFiles.length > 0) {
  relevantFiles.slice(0, 15).forEach((f: any) => {
    const reasons = (f.reasons || []).slice(0, 2).join("; ");
    out.human(`| \`${f.path}\` | ${reasons} |`);
  });
} else {
  out.human("| (none found) | No relevant files identified |");
}
out.human("");
out.human("## 5. Execution / Dependency Path");
out.human("");
if (callPaths.length > 0) {
  callPaths.slice(0, 5).forEach((cp: any) => {
    out.human(`**\`${cp.symbol}\`** in \`${cp.file}\``);
    if (cp.callers && cp.callers.length > 0) {
      cp.callers.forEach((c: any) => out.human(`  - Called by: ${c.caller || c.file}`));
    }
    if (cp.error_handling && cp.error_handling.length > 0) {
      out.human(`  - Error handling: ${cp.error_handling[0]}`);
    }
    out.human("");
  });
} else {
  out.human("No dependency paths traced. Manual analysis recommended.");
  out.human("");
}
out.human("## 6. Existing Patterns");
out.human("");
if (Object.keys(patterns).length > 0) {
  Object.entries(patterns).forEach(([kw, pats]: [string, any[]]) => {
    out.human(`**${kw}:**`);
    pats.slice(0, 3).forEach((p: any) => {
      out.human(`- \`${p.file}\`: ${p.snippet}`);
    });
    out.human("");
  });
} else {
  out.human("No issue-relevant patterns found in the codebase.");
  out.human("");
}
if (conventions.length > 0) {
  out.human("**Code conventions:**");
  conventions.slice(0, 3).forEach((c: any) => {
    out.human(`- ${c.pattern || c.convention} (${c.file || ""})`);
  });
  out.human("");
}
out.human("## 7. Implementation Changes");
out.human("");
if (changes.length > 0) {
  changes.slice(0, 10).forEach((ch: any, i: number) => {
    out.human(`### Step ${i + 1}`);
    out.human("");
    out.human(`**File:** \`${ch.file}\``);
    out.human(`**Symbol:** \`${ch.symbol}\``);
    if (ch.line) out.human(`**Line:** ${ch.line}`);
    out.human(`**Current behavior:** ${ch.current_behavior}`);
    out.human(`**Required behavior:** ${ch.required_behavior}`);
    out.human(`**Reason:** ${ch.reason}`);
    out.human(`**Confidence:** ${ch.confidence}`);
    out.human("");
  });
} else {
  out.human("No specific changes determined. Manual analysis required.");
  out.human("");
}
out.human("## 8. Testing Strategy");
out.human("");
out.human("### Existing Tests");
out.human("");
if (testFiles.length > 0) {
  testFiles.slice(0, 10).forEach((t: string) => out.human(`- \`${t}\``));
} else {
  out.human("- No existing tests found");
}
out.human("");
out.human("**Test framework:** " + testFramework);
out.human("");
out.human("### Missing Coverage");
out.human("");
if (missingCoverage.length > 0) {
  missingCoverage.forEach((m: string) => out.human(`- ${m}`));
} else {
  out.human("- No specific gaps identified");
}
out.human("");
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
out.human("## 10. Risks");
out.human("");
if (filesMissing.length > 0) {
  out.human("**Missing files:**");
  filesMissing.forEach((f: any) => out.human(`- \`${f.file}\` not found`));
  out.human("");
}
if (symbolsMissing.length > 0) {
  out.human("**Missing symbols:**");
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
out.human("## 11. Implementation Order");
out.human("");
if (implOrder.length > 0) {
  implOrder.forEach((o: any) => {
    out.human(`${o.step}. ${o.description}`);
  });
} else {
  out.human("1. Analyze requirements");
  out.human("2. Identify affected files");
  out.human("3. Implement changes");
  out.human("4. Add tests");
  out.human("5. Validate");
}
out.human("");
out.human("## 12. Evidence");
out.human("");
if (filesVerified.length > 0) {
  filesVerified.slice(0, 10).forEach((f: any) => out.human(`- \`${f.file}\` verified`));
}
if (symbolsVerified.length > 0) {
  symbolsVerified.slice(0, 10).forEach((s: any) => out.human(`- \`${s.symbol}\` in \`${s.file}\` verified`));
}
if (filesVerified.length === 0 && symbolsVerified.length === 0) {
  out.human("- Limited evidence available");
}
out.human("");
out.human("## 13. Validation Results");
out.human("");
out.human(`**Validation score:** ${validationScore}%`);
out.human("");
out.human(`- Files verified: ${filesVerified.length}`);
out.human(`- Files missing: ${filesMissing.length}`);
out.human(`- Symbols verified: ${symbolsVerified.length}`);
out.human(`- Symbols missing: ${symbolsMissing.length}`);
if (assumptions.length > 0) {
  out.human(`- Assumptions: ${assumptions.length}`);
}
out.human("");
out.human("## 14. Confidence");
out.human("");
out.human(`**${confidence}**`);
out.human("");
if (confidence === "HIGH") {
  out.human("All referenced files and symbols were verified. Repository evidence supports the recommendations.");
} else if (confidence === "MEDIUM") {
  out.human("Most evidence exists but some uncertainty remains. Manual review recommended for complex areas.");
} else {
  out.human("Limited evidence available. Significant manual analysis required before implementation.");
}

out.summary(`Issue2Plan: ${confidence} confidence plan for "${ctx.params.issue_title}"`);
out.result({
  run_id: ctx.run.run_id,
  issue_title: ctx.params.issue_title,
  repo_path: ctx.params.repo_path,
  confidence,
  validation_score: validationScore,
  keywords,
  requirements,
  languages: Object.keys(languages),
  frameworks,
  relevant_files: relevantFiles.length,
  changes: changes.length,
  test_files: testFiles.length,
  files_verified: filesVerified.length,
  files_missing: filesMissing.length,
});
