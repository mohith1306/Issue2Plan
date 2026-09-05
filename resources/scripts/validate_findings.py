import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")

# Read all context files
changes_path = os.path.join(context_dir, "changes.json")
if os.path.exists(changes_path):
    with open(changes_path) as f:
        ch = json.load(f)
    changes = ch.get("changes", [])
else:
    changes = []

context_path = os.path.join(context_dir, "issue_context.json")
if os.path.exists(context_path):
    with open(context_path) as f:
        ctx = json.load(f)
    issue_title = ctx.get("issue_title", "")
    issue_body = ctx.get("issue_body", "")
    keywords = ctx.get("keywords", [])
    problem = ctx.get("problem", "")
    acceptance_criteria = ctx.get("acceptance_criteria", [])
else:
    issue_title = ""
    issue_body = ""
    keywords = []
    problem = ""
    acceptance_criteria = []

tests_path = os.path.join(context_dir, "tests.json")
if os.path.exists(tests_path):
    with open(tests_path) as f:
        tests = json.load(f)
    recommended_tests = tests.get("recommended_tests", [])
    relevant_test_files = tests.get("relevant_test_files", [])
else:
    recommended_tests = []
    relevant_test_files = []

# Validation results
files_verified = []
files_missing = []
symbols_verified = []
symbols_missing = []
source_claims = []
change_relevance = []
test_location_validation = []
assumptions = []

# 1. Verify files exist
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

# 2. Verify symbols exist
for change in changes:
    filepath = change.get("file", "")
    symbol = change.get("symbol", "")

    if symbol and symbol != "(to be determined)" and filepath and filepath != "(to be determined)":
        full = os.path.join(repo, filepath)
        try:
            content = open(full, 'r', errors='ignore').read()
            # Check for definition
            pattern = re.compile(rf'(?:class|function|def|func|fn|interface|type|const|let|var)\s+{re.escape(symbol)}\b')
            if pattern.search(content):
                symbols_verified.append({"symbol": symbol, "file": filepath, "status": "found"})
            elif re.search(rf'\b{re.escape(symbol)}\b', content):
                symbols_verified.append({"symbol": symbol, "file": filepath, "status": "referenced"})
            else:
                symbols_missing.append({"symbol": symbol, "file": filepath, "status": "not found"})
        except:
            symbols_missing.append({"symbol": symbol, "file": filepath, "status": "unable to verify"})
    elif symbol == "(to be determined)":
        assumptions.append("Symbol name needs to be determined during implementation")

# 3. Verify source claims (do behavioral descriptions match reality?)
for change in changes:
    filepath = change.get("file", "")
    symbol = change.get("symbol", "")
    current_behavior = change.get("current_behavior", "")

    if filepath and symbol and filepath != "(to be determined)" and symbol != "(to be determined)":
        full = os.path.join(repo, filepath)
        try:
            content = open(full, 'r', errors='ignore').read()
            # Find the symbol's body
            sym_body = ""
            for m in re.finditer(rf'(?:function|class|def|func|fn)\s+{re.escape(symbol)}\s*[\(:]?\s*\n([\s\S]{{0,2000}}?)(?=\nclass|\ndef|\nfunc|\nfn|\nexport|\nmodule|\Z)', content, re.MULTILINE):
                sym_body = m.group(1)
                break

            claim_supported = True
            observation = ""

            if "handles errors" in current_behavior.lower():
                if 'throw' in sym_body or 'catch' in sym_body or 'Error' in sym_body or 'try' in sym_body:
                    observation = "Symbol contains error handling code (throw/catch/Error)"
                else:
                    claim_supported = False
                    observation = "Symbol does not appear to handle errors directly"

            if "returns result" in current_behavior.lower() or "returns results" in current_behavior.lower():
                if 'return' in sym_body:
                    observation = "Symbol contains return statements"
                else:
                    claim_supported = False
                    observation = "Symbol does not contain return statements"

            if "async" in current_behavior.lower():
                if 'async' in sym_body or 'await' in sym_body:
                    observation = "Symbol uses async/await pattern"
                else:
                    claim_supported = False
                    observation = "Symbol does not use async/await"

            if "http" in current_behavior.lower() or "fetch" in current_behavior.lower():
                if 'fetch' in sym_body or 'request' in sym_body or 'http' in sym_body:
                    observation = "Symbol makes HTTP requests"
                else:
                    claim_supported = False
                    observation = "Symbol does not make HTTP requests"

            if not observation:
                observation = "Symbol exists in codebase"

            source_claims.append({
                "file": filepath,
                "symbol": symbol,
                "claim": current_behavior,
                "supported": claim_supported,
                "observation": observation
            })
        except:
            source_claims.append({
                "file": filepath,
                "symbol": symbol,
                "claim": current_behavior,
                "supported": False,
                "observation": "Could not verify — file unreadable"
            })

