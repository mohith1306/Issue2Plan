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
    expected_behavior = ctx.get("expected_behavior", "")
else:
    keywords = []
    domain_concepts = []
    technical_keywords = []
    problem = ""
    expected_behavior = ""

# Read relevant files
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

# Build search terms from issue analysis
search_terms = []
for kw in technical_keywords:
    if len(kw) > 2:
        search_terms.append(kw)
for dc in domain_concepts:
    parts = dc.lower().split('/')
    for p in parts:
        p = p.strip()
        if len(p) > 2:
            search_terms.append(p)
# Add related terms based on domain concepts
related_term_map = {
    'Binary Data': ['Buffer', 'Uint8Array', 'Blob', 'Stream', 'binary', 'typed array'],
    'Response Handling': ['res.send', 'res.json', 'res.write', 'res.end', 'response.send', 'response.body'],
    'Serialization': ['JSON.parse', 'JSON.stringify', 'serialize', 'deserialize', 'encode', 'decode'],
    'Retry/Resilience': ['retry', 'backoff', 'exponential', 'timeout', 'delay', 'attempt'],
    'Error Handling': ['try', 'catch', 'throw', 'Error', 'Exception', 'reject'],
    'HTTP/Web': ['http', 'https', 'request', 'response', 'fetch', 'axios'],
    'Testing': ['describe', 'it', 'test', 'expect', 'assert', 'mock', 'stub'],
}
for dc in domain_concepts:
    if dc in related_term_map:
        search_terms.extend(related_term_map[dc])
search_terms = list(dict.fromkeys(search_terms))[:25]

# Search for patterns
relevant_patterns = []
for term in search_terms:
    term_lower = term.lower()
    patterns_found = []
    for filepath in scan_files[:25]:
        full = os.path.join(repo, filepath)
        try:
            content = open(full, 'r', errors='ignore').read()
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if term_lower in line.lower():
                    snippet = line.strip()[:120]
                    # Calculate similarity: how well does this pattern match the issue?
                    similarity = 0
                    how_it_applies = ""
                    line_lower = line.lower()

                    # Check if this line is related to the problem
                    if problem:
                        problem_words = [w for w in problem.lower().split() if len(w) > 3]
                        for pw in problem_words:
                            if pw in line_lower:
                                similarity += 0.2
                                how_it_applies = f"Pattern relates to problem: '{pw}' found in code"

                    # Check if this line is related to expected behavior
                    if expected_behavior:
                        exp_words = [w for w in expected_behavior.lower().split() if len(w) > 3]
                        for ew in exp_words:
                            if ew in line_lower:
                                similarity += 0.15
                                how_it_applies = f"Pattern relates to expected behavior: '{ew}' found in code"

                    # Check for TODO/FIXME indicating this area needs work
                    if 'TODO' in line or 'FIXME' in line:
                        similarity += 0.3
                        how_it_applies = "Area is marked as needing implementation (TODO/FIXME)"

                    # Check for existing error handling patterns
                    if any(x in line_lower for x in ['try', 'catch', 'throw', 'error']):
                        similarity += 0.1
                        how_it_applies = how_it_applies or "Shows existing error handling pattern"

                    # Check for similar function signatures
                    if 'function' in line_lower or 'def ' in line_lower or 'class ' in line_lower:
                        similarity += 0.1
                        how_it_applies = how_it_applies or "Defines a similar component"

                    similarity = min(1.0, round(similarity, 2))
                    if similarity > 0:
                        patterns_found.append({
                            "file": filepath,
                            "line": i + 1,
                            "snippet": snippet,
                            "similarity": similarity,
                            "how_it_applies": how_it_applies,
                            "confidence": min(1.0, similarity + 0.2)
                        })
                    elif len(patterns_found) < 2:
                        patterns_found.append({
                            "file": filepath,
                            "line": i + 1,
                            "snippet": snippet,
                            "similarity": 0.1,
                            "how_it_applies": f"Contains '{term}' reference",
                            "confidence": 0.3
                        })
                    if len(patterns_found) >= 3:
                        break
        except:
            pass
        if len(patterns_found) >= 3:
            break

    if patterns_found:
        relevant_patterns.append({
            "existing_pattern": term,
            "locations": patterns_found[:3],
            "evidence": patterns_found[0]["snippet"] if patterns_found else ""
        })

# Detect codebase conventions
conventions = []
seen = set()
convention_patterns = [
    (r'export default', "ES module default export"),
    (r'export \{', "Named exports"),
    (r'import \{', "Named imports"),
    (r'async\s+.*await\s+', "Async/await pattern"),
    (r'try\s*\{', "Error handling with try/catch"),
    (r'console\.log', "Console logging"),
    (r'\.then\(', "Promise chaining"),
    (r'=>\s*\{', "Arrow functions"),
    (r'class\s+\w+\s+extends', "Class inheritance"),
    (r'interface\s+\w+', "TypeScript interfaces"),
    (r'type\s+\w+\s*=', "TypeScript type aliases"),
    (r'@\w+\(', "Decorators"),
    (r'def\s+\w+\(self', "Python class methods"),
    (r'func\s+\w+\(', "Go functions"),
]
for filepath in scan_files[:15]:
    full = os.path.join(repo, filepath)
    try:
        content = open(full, 'r', errors='ignore').read()
        for pattern, name in convention_patterns:
            if re.search(pattern, content):
                if name not in seen:
                    conventions.append({
                        "pattern": name,
                        "file": filepath,
                        "count": len(re.findall(pattern, content))
                    })
                    seen.add(name)
    except:
        pass

result = {
    "relevant_patterns": relevant_patterns[:15],
    "conventions": conventions[:10],
    "files_scanned": len(scan_files),
    "search_terms_used": search_terms[:10]
}

with open(os.path.join(context_dir, "patterns.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
