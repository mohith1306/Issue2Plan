import os, json, re, sys, tempfile

issue_title = os.environ.get("ISSUE_TITLE", "")
issue_body = os.environ.get("ISSUE_BODY", "")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")
os.makedirs(context_dir, exist_ok=True)

text = f"{issue_title} {issue_body}".lower()

action_verbs = ["add", "implement", "create", "fix", "update", "remove", "refactor", "improve", "optimize", "fix", "support", "enable", "disable", "configure", "enhance"]
stop_words = {"the", "a", "an", "to", "for", "in", "on", "with", "from", "by", "as", "is", "was", "are", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their", "what", "which", "who", "whom", "where", "when", "why", "how", "all", "each", "every", "both", "few", "more", "most", "other", "some", "such", "no", "not", "only", "own", "same", "so", "than", "too", "very", "just", "because", "but", "and", "or", "if", "while", "of", "at", "by", "between", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "about", "into", "over", "under", "again", "further", "then", "once", "also", "here", "there", "now", "new", "first", "last", "long", "great", "high", "small", "large"}

action_keywords = []
for verb in action_verbs:
    if verb in text:
        action_keywords.append(verb)

words = re.findall(r'\b[a-z]{3,}\b', text)
meaningful_words = [w for w in words if w not in stop_words]

word_freq = {}
for w in meaningful_words:
    word_freq[w] = word_freq.get(w, 0) + 1
frequent_words = sorted(word_freq.items(), key=lambda x: -x[1])
top_words = [w for w, c in frequent_words[:15]]

code_terms = []
code_patterns = [
    (r'\b(api|endpoint|route|handler|controller)\b', 'code_infra'),
    (r'\b(retry|backoff|timeout|request|response)\b', 'networking'),
    (r'\b(error|exception|fail|catch|throw)\b', 'error_handling'),
    (r'\b(test|spec|assert|expect)\b', 'testing'),
    (r'\b(config|setting|env|option)\b', 'configuration'),
    (r'\b(database|db|query|sql|orm)\b', 'data_layer'),
    (r'\b(auth|login|token|session|jwt)\b', 'authentication'),
    (r'\b(cache|redis|memcache)\b', 'caching'),
    (r'\b(log|logger|logging)\b', 'logging'),
    (r'\b(queue|worker|job|task)\b', 'async_processing'),
    (r'\b(middleware|plugin|extension)\b', 'extensibility'),
    (r'\b(type|interface|schema|model)\b', 'data_modeling'),
    (r'\b(function|method|class|module)\b', 'code_structure'),
]
for pattern, category in code_patterns:
    matches = re.findall(pattern, text)
    if matches:
        code_terms.extend(matches)

all_keywords = list(dict.fromkeys(action_keywords + top_words + code_terms))

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

acceptance_criteria = []
for m in re.finditer(r'(?:should|must|will)\s+(.{10,80})', text):
    ac = m.group(0).strip().rstrip('.')
    if ac not in acceptance_criteria:
        acceptance_criteria.append(ac)
if not acceptance_criteria:
    acceptance_criteria.append(f"Successfully implement: {issue_title}")

constraints = []
for m in re.finditer(r'(?:without|do not|must not|cannot|should not|avoid)\s+(.{10,80})', text):
    c = m.group(0).strip().rstrip('.')
    if c not in constraints:
        constraints.append(c)

unknowns = []
for m in re.finditer(r'\?\s*', issue_body):
    idx = m.start()
    start = max(0, idx - 50)
    end = min(len(issue_body), idx + 50)
    snippet = issue_body[start:end].strip()
    unknowns.append(snippet)

context = {
    "issue_title": issue_title,
    "issue_body": issue_body,
    "keywords": all_keywords,
    "requirements": requirements,
    "acceptance_criteria": acceptance_criteria,
    "constraints": constraints,
    "unknowns": unknowns,
    "action_keywords": action_keywords,
    "code_terms": code_terms
}
with open(os.path.join(context_dir, "issue_context.json"), "w") as f:
    json.dump(context, f)

print(json.dumps(context))
