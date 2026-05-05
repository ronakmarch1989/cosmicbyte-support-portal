"""
Reverse proxy that runs Streamlit internally and strips
X-Frame-Options so the app embeds in iframes on WooCommerce.
"""
import asyncio
import os
import subprocess
import threading
import time

import aiohttp
from aiohttp import web

STREAMLIT_PORT = 8501
STREAMLIT_BASE = f"http://localhost:{STREAMLIT_PORT}"

# ── HTTP proxy ─────────────────────────────────────────────────────────────

async def proxy(request):
    path = request.path_qs or "/"

    # WebSocket upgrade
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return await ws_proxy(request, path)

    url = f"{STREAMLIT_BASE}{path}"
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "content-length")}

    async with aiohttp.ClientSession() as s:
        try:
            async with s.request(
                request.method, url,
                headers=headers,
                data=await request.read(),
                allow_redirects=False,
                ssl=False,
            ) as r:
                out_headers = {}
                for k, v in r.headers.items():
                    if k.lower() in ("x-frame-options",
                                     "content-length",
                                     "transfer-encoding",
                                     "connection"):
                        continue
                    out_headers[k] = v

                # Allow embedding from everywhere
                out_headers["Content-Security-Policy"] = "frame-ancestors *"
                out_headers["Access-Control-Allow-Origin"] = "*"

                body = await r.read()
                return web.Response(body=body, status=r.status,
                                    headers=out_headers)
        except aiohttp.ClientConnectorError:
            return web.Response(text="Starting up...", status=503)

# ── WebSocket proxy ────────────────────────────────────────────────────────

async def ws_proxy(request, path):
    ws_url = f"ws://localhost:{STREAMLIT_PORT}{path}"
    client_ws = web.WebSocketResponse()
    await client_ws.prepare(request)

    try:
        async with aiohttp.ClientSession() as s:
            async with s.ws_connect(ws_url) as server_ws:

                async def fwd_to_browser():
                    async for msg in server_ws:
                        if client_ws.closed:
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await client_ws.send_str(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            await client_ws.send_bytes(msg.data)
                        elif msg.type in (aiohttp.WSMsgType.CLOSE,
                                          aiohttp.WSMsgType.ERROR):
                            break

                async def fwd_to_streamlit():
                    async for msg in client_ws:
                        if server_ws.closed:
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await server_ws.send_str(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            await server_ws.send_bytes(msg.data)
                        elif msg.type in (aiohttp.WSMsgType.CLOSE,
                                          aiohttp.WSMsgType.ERROR):
                            break

                await asyncio.gather(fwd_to_browser(), fwd_to_streamlit())
    except Exception:
        pass

    return client_ws

# ── Start Streamlit in background ─────────────────────────────────────────

def launch_streamlit():
    time.sleep(4)
    subprocess.Popen([
        "streamlit", "run", "support_portal.py",
        f"--server.port={STREAMLIT_PORT}",
        "--server.address=localhost",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--server.headless=true",
    ])

# ── Entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    t = threading.Thread(target=launch_streamlit, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_route("*", "/{path_info:.*}", proxy)
    print(f"Proxy running on port {port}, Streamlit on {STREAMLIT_PORT}")
    web.run_app(app, host="0.0.0.0", port=port)
