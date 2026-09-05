import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")

# Read all context files
context_path = os.path.join(context_dir, "issue_context.json")
if os.path.exists(context_path):
    with open(context_path) as f:
        ctx = json.load(f)
    keywords = ctx.get("keywords", [])
    issue_title = ctx.get("issue_title", "")
    issue_body = ctx.get("issue_body", "")
    problem = ctx.get("problem", "")
    expected_behavior = ctx.get("expected_behavior", "")
    domain_concepts = ctx.get("domain_concepts", [])
    technical_keywords = ctx.get("technical_keywords", [])
    acceptance_criteria = ctx.get("acceptance_criteria", [])
else:
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_body = os.environ.get("ISSUE_BODY", "")
    keywords = []
    problem = issue_title
    expected_behavior = ""
    domain_concepts = []
    technical_keywords = []
    acceptance_criteria = []

relevant_files_path = os.path.join(context_dir, "relevant_files.json")
if os.path.exists(relevant_files_path):
    with open(relevant_files_path) as f:
        rf = json.load(f)
    relevant_files = [item["path"] for item in rf.get("files", [])]
else:
    relevant_files = []

call_paths_path = os.path.join(context_dir, "call_paths.json")
if os.path.exists(call_paths_path):
    with open(call_paths_path) as f:
        cp = json.load(f)
    call_paths = cp.get("call_paths", [])
else:
    call_paths = []

patterns_path = os.path.join(context_dir, "patterns.json")
if os.path.exists(patterns_path):
    with open(patterns_path) as f:
        pt = json.load(f)
    patterns = pt.get("relevant_patterns", [])
else:
    patterns = []

tests_path = os.path.join(context_dir, "tests.json")
if os.path.exists(tests_path):
    with open(tests_path) as f:
        ts = json.load(f)
    relevant_test_files = ts.get("relevant_existing_tests", [])
    proposed_modifications = ts.get("proposed_modifications", [])
else:
    relevant_test_files = []
    proposed_modifications = []

# --- Helper: Generate specific required_behavior ---
def generate_required_behavior(symbol, filepath, content, keywords, problem, expected_behavior, call_paths, patterns):
    """Generate a specific required behavior referencing code patterns to follow."""
    lines = content.split('\n')
    sym_body = ""
    sym_line = 0
    for i, line in enumerate(lines):
        if symbol in line and re.search(rf'(?:function|class|def|func|fn|const|let|var)\s+{re.escape(symbol)}', line):
            sym_line = i
            for j in range(i, min(len(lines), i + 40)):
                sym_body += lines[j] + '\n'
                if j > i and re.match(r'^(?:export\s+)?(?:async\s+)?(?:function|class|def|func|fn)\s+\w+', lines[j]):
                    break
            break

    # Analyze what the function currently does
    does_error_handling = any(x in sym_body for x in ['throw', 'catch', 'Error', 'try'])
    does_return = 'return' in sym_body
    is_async = 'async' in sym_body
    does_fetch = any(x in sym_body for x in ['fetch', 'request', 'http'])
    does_send = any(x in sym_body for x in ['send', 'write', 'end'])

    # Find reusable patterns from the codebase
    reusable = []
    for p in patterns:
        for loc in p.get("locations", []):
            if loc.get("reusability") and "exported" in loc["reusability"]:
                reusable.append({
                    "name": p["existing_pattern"],
                    "file": loc["file"],
                    "line": loc["line"]
                })

    # Build specific behavior description
    behaviors = []
    for kw in keywords:
        if len(kw) <= 3:
            continue
        if kw in symbol.lower():
            if does_fetch and kw in ['retry', 'backoff', 'timeout']:
                behaviors.append(f"add {kw} handling around the fetch operation")
            elif does_send and kw in ['buffer', 'arraybuffer', 'binary']:
                behaviors.append(f"handle {kw} data in the send operation")
            elif does_error_handling and kw in ['error', 'exception', 'fail']:
                behaviors.append(f"improve {kw} handling")
            else:
                behaviors.append(f"implement {kw} logic")
        elif kw in sym_body.lower():
            if does_fetch and kw in ['retry', 'backoff', 'timeout']:
                behaviors.append(f"add {kw} support using existing fetch pattern")
            else:
                behaviors.append(f"handle '{kw}' in the function body")

    if not behaviors:
        if problem:
            behaviors.append(f"address: {problem[:80]}")
        else:
            behaviors.append(f"modify to support: {issue_title[:60]}")

    # Add reuse guidance
    if reusable:
        reuse_names = [r["name"] for r in reusable[:3]]
        behaviors.append(f"reuse existing utilities: {', '.join(reuse_names)}")

    return "; ".join(behaviors[:3])

