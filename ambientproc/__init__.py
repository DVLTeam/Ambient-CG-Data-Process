import subprocess
import sys
import pkg_resources

required = {"numpy", "torch", "lmdb"}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

if missing:
    print(f"Installing missing packages for ambientcgproc: {missing}")
    python = sys.executable
    subprocess.check_call([python, "-m", "pip", "install", *missing], stdout=subprocess.DEVNULL)

