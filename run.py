"""
Streamlit launcher that removes X-Frame-Options headers
so the app can be embedded in iframes on WooCommerce product pages.
"""
import os
import sys
from streamlit.web import bootstrap
from streamlit import config as _config


def patch_tornado():
    """Remove X-Frame-Options from every Streamlit response."""
    try:
        from streamlit.web.server import server as st_server
        import tornado.web

        original_set_default_headers = tornado.web.RequestHandler.set_default_headers

        def patched_set_default_headers(self):
            original_set_default_headers(self)
            self.clear_header("X-Frame-Options")
            self.set_header("Content-Security-Policy", "frame-ancestors *")

        tornado.web.RequestHandler.set_default_headers = patched_set_default_headers
    except Exception as e:
        print(f"Warning: could not patch headers: {e}")


if __name__ == "__main__":
    patch_tornado()

    # Apply Streamlit server config
    _config.set_option("server.enableCORS", False)
    _config.set_option("server.enableXsrfProtection", False)
    _config.set_option("server.headless", True)

    port = int(os.environ.get("PORT", 8501))
    _config.set_option("server.port", port)
    _config.set_option("server.address", "0.0.0.0")

    # Launch the app
    bootstrap.run(
        "support_portal.py",
        is_hello=False,
        args=[],
        flag_options={},
    )
