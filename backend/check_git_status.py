import subprocess, os

cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
res = subprocess.run(["git", "status"], cwd=cwd, capture_output=True, text=True, shell=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
