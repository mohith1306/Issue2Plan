import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")

# Read relevant files
relevant_files_path = os.path.join(context_dir, "relevant_files.json")
if os.path.exists(relevant_files_path):
    with open(relevant_files_path) as f:
        rf = json.load(f)
    files_to_trace = [item["path"] for item in rf.get("files", [])]
else:
    files_to_trace = []
    skip_dirs = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build'}
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in {'.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rs', '.java'}:
                files_to_trace.append(os.path.relpath(os.path.join(root, f), repo))
files_to_trace = files_to_trace[:20]

# Read issue context for keywords
context_path = os.path.join(context_dir, "issue_context.json")
if os.path.exists(context_path):
    with open(context_path) as f:
        ctx = json.load(f)
    keywords = ctx.get("keywords", [])
else:
    keywords = []

# Step 1: Extract all symbols from all files
symbol_map = {}  # symbol -> {file, line, type, body_lines}
file_contents = {}
file_symbols = {}  # file -> [symbols]

for filepath in files_to_trace:
    full = os.path.join(repo, filepath)
    try:
        content = open(full, 'r', errors='ignore').read()
        file_contents[filepath] = content
        symbols = []
        lines = content.split('\n')

        # Export declarations
        for m in re.finditer(r'export\s+(?:default\s+)?(?:class|function|const|let|var|interface|type|enum)\s+(\w+)', content):
            sym = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            sym_type = 'export'
            for m2 in re.finditer(r'(class|function|const|let|var|interface|type|enum)', m.group(0)):
                sym_type = m2.group(1)
                break
            symbol_map[sym] = {"file": filepath, "line": line_num, "type": sym_type, "definition": m.group(0)[:100]}
            symbols.append(sym)

        # Non-export function/class definitions
        for m in re.finditer(r'(?:^|\n)(?:export\s+)?(?:async\s+)?(?:function|class|def|func|fn)\s+(\w+)', content):
            sym = m.group(1)
            if sym not in symbol_map:
                line_num = content[:m.start()].count('\n') + 1
                sym_type = 'function' if 'function' in m.group(0) or 'func' in m.group(0) or 'fn' in m.group(0) else 'class'
                symbol_map[sym] = {"file": filepath, "line": line_num, "type": sym_type, "definition": m.group(0).strip()[:100]}
                if sym not in symbols:
                    symbols.append(sym)

        file_symbols[filepath] = symbols
    except:
        pass

# Step 2: For each symbol, find what it calls (callees) and who calls it (callers)
call_paths = []

for filepath, symbols in file_symbols.items():
    content = file_contents.get(filepath, "")
    lines = content.split('\n')

    for symbol in symbols:
        sym_info = symbol_map.get(symbol, {})
        sym_line = sym_info.get("line", 1)

        # Find the function body (approximate: from definition line to next top-level definition)
        body_start = max(0, sym_line - 1)
        body_end = min(len(lines), sym_line + 50)
        for i in range(sym_line, min(len(lines), sym_line + 100)):
            if i > sym_line and re.match(r'^(?:export\s+)?(?:async\s+)?(?:function|class|def|func|fn|interface|type|enum)\s+\w+', lines[i]):
                body_end = i
                break
        body_lines = lines[body_start:body_end]
        body_text = '\n'.join(body_lines)

        # Find what this symbol calls (callees)
        called_symbols = []
        # Function calls: name(
        for m in re.finditer(r'(?<!\.)(\w+)\s*\(', body_text):
            callee = m.group(1)
            if callee != symbol and callee in symbol_map and callee not in [c["symbol"] for c in called_symbols]:
                called_symbols.append({
                    "symbol": callee,
                    "file": symbol_map[callee]["file"],
                    "relationship": "calls"
                })
        # Method calls: obj.method(
        for m in re.finditer(r'\.(\w+)\s*\(', body_text):
            callee = m.group(1)
            if callee in symbol_map and callee != symbol and callee not in [c["symbol"] for c in called_symbols]:
                called_symbols.append({
                    "symbol": callee,
                    "file": symbol_map[callee]["file"],
                    "relationship": "calls"
                })
        # Import statements
        for m in re.finditer(r'(?:import|require)\s+.*?(\w+)', body_text):
            imported = m.group(1)
            if imported in symbol_map and imported != symbol and imported not in [c["symbol"] for c in called_symbols]:
                called_symbols.append({
                    "symbol": imported,
                    "file": symbol_map[imported]["file"],
                    "relationship": "imports"
                })

        # Find who calls this symbol (callers)
        callers = []
        for other_file, other_content in file_contents.items():
            if other_file == filepath:
                continue
            other_lines = other_content.split('\n')
            for i, line in enumerate(other_lines):
                # Check if this symbol is called in the other file
                if re.search(rf'{re.escape(symbol)}\s*\(', line):
                    # Find what function contains this call
                    containing_func = None
                    for j in range(i, -1, -1):
                        m = re.match(r'(?:export\s+)?(?:async\s+)?(?:function|class|def|func|fn)\s+(\w+)', other_lines[j])
                        if m:
                            containing_func = m.group(1)
                            break
                    callers.append({
                        "symbol": containing_func or "unknown",
                        "file": other_file,
                        "line": i + 1,
                        "relationship": "calls"
                    })
                    break  # one caller per file is enough

        # Find error handling
        error_handling = []
        for m in re.finditer(r'(throw|raise|Error|Exception|catch|try|\.catch\(|reject)', body_text):
            error_handling.append(m.group(0))
        error_handling = list(dict.fromkeys(error_handling))[:5]

        # Find exports
        exports = []
        if re.search(rf'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+{re.escape(symbol)}', content):
            exports.append(f"exported from {filepath}")

        # Build evidence lines
        evidence = []
        for i, line in enumerate(body_lines):
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('//') and not line_stripped.startswith('#'):
                for kw in keywords:
                    if len(kw) > 2 and kw in line_stripped.lower():
                        evidence.append({"line": sym_line + i, "text": line_stripped[:120], "keyword": kw})
                        break
                if len(evidence) >= 3:
                    break

        # Determine relationship type
        relationship = "defines"
        if called_symbols:
            relationship = "defines and calls"
        if callers:
            relationship += " (called by others)"
        if error_handling:
            relationship += " with error handling"

        call_paths.append({
            "entry_symbol": symbol,
            "file": filepath,
            "line": sym_line,
            "called_symbols": called_symbols[:10],
            "callers": callers[:10],
            "files": list(dict.fromkeys([filepath] + [c["file"] for c in called_symbols])),
            "relationship": relationship,
            "error_handling": error_handling,
            "exports": exports,
            "evidence": evidence
        })

# Deduplicate and sort
seen = set()
unique_paths = []
for cp in call_paths:
    key = f"{cp['entry_symbol']}:{cp['file']}"
    if key not in seen:
        seen.add(key)
        unique_paths.append(cp)

result = {
    "call_paths": unique_paths[:50],
    "files_traced": len(files_to_trace),
    "symbols_found": sum(len(s) for s in file_symbols.values())
}

with open(os.path.join(context_dir, "call_paths.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