# --- Helper: Generate why-this-location explanation ---
def generate_why_this_location(symbol, filepath, content, call_paths, keywords):
    """Explain why this symbol is the correct change point."""
    reasons = []

    # Check if it's a shared boundary (called by multiple callers)
    callers = []
    for cp_item in call_paths:
        if cp_item.get("entry_symbol") == symbol and cp_item.get("file") == filepath:
            callers = cp_item.get("callers", [])
            break
    if len(callers) > 1:
        reasons.append(f"Shared boundary: called by {len(callers)} functions ({', '.join(c['symbol'] for c in callers[:3])})")
    elif len(callers) == 1:
        reasons.append(f"Called by {callers[0]['symbol']} in {callers[0]['file']}")

    # Check for TODO/FIXME markers
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if symbol in line and ('TODO' in line or 'FIXME' in line):
            reasons.append(f"TODO/FIXME marker indicates planned work at this location")
            break
        # Check nearby lines
        for j in range(max(0, i-2), min(len(lines), i+3)):
            if 'TODO' in lines[j] or 'FIXME' in lines[j]:
                if any(kw in lines[j].lower() for kw in keywords if len(kw) > 2):
                    reasons.append(f"TODO/FIXME nearby mentions issue-related keywords")
                    break

    # Check if it handles errors (good insertion point for retry)
    sym_body = ""
    for m in re.finditer(rf'(?:function|class|def|func|fn)\s+{re.escape(symbol)}\s*[\(:]?\s*\n([\s\S]{{0,2000}}?)(?=\nclass|\ndef|\nfunc|\nfn|\nexport|\nmodule|\Z)', content, re.MULTILINE):
        sym_body = m.group(1)
        break
    if any(x in sym_body for x in ['throw', 'catch', 'Error']):
        reasons.append("Already has error handling — natural insertion point for retry logic")

    # Check if it's exported (public API)
    if re.search(rf'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+{re.escape(symbol)}', content):
        reasons.append("Public API surface — changes here affect all consumers")

    if not reasons:
        reasons.append(f"Symbol '{symbol}' is relevant to the issue requirements")

    return reasons

# --- Helper: Generate test guidance ---
def generate_test_guidance(symbol, filepath, acceptance_criteria, keywords, relevant_test_files):
    """Generate specific test cases needed for this change."""
    test_cases = []

    # From acceptance criteria
    for ac in acceptance_criteria[:3]:
        test_cases.append(f"Verify: {ac[:80]}")

    # From keywords
    for kw in keywords[:3]:
        if len(kw) > 3 and kw not in ['add', 'create', 'update', 'remove', 'fix']:
            test_cases.append(f"Test '{kw}' handling")

    # General test scenarios
    test_cases.append("Test successful path unchanged")
    test_cases.append("Test error handling path")

    return test_cases[:5]

# --- Main change determination ---
changes = []

