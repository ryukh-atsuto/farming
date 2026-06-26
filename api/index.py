import os
import sys

# Ensure root folder is in path so we can import the 'app' package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import app
