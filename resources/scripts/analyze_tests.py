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
    acceptance_criteria = ctx.get("acceptance_criteria", [])
    expected_behavior = ctx.get("expected_behavior", "")
else:
    keywords = []
    domain_concepts = []
    technical_keywords = []
    problem = ""
    acceptance_criteria = []
    expected_behavior = ""

# Read relevant files for context
relevant_files_path = os.path.join(context_dir, "relevant_files.json")
if os.path.exists(relevant_files_path):
    with open(relevant_files_path) as f:
        rf = json.load(f)
    relevant_source_files = [item["path"] for item in rf.get("files", []) if not re.match(r'.*\.(test|spec)\.', item["path"])]
else:
    relevant_source_files = []

skip_dirs = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build', 'target', '.venv', 'venv'}

# Find all test files (ONLY files that actually exist on disk)
test_files = []
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        if re.match(r'.*\.(test|spec)\.(ts|tsx|js|jsx|py|go|rs|java|rb)$', f):
            test_files.append(os.path.relpath(os.path.join(root, f), repo))
        elif f in {'conftest.py', 'setup.cfg', 'pytest.ini', 'jest.config.js', 'jest.config.ts', 'vitest.config.ts'}:
            test_files.append(os.path.relpath(os.path.join(root, f), repo))

# Detect test framework from package.json or config files (not arbitrary file content)
test_framework = "unknown"
pkg_json = os.path.join(repo, "package.json")
if os.path.exists(pkg_json):
    try:
        pkg = json.load(open(pkg_json))
        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "jest" in all_deps or "ts-jest" in all_deps:
            test_framework = "jest"
        elif "vitest" in all_deps:
            test_framework = "vitest"
        elif "mocha" in all_deps:
            test_framework = "mocha"
        elif "jasmine" in all_deps:
            test_framework = "jasmine"
    except:
        pass

if test_framework == "unknown":
    pyproject = os.path.join(repo, "pyproject.toml")
    if os.path.exists(pyproject):
        try:
            content = open(pyproject).read()
            if "pytest" in content:
                test_framework = "pytest"
        except:
            pass

if test_framework == "unknown":
    req_txt = os.path.join(repo, "requirements.txt")
    if os.path.exists(req_txt):
        try:
            content = open(req_txt).read().lower()
            if "pytest" in content:
                test_framework = "pytest"
        except:
            pass

if test_framework == "unknown":
    # Fallback: check config files already found
    for tf in test_files:
        if tf.endswith(('.config.js', '.config.ts')):
            try:
                content = open(os.path.join(repo, tf), 'r', errors='ignore').read()
                if 'jest' in content:
                    test_framework = 'jest'
                    break
                elif 'vitest' in content:
                    test_framework = 'vitest'
                    break
            except:
                pass

# Detect project test conventions from ACTUAL test files
test_naming_convention = None
test_dir_convention = None
if test_files:
    # Analyze first test file for naming pattern
    first_test = test_files[0]
    fname = os.path.basename(first_test)
    if '.test.' in fname:
        test_naming_convention = '.test.'
    elif '.spec.' in fname:
        test_naming_convention = '.spec.'
    elif '_test.' in fname:
        test_naming_convention = '_test.'

    # Analyze directory convention
    test_dir = os.path.dirname(first_test)
    if test_dir:
        test_dir_convention = test_dir
    else:
        test_dir_convention = "."

# Analyze test details
test_details = []
all_test_names = []
all_test_bodies = {}  # test_name -> body text
for tf in test_files:
    full = os.path.join(repo, tf)
    try:
        content = open(full, 'r', errors='ignore').read()
        test_names = []
        # Match describe/it/test blocks with their bodies
        for m in re.finditer(r'(?:describe|it|test|spec)\s*\(\s*["\'](.+?)["\']\s*(?:,\s*(?:async\s*)?\(?[^)]*\)?\s*(?:=>|function))?\s*\{([\s\S]*?)\}\s*\)', content):
            name = m.group(1)
            body = m.group(2)
            test_names.append(name)
            all_test_bodies[name] = body
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
                "reasons": reasons[:5],
                "confidence": "HIGH"  # file exists on disk
            })
    except:
        pass
relevant_test_files.sort(key=lambda x: -x["relevance"])
relevant_test_files = relevant_test_files[:10]

