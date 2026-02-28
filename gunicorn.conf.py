# Gunicorn config for BHV (prototype / low-traffic)
import os

# Bind to Render's dynamic PORT
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Single worker — prototype, no concurrent load expected
workers = 1

# Longer timeout for git operations (commits can take a moment)
timeout = 120

# Log to stdout so Render picks it up
accesslog = "-"
errorlog = "-"
loglevel = "info"
