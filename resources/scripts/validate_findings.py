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
    keywords = ctx.get("keywords", [])
    acceptance_criteria = ctx.get("acceptance_criteria", [])
else:
    issue_title = ""
    keywords = []
    acceptance_criteria = []

tests_path = os.path.join(context_dir, "tests.json")
if os.path.exists(tests_path):
    with open(tests_path) as f:
        tests = json.load(f)
    proposed_new_tests = tests.get("proposed_new_tests", [])
    proposed_modifications = tests.get("proposed_modifications", [])
else:
    proposed_new_tests = []
    proposed_modifications = []

call_paths_path = os.path.join(context_dir, "call_paths.json")
if os.path.exists(call_paths_path):
    with open(call_paths_path) as f:
        cp_data = json.load(f)
    call_paths = cp_data.get("call_paths", [])
else:
    call_paths = []

# --- Helper: Parse behavioral claim into structured intent ---
def parse_behavioral_claim(claim):
    """Parse a behavioral claim into action + target for verification."""
    claim_lower = claim.lower()
    patterns = [
        (r'handles?\s+(\w+)', 'handles'),
        (r'returns?\s+(\w+)', 'returns'),
        (r'throws?\s+(\w+)', 'throws'),
        (r'catches?\s+(\w+)', 'catches'),
        (r'makes?\s+(\w+)\s+request', 'makes_request'),
        (r'sends?\s+(\w+)', 'sends'),
        (r'calls?\s+(\w+)', 'calls'),
        (r'performs?\s+(\w+)', 'performs'),
        (r'implements?\s+(\w+)', 'implements'),
        (r'validates?\s+(\w+)', 'validates'),
        (r'processes?\s+(\w+)', 'processes'),
        (r'async', 'is_async'),
    ]
    for pattern, action in patterns:
        m = re.search(pattern, claim_lower)
        if m:
            target = m.group(1) if m.lastindex else ""
            return {"action": action, "target": target}
    return {"action": "unknown", "target": claim_lower[:50]}

# --- Helper: Verify behavioral claim against source code ---
def verify_behavioral_claim(filepath, symbol, claim, repo):
    """Verify that source code supports a behavioral claim."""
    full = os.path.join(repo, filepath)
    try:
        content = open(full, 'r', errors='ignore').read()
    except:
        return {"verified": False, "reason": "File not readable", "status": "unknown"}

    # Extract symbol body
    sym_body = ""
    for m in re.finditer(rf'(?:function|class|def|func|fn)\s+{re.escape(symbol)}\s*[\(:]?\s*\n([\s\S]{{0,3000}}?)(?=\nclass|\ndef|\nfunc|\nfn|\nexport|\nmodule|\Z)', content, re.MULTILINE):
        sym_body = m.group(1)
        break

    if not sym_body:
        # Try to find symbol by reference
        if re.search(rf'\b{re.escape(symbol)}\b', content):
            return {"verified": True, "reason": "Symbol exists in code (body not extracted for verification)", "status": "inferred"}
        return {"verified": False, "reason": "Symbol not found", "status": "unknown"}

    parsed = parse_behavioral_claim(claim)
    action = parsed["action"]
    target = parsed["target"]

    # Verify based on action type
    if action == "handles":
        if any(x in sym_body for x in ['try', 'catch', 'throw', 'Error', 'Exception', 'reject']):
            return {"verified": True, "reason": f"Symbol contains error handling (try/catch/throw)", "status": "verified"}
        return {"verified": False, "reason": "Claim says 'handles' but no error handling found in symbol body", "status": "contradicted"}

    if action == "returns":
        if 'return' in sym_body:
            return {"verified": True, "reason": "Symbol contains return statements", "status": "verified"}
        return {"verified": False, "reason": "Claim says 'returns' but no return statement found", "status": "contradicted"}

    if action == "throws":
        if 'throw' in sym_body or 'raise' in sym_body:
            return {"verified": True, "reason": "Symbol contains throw/raise statements", "status": "verified"}
        return {"verified": False, "reason": "Claim says 'throws' but no throw/raise found", "status": "contradicted"}

    if action == "catches":
        if 'catch' in sym_body or 'except' in sym_body:
            return {"verified": True, "reason": "Symbol contains catch/except blocks", "status": "verified"}
        return {"verified": False, "reason": "Claim says 'catches' but no catch/except found", "status": "contradicted"}

    if action == "is_async":
        if 'async' in sym_body or 'await' in sym_body:
            return {"verified": True, "reason": "Symbol uses async/await", "status": "verified"}
        return {"verified": False, "reason": "Claim says 'async' but no async/await found", "status": "contradicted"}

    if action == "makes_request":
        if any(x in sym_body for x in ['fetch', 'request', 'http', 'axios', 'got']):
            return {"verified": True, "reason": "Symbol makes HTTP requests", "status": "verified"}
        return {"verified": False, "reason": "Claim says 'makes request' but no HTTP call found", "status": "contradicted"}

    if action == "calls":
        if f'{target}(' in sym_body or f'.{target}(' in sym_body:
            return {"verified": True, "reason": f"Symbol calls {target}", "status": "verified"}
        return {"verified": False, "reason": f"Claim says 'calls {target}' but not found in body", "status": "inferred"}

    # Generic: if claim mentions keywords that appear in body, consider it supported
    claim_words = [w for w in claim.lower().split() if len(w) > 3]
    body_lower = sym_body.lower()
    matches = sum(1 for w in claim_words if w in body_lower)
    if matches >= len(claim_words) * 0.5:
        return {"verified": True, "reason": f"Claim keywords found in symbol body ({matches}/{len(claim_words)})", "status": "verified"}

    return {"verified": False, "reason": "Could not verify claim against source code", "status": "inferred"}

