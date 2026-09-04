import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")

context_path = os.path.join(context_dir, "issue_context.json")
if os.path.exists(context_path):
    with open(context_path) as f:
        ctx = json.load(f)
    keywords = ctx.get("keywords", [])
else:
    keywords_str = os.environ.get("KEYWORDS", "")
    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

skip_dirs = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build', 'target', '.venv', 'venv'}

test_files = []
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        if re.match(r'.*\.(test|spec)\.(ts|tsx|js|jsx|py|go|rs|java|rb)$', f):
            test_files.append(os.path.relpath(os.path.join(root, f), repo))
        elif f in {'conftest.py', 'setup.cfg', 'pytest.ini'}:
            test_files.append(os.path.relpath(os.path.join(root, f), repo))

test_framework = "unknown"
for tf in ['jest', 'vitest', 'mocha', 'jasmine', 'pytest', 'unittest', 'go test', 'rs test']:
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            try:
                content = open(os.path.join(root, f), 'r', errors='ignore').read()
                if tf == 'jest' and ('jest' in content.lower() or 'describe(' in content or 'it(' in content):
                    test_framework = 'jest'
                elif tf == 'vitest' and 'vitest' in content.lower():
                    test_framework = 'vitest'
                elif tf == 'pytest' and ('pytest' in content or 'def test_' in content or '@pytest' in content):
                    test_framework = 'pytest'
                elif tf == 'unittest' and 'unittest' in content:
                    test_framework = 'unittest'
                elif tf == 'mocha' and ('mocha' in content or 'describe(' in content):
                    test_framework = 'mocha'
            except:
                pass
        if test_framework != "unknown":
            break
    if test_framework != "unknown":
        break

tested_features = []
test_details = []
for tf in test_files:
    full = os.path.join(repo, tf)
    try:
        content = open(full, 'r', errors='ignore').read()
        test_names = []
        for m in re.finditer(r'(?:describe|it|test|def test_|func Test)\s*\(\s*["\'](.+?)["\']', content):
            test_names.append(m.group(1))
        test_details.append({"file": tf, "test_count": len(test_names), "tests": test_names[:10]})
        for name in test_names:
            tested_features.append(name)
    except:
        pass

stop_words = {"the", "a", "an", "to", "for", "in", "on", "with", "from", "by", "as", "is", "was", "are", "this", "that", "should", "must", "will", "can", "may", "add", "create", "update", "remove", "fix", "all", "new", "first", "last", "also", "here", "there", "now", "support", "failed", "requests", "application", "automatically", "handle"}
missing_coverage = []
if keywords:
    for kw in keywords:
        if len(kw) <= 3 or kw in stop_words:
            continue
        found = False
        for feat in tested_features:
            if kw in feat.lower():
                found = True
                break
        if not found:
            missing_coverage.append(f"No tests for '{kw}'")

if not missing_coverage:
    missing_coverage.append("No specific test gaps identified")

result = {
    "test_files": test_files[:20],
    "test_framework": test_framework,
    "test_details": test_details[:10],
    "tested_features": tested_features[:20],
    "missing_coverage": missing_coverage[:10],
    "total_test_files": len(test_files)
}

with open(os.path.join(context_dir, "tests.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