for filepath in relevant_files[:20]:
    full = os.path.join(repo, filepath)
    try:
        content = open(full, 'r', errors='ignore').read()
    except:
        continue

    lines = content.split('\n')

    # Extract symbols
    symbols = []
    for m in re.finditer(r'(?:export\s+(?:default\s+)?(?:class|function|const|let|var|interface|type|enum)\s+(\w+))', content):
        symbols.append(m.group(1))
    for m in re.finditer(r'(?:class|function|def|func|fn)\s+(\w+)', content):
        name = m.group(1)
        if name not in symbols:
            symbols.append(name)

    for symbol in symbols[:10]:
        relevance = 0
        reasons = []
        evidence = []

        # Check symbol name against keywords
        symbol_lower = symbol.lower()
        for kw in keywords:
            if len(kw) > 2 and kw in symbol_lower:
                relevance += 10
                reasons.append(f"symbol name contains '{kw}'")

        # Check symbol body against keywords
        sym_body = ""
        sym_line = 0
        for i, line in enumerate(lines):
            if symbol in line and re.search(rf'(?:function|class|def|func|fn|const|let|var)\s+{re.escape(symbol)}', line):
                sym_line = i
                for j in range(i, min(len(lines), i + 40)):
                    sym_body += lines[j] + '\n'
                    if j > i and re.match(r'^(?:export\s+)?(?:async\s+)?(?:function|class|def|func|fn)\s+\w+', lines[j]):
                        break
                break

        for kw in keywords:
            if len(kw) > 2 and kw in sym_body.lower():
                relevance += 3
                reasons.append(f"body references '{kw}'")

        # Check nearby code
        nearby_start = max(0, sym_line - 5)
        nearby_end = min(len(lines), sym_line + 40)
        nearby_text = '\n'.join(lines[nearby_start:nearby_end])
        for kw in keywords:
            if len(kw) > 2 and kw in nearby_text.lower() and kw not in symbol_lower:
                relevance += 5
                reasons.append(f"nearby code references '{kw}'")
                for i in range(nearby_start, nearby_end):
                    if kw in lines[i].lower():
                        evidence.append({"line": i + 1, "text": lines[i].strip()[:120], "keyword": kw})
                        break

        # Check TODO/FIXME
        for i in range(nearby_start, nearby_end):
            if i < len(lines) and ('TODO' in lines[i] or 'FIXME' in lines[i]):
                for kw in keywords:
                    if len(kw) > 2 and kw in lines[i].lower():
                        relevance += 8
                        reasons.append(f"TODO/FIXME mentions '{kw}'")
                        evidence.append({"line": i + 1, "text": lines[i].strip()[:120], "keyword": kw})
                        break

        if relevance > 0:
            # Determine confidence with reasoning
            has_file_evidence = any(e["keyword"] in sym_body.lower() for e in evidence)
            has_nearby_evidence = any(e["keyword"] not in symbol_lower for e in evidence)
            has_todo = any('TODO' in e.get("text", "") or 'FIXME' in e.get("text", "") for e in evidence)

            if relevance >= 15 and (has_todo or (has_file_evidence and has_nearby_evidence)):
                confidence = "HIGH"
                confidence_reason = "Strong evidence: TODO marker + multiple keyword matches in code"
            elif relevance >= 8 and has_file_evidence:
                confidence = "MEDIUM"
                confidence_reason = "Moderate evidence: keywords found in symbol body"
            else:
                confidence = "LOW"
                confidence_reason = "Limited evidence: based on issue text similarity"

            # Current behavior
            current_behavior = "Component exists in current codebase"
            if 'throw' in sym_body or 'Error' in sym_body:
                current_behavior = "Handles errors and may throw on failure"
            if 'return' in sym_body:
                current_behavior += "; returns results"
            if 'async' in sym_body:
                current_behavior = "Async operation that returns a Promise"
            if 'fetch' in sym_body or 'request' in sym_body:
                current_behavior = "Makes HTTP requests"
            if 'send' in sym_body:
                current_behavior = "Sends data in current implementation"

            # Required behavior
            required_behavior = generate_required_behavior(symbol, filepath, content, keywords, problem, expected_behavior, call_paths, patterns)

            # Why this location
            why_this_location = generate_why_this_location(symbol, filepath, content, call_paths, keywords)

            # Dependencies
            dependencies = []
            depended_by = []
            for cp_item in call_paths:
                if cp_item.get("entry_symbol") == symbol and cp_item.get("file") == filepath:
                    for callee in cp_item.get("called_symbols", []):
                        dependencies.append({
                            "symbol": callee["symbol"],
                            "file": callee["file"],
                            "relationship": callee["relationship"]
                        })
                elif cp_item.get("file") != filepath:
                    for callee in cp_item.get("called_symbols", []):
                        if callee.get("symbol") == symbol:
                            depended_by.append({
                                "symbol": cp_item["entry_symbol"],
                                "file": cp_item["file"]
                            })

            # Reuse guidance
            reuse = []
            for p in patterns:
                for loc in p.get("locations", []):
                    if loc.get("reusability") and "exported" in loc["reusability"]:
                        reuse.append(f"{p['existing_pattern']} ({loc['file']}:{loc['line']})")

            # Affected callers with breakage risk
            affected_callers = []
            for caller in depended_by:
                breakage_risk = "LOW"  # default
                # If caller has error handling, risk is lower
                try:
                    caller_content = open(os.path.join(repo, caller["file"]), 'r', errors='ignore').read()
                    for m in re.finditer(rf'(?:function|class|def|func|fn)\s+{re.escape(caller["symbol"])}\s*[\(:]?\s*\n([\s\S]{{0,1000}}?)(?=\nclass|\ndef|\nfunc|\nfn|\nexport|\nmodule|\Z)', caller_content, re.MULTILINE):
                        caller_body = m.group(1)
                        if any(x in caller_body for x in ['try', 'catch', '.catch']):
                            breakage_risk = "LOW"
                        else:
                            breakage_risk = "MEDIUM"
                        break
                except:
                    pass
                affected_callers.append({
                    "symbol": caller["symbol"],
                    "file": caller["file"],
                    "breakage_risk": breakage_risk
                })

            # Test guidance
            test_guidance = generate_test_guidance(symbol, filepath, acceptance_criteria, keywords, relevant_test_files)

            # Risks
            risks = []
            if depended_by:
                risks.append(f"Affects {len(depended_by)} downstream caller(s)")
            if not any(x in sym_body for x in ['try', 'catch']):
                risks.append("No existing error handling — must add carefully")
            if 'async' in sym_body:
                risks.append("Async operation — ensure retry timing is correct")
            if not risks:
                risks.append("Standard modification with low risk")

            changes.append({
                "file": filepath,
                "symbol": symbol,
                "line": sym_line + 1,
                "current_behavior": current_behavior,
                "required_behavior": required_behavior,
                "why_this_location": why_this_location,
                "reuse": reuse[:3],
                "affected_callers": affected_callers[:5],
                "evidence": evidence[:5],
                "test_guidance": test_guidance,
                "risks": risks,
                "reason": "; ".join(reasons) if reasons else "Related to issue requirements",
                "confidence": {
                    "level": confidence,
                    "reason": confidence_reason,
                    "score": round(min(1.0, relevance / 20), 2)
                }
            })