# --- Helper: Verify relationship claim ---
def verify_relationship(caller_file, caller_symbol, callee_symbol, repo):
    """Verify that caller actually invokes callee."""
    full = os.path.join(repo, caller_file)
    try:
        content = open(full, 'r', errors='ignore').read()
    except:
        return {"verified": False, "reason": "File not readable", "status": "unknown"}

    # Find caller's function definition and extract body
    # Try multiple patterns to handle different code styles
    patterns = [
        # Pattern 1: function with body on next lines
        rf'(?:export\s+)?(?:async\s+)?function\s+{re.escape(caller_symbol)}\s*\([^)]*\)\s*\{{([\s\S]{{0,3000}}?)\}}\s*(?:\n|$)',
        # Pattern 2: const arrow function
        rf'(?:export\s+)?const\s+{re.escape(caller_symbol)}\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{{([\s\S]{{0,3000}}?)\}}\s*(?:;|\n|$)',
        # Pattern 3: const arrow function with body
        rf'(?:export\s+)?const\s+{re.escape(caller_symbol)}\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*([\s\S]{{0,1000}}?)(?=\n(?:export|const|function|class|\Z))',
        # Pattern 4: Simple function search
        rf'(?:function|class|def|func|fn)\s+{re.escape(caller_symbol)}\s*[\(:]?\s*\n([\s\S]{{0,2000}}?)(?=\nclass|\ndef|\nfunc|\nfn|\nexport|\nmodule|\Z)',
    ]
    
    for pattern in patterns:
        for m in re.finditer(pattern, content, re.MULTILINE):
            body = m.group(1)
            # Check if callee is called in the body
            if f'{callee_symbol}(' in body or f'.{callee_symbol}(' in body:
                return {"verified": True, "reason": f"{caller_symbol} calls {callee_symbol} in its body", "status": "verified"}
            break
    
    # Also check if the callee is imported and used anywhere in the file
    if re.search(rf'import\s+.*{re.escape(callee_symbol)}', content):
        # Check if callee is used in the file (not just imported)
        if re.search(rf'\b{re.escape(callee_symbol)}\s*\(', content):
            return {"verified": True, "reason": f"{caller_file} imports and uses {callee_symbol}", "status": "verified"}
    
    # Check for method calls like obj.callee()
    if re.search(rf'\.\s*{re.escape(callee_symbol)}\s*\(', content):
        return {"verified": True, "reason": f"{caller_file} calls {callee_symbol} as a method", "status": "verified"}
    
    return {"verified": False, "reason": f"Could not verify {caller_symbol} calls {callee_symbol}", "status": "inferred"}

