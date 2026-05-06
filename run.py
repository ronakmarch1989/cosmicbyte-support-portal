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
    FAVICON_B64 = "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"
    OG_TAGS = f"""<link rel="icon" type="image/png" href="data:image/png;base64,{FAVICON_B64}">
<link rel="shortcut icon" type="image/png" href="data:image/png;base64,{FAVICON_B64}">
<meta property="og:title" content="Cosmic Byte AI Support">
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
