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

relevant_files_path = os.path.join(context_dir, "relevant_files.json")
if os.path.exists(relevant_files_path):
    with open(relevant_files_path) as f:
        rf = json.load(f)
    scan_files = [item["path"] for item in rf.get("files", [])]
else:
    scan_files = []
    skip_dirs = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build'}
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in {'.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rs', '.java', '.rb', '.php'}:
                scan_files.append(os.path.relpath(os.path.join(root, f), repo))

relevant_patterns = {}
for kw in keywords[:5]:
    patterns = []
    for filepath in scan_files[:20]:
        full = os.path.join(repo, filepath)
        try:
            content = open(full, 'r', errors='ignore').read()
            for i, line in enumerate(content.split('\n')):
                if kw in line.lower():
                    snippet = line.strip()[:100]
                    patterns.append({"file": filepath, "line": i + 1, "snippet": snippet})
                    if len(patterns) >= 3:
                        break
        except:
            pass
        if len(patterns) >= 3:
            break
    if patterns:
        relevant_patterns[kw] = patterns

conventions = []
seen = set()
for filepath in scan_files[:10]:
    full = os.path.join(repo, filepath)
    try:
        content = open(full, 'r', errors='ignore').read()
        if 'export default' in content:
            conv = "ES module default export"
            if conv not in seen:
                conventions.append({"pattern": conv, "file": filepath, "count": content.count('export default')})
                seen.add(conv)
        if 'import {' in content:
            conv = "Named imports"
            if conv not in seen:
                conventions.append({"pattern": conv, "file": filepath, "count": content.count('import {')})
                seen.add(conv)
        if 'async ' in content and 'await ' in content:
            conv = "Async/await pattern"
            if conv not in seen:
                conventions.append({"pattern": conv, "file": filepath, "count": content.count('async ')})
                seen.add(conv)
        if 'try {' in content or 'try:' in content:
            conv = "Error handling with try/catch"
            if conv not in seen:
                conventions.append({"pattern": conv, "file": filepath, "count": content.count('try')})
                seen.add(conv)
        if 'console.log' in content:
            conv = "Console logging"
            if conv not in seen:
                conventions.append({"pattern": conv, "file": filepath, "count": content.count('console.log')})
                seen.add(conv)
    except:
        pass

result = {
    "relevant_patterns": relevant_patterns,
    "conventions": conventions[:10],
    "files_scanned": len(scan_files)
}

with open(os.path.join(context_dir, "patterns.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
