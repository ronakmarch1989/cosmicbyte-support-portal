"""
Patches Streamlit + Tornado to remove X-Frame-Options before launching.
Also patches index.html to inject OG meta tags for WhatsApp/social link previews.
Streamlit runs directly on $PORT — no proxy, no WebSocket issues.
"""
import os
import sys
import subprocess

def patch_file(filepath, replacements):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        modified = source
        for old, new in replacements:
            modified = modified.replace(old, new)
        if modified != source:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified)
            print(f"✓ Patched {filepath}")
        else:
            print(f"  No changes in {filepath}")
    except Exception as e:
        print(f"  Could not patch {filepath}: {e}")

def get_package_file(import_str):
    result = subprocess.run(
        [sys.executable, '-c', import_str],
        capture_output=True, text=True
    )
    return result.stdout.strip()

print("=== Patching X-Frame-Options ===")

# 1. Patch Streamlit server
st_server = get_package_file(
    'import streamlit.web.server.server as m; print(m.__file__)'
)
if st_server:
    patch_file(st_server, [
        ('"X-Frame-Options"',  '"_disabled_xfo"'),
        ("'X-Frame-Options'",  "'_disabled_xfo'"),
        ('"SAMEORIGIN"',       '"ALLOWALL"'),
        ("'SAMEORIGIN'",       "'ALLOWALL'"),
    ])

# 2. Patch Streamlit browser server util (if it exists)
st_util = get_package_file(
    'import streamlit.web.server.browser_websocket_handler as m; print(m.__file__)'
)
if st_util:
    patch_file(st_util, [
        ('"X-Frame-Options"', '"_disabled_xfo"'),
        ("'X-Frame-Options'", "'_disabled_xfo'"),
    ])

# 3. Patch Tornado web.py where SAMEORIGIN is set
tornado_web = get_package_file(
    'import tornado.web as m; print(m.__file__)'
)
if tornado_web:
    patch_file(tornado_web, [
        ('"X-Frame-Options"',  '"_disabled_xfo"'),
        ("'X-Frame-Options'",  "'_disabled_xfo'"),
        ('"SAMEORIGIN"',       '"ALLOWALL"'),
        ("'SAMEORIGIN'",       "'ALLOWALL'"),
    ])

# 4. Patch Streamlit index.html — inject OG meta tags for WhatsApp/social previews
print("=== Patching OG meta tags ===")
st_index = get_package_file(
    'import streamlit; import os; print(os.path.join(os.path.dirname(streamlit.__file__), "static", "index.html"))'
)
if st_index and os.path.exists(st_index):
    OG_TAGS = """<meta property="og:title" content="Cosmic Byte AI Support">
<meta property="og:description" content="Instant AI-powered support for all Cosmic Byte gaming products.">
<meta property="og:image" content="https://ai.thecosmicbyte.com/app/static/favicon.png">
<meta property="og:url" content="https://ai.thecosmicbyte.com/">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Cosmic Byte AI Support">
<meta name="twitter:description" content="Instant AI-powered support for all Cosmic Byte gaming products.">"""
    patch_file(st_index, [
        ('<title>Streamlit</title>', f'<title>Cosmic Byte AI Support</title>\n    {OG_TAGS}'),
    ])
else:
    print(f"  index.html not found at: {st_index}")

print("=== Starting Streamlit ===")

# Run Streamlit directly on Render's PORT — no proxy needed
port = os.environ.get('PORT', '8501')
os.execvp(sys.executable, [
    sys.executable, '-m', 'streamlit', 'run', 'support_portal.py',
    f'--server.port={port}',
    '--server.address=0.0.0.0',
    '--server.enableCORS=false',
    '--server.enableXsrfProtection=false',
    '--server.headless=true',
])
