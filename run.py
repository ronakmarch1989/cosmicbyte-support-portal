"""
Streamlit launcher with X-Frame-Options removed.
Patches tornado's finish() before Streamlit loads — works on every response.
"""
import os

# ── Patch tornado BEFORE streamlit touches it ──────────────────────────────
import tornado.web

_orig_finish = tornado.web.RequestHandler.finish

def _patched_finish(self, chunk=None):
    try:
        self.clear_header("X-Frame-Options")
        self.set_header("Content-Security-Policy", "frame-ancestors *")
        self.set_header("Access-Control-Allow-Origin", "*")
    except Exception:
        pass
    return _orig_finish(self, chunk)

tornado.web.RequestHandler.finish = _patched_finish

# ── Also patch set_default_headers as backup ──────────────────────────────
_orig_sdh = tornado.web.RequestHandler.set_default_headers

def _patched_sdh(self):
    _orig_sdh(self)
    try:
        self.clear_header("X-Frame-Options")
        self.set_header("Content-Security-Policy", "frame-ancestors *")
    except Exception:
        pass

tornado.web.RequestHandler.set_default_headers = _patched_sdh

# ── NOW import and launch Streamlit ───────────────────────────────────────
from streamlit.web import bootstrap
from streamlit import config as _config

if __name__ == "__main__":
    _config.set_option("server.enableCORS", False)
    _config.set_option("server.enableXsrfProtection", False)
    _config.set_option("server.headless", True)

    port = int(os.environ.get("PORT", 8501))
    _config.set_option("server.port", port)
    _config.set_option("server.address", "0.0.0.0")

    bootstrap.run(
        "support_portal.py",
        is_hello=False,
        args=[],
        flag_options={},
    )