# Missing coverage — check test body content, not just test names
stop_coverage_words = {"the", "a", "an", "to", "for", "in", "on", "with", "from", "by", "as", "is", "was", "add", "create", "update", "remove", "fix", "support", "failed", "requests", "application", "automatically", "handle"}
missing_coverage = []
if keywords:
    for kw in keywords:
        if len(kw) <= 3 or kw in stop_coverage_words:
            continue
        found_in_name = False
        found_in_body = False
        for name in all_test_names:
            if kw in name.lower():
                found_in_name = True
                break
        if not found_in_name:
            for name, body in all_test_bodies.items():
                if kw in body.lower():
                    found_in_body = True
                    break
        if not found_in_name and not found_in_body:
            missing_coverage.append(kw)

# Proposed test modifications — ONLY for existing files
proposed_modifications = []
for rtf in relevant_test_files:
    tf_path = rtf["file"]
    full = os.path.join(repo, tf_path)
    try:
        content = open(full, 'r', errors='ignore').read()
        # Determine what to add based on missing coverage and acceptance criteria
        what_to_add_parts = []
        for kw in missing_coverage[:3]:
            if kw not in content.lower():
                what_to_add_parts.append(f"test for '{kw}' behavior")
        if acceptance_criteria:
            for ac in acceptance_criteria[:2]:
                if not any(kw in content.lower() for kw in ac.lower().split() if len(kw) > 3):
                    what_to_add_parts.append(f"verify: {ac[:60]}")
        if what_to_add_parts:
            proposed_modifications.append({
                "file": tf_path,
                "what_to_add": "; ".join(what_to_add_parts[:3]),
                "confidence": "HIGH",  # file exists
                "reason": f"Existing test file can be extended to cover missing scenarios"
            })
    except:
        pass

# Proposed new tests — clearly labeled as PROPOSED, validated against conventions
proposed_new_tests = []
for src in relevant_source_files[:5]:
    src_name = os.path.splitext(os.path.basename(src))[0]
    ext = os.path.splitext(src)[1]

    # Check if a test file already exists for this source
    test_file_exists = False
    for tf in test_files:
        if src_name in tf:
            test_file_exists = True
            break

    if not test_file_exists:
        # Build proposed path using actual project conventions
        if test_naming_convention and test_dir_convention:
            test_location = f"{test_dir_convention}/{src_name}{test_naming_convention}{ext.lstrip('.')}"
        else:
            # Use most common convention in the project
            test_location = f"tests/{src_name}.test{ext}"

        # Validate: does the test directory actually exist?
        test_dir_path = os.path.dirname(os.path.join(repo, test_location))
        dir_exists = os.path.isdir(test_dir_path)

        # Derive what_to_test from source file's public API
        what_to_test = f"Public API of {src_name}"
        try:
            src_content = open(os.path.join(repo, src), 'r', errors='ignore').read()
            exports = []
            for m in re.finditer(r'export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var)\s+(\w+)', src_content):
                exports.append(m.group(1))
            if exports:
                what_to_test = f"Behavior of exported functions: {', '.join(exports[:5])}"
        except:
            pass

        # Add issue-specific test scenarios
        test_scenarios = []
        for ac in acceptance_criteria[:3]:
            test_scenarios.append(f"Verify: {ac[:80]}")
        for kw in missing_coverage[:2]:
            test_scenarios.append(f"Test '{kw}' handling")

        confidence = "MEDIUM" if dir_exists else "LOW"
        reason = f"No existing tests for {src_name}"
        if not dir_exists:
            reason += f"; test directory '{os.path.dirname(test_location)}' does not exist"

        proposed_new_tests.append({
            "source_file": src,
            "proposed_test_file": test_location,
            "test_directory_exists": dir_exists,
            "what_to_test": what_to_test,
            "test_scenarios": test_scenarios[:5],
            "reason": reason,
            "confidence": confidence,
            "status": "proposed"
        })

# Summary
existing_test_count = len(test_files)
proposed_mod_count = len(proposed_modifications)
proposed_new_count = len(proposed_new_tests)

result = {
    "test_framework": test_framework,
    "test_naming_convention": test_naming_convention,
    "test_dir_convention": test_dir_convention,
    "existing_test_files": test_files[:20],
    "existing_test_count": existing_test_count,
    "test_details": test_details[:10],
    "relevant_existing_tests": relevant_test_files,
    "proposed_modifications": proposed_modifications[:10],
    "proposed_new_tests": proposed_new_tests[:10],
    "missing_coverage": missing_coverage[:10],
    "proposed_modifications_count": proposed_mod_count,
    "proposed_new_tests_count": proposed_new_count,
    "all_test_names": all_test_names[:30]
}

with open(os.path.join(context_dir, "tests.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
