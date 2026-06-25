import os
import sys
import importlib.util

# 1. Metaprogramming Hook: Force 'app' to resolve to the 'app/' directory package
# This prevents Python from colliding the root 'app.py' launcher with the 'app' package.
script_dir = os.path.dirname(os.path.abspath(__file__))
app_package_init = os.path.join(script_dir, "app", "__init__.py")

spec = importlib.util.spec_from_file_location("app", app_package_init)
app_module = importlib.util.module_from_spec(spec)
sys.modules["app"] = app_module
spec.loader.exec_module(app_module)

# 2. Import actual application from app/app.py package
from app.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Launching KrishiKantho AI on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
