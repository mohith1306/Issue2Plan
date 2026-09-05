import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")

# Read issue context for keywords and search concepts
context_path = os.path.join(context_dir, "issue_context.json")
if os.path.exists(context_path):
    with open(context_path) as f:
        ctx = json.load(f)
    keywords = ctx.get("keywords", [])
    domain_concepts = ctx.get("domain_concepts", [])
    technical_keywords = ctx.get("technical_keywords", [])
    likely_components = ctx.get("likely_components", [])
else:
    keywords_str = os.environ.get("KEYWORDS", "")
    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
    domain_concepts = []
    technical_keywords = []
    likely_components = []

# Read repo context for source directories
repo_ctx_path = os.path.join(context_dir, "repo_context.json")
if os.path.exists(repo_ctx_path):
    with open(repo_ctx_path) as f:
        repo_ctx = json.load(f)
    source_dirs = repo_ctx.get("source_directories", [])
    test_dirs = repo_ctx.get("test_directories", [])
else:
    source_dirs = []
    test_dirs = []

skip_dirs = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build', 'target', '.venv', 'venv', '.next', '.nuxt', 'coverage'}

# Build search concepts from issue analysis
search_concepts = []
for kw in technical_keywords:
    if len(kw) > 2:
        search_concepts.append(kw)
for dc in domain_concepts:
    parts = dc.lower().split('/')
    for p in parts:
        if len(p) > 2:
            search_concepts.append(p.strip())
for comp in likely_components:
    parts = comp.lower().split()
    for p in parts:
        if len(p) > 2:
            search_concepts.append(p.strip())
search_concepts = list(dict.fromkeys(search_concepts))[:20]

# Collect all files
all_files = []
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), repo)
        all_files.append(rel)

# Score files
file_scores = []
for filepath in all_files:
    score = 0
    reasons = []
    matched_concepts = []
    fname = os.path.basename(filepath).lower()
    dirpath = os.path.dirname(filepath).lower()

    ext = os.path.splitext(filepath)[1].lower()
    code_exts = {'.ts': 5, '.tsx': 5, '.js': 5, '.jsx': 5, '.py': 5, '.go': 4, '.rs': 4, '.java': 4, '.rb': 4, '.php': 4, '.vue': 3, '.svelte': 3}
    if ext in code_exts:
        score += code_exts[ext]
        reasons.append(f"code file ({ext})")

    is_test = bool(re.match(r'.*\.(test|spec)\.(ts|tsx|js|jsx|py)$', filepath))
    if is_test:
        score += 3
        reasons.append("test file")

    # Match against search concepts
    for concept in search_concepts:
        concept_lower = concept.lower()
        if concept_lower in fname:
            score += 10
            reasons.append(f"filename matches '{concept}'")
            matched_concepts.append(concept)
        if concept_lower in dirpath:
            score += 3
            reasons.append(f"directory matches '{concept}'")
            matched_concepts.append(concept)

    # Match against keywords in content
    full_path = os.path.join(repo, filepath)
    relevant_lines = []
    try:
        content = open(full_path, 'r', errors='ignore').read()
        content_lines = content.split('\n')
        for i, line in enumerate(content_lines):
            line_lower = line.lower()
            for kw in keywords:
                if len(kw) > 2 and kw in line_lower:
                    score += 2
                    if kw not in matched_concepts:
                        matched_concepts.append(kw)
                    if len(relevant_lines) < 5:
                        relevant_lines.append({"line": i + 1, "text": line.strip()[:120], "keyword": kw})
                    break  # one match per line is enough

        # Check for TODO/FIXME related to keywords
        for i, line in enumerate(content_lines):
            if 'TODO' in line or 'FIXME' in line:
                line_lower = line.lower()
                for kw in keywords:
                    if len(kw) > 2 and kw in line_lower:
                        score += 5
                        reasons.append(f"TODO/FIXME mentions '{kw}'")
                        if len(relevant_lines) < 5:
                            relevant_lines.append({"line": i + 1, "text": line.strip()[:120], "keyword": kw})
                        break
    except:
        pass

    # Boost source dirs
    if source_dirs:
        for sd in source_dirs:
            if dirpath.startswith(sd) or dirpath == sd:
                score += 2
                reasons.append(f"in source directory ({sd})")
                break

    # Penalize non-essential files
    if any(x in filepath.lower() for x in ['readme', 'changelog', 'license', '.md', '.txt']):
        score -= 5

    if score > 0:
        # Normalize confidence to 0-1 range
        max_possible = 10 + len(keywords) * 2 + 5  # filename match + content matches + TODO boost
        confidence = min(1.0, round(score / max(max_possible, 1), 2))

        file_scores.append({
            "path": filepath,
            "score": score,
            "reasons": reasons,
            "matched_concept": matched_concepts[0] if matched_concepts else "general relevance",
            "relevant_lines": relevant_lines,
            "confidence": confidence
        })

file_scores.sort(key=lambda x: -x["score"])
relevant = [f for f in file_scores if f["score"] >= 5][:30]

result = {
    "files": [
        {
            "path": f["path"],
            "score": f["score"],
            "reasons": f["reasons"],
            "matched_concept": f["matched_concept"],
            "relevant_lines": f["relevant_lines"],
            "confidence": f["confidence"]
        }
        for f in relevant
    ],
    "total_files": len(all_files),
    "relevant_count": len(relevant),
    "search_concepts_used": search_concepts[:10]
}

with open(os.path.join(context_dir, "relevant_files.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