# 4. Verify change relevance (do changes address the issue?)
for change in changes:
    filepath = change.get("file", "")
    symbol = change.get("symbol", "")
    required_behavior = change.get("required_behavior", "")
    evidence = change.get("evidence", [])

    relevance_score = 0
    relevance_reasons = []

    # Check if the change's evidence matches issue keywords
    for ev in evidence:
        kw = ev.get("keyword", "")
        if kw in keywords:
            relevance_score += 1
            relevance_reasons.append(f"Evidence keyword '{kw}' matches issue")

    # Check if the symbol name relates to the issue
    symbol_lower = symbol.lower()
    for kw in keywords:
        if len(kw) > 2 and kw in symbol_lower:
            relevance_score += 2
            relevance_reasons.append(f"Symbol name contains '{kw}'")

    # Check if the change file is in a relevant directory
    if filepath and filepath != "(to be determined)":
        for kw in keywords:
            if len(kw) > 2 and kw in filepath.lower():
                relevance_score += 1
                relevance_reasons.append(f"File path contains '{kw}'")

    is_relevant = relevance_score > 0
    change_relevance.append({
        "file": filepath,
        "symbol": symbol,
        "relevant": is_relevant,
        "score": relevance_score,
        "reasons": relevance_reasons[:5]
    })

# 5. Validate test locations
for rec in recommended_tests:
    test_file = rec.get("suggested_test_file", "")
    source_file = rec.get("source_file", "")

    # Check if the suggested test directory exists
    test_dir = os.path.dirname(test_file)
    full_test_dir = os.path.join(repo, test_dir)
    dir_exists = os.path.isdir(full_test_dir)

    # Check if there are existing tests in that directory
    existing_tests_in_dir = 0
    if dir_exists:
        try:
            for f in os.listdir(full_test_dir):
                if re.match(r'.*\.(test|spec)\.(ts|tsx|js|jsx|py)$', f):
                    existing_tests_in_dir += 1
        except:
            pass

    test_location_validation.append({
        "suggested_test_file": test_file,
        "source_file": source_file,
        "directory_exists": dir_exists,
        "existing_tests_in_dir": existing_tests_in_dir,
        "valid": dir_exists or existing_tests_in_dir > 0
    })

# Compute validation score
total_verified = len(files_verified) + len(symbols_verified)
total_missing = len(files_missing) + len(symbols_missing)
total_checks = total_verified + total_missing
file_symbol_score = (total_verified / total_checks * 100) if total_checks > 0 else 0

# Source claims score
claims_supported = sum(1 for c in source_claims if c["supported"])
claims_total = len(source_claims)
claims_score = (claims_supported / claims_total * 100) if claims_total > 0 else 100

# Change relevance score
relevant_changes = sum(1 for r in change_relevance if r["relevant"])
relevant_total = len(change_relevance)
relevance_score = (relevant_changes / relevant_total * 100) if relevant_total > 0 else 0

# Overall validation score
validation_score = round(
    (file_symbol_score * 0.4) + (claims_score * 0.3) + (relevance_score * 0.3),
    1
)

result = {
    "files_verified": files_verified[:20],
    "files_missing": files_missing[:10],
    "symbols_verified": symbols_verified[:20],
    "symbols_missing": symbols_missing[:10],
    "source_claims": source_claims[:15],
    "change_relevance": change_relevance[:15],
    "test_location_validation": test_location_validation[:10],
    "assumptions": assumptions[:10],
    "validation_score": validation_score,
    "file_symbol_score": round(file_symbol_score, 1),
    "claims_score": round(claims_score, 1),
    "relevance_score": round(relevance_score, 1),
    "total_checks": total_checks
}

with open(os.path.join(context_dir, "validation.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