# Sort by confidence
confidence_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
changes.sort(key=lambda x: confidence_order.get(x["confidence"]["level"], 3))

# Generate implementation order based on dependencies
implementation_order = []
step = 1

# First: changes with no dependents (leaf nodes) and HIGH confidence
for change in changes:
    if change["confidence"]["level"] == "HIGH" and not change.get("affected_callers"):
        implementation_order.append({
            "step": step,
            "description": f"Modify `{change['symbol']}` in `{change['file']}` (line {change['line']})",
            "details": change["required_behavior"],
            "file": change["file"],
            "symbol": change["symbol"],
            "type": "implementation"
        })
        step += 1

# Then: HIGH confidence changes with dependents
for change in changes:
    if change["confidence"]["level"] == "HIGH" and change.get("affected_callers"):
        already_listed = any(o["file"] == change["file"] and o["symbol"] == change["symbol"] for o in implementation_order)
        if not already_listed:
            implementation_order.append({
                "step": step,
                "description": f"Modify `{change['symbol']}` in `{change['file']}` (line {change['line']})",
                "details": change["required_behavior"],
                "file": change["file"],
                "symbol": change["symbol"],
                "type": "implementation"
            })
            step += 1

# Then: MEDIUM confidence
for change in changes:
    if change["confidence"]["level"] == "MEDIUM":
        already_listed = any(o["file"] == change["file"] and o["symbol"] == change["symbol"] for o in implementation_order)
        if not already_listed:
            implementation_order.append({
                "step": step,
                "description": f"Review and modify `{change['symbol']}` in `{change['file']}`",
                "details": change["required_behavior"],
                "file": change["file"],
                "symbol": change["symbol"],
                "type": "review"
            })
            step += 1

# Add testing steps
if relevant_test_files:
    for rtf in relevant_test_files[:1]:
        implementation_order.append({
            "step": step,
            "description": f"Extend existing tests in `{rtf['file']}`",
            "details": "Add test cases for new behavior",
            "file": rtf["file"],
            "symbol": "N/A",
            "type": "testing"
        })
        step += 1

implementation_order.append({
    "step": step,
    "description": "Run the repository's existing test suite to verify no regressions",
    "details": "Ensure all existing tests still pass",
    "file": "N/A",
    "symbol": "N/A",
    "type": "validation"
})

result = {
    "changes": changes[:15],
    "implementation_order": implementation_order[:15],
    "total_changes": len(changes)
}

with open(os.path.join(context_dir, "changes.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
