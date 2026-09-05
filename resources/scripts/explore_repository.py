import os, json, re, sys

repo = os.environ.get("REPO_PATH", ".")
context_dir = os.environ.get("CONTEXT_DIR", "/tmp/issue2plan_context")
os.makedirs(context_dir, exist_ok=True)

skip_dirs = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build', 'target', '.venv', 'venv', '.next', '.nuxt', 'coverage', '.idea', '.vscode'}

# --- Languages ---
languages = {}
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        ext_map = {'.ts': 'TypeScript', '.tsx': 'TypeScript', '.js': 'JavaScript', '.jsx': 'JavaScript', '.py': 'Python', '.go': 'Go', '.rs': 'Rust', '.java': 'Java', '.rb': 'Ruby', '.php': 'PHP', '.vue': 'Vue', '.svelte': 'Svelte', '.c': 'C', '.cpp': 'C++', '.h': 'C/C++ Header', '.cs': 'C#', '.swift': 'Swift', '.kt': 'Kotlin', '.scala': 'Scala', '.ex': 'Elixir', '.erl': 'Erlang', '.hs': 'Haskell', '.r': 'R', '.lua': 'Lua', '.pl': 'Perl', '.sh': 'Shell', '.bash': 'Shell'}
        if ext in ext_map:
            lang = ext_map[ext]
            languages[lang] = languages.get(lang, 0) + 1

# --- Frameworks ---
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
                if '@nestjs/core' in deps: frameworks.append('NestJS')
                if 'svelte' in deps: frameworks.append('Svelte')
                if 'tailwindcss' in deps: frameworks.append('Tailwind CSS')
                if 'angular' in deps or '@angular/core' in deps: frameworks.append('Angular')
                if 'ember-cli' in deps or 'ember' in deps: frameworks.append('Ember')
                if 'vue' in deps: frameworks.append('Vue.js')
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
                    if 'tornado' in reqs: frameworks.append('Tornado')
                    if 'aiohttp' in reqs: frameworks.append('aiohttp')
            except: pass
        elif f == 'go.mod':
            package_managers.append('go mod')
        elif f == 'Cargo.toml':
            package_managers.append('cargo')
        elif f == 'Gemfile':
            package_managers.append('bundler')
        elif f == 'pom.xml':
            package_managers.append('maven')
        elif f == 'build.gradle' or f == 'build.gradle.kts':
            package_managers.append('gradle')
        elif f in {'tsconfig.json', 'jsconfig.json'}:
            config_files['typescript'] = rel
        elif f == '.eslintrc.js' or f == '.eslintrc.json' or f == '.eslintrc.yml':
            config_files['eslint'] = rel
        elif f == '.prettierrc' or f == '.prettierrc.json' or f == 'prettier.config.js':
            config_files['prettier'] = rel
        elif f == 'jest.config.js' or f == 'jest.config.ts' or f == 'vitest.config.ts':
            config_files['test_config'] = rel
        elif f == 'webpack.config.js' or f == 'webpack.config.ts':
            config_files['webpack'] = rel
        elif f == 'vite.config.ts' or f == 'vite.config.js':
            config_files['vite'] = rel
        elif f == 'tsup.config.ts' or f == 'rollup.config.js':
            config_files['bundler'] = rel
        elif f == 'Dockerfile' or f == 'docker-compose.yml' or f == 'docker-compose.yaml':
            config_files['docker'] = rel
        elif f == '.github' and os.path.isdir(full):
            config_files['github_actions'] = rel
        elif f == 'Makefile':
            config_files['make'] = rel
        elif f == 'CMakeLists.txt':
            config_files['cmake'] = rel
        elif f == '.env' or f == '.env.example':
            config_files['env'] = rel
frameworks = list(set(frameworks))
package_managers = list(set(package_managers))

