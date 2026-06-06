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

def fix_file(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # The broken string looks like:
    # <div className="flex min-h-screen
    #   <div className="absolute top-4 right-4 z-50"><ThemeToggle /></div>
    #  bg-white dark:bg-slate-950 font-sans">
    
    broken_pattern = r'<div className="([^"]*)\n\s*<div className="absolute top-4 right-4 z-50"><ThemeToggle /></div>\n\s*([^"]*)">'
    replacement = r'<div className="\1 \2">\n      <div className="absolute top-4 right-4 z-50"><ThemeToggle /></div>'
    
    new_content = re.sub(broken_pattern, replacement, content)
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

for f in files_to_patch:
    fix_file(f)