# --- Per-change validation ---
per_change_validation = []
for change in changes:
    filepath = change.get("file", "")
    symbol = change.get("symbol", "")
    current_behavior = change.get("current_behavior", "")
    required_behavior = change.get("required_behavior", "")
    evidence = change.get("evidence", [])
    dependencies = change.get("dependencies", [])
    depended_by = change.get("depended_by", [])

    validation = {
        "file": filepath,
        "symbol": symbol,
        "checks": []
    }

    # 1. Repository facts: file exists
    file_exists = False
    if filepath and filepath != "(to be determined)":
        file_exists = os.path.exists(os.path.join(repo, filepath))
    validation["checks"].append({
        "type": "file_exists",
        "verified": file_exists,
        "status": "verified" if file_exists else "contradicted",
        "evidence": f"File {'found' if file_exists else 'not found'} at {filepath}"
    })

    # 2. Repository facts: symbol exists
    symbol_exists = False
    if file_exists and symbol and symbol != "(to be determined)":
        try:
            content = open(os.path.join(repo, filepath), 'r', errors='ignore').read()
            pattern = re.compile(rf'(?:class|function|def|func|fn|interface|type|const|let|var)\s+{re.escape(symbol)}\b')
            symbol_exists = bool(pattern.search(content)) or bool(re.search(rf'\b{re.escape(symbol)}\b', content))
        except:
            pass
    validation["checks"].append({
        "type": "symbol_exists",
        "verified": symbol_exists,
        "status": "verified" if symbol_exists else ("unknown" if not file_exists else "contradicted"),
        "evidence": f"Symbol {'found' if symbol_exists else 'not found'} in {filepath}"
    })

    # 3. Behavioral claim verification
    if current_behavior and file_exists and symbol_exists:
        claim_result = verify_behavioral_claim(filepath, symbol, current_behavior, repo)
        validation["checks"].append({
            "type": "behavioral_claim",
            "claim": current_behavior,
            "verified": claim_result["verified"],
            "status": claim_result["status"],
            "evidence": claim_result["reason"]
        })

    # 4. Relationship verification
    for dep in dependencies[:3]:
        dep_file = dep.get("file", "")
        dep_symbol = dep.get("symbol", "")
        if dep_file and dep_symbol and os.path.exists(os.path.join(repo, dep_file)):
            rel_result = verify_relationship(filepath, symbol, dep_symbol, repo)
            validation["checks"].append({
                "type": "relationship",
                "claim": f"{symbol} calls {dep_symbol}",
                "verified": rel_result["verified"],
                "status": rel_result["status"],
                "evidence": rel_result["reason"]
            })

    # 5. Change recommendation follows from evidence
    has_evidence = len(evidence) > 0
    evidence_matches_keywords = False
    if has_evidence:
        evidence_text = " ".join(e.get("text", "") for e in evidence).lower()
        evidence_matches_keywords = any(kw in evidence_text for kw in keywords if len(kw) > 2)
    validation["checks"].append({
        "type": "change_recommendation",
        "verified": has_evidence and evidence_matches_keywords,
        "status": "verified" if (has_evidence and evidence_matches_keywords) else "inferred",
        "evidence": f"Evidence {'supports' if evidence_matches_keywords else 'partially supports'} change recommendation"
    })

    # Compute per-change validation status
    verified_count = sum(1 for c in validation["checks"] if c["status"] == "verified")
    contradicted_count = sum(1 for c in validation["checks"] if c["status"] == "contradicted")
    total_checks = len(validation["checks"])

    if contradicted_count > 0:
        validation["overall_status"] = "contradicted"
    elif verified_count == total_checks:
        validation["overall_status"] = "fully_verified"
    elif verified_count > 0:
        validation["overall_status"] = "partially_verified"
    else:
        validation["overall_status"] = "unverified"

    validation["verified_count"] = verified_count
    validation["contradicted_count"] = contradicted_count
    validation["total_checks"] = total_checks

    per_change_validation.append(validation)

