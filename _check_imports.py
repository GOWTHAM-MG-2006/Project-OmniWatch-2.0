import ast, os

root = 'E:/Project-OmniWatch-2.0'
success = 0
no_imports = 0
syntax_errors = 0
errors = []
missing_imports = []

for dp, dn, fns in os.walk(root):
    if '__pycache__' in dp or '.git' in dp or 'node_modules' in dp:
        continue
    for fn in fns:
        if not fn.endswith('.py'):
            continue
        fp = os.path.join(dp, fn)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
            imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
            if imports:
                success += 1
                # Check for mobile imports
                for imp in imports:
                    if isinstance(imp, ast.Import):
                        for alias in imp.names:
                            if 'mobile' in alias.name.lower():
                                missing_imports.append(f'{fp}: imports mobile module {alias.name}')
                    elif isinstance(imp, ast.ImportFrom):
                        if imp.module and 'mobile' in imp.module.lower():
                            missing_imports.append(f'{fp}: imports from mobile module {imp.module}')
            else:
                no_imports += 1
        except SyntaxError as e:
            syntax_errors += 1
            errors.append(f'{fp}: {e}')

print(f'Parseable with imports: {success}')
print(f'Parseable without imports: {no_imports}')
print(f'Syntax errors: {syntax_errors}')
print(f'Total: {success + no_imports + syntax_errors}')
if errors:
    print(f'\nSyntax Errors ({len(errors)}):')
    for e in errors[:10]:
        print(f'  {e}')
if missing_imports:
    print(f'\nMobile Imports ({len(missing_imports)}):')
    for m in missing_imports[:10]:
        print(f'  {m}')
else:
    print('\nNo mobile imports found.')
