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

skip_dirs = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build', 'target', '.venv', 'venv', '.next', '.nuxt', 'coverage'}

all_files = []
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), repo)
        all_files.append(rel)

file_scores = []
for filepath in all_files:
    score = 0
    reasons = []
    fname = os.path.basename(filepath).lower()
    dirpath = os.path.dirname(filepath).lower()

    ext_map = {
        '.ts': 5, '.tsx': 5, '.js': 5, '.jsx': 5, '.py': 5,
        '.go': 4, '.rs': 4, '.java': 4, '.rb': 4, '.php': 4,
        '.vue': 3, '.svelte': 3
    }
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ext_map:
        score += ext_map[ext]
        reasons.append(f"code file ({ext})")

    if any(x in filepath.lower() for x in ['config', 'setting', 'env']):
        score += 2
        reasons.append("configuration")

    for kw in keywords:
        if kw in fname:
            score += 10
            reasons.append(f"filename matches '{kw}'")
        if kw in dirpath:
            score += 3
            reasons.append(f"directory matches '{kw}'")

    if ext in {'.test.ts', '.spec.ts', '.test.js', '.spec.js', '.test.py', '_test.go', '.spec.py'}:
        score += 3
        reasons.append("test file")

    if any(x in filepath.lower() for x in ['readme', 'changelog', 'license']):
        score -= 5

    if score > 0:
        file_scores.append({"path": filepath, "score": score, "reasons": reasons})

file_scores.sort(key=lambda x: -x["score"])

relevant = [f for f in file_scores if f["score"] >= 5]

for entry in relevant:
    full_path = os.path.join(repo, entry["path"])
    try:
        content = open(full_path, 'r', errors='ignore').read()
        for kw in keywords:
            if kw in content.lower():
                if not any(kw in r for r in entry["reasons"]):
                    entry["reasons"].append(f"contains '{kw}'")
                entry["score"] += 2
    except:
        pass

relevant.sort(key=lambda x: -x["score"])

result = {
    "files": [{"path": f["path"], "score": f["score"], "reasons": f["reasons"]} for f in relevant[:30]],
    "total_files": len(all_files),
    "relevant_count": len(relevant),
    "keywords_used": keywords[:10]
}

with open(os.path.join(context_dir, "relevant_files.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
