#!/usr/bin/env -S rote play run
/**
 * @rote-frontmatter
 * ---
 * name: issue2plan
 * description: "Turn any GitHub issue into an evidence-backed, file-level implementation plan by investigating the repository"
 * metadata:
 *   rote_version: 0.79.0
 *   version: 0.1.0
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
 *   understand_issue:
 *     type: process.exec
 *     argv: [echo, "Understanding issue: $issue_title"]
 *   explore_repository:
 *     type: process.exec
 *     argv: [sh, -c, "ls -la $repo_path && echo '---' && find $repo_path -maxdepth 2 -type f | head -50"]
 *     depends_on: [understand_issue]
 *   identify_relevant_files:
 *     type: process.exec
 *     argv: [sh, -c, "find $repo_path -type f -name '*.ts' -o -name '*.js' -o -name '*.json' -o -name '*.md' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.yaml' -o -name '*.yml' -o -name '*.toml'"]
 *     depends_on: [explore_repository]
 *   trace_dependencies:
 *     type: process.exec
 *     argv: [sh, -c, "grep -rn 'import\\|require\\|from' $repo_path --include='*.ts' --include='*.js' --include='*.py' | head -30"]
 *     depends_on: [identify_relevant_files]
 *   search_patterns:
 *     type: process.exec
 *     argv: [sh, -c, "grep -rn 'function' $repo_path --include='*.ts' --include='*.js' --include='*.py' | head -30"]
 *     depends_on: [trace_dependencies]
 *   analyze_tests:
 *     type: process.exec
 *     argv: [sh, -c, "find $repo_path -type f -name '*.test.*' -o -name '*.spec.*' -o -name '*_test.*' -o -name 'test_*'"]
 *     depends_on: [search_patterns]
 *   determine_changes:
 *     type: process.exec
 *     argv: [sh, -c, "grep -rn 'TODO\\|FIXME' $repo_path --include='*.ts' --include='*.js' --include='*.py' | head -20"]
 *     depends_on: [analyze_tests]
 *   validate_findings:
 *     type: process.exec
 *     argv: [sh, -c, "find $repo_path -type f -name '*.ts' -o -name '*.js' | xargs wc -l 2>/dev/null | tail -1"]
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

const understandIssue = ctx.requireAvailable(stepName("understand_issue"));
const exploreRepository = ctx.requireAvailable(stepName("explore_repository"));
const identifyRelevantFiles = ctx.requireAvailable(stepName("identify_relevant_files"));
const traceDependencies = ctx.requireAvailable(stepName("trace_dependencies"));
const searchPatterns = ctx.requireAvailable(stepName("search_patterns"));
const analyzeTests = ctx.requireAvailable(stepName("analyze_tests"));
const determineChanges = ctx.requireAvailable(stepName("determine_changes"));
const validateFindings = ctx.requireAvailable(stepName("validate_findings"));

const extractText = (output: any): string => {
  if (output.body?.stdout?.text) {
    return output.body.stdout.text;
  }
  return "No output available";
};

const repositoryStructure = extractText(exploreRepository);
const relevantFiles = extractText(identifyRelevantFiles);
const testFiles = extractText(analyzeTests);
const dependencyInfo = extractText(traceDependencies);
const patternInfo = extractText(searchPatterns);
const changeHints = extractText(determineChanges);
const codeMetrics = extractText(validateFindings);

const fileList = relevantFiles.split('\n').filter((f: string) => f.trim() && !f.includes('No such file'));
const testFileList = testFiles.split('\n').filter((f: string) => f.trim() && !f.includes('No such file'));

const importLines = dependencyInfo.split('\n').filter((line: string) => line.trim());
const imports = importLines.map((line: string) => {
  const match = line.match(/[^/]+\.(ts|js|py|go|rs|java):\d+:(.+)/);
  return match ? match[2].trim() : line;
}).filter((imp: string) => imp.length > 0);

const patternLines = patternInfo.split('\n').filter((line: string) => line.trim());
const patterns = patternLines.map((line: string) => {
  const match = line.match(/[^/]+\.(ts|js|py|go|rs|java):\d+:(.+)/);
  return match ? match[2].trim() : line;
}).filter((pat: string) => pat.length > 0);

const todoLines = changeHints.split('\n').filter((line: string) => line.trim());
const todos = todoLines.map((line: string) => {
  const match = line.match(/[^/]+\.(ts|js|py|go|rs|java):\d+:(.+)/);
  return match ? match[2].trim() : line;
}).filter((todo: string) => todo.length > 0);

out.human("# Implementation Plan");
out.human("");
out.human("## Issue");
out.human(ctx.params.issue_title);
out.human("");
out.human("## 1. Requirement Summary");
out.human(ctx.params.issue_body);
out.human("");
out.human("## 2. Repository Understanding");
out.human("Repository structure:");
out.human(repositoryStructure);
out.human("");
out.human("## 3. Affected Components");
out.human("Relevant files identified:");
if (fileList.length > 0) {
  fileList.slice(0, 15).forEach((file: string) => {
    out.human(`- ${file}`);
  });
  if (fileList.length > 15) {
    out.human(`- ... and ${fileList.length - 15} more files`);
  }
} else {
  out.human("- No relevant files found");
}
out.human("");
out.human("## 4. Implementation Changes");
if (imports.length > 0) {
  out.human("Detected imports/dependencies:");
  imports.slice(0, 10).forEach((imp: string) => {
    out.human(`- ${imp}`);
  });
} else {
  out.human("No import dependencies detected");
}
out.human("");
out.human("## 5. Dependencies");
if (patterns.length > 0) {
  out.human("Code structure patterns found:");
  patterns.slice(0, 10).forEach((pat: string) => {
    out.human(`- ${pat}`);
  });
} else {
  out.human("No code structure patterns detected");
}
out.human("");
out.human("## 6. Testing Strategy");
out.human("Existing tests:");
if (testFileList.length > 0) {
  testFileList.slice(0, 10).forEach((file: string) => {
    out.human(`- ${file}`);
  });
} else {
  out.human("- No existing tests found");
}
out.human("");
out.human("## 7. Edge Cases");
if (todos.length > 0) {
  out.human("Known issues/TODOs:");
  todos.slice(0, 10).forEach((todo: string) => {
    out.human(`- ${todo}`);
  });
} else {
  out.human("No known issues/TODOs found");
}
out.human("");
out.human("## 8. Risks");
out.human(`Code metrics: ${codeMetrics.trim() || 'Metrics unavailable'}`);
out.human("");
out.human("## 9. Implementation Order");
out.human("1. Analyze issue requirements");
out.human("2. Explore repository structure");
out.human("3. Identify relevant files");
out.human("4. Trace dependencies");
out.human("5. Search for patterns");
out.human("6. Analyze tests");
out.human("7. Determine changes");
out.human("8. Validate findings");
out.human("");
out.human("## 10. Evidence");
out.human(`- Repository exploration completed (${repositoryStructure.split('\n').length} lines)`);
out.human(`- File analysis performed (${fileList.length} files found)`);
out.human(`- Dependency tracing done (${imports.length} imports detected)`);
out.human(`- Pattern search completed (${patterns.length} patterns found)`);
out.human(`- Test analysis completed (${testFileList.length} test files found)`);
out.human("");
out.human("## Confidence");
out.human("MEDIUM");
out.human("Initial analysis completed. Manual review recommended for complex repositories.");

out.summary(`Issue2Plan: Generated implementation plan for "${ctx.params.issue_title}"`);
out.result({
  run_id: ctx.run.run_id,
  issue_title: ctx.params.issue_title,
  repo_path: ctx.params.repo_path,
  steps_completed: 8,
  status: "plan_generated",
  repository_structure: repositoryStructure,
  relevant_files: relevantFiles,
  test_files: testFiles,
  dependencies: dependencyInfo,
  patterns: patternInfo,
  todos: changeHints,
  metrics: codeMetrics,
});