# --- Test validation ---
test_validation = []
for rec in proposed_new_tests:
    test_file = rec.get("proposed_test_file", "")
    dir_exists = rec.get("test_directory_exists", False)
    test_validation.append({
        "type": "proposed_new_test",
        "file": test_file,
        "directory_exists": dir_exists,
        "status": "verified" if dir_exists else "unverified",
        "evidence": f"Test directory {'exists' if dir_exists else 'does not exist'}"
    })
for mod in proposed_modifications:
    test_file = mod.get("file", "")
    file_exists = os.path.exists(os.path.join(repo, test_file))
    test_validation.append({
        "type": "proposed_modification",
        "file": test_file,
        "file_exists": file_exists,
        "status": "verified" if file_exists else "contradicted",
        "evidence": f"Test file {'exists' if file_exists else 'does not exist'}"
    })

# --- Aggregate scores ---
all_checks = []
for cv in per_change_validation:
    all_checks.extend(cv["checks"])
all_checks.extend(test_validation)

verified_total = sum(1 for c in all_checks if c["status"] == "verified")
contradicted_total = sum(1 for c in all_checks if c["status"] == "contradicted")
inferred_total = sum(1 for c in all_checks if c["status"] == "inferred")
unknown_total = sum(1 for c in all_checks if c["status"] == "unknown")
total_checks = len(all_checks)

# Compute granular confidence
repository_fact_score = 0
behavioral_claim_score = 0
relationship_score = 0
test_score = 0

repo_checks = [c for c in all_checks if c["type"] in ("file_exists", "symbol_exists")]
if repo_checks:
    repository_fact_score = round(sum(1 for c in repo_checks if c["verified"]) / len(repo_checks) * 100, 1)

behavior_checks = [c for c in all_checks if c["type"] == "behavioral_claim"]
if behavior_checks:
    behavioral_claim_score = round(sum(1 for c in behavior_checks if c["verified"]) / len(behavior_checks) * 100, 1)

rel_checks = [c for c in all_checks if c["type"] == "relationship"]
if rel_checks:
    relationship_score = round(sum(1 for c in rel_checks if c["verified"]) / len(rel_checks) * 100, 1)

test_checks = [c for c in all_checks if c["type"] in ("proposed_new_test", "proposed_modification")]
if test_checks:
    test_score = round(sum(1 for c in test_checks if c["status"] == "verified") / len(test_checks) * 100, 1)

# Overall validation score
if total_checks > 0:
    validation_score = round((verified_total / total_checks) * 100, 1)
else:
    validation_score = 100.0

# --- Confidence model per finding type ---
confidence_model = {
    "symbol_existence": {
        "level": "HIGH" if repository_fact_score >= 90 else ("MEDIUM" if repository_fact_score >= 50 else "LOW"),
        "reason": f"{repository_fact_score}% of files/symbols verified on disk",
        "score": repository_fact_score
    },
    "behavioral_claims": {
        "level": "HIGH" if behavioral_claim_score >= 80 else ("MEDIUM" if behavioral_claim_score >= 50 else "LOW"),
        "reason": f"{behavioral_claim_score}% of behavioral claims verified against source",
        "score": behavioral_claim_score
    },
    "relationships": {
        "level": "HIGH" if relationship_score >= 80 else ("MEDIUM" if relationship_score >= 50 else "LOW"),
        "reason": f"{relationship_score}% of caller/callee relationships verified",
        "score": relationship_score
    },
    "test_recommendations": {
        "level": "HIGH" if test_score >= 80 else ("MEDIUM" if test_score >= 50 else "LOW"),
        "reason": f"{test_score}% of test locations verified to exist",
        "score": test_score
    }
}

result = {
    "per_change_validation": per_change_validation[:15],
    "test_validation": test_validation[:10],
    "validation_score": validation_score,
    "verified_count": verified_total,
    "contradicted_count": contradicted_total,
    "inferred_count": inferred_total,
    "unknown_count": unknown_total,
    "total_checks": total_checks,
    "repository_fact_score": repository_fact_score,
    "behavioral_claim_score": behavioral_claim_score,
    "relationship_score": relationship_score,
    "test_score": test_score,
    "confidence_model": confidence_model
}

with open(os.path.join(context_dir, "validation.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
