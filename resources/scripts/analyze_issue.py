import os, json, re, sys

issue_title = os.environ.get("ISSUE_TITLE", "")
issue_body = os.environ.get("ISSUE_BODY", "")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")
os.makedirs(context_dir, exist_ok=True)

text = f"{issue_title} {issue_body}".lower()
full_text = f"{issue_title} {issue_body}"

stop_words = {"the", "a", "an", "to", "for", "in", "on", "with", "from", "by", "as", "is", "was", "are", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their", "what", "which", "who", "whom", "where", "when", "why", "how", "all", "each", "every", "both", "few", "more", "most", "other", "some", "such", "no", "not", "only", "own", "same", "so", "than", "too", "very", "just", "because", "but", "and", "or", "if", "while", "of", "at", "between", "through", "during", "before", "after", "above", "below", "up", "down", "out", "about", "into", "over", "under", "again", "further", "then", "once", "also", "here", "there", "now", "new", "first", "last", "long", "great", "high", "small", "large"}

# --- Problem Statement ---
problem = ""
problem_patterns = [
    r'(?:bug|issue|problem|error|crash|fail|broken|incorrect|wrong|unexpected)\s+(?:when|in|with|on|during|at|for|of)\s+(.{10,120})',
    r'(?:res\.send|response\.send|send\()\s*\((\w+)\)\s+(?:results?\s+in|returns?|produces?|sends?)\s+(.{5,80})',
    r'(?:the\s+)?(\w+(?:\.\w+)*)\s+(?:crashes?|fails?|breaks?|errors?|returns?\s+(?:null|undefined|empty|wrong))\s+(?:when|if|during|with)\s+(.{10,120})',
]
for pattern in problem_patterns:
    m = re.search(pattern, text)
    if m:
        problem = m.group(0).strip().rstrip('.')
        break
if not problem:
    sentences = re.split(r'[.!?]+', full_text)
    for s in sentences:
        s = s.strip()
        if any(w in s.lower() for w in ['bug', 'issue', 'error', 'crash', 'fail', 'broken', 'incorrect', 'wrong', 'unexpected', 'problem']):
            problem = s
            break
if not problem:
    problem = issue_title

# --- Expected Behavior ---
expected_behavior = ""
expected_patterns = [
    r'(?:should|must|need to|expected to|supposed to)\s+(.{10,150})',
    r'(?:instead|rather than|rather)\s+(?:of\s+)?(.{10,120})',
    r'(?:so that|to allow|to enable|to support)\s+(.{10,120})',
]
for pattern in expected_patterns:
    m = re.search(pattern, text)
    if m:
        expected_behavior = m.group(0).strip().rstrip('.')
        break
if not expected_behavior:
    if issue_body:
        sentences = re.split(r'[.!?]+', issue_body)
        for s in sentences:
            s = s.strip()
            if any(w in s.lower() for w in ['should', 'must', 'expected', 'instead', 'rather', 'would like']):
                expected_behavior = s
                break
if not expected_behavior:
    expected_behavior = f"Implement the behavior described in: {issue_title}"

# --- Domain Concepts ---
domain_concepts = []
concept_patterns = [
    (r'\b(http|https|request|response|header|body|status|method|url|endpoint|api|route)\b', 'HTTP/Web'),
    (r'\b(res\.send|res\.json|res\.write|res\.end|response\.send)\b', 'Response Handling'),
    (r'\b(arraybuffer|buffer|uint8array|blob|stream|binary|typed array)\b', 'Binary Data'),
    (r'\b(json|serialize|deserialize|parse|stringify|encode|decode)\b', 'Serialization'),
    (r'\b(retry|backoff|timeout|delay|sleep|wait)\b', 'Retry/Resilience'),
    (r'\b(error|exception|throw|catch|try|reject|fail)\b', 'Error Handling'),
    (r'\b(auth|login|token|session|jwt|oauth|password|credential)\b', 'Authentication'),
    (r'\b(database|db|query|sql|orm|model|schema|migration)\b', 'Data Layer'),
    (r'\b(cache|redis|memcache|store|persist)\b', 'Storage'),
    (r'\b(log|logger|logging|debug|trace|info|warn|error)\b', 'Logging'),
    (r'\b(test|spec|mock|stub|fixture|assert|expect|describe|it)\b', 'Testing'),
    (r'\b(config|setting|env|environment|option|parameter)\b', 'Configuration'),
    (r'\b(middleware|plugin|extension|hook|interceptor)\b', 'Extensibility'),
    (r'\b(middleware|router|handler|controller|service)\b', 'Architecture'),
    (r'\b(type|interface|class|struct|enum|generics)\b', 'Type System'),
]
for pattern, concept in concept_patterns:
    if re.search(pattern, text):
        domain_concepts.append(concept)
domain_concepts = list(dict.fromkeys(domain_concepts))

# --- Technical Keywords ---
action_verbs = ["add", "implement", "create", "fix", "update", "remove", "refactor", "improve", "optimize", "support", "enable", "disable", "configure", "enhance"]
action_keywords = [v for v in action_verbs if v in text]

words = re.findall(r'\b[a-z]{3,}\b', text)
meaningful_words = [w for w in words if w not in stop_words]
word_freq = {}
for w in meaningful_words:
    word_freq[w] = word_freq.get(w, 0) + 1
frequent_words = sorted(word_freq.items(), key=lambda x: -x[1])
top_words = [w for w, c in frequent_words[:15]]

technical_keywords = list(dict.fromkeys(action_keywords + top_words))

# --- Likely Components ---
likely_components = []
component_hints = {
    'response': ['response handler', 'HTTP response', 'res.send'],
    'send': ['response handler', 'HTTP response'],
    'arraybuffer': ['binary data handler', 'response serializer'],
    'buffer': ['binary data handler', 'buffer manager'],
    'retry': ['retry logic', 'resilience layer', 'error recovery'],
    'backoff': ['retry logic', 'exponential backoff'],
    'timeout': ['timeout handler', 'connection manager'],
    'error': ['error handler', 'exception manager'],
    'auth': ['authentication module', 'auth middleware'],
    'cache': ['caching layer', 'cache manager'],
    'database': ['data access layer', 'ORM module'],
    'config': ['configuration module', 'settings manager'],
    'test': ['test suite', 'test utilities'],
    'log': ['logging module', 'logger'],
    'api': ['API layer', 'route handler'],
    'handler': ['request handler', 'event handler'],
    'middleware': ['middleware chain', 'request pipeline'],
    'schema': ['data model', 'schema definition'],
    'type': ['type definitions', 'interfaces'],
}
for kw in technical_keywords:
    if kw in component_hints:
        likely_components.extend(component_hints[kw])
likely_components = list(dict.fromkeys(likely_components))[:10]

# --- Requirements ---
requirements = []
req_patterns = [
    r'(?:should|must|need to|have to|required to|implement|support|add|create|fix)\s+(.{10,80})',
    r'(?:when|if|given)\s+(.{10,80})',
]
for pattern in req_patterns:
    for m in re.finditer(pattern, text):
        req = m.group(0).strip().rstrip('.')
        if req not in requirements:
            requirements.append(req)
if not requirements:
    requirements.append(f"Implement: {issue_title}")

# --- Acceptance Criteria (behavioral, not title-echo) ---
acceptance_criteria = []
ac_patterns = [
    r'(?:should|must|will)\s+((?:handle|return|send|provide|support|allow|prevent|ensure|maintain|preserve|throw|reject|resolve|complete|process|validate|check|detect|log|ignore|skip|fallback|default)\s+.{10,120})',
    r'(?:the\s+)?(\w+(?:\.\w+)*)\s+(?:should|must|will)\s+(.{10,120})',
    r'(?:instead of|rather than)\s+(.{10,120})',
    r'(?:without|no)\s+(?:longer\s+)?(.{10,120})',
]
for pattern in ac_patterns:
    for m in re.finditer(pattern, text):
        ac = m.group(0).strip().rstrip('.')
        if ac not in acceptance_criteria and len(ac) > 15:
            acceptance_criteria.append(ac)
if not acceptance_criteria:
    acceptance_criteria.append(f"The implementation described in the issue works correctly")
acceptance_criteria = acceptance_criteria[:8]

# --- Constraints ---
constraints = []
constraint_patterns = [
    r'(?:without|do not|must not|cannot|should not|avoid)\s+(.{10,100})',
    r'(?:no\s+(?:new|additional|extra|further))\s+(.{10,80})',
    r'(?:backward|backwards)\s+compatible',
    r'(?:non.?breaking|without\s+breaking)\s+(.{10,80})',
]
for pattern in constraint_patterns:
    for m in re.finditer(pattern, text):
        c = m.group(0).strip().rstrip('.')
        if c not in constraints:
            constraints.append(c)

# --- Unknowns ---
unknowns = []
unknown_patterns = [
    r'(?:where|how|which|what)\s+(?:is|are|does|do|should|would|could|can)\s+(.{10,120})',
    r'\?\s*',
]
for pattern in unknown_patterns:
    for m in re.finditer(pattern, full_text):
        idx = m.start()
        start = max(0, idx - 30)
        end = min(len(full_text), idx + 100)
        snippet = full_text[start:end].strip()
        if snippet and snippet not in unknowns:
            unknowns.append(snippet)
if not unknowns:
    unknowns.append("Where is the affected code located?")
    unknowns.append("What existing patterns should be followed?")
unknowns = unknowns[:6]

context = {
    "issue_title": issue_title,
    "issue_body": issue_body,
    "problem": problem,
    "expected_behavior": expected_behavior,
    "domain_concepts": domain_concepts,
    "technical_keywords": technical_keywords,
    "likely_components": likely_components,
    "keywords": technical_keywords + [c.split()[0].lower() for c in domain_concepts],
    "requirements": requirements,
    "acceptance_criteria": acceptance_criteria,
    "constraints": constraints,
    "unknowns": unknowns,
}
with open(os.path.join(context_dir, "issue_context.json"), "w") as f:
    json.dump(context, f)

print(json.dumps(context))
