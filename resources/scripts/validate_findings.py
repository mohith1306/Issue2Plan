import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")

changes_path = os.path.join(context_dir, "changes.json")
if os.path.exists(changes_path):
    with open(changes_path) as f:
        ch = json.load(f)
    changes = ch.get("changes", [])
else:
    changes_str = os.environ.get("CHANGES", "[]")
    try:
        changes = json.loads(changes_str)
    except:
        changes = []

files_verified = []
files_missing = []
symbols_verified = []
symbols_missing = []
assumptions = []

for change in changes:
    filepath = change.get("file", "")
    symbol = change.get("symbol", "")

    if filepath and filepath != "(to be determined)":
        full = os.path.join(repo, filepath)
        if os.path.exists(full):
            files_verified.append({"file": filepath, "status": "exists"})
        else:
            files_missing.append({"file": filepath, "status": "not found"})
    elif filepath == "(to be determined)":
        assumptions.append("File location needs to be determined during implementation")

    if symbol and symbol != "(to be determined)" and filepath and filepath != "(to be determined)":
        full = os.path.join(repo, filepath)
        try:
            content = open(full, 'r', errors='ignore').read()
            pattern = re.compile(rf'(?:class|function|def|func|fn|interface|type|const|let|var)\s+{re.escape(symbol)}\b')
            if pattern.search(content):
                symbols_verified.append({"symbol": symbol, "file": filepath, "status": "found"})
            else:
                if re.search(rf'\b{re.escape(symbol)}\b', content):
                    symbols_verified.append({"symbol": symbol, "file": filepath, "status": "referenced"})
                else:
                    symbols_missing.append({"symbol": symbol, "file": filepath, "status": "not found"})
        except:
            symbols_missing.append({"symbol": symbol, "file": filepath, "status": "unable to verify"})
    elif symbol == "(to be determined)":
        assumptions.append("Symbol name needs to be determined during implementation")

pattern_consistency = []
for change in changes:
    filepath = change.get("file", "")
    if filepath and filepath != "(to be determined)":
        full = os.path.join(repo, filepath)
        try:
            content = open(full, 'r', errors='ignore').read()
            if 'export default' in content:
                pattern_consistency.append({"file": filepath, "convention": "ES module default export"})
            elif 'module.exports' in content:
                pattern_consistency.append({"file": filepath, "convention": "CommonJS export"})
            elif 'def ' in content and 'self' in content:
                pattern_consistency.append({"file": filepath, "convention": "Python class method"})
        except:
            pass

test_consistency = []
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'vendor', '__pycache__'}]
    for f in files:
        if re.match(r'.*\.(test|spec)\.(ts|tsx|js|jsx|py)$', f):
            full = os.path.join(root, f)
            try:
                content = open(full, 'r', errors='ignore').read()
                if 'describe(' in content and ('it(' in content or 'test(' in content):
                    test_consistency.append({"convention": "describe/it blocks", "file": os.path.relpath(full, repo)})
                elif 'def test_' in content:
                    test_consistency.append({"convention": "pytest functions", "file": os.path.relpath(full, repo)})
            except:
                pass
            break
    if test_consistency:
        break

missing_evidence = []
for change in changes:
    if change.get("confidence") == "LOW":
        missing_evidence.append(f"Recommendation for `{change.get('symbol', 'unknown')}` in `{change.get('file', 'unknown')}` lacks strong evidence")

total_verified = len(files_verified) + len(symbols_verified)
total_missing = len(files_missing) + len(symbols_missing)
total_checks = total_verified + total_missing
validation_score = (total_verified / total_checks * 100) if total_checks > 0 else 0

result = {
    "files_verified": files_verified[:20],
    "files_missing": files_missing[:10],
    "symbols_verified": symbols_verified[:20],
    "symbols_missing": symbols_missing[:10],
    "assumptions": assumptions[:10],
    "pattern_consistency": pattern_consistency[:5],
    "test_consistency": test_consistency[:3],
    "missing_evidence": missing_evidence[:10],
    "validation_score": round(validation_score, 1),
    "total_checks": total_checks
}

with open(os.path.join(context_dir, "validation.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
