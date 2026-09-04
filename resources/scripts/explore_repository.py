import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")
os.makedirs(context_dir, exist_ok=True)

skip_dirs = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build', 'target', '.venv', 'venv', '.next', '.nuxt'}

languages = {}
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        ext_map = {'.ts': 'TypeScript', '.tsx': 'TypeScript', '.js': 'JavaScript', '.jsx': 'JavaScript', '.py': 'Python', '.go': 'Go', '.rs': 'Rust', '.java': 'Java', '.rb': 'Ruby', '.php': 'PHP', '.vue': 'Vue', '.svelte': 'Svelte'}
        if ext in ext_map:
            lang = ext_map[ext]
            languages[lang] = languages.get(lang, 0) + 1

frameworks = []
package_managers = []
config_files = {}
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, repo)
        if f == 'package.json':
            try:
                pkg = json.load(open(full))
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                if 'next' in deps: frameworks.append('Next.js')
                if 'react' in deps: frameworks.append('React')
                if 'vue' in deps: frameworks.append('Vue')
                if 'nuxt' in deps: frameworks.append('Nuxt.js')
                if 'express' in deps: frameworks.append('Express')
                if 'fastify' in deps: frameworks.append('Fastify')
                if 'nestjs' in deps or '@nestjs/core' in deps: frameworks.append('NestJS')
                if 'svelte' in deps: frameworks.append('Svelte')
                if 'tailwindcss' in deps: frameworks.append('Tailwind CSS')
                package_managers.append('npm/yarn')
            except: pass
        elif f == 'requirements.txt' or f == 'setup.py' or f == 'pyproject.toml':
            package_managers.append('pip')
            try:
                if f == 'requirements.txt':
                    reqs = open(full).read().lower()
                    if 'django' in reqs: frameworks.append('Django')
                    if 'flask' in reqs: frameworks.append('Flask')
                    if 'fastapi' in reqs: frameworks.append('FastAPI')
                    if 'pytest' in reqs: pass
            except: pass
        elif f == 'go.mod':
            package_managers.append('go mod')
        elif f == 'Cargo.toml':
            package_managers.append('cargo')
        elif f in {'tsconfig.json', 'jsconfig.json'}:
            config_files['typescript'] = rel
        elif f == '.eslintrc.js' or f == '.eslintrc.json':
            config_files['eslint'] = rel

entry_points = []
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        if f == 'main.ts' or f == 'main.js':
            entry_points.append(os.path.relpath(os.path.join(root, f), repo))
        elif f == 'index.ts' or f == 'index.js':
            entry_points.append(os.path.relpath(os.path.join(root, f), repo))
        elif f == 'app.py':
            entry_points.append(os.path.relpath(os.path.join(root, f), repo))
        elif f == 'manage.py':
            entry_points.append(os.path.relpath(os.path.join(root, f), repo))

test_framework = "unknown"
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        try:
            content = open(os.path.join(root, f), 'r', errors='ignore').read()
            if 'jest' in content.lower() or ('describe(' in content and ('it(' in content or 'test(' in content)):
                test_framework = 'jest'
                break
            elif 'vitest' in content.lower():
                test_framework = 'vitest'
                break
            elif 'pytest' in content:
                test_framework = 'pytest'
                break
        except: pass
    if test_framework != "unknown":
        break

context_path = os.path.join(context_dir, "issue_context.json")
if os.path.exists(context_path):
    with open(context_path) as f:
        ctx = json.load(f)
    keywords = ctx.get("keywords", [])
else:
    keywords = []

result = {
    "languages": languages,
    "frameworks": list(set(frameworks)),
    "package_managers": list(set(package_managers)),
    "entry_points": entry_points[:10],
    "test_framework": test_framework,
    "config_files": config_files,
    "keywords": keywords
}

with open(os.path.join(context_dir, "repo_context.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
