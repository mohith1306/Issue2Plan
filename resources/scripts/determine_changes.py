import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")

context_path = os.path.join(context_dir, "issue_context.json")
if os.path.exists(context_path):
    with open(context_path) as f:
        ctx = json.load(f)
    keywords = ctx.get("keywords", [])
    issue_title = ctx.get("issue_title", "")
    issue_body = ctx.get("issue_body", "")
else:
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_body = os.environ.get("ISSUE_BODY", "")
    keywords_str = os.environ.get("KEYWORDS", "")
    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]

relevant_files_path = os.path.join(context_dir, "relevant_files.json")
if os.path.exists(relevant_files_path):
    with open(relevant_files_path) as f:
        rf = json.load(f)
    relevant_files = [item["path"] for item in rf.get("files", [])]
else:
    files_str = os.environ.get("RELEVANT_FILES", "")
    relevant_files = [f.strip() for f in files_str.split(",") if f.strip()]

changes = []

for filepath in relevant_files[:20]:
    full = os.path.join(repo, filepath)
    try:
        content = open(full, 'r', errors='ignore').read()
    except:
        continue

    symbols = []
    for m in re.finditer(r'(?:export\s+(?:default\s+)?(?:class|function|const|let|var|interface|type|enum)\s+(\w+))', content):
        symbols.append(m.group(1))
    for m in re.finditer(r'(?:class|function|def|func|fn)\s+(\w+)', content):
        name = m.group(1)
        if name not in symbols:
            symbols.append(name)

    for symbol in symbols[:10]:
        symbol_lower = symbol.lower()
        relevance = 0
        reasons = []
        for kw in keywords:
            if kw in symbol_lower:
                relevance += 10
                reasons.append(f"symbol name contains '{kw}'")

        try:
            symbol_pattern = re.compile(rf'(?:class|function|def|func|fn)\s+{re.escape(symbol)}\s*[\(:]?\s*\n([\s\S]{{0,2000}}?)(?=\nclass|\ndef|\nfunc|\nfn|\nexport|\nmodule|\Z)', re.MULTILINE)
            sm = symbol_pattern.search(content)
            if sm:
                body = sm.group(1)
                for kw in keywords:
                    if kw in body.lower():
                        relevance += 3
                        reasons.append(f"body references '{kw}'")
        except:
            pass

        try:
            symbol_lines = content.split('\n')
            for i, line in enumerate(symbol_lines):
                if symbol in line:
                    context_start = max(0, i - 3)
                    context_end = min(len(symbol_lines), i + 15)
                    nearby = ' '.join(symbol_lines[context_start:context_end])
                    for kw in keywords:
                        if kw in nearby.lower() and kw not in symbol_lower:
                            relevance += 5
                            reasons.append(f"nearby code references '{kw}'")
                    if 'TODO' in nearby or 'FIXME' in nearby or 'HACK' in nearby:
                        for kw in keywords:
                            if kw in nearby.lower():
                                relevance += 8
                                reasons.append(f"TODO/FIXME mentions '{kw}'")
                    break
        except:
            pass

        if relevance > 0:
            line_num = 0
            for i, line in enumerate(content.split('\n'), 1):
                if symbol in line:
                    line_num = i
                    break

            current_behavior = "Component exists in current codebase"
            try:
                symbol_lines = content.split('\n')
                for i, line in enumerate(symbol_lines):
                    if symbol in line and (i + 5) < len(symbol_lines):
                        body_text = ' '.join(symbol_lines[i:i+10])
                        if 'error' in body_text.lower() or 'throw' in body_text.lower() or 'catch' in body_text.lower():
                            current_behavior = "Handles errors in current implementation"
                        if 'return' in body_text.lower():
                            current_behavior = "Returns result from current implementation"
                        if 'async' in body_text.lower() or 'await' in body_text.lower():
                            current_behavior = "Async operation in current implementation"
                        break
            except:
                pass

            changes.append({
                "file": filepath,
                "symbol": symbol,
                "line": line_num,
                "current_behavior": current_behavior,
                "required_behavior": f"Modify to support: {issue_title}",
                "reason": "; ".join(reasons) if reasons else "Related to issue requirements",
                "confidence": "HIGH" if relevance >= 10 else "MEDIUM"
            })

if not changes:
    for kw in keywords[:3]:
        if len(kw) > 3:
            changes.append({
                "file": "(to be determined)",
                "symbol": "(to be determined)",
                "line": 0,
                "current_behavior": "No directly matching component found",
                "required_behavior": f"Implement {kw} functionality",
                "reason": f"Issue requires '{kw}' but no matching code found",
                "confidence": "LOW"
            })

changes.sort(key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x["confidence"], 3))

implementation_order = []
step = 1
for change in changes:
    if change["confidence"] == "HIGH":
        implementation_order.append({
            "step": step,
            "description": f"Modify `{change['symbol']}` in `{change['file']}` (line {change['line']})",
            "file": change["file"],
            "symbol": change["symbol"]
        })
        step += 1
for change in changes:
    if change["confidence"] == "MEDIUM" and change["file"] not in [o["file"] for o in implementation_order]:
        implementation_order.append({
            "step": step,
            "description": f"Review and modify `{change['symbol']}` in `{change['file']}`",
            "file": change["file"],
            "symbol": change["symbol"]
        })
        step += 1

implementation_order.append({
    "step": step,
    "description": "Validate all changes and run tests",
    "file": "N/A",
    "symbol": "N/A"
})

result = {
    "changes": changes[:15],
    "implementation_order": implementation_order[:15],
    "total_changes": len(changes)
}

with open(os.path.join(context_dir, "changes.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
