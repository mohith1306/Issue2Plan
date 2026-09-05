import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")

# Read issue context
context_path = os.path.join(context_dir, "issue_context.json")
if os.path.exists(context_path):
    with open(context_path) as f:
        ctx = json.load(f)
    keywords = ctx.get("keywords", [])
    domain_concepts = ctx.get("domain_concepts", [])
    technical_keywords = ctx.get("technical_keywords", [])
    problem = ctx.get("problem", "")
else:
    keywords = []
    domain_concepts = []
    technical_keywords = []
    problem = ""

# Read relevant files for context
relevant_files_path = os.path.join(context_dir, "relevant_files.json")
if os.path.exists(relevant_files_path):
    with open(relevant_files_path) as f:
        rf = json.load(f)
    relevant_source_files = [item["path"] for item in rf.get("files", []) if not re.match(r'.*\.(test|spec)\.', item["path"])]
else:
    relevant_source_files = []

skip_dirs = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build', 'target', '.venv', 'venv'}

# Find all test files
test_files = []
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        if re.match(r'.*\.(test|spec)\.(ts|tsx|js|jsx|py|go|rs|java|rb)$', f):
            test_files.append(os.path.relpath(os.path.join(root, f), repo))
        elif f in {'conftest.py', 'setup.cfg', 'pytest.ini', 'jest.config.js', 'jest.config.ts', 'vitest.config.ts'}:
            test_files.append(os.path.relpath(os.path.join(root, f), repo))

# Detect test framework
test_framework = "unknown"
framework_indicators = {
    'jest': ['jest', 'describe(', 'it(', 'test(', 'expect(', 'beforeEach', 'afterEach'],
    'vitest': ['vitest', 'describe(', 'it(', 'test(', 'expect('],
    'mocha': ['mocha', 'describe(', 'it(', 'before(', 'after('],
    'jasmine': ['jasmine', 'describe(', 'it(', 'expect(', 'beforeEach'],
    'pytest': ['pytest', 'def test_', '@pytest', 'import pytest'],
    'unittest': ['unittest', 'TestCase', 'setUp', 'tearDown'],
    'go test': ['func Test', 'testing.T', 'testing.B'],
    'rs test': ['#[test]', '#[cfg(test)]', 'assert_eq!'],
}
for tf in test_files:
    full = os.path.join(repo, tf)
    try:
        content = open(full, 'r', errors='ignore').read()
        for framework, indicators in framework_indicators.items():
            matches = sum(1 for ind in indicators if ind in content)
            if matches >= 2:
                test_framework = framework
                break
    except:
        pass
    if test_framework != "unknown":
        break

# Analyze test details
test_details = []
all_test_names = []
for tf in test_files:
    full = os.path.join(repo, tf)
    try:
        content = open(full, 'r', errors='ignore').read()
        test_names = []
        # Match describe/it/test blocks
        for m in re.finditer(r'(?:describe|it|test|spec)\s*\(\s*["\'](.+?)["\']', content):
            test_names.append(m.group(1))
        for m in re.finditer(r'(?:def test_\w+|func Test\w+)', content):
            test_names.append(m.group(0).split('(')[0].split('def ')[-1].split('func ')[-1])
        test_details.append({
            "file": tf,
            "test_count": len(test_names),
            "tests": test_names[:15]
        })
        all_test_names.extend(test_names)
    except:
        pass

# Find relevant test files (those related to the issue)
relevant_test_files = []
for tf in test_files:
    full = os.path.join(repo, tf)
    try:
        content = open(full, 'r', errors='ignore').read()
        content_lower = content.lower()
        relevance = 0
        reasons = []
        for kw in keywords:
            if len(kw) > 2 and kw in content_lower:
                relevance += 1
                reasons.append(kw)
        # Check if test file tests relevant source files
        for src in relevant_source_files:
            src_name = os.path.splitext(os.path.basename(src))[0]
            if src_name in content_lower or src_name in tf:
                relevance += 2
                reasons.append(f"tests {src_name}")
        if relevance > 0:
            relevant_test_files.append({
                "file": tf,
                "relevance": relevance,
                "reasons": reasons[:5]
            })
    except:
        pass
relevant_test_files.sort(key=lambda x: -x["relevance"])
relevant_test_files = relevant_test_files[:10]

# Missing coverage
stop_coverage_words = {"the", "a", "an", "to", "for", "in", "on", "with", "from", "by", "as", "is", "was", "add", "create", "update", "remove", "fix", "support", "failed", "requests", "application", "automatically", "handle"}
missing_coverage = []
if keywords:
    for kw in keywords:
        if len(kw) <= 3 or kw in stop_coverage_words:
            continue
        found = False
        for name in all_test_names:
            if kw in name.lower():
                found = True
                break
        if not found:
            missing_coverage.append(kw)

# Recommended tests
recommended_tests = []
for src in relevant_source_files[:5]:
    src_name = os.path.splitext(os.path.basename(src))[0]
    ext = os.path.splitext(src)[1]
    # Determine test file location convention
    test_dir = "tests"
    test_ext = ".test.ts"
    if ext == '.py':
        test_ext = "_test.py"
    elif ext == '.go':
        test_ext = "_test.go"

    # Check if a test file already exists for this source
    test_file_exists = False
    for tf in test_files:
        if src_name in tf:
            test_file_exists = True
            break

    if not test_file_exists:
        test_location = f"tests/{src_name}{test_ext}"
        # Check common test directories
        for td in ['test', 'tests', '__tests__', 'spec']:
            candidate = f"{td}/{src_name}{test_ext}"
            candidate_path = os.path.join(repo, candidate)
            if os.path.isdir(os.path.dirname(candidate_path)):
                test_location = candidate
                break

        recommended_tests.append({
            "source_file": src,
            "suggested_test_file": test_location,
            "what_to_test": f"Behavior of {src_name} functions",
            "reason": f"No existing tests found for {src_name}"
        })

# Add recommendations for missing coverage
for kw in missing_coverage[:3]:
    recommended_tests.append({
        "source_file": "(related to issue)",
        "suggested_test_file": f"tests/{kw.replace(' ', '_')}_test.ts",
        "what_to_test": f"Behavior related to '{kw}'",
        "reason": f"No tests found for '{kw}' functionality"
    })

result = {
    "test_files": test_files[:20],
    "test_framework": test_framework,
    "test_details": test_details[:10],
    "relevant_test_files": relevant_test_files,
    "missing_coverage": missing_coverage[:10],
    "recommended_tests": recommended_tests[:10],
    "total_test_files": len(test_files)
}

with open(os.path.join(context_dir, "tests.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
