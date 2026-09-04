import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")

relevant_files_path = os.path.join(context_dir, "relevant_files.json")
if os.path.exists(relevant_files_path):
    with open(relevant_files_path) as f:
        rf = json.load(f)
    files_to_trace = [item["path"] for item in rf.get("files", [])]
else:
    files_str = os.environ.get("RELEVANT_FILES", "")
    files_to_trace = [f.strip() for f in files_str.split(",") if f.strip()]

call_paths = []
symbol_map = {}
file_contents = {}

for filepath in files_to_trace[:20]:
    full = os.path.join(repo, filepath)
    try:
        content = open(full, 'r', errors='ignore').read()
        file_contents[filepath] = content
        symbols = []
        for m in re.finditer(r'(?:export\s+(?:default\s+)?(?:class|function|const|let|var|interface|type|enum)\s+(\w+))', content):
            symbols.append(m.group(1))
        for m in re.finditer(r'(?:class|function|def|func|fn)\s+(\w+)', content):
            name = m.group(1)
            if name not in symbols:
                symbols.append(name)
        symbol_map[filepath] = symbols
    except:
        pass

for filepath, symbols in symbol_map.items():
    content = file_contents.get(filepath, "")
    for symbol in symbols:
        callers = []
        error_handling = []
        exports = []

        for other_file, other_content in file_contents.items():
            if other_file == filepath:
                continue
            import_pattern = re.compile(rf'import\s+.*?{re.escape(symbol)}\s+from\s+')
            if import_pattern.search(other_content):
                callers.append({"file": other_file, "type": "import"})
            if symbol in other_content and other_file != filepath:
                if not any(c["file"] == other_file for c in callers):
                    callers.append({"file": other_file, "type": "reference"})

        try:
            symbol_pattern = re.compile(rf'(?:class|function|def|func|fn)\s+{re.escape(symbol)}\s*[\(:]?\s*\n([\s\S]{{0,3000}}?)(?=\nclass|\ndef|\nfunc|\nfn|\nexport|\nmodule|\Z)', re.MULTILINE)
            sm = symbol_pattern.search(content)
            if sm:
                body = sm.group(1)
                for m in re.finditer(r'(throw|raise|Error|Exception|catch|try|if\s+.*error|if\s+.*err)', body):
                    error_handling.append(m.group(0))
        except:
            pass

        export_pattern = re.compile(rf'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+{re.escape(symbol)}')
        if export_pattern.search(content):
            exports.append(f"exported from {filepath}")

        call_paths.append({
            "file": filepath,
            "symbol": symbol,
            "callers": callers[:5],
            "error_handling": error_handling[:3],
            "exports": exports
        })

result = {
    "call_paths": call_paths[:50],
    "files_traced": len(files_to_trace),
    "symbols_found": sum(len(s) for s in symbol_map.values())
}

with open(os.path.join(context_dir, "call_paths.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
