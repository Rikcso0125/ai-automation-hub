# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure VERCEL environment flag
os.environ["VERCEL"] = "1"

import urllib.parse
from hub_server import app as fastapi_app

# ASGI wrapper to restore original path from Vercel rewrites
async def app(scope, receive, send):
    if scope["type"] == "http":
        qs = scope.get("query_string", b"").decode("latin-1", errors="ignore")
        params = urllib.parse.parse_qs(qs)
        if "__path" in params:
            real_path = params["__path"][0]
            if not real_path.startswith("/"):
                real_path = "/" + real_path
            scope["path"] = real_path
            scope["raw_path"] = real_path.encode("latin-1", errors="ignore")
            # Clean up query string so FastAPI routes and endpoints don't see __path
            clean_params = {k: v for k, v in params.items() if k != "__path"}
            clean_qs = urllib.parse.urlencode(clean_params, doseq=True)
            scope["query_string"] = clean_qs.encode("latin-1", errors="ignore")

    await fastapi_app(scope, receive, send)
