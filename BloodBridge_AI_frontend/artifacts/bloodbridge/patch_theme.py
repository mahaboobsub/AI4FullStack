import os
import re

files_to_patch = [
    "src/pages/Login.tsx",
    "src/pages/SignUp.tsx",
    "src/pages/PatientLogin.tsx",
    "src/pages/DonorLogin.tsx",
    "src/pages/DonorPortal.tsx",
    "src/pages/PatientDashboard.tsx",
]

replacements = {
    'bg-white': 'bg-white dark:bg-slate-950',
    'text-slate-900': 'text-slate-900 dark:text-slate-100',
    'text-slate-800': 'text-slate-800 dark:text-slate-200',
    'text-slate-500': 'text-slate-500 dark:text-slate-400',
    'bg-slate-50': 'bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100',
    'bg-slate-100': 'bg-slate-100 dark:bg-slate-800',
    'border-slate-200': 'border-slate-200 dark:border-slate-800',
    'border-slate-100': 'border-slate-100 dark:border-slate-800',
}

def patch_file(filepath):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Apply simple class replacements
    for old, new in replacements.items():
        # Only replace if dark: isn't already there
        content = re.sub(rf'(?<!dark:){old}', new, content)

    # Insert ThemeToggle import
    if "import { ThemeToggle }" not in content:
        import_stmt = 'import { ThemeToggle } from "@/components/ThemeToggle";\n'
        content = re.sub(r'(import .*?;)', rf'\1\n{import_stmt}', content, count=1)
    
    # Add ThemeToggle to the top right of the screen
    # For login/signup screens, they start with `<div className="flex min-h-screen`
    toggle_ui = '\n      <div className="absolute top-4 right-4 z-50"><ThemeToggle /></div>\n'
    if "ThemeToggle />" not in content:
        content = content.replace('<div className="flex min-h-screen', f'<div className="flex min-h-screen{toggle_ui}')
        # For portals that don't have flex min-h-screen but just min-h-screen
        content = content.replace('<div className="min-h-screen', f'<div className="min-h-screen{toggle_ui}')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Patched {filepath}")

for f in files_to_patch:
    patch_file(f)
