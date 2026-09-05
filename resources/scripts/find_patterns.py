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

# --- Helper: Detect context type of a line ---
def detect_context_type(line, prev_lines):
    """Detect whether a line is in a comment, import, function body, type annotation, etc."""
    stripped = line.strip()

    # Comment detection
    if stripped.startswith('//') or stripped.startswith('#') or stripped.startswith('/*') or stripped.startswith('*'):
        return "comment"
    if stripped.startswith('<!--'):
        return "comment"

    # Import detection
    if re.match(r'^(?:import|from|require)\s', stripped):
        return "import"

    # Type annotation detection
    if re.match(r'^(?:export\s+)?(?:type|interface|enum)\s', stripped):
        return "type_definition"

    # Function/class definition
    if re.match(r'^(?:export\s+)?(?:async\s+)?(?:function|class|def|func|fn)\s', stripped):
        return "definition"

    # Check if inside a function (heuristic: indented and previous line is a definition)
    if prev_lines:
        for prev in reversed(prev_lines):
            prev_stripped = prev.strip()
            if prev_stripped and not prev_stripped.startswith('//') and not prev_stripped.startswith('#'):
                if re.match(r'(?:function|class|def|func|fn)\s', prev_stripped):
                    return "function_body"
                break

    return "general_code"

# --- Helper: Check if symbol is exported/reusable ---
def check_reusability(filepath, symbol, content):
    """Check if a symbol is exported, tested, or documented."""
    reusability = []
    if re.search(rf'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+{re.escape(symbol)}', content):
        reusability.append("exported")
    if re.search(rf'export\s+\{{\s*{re.escape(symbol)}', content):
        reusability.append("exported")
    # Check if referenced in test files
    skip_dirs_local = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build'}
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip_dirs_local and not d.startswith('.')]
        for f in files:
            if re.match(r'.*\.(test|spec)\.(ts|tsx|js|jsx|py)$', f):
                try:
                    test_content = open(os.path.join(root, f), 'r', errors='ignore').read()
                    if symbol in test_content:
                        reusability.append("tested")
                        return reusability  # early exit
                except:
                    pass
    # Check for JSDoc/docstring
    for m in re.finditer(rf'(?:/\*\*[\s\S]*?\*/\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+{re.escape(symbol)}|"""\s*(?:def|class)\s+{re.escape(symbol)})', content):
        reusability.append("documented")
        break
    return reusability

# --- Search for patterns with structure awareness ---
relevant_patterns = []
for term in search_terms:
    term_lower = term.lower()
    locations_found = []

    for filepath in scan_files[:25]:
        full = os.path.join(repo, filepath)
        try:
            content = open(full, 'r', errors='ignore').read()
            lines = content.split('\n')
        except:
            continue

        prev_lines = []
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if term_lower in line_lower:
                context_type = detect_context_type(line, prev_lines)
                snippet = line.strip()[:120]

                # Calculate similarity with structure awareness
                similarity = 0
                how_it_applies = ""

                # Weight by context type
                context_weight = {
                    "definition": 1.0,
                    "function_body": 0.9,
                    "general_code": 0.7,
                    "import": 0.5,
                    "type_definition": 0.6,
                    "comment": 0.2
                }.get(context_type, 0.5)

                # Check relationship to problem
                problem_words = [w for w in problem.lower().split() if len(w) > 3]
                exp_words = [w for w in expected_behavior.lower().split() if len(w) > 3]
                nearby_text = '\n'.join(lines[max(0, i-3):min(len(lines), i+4)]).lower()

                for pw in problem_words:
                    if pw in nearby_text:
                        similarity += 0.15
                        how_it_applies = f"Related to problem: '{pw}' in nearby code"
                for ew in exp_words:
                    if ew in nearby_text:
                        similarity += 0.1
                        how_it_applies = how_it_applies or f"Related to expected behavior: '{ew}'"

                # TODO/FIXME in nearby code
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    if 'TODO' in lines[j] or 'FIXME' in lines[j]:
                        if term_lower in lines[j].lower():
                            similarity += 0.25
                            how_it_applies = "Area marked as needing implementation (TODO/FIXME)"
                            break

                # Existing implementation (not just a comment)
                if context_type in ("definition", "function_body"):
                    similarity += 0.2
                    if not how_it_applies:
                        how_it_applies = f"Existing implementation in {context_type}"

                # Apply context weight
                similarity = similarity * context_weight
                similarity = min(1.0, round(similarity, 2))

                # Confidence based on evidence quality
                confidence = 0.1  # minimum for any match
                if context_type == "definition":
                    confidence = 0.8
                elif context_type == "function_body":
                    confidence = 0.7
                elif context_type == "general_code":
                    confidence = 0.5
                elif context_type == "import":
                    confidence = 0.4
                elif context_type == "comment":
                    confidence = 0.2

                if similarity > 0.3:
                    confidence = min(1.0, confidence + similarity * 0.2)

                # Check reusability
                symbol_in_line = ""
                m = re.search(r'(?:function|class|def|func|fn|const|let|var)\s+(\w+)', line)
                if m:
                    symbol_in_line = m.group(1)
                reusability = []
                if symbol_in_line:
                    reusability = check_reusability(filepath, symbol_in_line, content)

                if similarity > 0 or context_type == "definition":
                    locations_found.append({
                        "file": filepath,
                        "line": i + 1,
                        "snippet": snippet,
                        "context_type": context_type,
                        "similarity": similarity,
                        "how_it_applies": how_it_applies or f"Contains '{term}' reference",
                        "reusability": reusability,
                        "confidence": round(confidence, 2)
                    })

            prev_lines.append(line)
            if len(prev_lines) > 5:
                prev_lines.pop(0)

            if len(locations_found) >= 3:
                break
        if len(locations_found) >= 3:
            break

    # Sort by confidence * similarity
    locations_found.sort(key=lambda x: x["confidence"] * x["similarity"], reverse=True)

    if locations_found:
        best = locations_found[0]
        relevant_patterns.append({
            "existing_pattern": term,
            "locations": locations_found[:3],
            "evidence": best["snippet"],
            "how_it_applies": best["how_it_applies"],
            "confidence": best["confidence"]
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