# --- Source Directories ---
source_directories = []
test_directories = []
common_source = ['src', 'lib', 'app', 'source', 'sources', 'pkg', 'internal', 'cmd']
common_test = ['test', 'tests', '__tests__', 'spec', '__spec__', 'test_dir', 'tests_dir']
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    rel = os.path.relpath(root, repo)
    if rel == '.':
        continue
    dir_name = os.path.basename(root)
    if dir_name in common_source:
        source_directories.append(rel)
    elif dir_name in common_test:
        test_directories.append(rel)
    elif root == repo:
        pass
    else:
        code_count = sum(1 for f in files if os.path.splitext(f)[1].lower() in {'.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rs', '.java', '.rb', '.php'})
        test_count = sum(1 for f in files if re.match(r'.*\.(test|spec)\.(ts|tsx|js|jsx|py)$', f))
        if code_count > 3 and test_count == 0:
            source_directories.append(rel)
        elif test_count > 0:
            test_directories.append(rel)
if not source_directories:
    top_code = sum(1 for f in os.listdir(repo) if os.path.splitext(f)[1].lower() in {'.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rs', '.java', '.rb', '.php'})
    if top_code > 0:
        source_directories.append('.')
source_directories = list(set(source_directories))[:10]
test_directories = list(set(test_directories))[:10]

# --- Entry Points ---
entry_points = []
entry_names = {'main.ts', 'main.js', 'main.py', 'index.ts', 'index.js', 'app.ts', 'app.js', 'app.py', 'manage.py', 'server.ts', 'server.js', 'index.html', 'Program.cs', 'main.go', 'main.rs', 'cmd/main.go', 'src/main.rs'}
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        if f in entry_names:
            entry_points.append(os.path.relpath(os.path.join(root, f), repo))
entry_points = entry_points[:10]

# --- Build System ---
build_system = []
build_files = {
    'Makefile': 'make', 'CMakeLists.txt': 'cmake', 'build.gradle': 'gradle',
    'build.gradle.kts': 'gradle', 'pom.xml': 'maven', 'webpack.config.js': 'webpack',
    'webpack.config.ts': 'webpack', 'vite.config.ts': 'vite', 'vite.config.js': 'vite',
    'tsup.config.ts': 'tsup', 'rollup.config.js': 'rollup', 'esbuild.config.js': 'esbuild',
    'turbo.json': 'turborepo', 'nx.json': 'nx', 'lerna.json': 'lerna',
    'Dockerfile': 'docker', 'docker-compose.yml': 'docker-compose',
    'docker-compose.yaml': 'docker-compose', '.github/workflows': 'github-actions',
    'Taskfile.yml': 'task', 'justfile': 'just',
}
for root, dirs, files in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, repo)
        if f in build_files:
            build_system.append(build_files[f])
        elif f == '.github' and os.path.isdir(full):
            try:
                workflows = os.path.join(full, 'workflows')
                if os.path.isdir(workflows):
                    build_system.append('github-actions')
            except: pass
build_system = list(set(build_system))

# --- Repository Structure ---
repository_structure = []
try:
    entries = sorted(os.listdir(repo))
    for entry in entries:
        if entry.startswith('.'):
            continue
        full = os.path.join(repo, entry)
        if os.path.isdir(full):
            if entry not in skip_dirs:
                repository_structure.append(f"{entry}/")
        else:
            repository_structure.append(entry)
except: pass
repository_structure = repository_structure[:25]

# --- Test Framework ---
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
            elif 'pytest' in content or 'def test_' in content:
                test_framework = 'pytest'
                break
            elif 'mocha' in content.lower():
                test_framework = 'mocha'
                break
            elif 'jasmine' in content.lower():
                test_framework = 'jasmine'
                break
        except: pass
    if test_framework != "unknown":
        break

# Read keywords from issue context if available
context_path = os.path.join(context_dir, "issue_context.json")
if os.path.exists(context_path):
    with open(context_path) as f:
        ctx = json.load(f)
    keywords = ctx.get("keywords", [])
else:
    keywords = []

result = {
    "language": languages,
    "framework": frameworks,
    "package_manager": package_managers,
    "source_directories": source_directories,
    "test_directories": test_directories,
    "entry_points": entry_points,
    "config_files": config_files,
    "build_system": build_system,
    "repository_structure": repository_structure,
    "test_framework": test_framework,
    "keywords": keywords
}

with open(os.path.join(context_dir, "repo_context.json"), "w") as f:
    json.dump(result, f)

print(json.dumps(result))
