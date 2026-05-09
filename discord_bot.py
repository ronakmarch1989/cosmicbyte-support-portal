"""
Cosmic Byte Discord Support Bot
================================

A Discord bot that runs alongside the Streamlit web portal
(support_portal.py / support_portal_v2.py) and answers customer questions in
the Cosmic Byte Discord server using the same AI + knowledge base.

STANDING EDIT PROTOCOL (same as support_portal_v2.py + cb_kb.py)
----------------------------------------------------------------
- Only Claude edits this file. Ronak does not edit it manually.
- Every edit MUST:
    (1) Increment `__version__` appropriately (X=major, Y=feature, Z=bugfix).
    (2) Add a CHANGELOG entry below in the format:
        `vX.Y.Z (YYYY-MM-DD) -- Claude` with descriptive bullet points.
    (3) Be verified to pass `ast.parse` before delivery.

DEPLOYMENT (current as of v1.1.1, 2026-05-09)
---------------------------------------------
This file runs on a Hetzner Cloud Singapore VPS, NOT on Render.
Render only runs support_portal.py + cb_kb.py.

Where it runs:
  Host          : Hetzner CPX12 VPS, IPv4 5.223.52.60, Singapore region
  SSH access    : `ssh root@5.223.52.60` from Ronak's Mac (key-based,
                  no password)
  Process mgr   : systemd unit `cosmic-bot.service`, runs as user
                  `cosmic` (unprivileged), Restart=on-failure with
                  10s delay, starts at boot
  Code path     : /home/cosmic/bot/  (git clone of the GitHub repo
                  https://github.com/ronakmarch1989/cosmicbyte-support-portal)
  Python venv   : /home/cosmic/bot/.venv/
  Data dir      : /var/lib/cosmic-bot/  (CB_DATA_DIR env var)
                  Holds support_log.jsonl + chat_history.json
  Env file      : /etc/cosmic-bot.env  (mode 0600, owned by root,
                  read by systemd before privilege drop)

Required env vars in /etc/cosmic-bot.env:
  DISCORD_BOT_TOKEN          -- Discord bot's auth token
  ANTHROPIC_API_KEY          -- for AI responses
  DISCORD_GUILD_ID           -- 1416742276322955296
  DISCORD_SUPPORT_CHANNEL_ID -- 1502355643233730610
  DISCORD_BOT_REPLY_TO_DMS   -- false (default)
  CB_DATA_DIR                -- /var/lib/cosmic-bot
  LOG_API_SECRET             -- shared secret for the v1.1.0 log API
                                (must match BOT_API_SECRET on Render)
  Optional:
    LOG_API_PORT             -- default 8080
    LOG_API_BIND             -- default 0.0.0.0
    QUOTAGUARDSTATIC_URL or
    HTTPS_PROXY etc.         -- not currently used (VPS has dedicated
                                IP, no proxy needed). Leave unset.

How Ronak deploys changes to this file:
  Auto (preferred):
    1. Push to GitHub main branch.
    2. /etc/cron.d/cosmic-bot-deploy polls every 60 seconds. When
       it finds new commits, it runs:
         - sudo -u cosmic git pull
         - sudo -u cosmic .venv/bin/pip install -r requirements.txt
         - systemctl restart cosmic-bot
    3. Wait ~60-90 seconds. Done.
  Auto-deploy log: /var/log/cosmic-bot-deploy.log

  Manual (faster, useful while iterating):
    SSH to VPS as root, then:
      sudo -u cosmic bash -c 'cd /home/cosmic/bot && git pull'
      sudo -u cosmic /home/cosmic/bot/.venv/bin/pip install \
        -r /home/cosmic/bot/requirements.txt
      systemctl restart cosmic-bot
      journalctl -u cosmic-bot -n 20

Operator commands (all run as root via SSH):
  systemctl status cosmic-bot           -- is it running?
  systemctl restart cosmic-bot          -- restart now
  journalctl -u cosmic-bot -f           -- tail logs in real time
  journalctl -u cosmic-bot -n 100       -- last 100 log lines
  cat /var/log/cosmic-bot-deploy.log    -- recent auto-deploy events
  nano /etc/cosmic-bot.env              -- edit env vars
                                          (then `systemctl restart cosmic-bot`)
  curl -s http://localhost:8080/health  -- check log API liveness

Companion service:
  support_portal.py runs on Render and consumes this bot's log API
  (GET /log/recent, Bearer-auth) starting at portal v2.24.0. See
  support_portal.py's DEPLOYMENT section for the portal side.

CHANGELOG
---------
v1.2.1 (2026-05-10) -- Claude
  - Z-bump: cosmetic-only updates to two
    operator-facing error messages that
    still talked about the bot living on
    Render. Bot moved to the Hetzner VPS
    on 2026-05-09 (v1.1.0); these two
    messages were left over from the
    Render era and would have misdirected
    the operator on misconfiguration.

  Messages updated:
    1. DISCORD_BOT_TOKEN missing fatal
       (the early validation block that
       runs at module load if the env var
       is unset). Was: "Set it in
       Render -> Environment." Now: "Edit
       /etc/cosmic-bot.env on the VPS to
       set it, then `systemctl restart
       cosmic-bot`." Matches the actual
       deploy topology and gives the
       operator an immediately runnable
       command.

    2. Final-retry-exhausted fatal in the
       startup retry loop (fires when 12
       startup retries all hit Discord
       rate limits / network errors). Was
       referencing "QuotaGuard/Fixie's
       status page" -- those were the
       Render-era proxy add-ons; the bot
       no longer uses any proxy on the
       VPS. Now the message references
       the journalctl log path and lays
       out the three actually-useful
       recovery options (wait it out,
       contact Discord support, or
       migrate the bot to a fresh VPS
       IPv4). Also includes the host's
       HOSTNAME env var so the operator
       can see at a glance which VPS the
       message is coming from -- helpful
       if multiple bots are ever running
       in parallel during a migration.

  Behaviour: identical when the bot is
  configured correctly. The two messages
  only fire on startup misconfiguration
  (TOKEN missing) or on persistent rate-
  limiting (12 consecutive retry failures);
  in normal operation neither path is hit.

  Code paths NOT touched in this Z-bump:
    The full proxy-handling code path
    (PROXY_URL_RAW parsing, SOCKS connector
    construction, HTTP/HTTPS proxy plumbing)
    is intentionally left in place even
    though it's dead on the current VPS.
    Reason: it's documented in the
    DEPLOYMENT section ("not currently used
    -- leave unset") and provides a working
    migration path if the bot ever has to
    move back to a shared-egress host. The
    cost of keeping it is just one extra
    branch that's never taken; the cost of
    removing it would be losing a tested,
    proven proxy implementation that took
    several iterations (v1.0.2 - v1.0.5) to
    get right.

  ast.parse before/after.

v1.2.0 (2026-05-09) -- Claude
  - Y-bump: enable Anthropic prompt caching on the
    Anthropic API call. Same change as the parallel
    support_portal.py v2.25.0 bump -- both files
    share the same call structure (build a system
    prompt from SYSTEM_PROMPT + product knowledge
    + optional third-party brand manual, then call
    client.messages.create), and we want the bot
    and the portal to benefit from the same input-
    cost reduction.

  Why:
    Ronak flagged that current Anthropic API spend
    is high. Every bot reply re-sent the full
    system prompt (~15-30K tokens of identical
    content) as fresh input. Prompt caching
    addresses this exact pattern.

  How (no quality impact):
    Anthropic's prompt caching stores the pre-
    computed key-value cache for the cached portion
    of the input server-side. On a subsequent
    request with matching cached content, the model
    reuses the KV cache instead of recomputing it
    -- but it still processes the full input
    identically. Output quality is unchanged. Per-
    token input price drops on the cached portion:
    cache reads cost 0.1x base input price, cache
    writes cost 1.25x (so caching pays off after
    ~1.25 reuses within the 5-minute TTL window,
    per Anthropic's published pricing rules).

  Implementation:
    Refactored the api_kwargs construction in the
    customer-message handler:
      - Build the full system text as a string
        first (same logic as before -- SYSTEM_PROMPT
        + knowledge + optional brand manual / web
        search instruction).
      - Wrap that string in a single text content
        block with cache_control set to
        {"type": "ephemeral"}.
      - Pass system as a list of one block (the
        list form is required when using
        cache_control; the bare-string convenience
        form does not support caching).

    Pure structural change: same model, same
    max_tokens, same content, same messages. The
    only difference is that subsequent calls with
    the same (product, brand) combo within the
    5-minute TTL will hit the cache.

  Threshold caveat:
    Haiku 4.5 has a 4096-token minimum for caching
    to engage. Our system text reliably exceeds
    this for any production query. If it ever
    falls below the minimum the API request still
    succeeds; we just silently pay full price on
    that one call (cache_creation_input_tokens
    comes back as 0 in the response usage object).

  Verifying after deploy:
    Check console.anthropic.com -> Usage. The Cache
    Read and Cache Write columns should populate
    after a few bot replies. If Cache Read stays
    at 0 across many calls, the cache key is
    changing between calls -- the most common
    cause is a non-deterministic value sneaking
    into the system text (timestamp, random ID,
    dict ordering).

  ast.parse before/after.

v1.1.1 (2026-05-09) -- Claude
  * Z-bump: docs only -- added DEPLOYMENT section to the
    file's top docstring so future Claude sessions
    inherit context about where/how this file runs and
    can give Ronak correct answers for SSH paths,
    deploy commands, env-file location, etc. without
    re-deriving them from scratch.

  No code change. ast.parse before/after.

v1.1.0 (2026-05-09) -- Claude
  * Y-bump: HTTP log API for portal-bot integration.

  Why:
    After today's migration, the bot lives on a Hetzner VPS
    while the Streamlit portal stays on Render. They no
    longer share a filesystem, so the portal's admin
    dashboard can't see new Discord conversations -- they're
    written to /var/lib/cosmic-bot/support_log.jsonl on the
    VPS, not /var/data/support_log.jsonl on Render. This
    bump exposes the bot's log over HTTP so the portal can
    fetch it.

  What's new:
    * GET /log/recent?limit=N -- returns the last N rows
      from the bot's log file as a JSON array. Default 1000,
      max 10000. Read-only.
    * Auth: Authorization: Bearer <LOG_API_SECRET> header.
      Constant-time comparison via hmac.compare_digest.
      If the env var is empty, the API is disabled
      entirely (the listener doesn't start).
    * Listens on $LOG_API_BIND:$LOG_API_PORT
      (default 0.0.0.0:8080).
    * Runs in the same asyncio event loop as the Discord
      client. No threads. The aiohttp web app is spun up
      from inside _run_bot_async() before bot.start(), and
      cleaned up in the finally block when bot.start
      returns/raises.
    * The endpoint reads the log file under fcntl.LOCK_SH
      (shared/read lock) to coordinate with the writer's
      LOCK_EX -- the read won't tear a partially-written
      append, and the write won't block on long reads.

  Behaviour:
    * If LOG_API_SECRET is unset -- API disabled, bot runs
      exactly like v1.0.5.
    * If LOG_API_SECRET is set -- API binds and serves; if
      bind fails (port in use, etc.), bot logs the error
      and continues without the API rather than crashing
      the Discord bot. The Discord bot is the priority;
      the API is an add-on.

  Operator action needed (on Hetzner VPS):
    1. Generate a long random secret (any string >= 32
       chars). Easy way: `openssl rand -hex 32`.
    2. Add to /etc/cosmic-bot.env:
          LOG_API_SECRET=<the secret>
    3. Open inbound TCP 8080 in Hetzner Cloud Firewall
       (or leave the network open as-is; default Hetzner
       Cloud servers have no firewall).
    4. systemctl restart cosmic-bot
    5. Verify: `curl -H "Authorization: Bearer <secret>"
       http://localhost:8080/log/recent?limit=5`
       Should return JSON.

  Note on TLS:
    The endpoint serves plain HTTP. The data IS sensitive
    (customer conversations). For tonight we're shipping
    HTTP+secret as MVP; the threat model is "someone on
    the network path between Hetzner Singapore and Render
    eavesdropping", which is narrow but real. A follow-up
    bump should put Caddy or nginx in front with
    Let's Encrypt for proper TLS. That's a Z-bump-able
    operations change, no portal/bot code change required.

v1.0.5 (2026-05-09) -- Claude
  * Z-bump: hotfix for a v1.0.4 bug that crashed the bot at
    module-load time when QUOTAGUARDSTATIC_URL was a SOCKS5
    URL.

  Bug:
    `aiohttp_socks.ProxyConnector.from_url(...)` ultimately
    calls `asyncio.get_running_loop()` inside aiohttp's
    TCPConnector __init__. That function raises RuntimeError
    when there's no running event loop -- which is the case
    at module-load time, before bot.run() has set one up.
    v1.0.4 created the connector inside _build_bot() at
    module level (and also on each retry), so the bot
    crashed immediately on import:

        RuntimeError: no running event loop

    HTTP/HTTPS proxy was unaffected because that path uses
    `proxy=` / `proxy_auth=` kwargs (no connector).

  Fix:
    Moved bot construction from a sync _build_bot() called at
    module load to an async _run_bot_async() called via
    asyncio.run() inside the retry loop. Both the connector
    (for SOCKS) and the discord.Client are now built inside
    the running event loop where aiohttp's loop lookup
    works. The module no longer pre-creates a placeholder
    bot instance; `bot` starts as None and is set on the
    first iteration of the retry loop.

  Behaviour:
    * SOCKS5/SOCKS4 proxy (via aiohttp_socks): now works.
    * HTTP/HTTPS proxy: identical to v1.0.3/v1.0.4.
    * No proxy: identical to v1.0.2.
    * Retry-on-startup loop: identical -- still 12 attempts
      with exponential backoff up to ~3.7 hours, still
      LoginFailure-terminal, still rebuilds the Client from
      scratch on each retry. Just runs through asyncio.run()
      instead of bot.run() so we control connector creation
      timing.

  Also broadened:
    The retry path now catches `aiohttp.ClientError` and
    `asyncio.TimeoutError` in addition to
    `discord.HTTPException`. The "Server disconnected" error
    we saw on the v1.0.3-with-SOCKS-URL misconfiguration was
    `aiohttp.ServerDisconnectedError`, which is a ClientError
    subclass and was falling through to the generic Exception
    fatal-exit. With v1.0.5, transient network blips (proxy
    hiccups, brief Discord gateway disconnects during login)
    get retried instead of killed.

  Implementation note:
    bot.run() is itself a thin wrapper around
    asyncio.run(client.start()) with signal-handling glue,
    so dropping it costs nothing -- KeyboardInterrupt is
    handled by asyncio.run + discord.Client's async context
    manager (__aexit__ closes the client cleanly).

v1.0.4 (2026-05-09) -- Claude
  * Z-bump: SOCKS5 proxy support (in addition to HTTP/HTTPS).

  Why:
    v1.0.3 added HTTP proxy support, which lets the bot's
    initial Discord login go out through a static-IP proxy
    and bypass the rate-limit problem on /users/@me. Tested
    on Render with QuotaGuard: login succeeded, bot showed
    online in Discord. BUT no messages were being delivered
    -- the gateway WebSocket established its TLS handshake
    through the HTTP proxy's CONNECT tunnel, then sat there
    silent. HTTP proxies are notoriously flaky at carrying
    long-lived WebSocket connections; the bot looked
    "connected" while actually getting zero MESSAGE_CREATE
    events from Discord.

    SOCKS5 proxies tunnel at the TCP layer rather than
    speaking HTTP, so a WebSocket inside a SOCKS5 tunnel is
    just a TCP connection -- the proxy doesn't need to know
    or care that it's a WebSocket. Long-lived connections
    work cleanly. QuotaGuard provides both protocols on the
    same plan; we just point at a different port.

  Behaviour:
    * Detects the proxy URL's scheme:
        - socks5://, socks5h://, socks4://, socks4a://
              -> build aiohttp_socks.ProxyConnector and
                 pass to discord.Client(connector=...).
                 Both REST and gateway WebSocket flow
                 through the SOCKS tunnel.
        - http://, https://
              -> existing v1.0.3 behaviour: pass
                 proxy=/proxy_auth= to discord.Client.
        - anything else -> warn, no proxy.
    * Same env var names and priority as v1.0.3
      (QUOTAGUARDSTATIC_URL, FIXIE_URL, HTTPS_PROXY,
      HTTP_PROXY).
    * If aiohttp_socks is not importable but the URL is
      SOCKS, we WARN and fall back to no proxy rather than
      crash -- so a missing requirements.txt update is a
      visible operator problem, not a silent rate-limit
      regression.

  Implementation note:
    aiohttp_socks.ProxyConnector instances are single-use
    -- once the aiohttp session that owns them is closed,
    the connector cannot be reused. The v1.0.2 retry loop
    creates a fresh discord.Client on each attempt, and now
    each retry also creates a fresh ProxyConnector inside
    _build_bot() for the same reason. The full SOCKS URL
    (including credentials) is held in PROXY_URL_FOR_SOCKS
    at module level so each rebuild can reconstruct the
    connector cleanly.

  Operator action needed:
    1. Add `aiohttp-socks` to requirements.txt.
    2. Update QUOTAGUARDSTATIC_URL on Render to the SOCKS5
       URL from QuotaGuard's Connection Information page
       (port 1080, scheme socks5://, same username/password
       as the HTTP URL).
    3. Redeploy.

  No behaviour change when the proxy URL is HTTP/HTTPS or
  unset -- v1.0.3 paths are preserved unchanged.

v1.0.3 (2026-05-09) -- Claude
  * Z-bump: optional outbound HTTP proxy for the Discord
    connection, gated on env var. Lets the bot route its
    Discord REST + gateway traffic through a static-IP proxy
    (QuotaGuard, Fixie, or anything HTTP-proxy-compatible)
    instead of Render's shared egress IP pool.

  Why:
    The /users/@me 429 + 40062 rate-limit problem we keep
    hitting on Render is a Cloudflare per-IP rate limit on
    Discord's API. Render's egress IPs are shared with every
    other tenant in the region, so when a noisy neighbour
    burns the rate-limit budget we all eat 429s. A static-IP
    proxy gives us IPs from a different (less-noisy) pool.

  Behaviour:
    * If env var QUOTAGUARDSTATIC_URL is set (Render's
      QuotaGuard add-on uses this name) -- use it as the
      proxy.
    * Else if FIXIE_URL is set (Fixie add-on uses this name)
      -- use it.
    * Else if HTTPS_PROXY or HTTP_PROXY is set (generic
      Unix convention; useful for local testing) -- use it.
    * Else -- no proxy, behave exactly like v1.0.2.

    URL format expected:  http://user:pass@host:port
    Auth is parsed out of the URL, percent-decoded, and
    passed to discord.py via aiohttp.BasicAuth. The proxy
    URL stripped of credentials goes to discord.Client's
    `proxy=` kwarg. Both REST calls (where the rate limit
    is) and the gateway WebSocket are routed through the
    proxy -- discord.py does this automatically once `proxy`
    is set on the Client.

  Operator-friendly logging:
    * Startup banner adds a `proxy: host:port` line so you
      can verify the env var is being read. Password is NOT
      logged.
    * If proxy URL is malformed, we WARN and fall back to no
      proxy rather than crashing -- the v1.0.2 retry would
      hide the misconfiguration as transient HTTP errors
      otherwise.

  Compatibility:
    * Setting the env var requires no code changes. Unset it
      to revert to the previous behaviour.
    * Same code works on Render (with proxy env var) and on
      a VPS later (without it). No conditional deploys.

  Not a permanent fix:
    Even with this in place, the proxy provider's IPs are
    shared with their other customers. If those customers
    also run Discord bots, we may still see rate limits
    eventually -- just less often. The truly permanent fix
    is a host with a dedicated egress IP (separate VPS).
    This bump is the cheap experiment to find out whether
    a different shared pool is enough for our traffic.

v1.0.2 (2026-05-09) -- Claude
  * Z-bump: startup retry-resilience after the bot crashed
    permanently on a 429 from Discord's /users/@me endpoint.

  Background:
    Render's egress IP is shared across all tenants in the
    region. Discord rate-limits /users/@me at the IP level via
    Cloudflare, so when a noisy neighbour or a flurry of
    redeploys gets the IP into Discord's penalty box, every
    bot startup eats a 429 on the very first API call. On
    2026-05-08 the bot deployed at 20:53, hit five 429s in
    14 seconds, and then got an error code 40062 ("Service
    resource is being rate limited" -- Discord's "scaled"
    rate limit, much longer-lived than the standard 429).
    discord.py's internal retry-after loop gave up and raised
    HTTPException, which our bottom-of-file `except Exception`
    caught and called _fatal() on. Bot exited and stayed dead
    until manual redeploy -- which would just hit the same
    rate limit.

  Fix:
    Wrap the bot.run() call in a retry loop that:
      - keeps discord.LoginFailure terminal (token problems
        aren't going to fix themselves);
      - catches discord.HTTPException (the 429 case), sleeps
        with exponential backoff, rebuilds the Client, and
        retries;
      - keeps generic Exception terminal (anything we can't
        classify needs human attention, not a retry).
    Backoff schedule: 60s, 2m, 4m, 8m, 16m, 30m (capped),
    then 30m for the remaining attempts. 12 attempts total,
    ~3.7 hours wall-clock budget. That window matches the
    typical duration of a 40062 scaled rate limit. If we're
    still rate-limited after 3.7 hours, the IP is likely
    persistently flagged and the bot fatal-exits with an
    operator-actionable message pointing at the static-IP
    proxy / VPS-move options.

  Implementation note:
    discord.py's Client cannot be reused across .run() calls
    -- its event loop and HTTP session are torn down inside
    .run() when it raises. Refactored the bot creation into a
    small _build_bot() function that the retry loop calls each
    iteration. The on_ready / on_message coroutines stay at
    module level (no body change) and are registered onto the
    fresh Client via bot.event() rather than the @bot.event
    decorator, so the same coroutine objects are bound to
    whichever Client is currently active. They look up `bot`
    at call time via the global, so they always see the live
    instance.

  Note: this fix does NOT make the rate limit go away. It just
  makes the bot recover automatically once Discord lifts it,
  instead of requiring a manual redeploy. The longer-term fix
  is still to move the bot to a host with a non-shared egress
  IP (separate VPS, or a static-IP proxy).

v1.0.1 (2026-05-09) -- Claude
  * Z-bump alongside support_portal_v2 v2.23.2.

  Bug: _split_for_discord could emit empty chunks
    If a long AI response had a run of whitespace right around
    the DISCORD_MSG_LIMIT cut point, `remaining[:cut].rstrip()`
    could evaluate to "" -- and then we'd append an empty
    string to `chunks`. Discord's API rejects empty messages
    with a 400, so the surrounding HTTPException handler would
    log the failure and the user would see a partial reply
    (or no reply for the affected chunk). Edge case in
    practice -- AI responses rarely have 1900 leading spaces
    -- but worth closing.

    Fix: skip the chunk when rstrip'd to empty, and fall back
    to a single "(no response)" placeholder if -- by some
    pathological run of whitespace -- we built no chunks at
    all. Discord still gets a non-empty message either way.

  No behaviour change for normal AI responses (which are well-
  formed prose with no rogue whitespace at the cut points).

v1.0.0 (2026-05-08) -- Claude
  * Initial implementation alongside support_portal_v2.py v2.22.0.

  Behaviour:
    - Replies when @mentioned in any channel of the server.
    - Replies to every message in the dedicated support channel
      (DISCORD_SUPPORT_CHANNEL_ID = 1502355643233730610).
    - Does NOT reply in DMs unless DISCORD_BOT_REPLY_TO_DMS=true
      (default false). Easy to flip later via Render env var.
    - Ignores its own messages (no infinite loops).

  Conversation context:
    - Stateless. Each request walks up the Discord reply chain to
      reconstruct conversation history. No per-user database. If
      the user wants the bot to remember context, they reply to
      the bot's previous message; if they start fresh, they post
      a new top-level message.
    - Walks up to MAX_REPLY_DEPTH (10) ancestors. Beyond that we
      drop history -- a single conversation rarely needs more.

  Knowledge base:
    - Imports SYSTEM_PROMPT, KNOWLEDGE_BASE, PRODUCT_URLS, etc.
      from cb_kb.py (shared with the web portal). Single source of
      truth -- whatever the web AI knows, the Discord AI knows.
    - Uses detect_products_from_message() to figure out which
      product(s) the user is asking about. Defaults to
      CATALOGUE_ALL on recommendation queries, asks for clarity
      otherwise.
    - Third-party brand handling (Logitech, Razer, etc.) mirrors
      the web portal: use the THIRD_PARTY_BRAND_MANUALS entry if
      we have one, else add the web_search tool.

  Output handling:
    - Discord caps messages at 2000 chars. We split at 1900 to
      leave headroom for code-fences and to avoid mid-word cuts.
      Splits at \\n\\n boundaries when possible, else at \\n,
      else hard-cut.
    - Shows typing indicator while the API call is in flight so
      the user sees the bot working.

  Logging:
    - Writes the same row schema as the web portal to
      /var/data/support_log.jsonl, with Source="discord". Uses
      fcntl.flock() for cross-process safety against the portal's
      concurrent writes (the portal still uses threading.Lock
      which is intra-process only -- this is a known small race
      window and acceptable for now).

  Process model:
    - Launched from run.py as a subprocess BEFORE Streamlit
      replaces the parent process via os.execvp. After the
      execvp, this subprocess gets reparented to PID 1 and
      keeps running. Standard Linux behaviour, works fine on
      Render's single-instance web service.

  Env vars (read at startup):
    - DISCORD_BOT_TOKEN              (required; bot exits if absent)
    - DISCORD_SUPPORT_CHANNEL_ID     (required; channel where every
                                      message gets a reply)
    - DISCORD_GUILD_ID               (optional; logs only)
    - DISCORD_BOT_REPLY_TO_DMS       (optional; default "false")
    - ANTHROPIC_API_KEY              (required; same one the
                                      portal uses)
    - CB_DATA_DIR                    (optional; defaults to
                                      /var/data, matches portal)
"""

__version__ = "1.2.1"

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote

import aiohttp  # already a transitive dep via discord.py; we use it for BasicAuth
from aiohttp import web  # v1.1.0: aiohttp.web hosts the read-only log API.
import discord
import anthropic

# v1.0.4: aiohttp_socks is required only when the configured proxy URL is
# SOCKS (scheme socks5://, socks5h://, socks4://, socks4a://). HTTP/HTTPS
# proxies don't need it. We import it lazily so that running the bot
# without a SOCKS proxy doesn't require the package to be installed -- a
# missing dep at SOCKS-config time becomes a visible warning, not an
# import-time crash.
try:
    from aiohttp_socks import ProxyConnector as _SocksProxyConnector
    _HAS_AIOHTTP_SOCKS = True
except ImportError:
    _SocksProxyConnector = None
    _HAS_AIOHTTP_SOCKS = False

# Shared knowledge base. cb_kb.py has zero Streamlit/discord.py deps,
# so this import is cheap and side-effect-free.
from cb_kb import (
    SYSTEM_PROMPT,
    KNOWLEDGE_BASE,
    CATALOGUE_ALL,
    THIRD_PARTY_BRAND_MANUALS,
    detect_third_party_brand,
    detect_products_from_message,
)


# ─────────────────────────────────────────────────────────────────────
# Config (env vars)
# ─────────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
SUPPORT_CHANNEL_ID = int(os.environ.get("DISCORD_SUPPORT_CHANNEL_ID", "0") or "0")
GUILD_ID = int(os.environ.get("DISCORD_GUILD_ID", "0") or "0")
REPLY_TO_DMS = os.environ.get("DISCORD_BOT_REPLY_TO_DMS", "false").lower() in ("1", "true", "yes")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Persistence (matches support_portal_v2.py's contract)
PERSISTENT_DATA_DIR = os.environ.get("CB_DATA_DIR", "/var/data")
LOG_FILE_PATH = os.path.join(PERSISTENT_DATA_DIR, "support_log.jsonl") \
    if os.path.isdir(PERSISTENT_DATA_DIR) else None

# How many ancestor messages to walk up the reply chain. 10 is plenty for
# real customer support exchanges; nobody re-replies 10+ levels deep on a
# single ticket. Past that we drop history rather than blowing the API
# context window.
MAX_REPLY_DEPTH = 10

# Discord hard-caps at 2000 chars. Split at 1900 to leave room for code
# fences / formatting and to avoid mid-word cuts.
DISCORD_MSG_LIMIT = 1900

# Anthropic model + token budget (same as web portal)
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 600


# ─────────────────────────────────────────────────────────────────────
# Optional outbound HTTP/SOCKS proxy for the Discord connection
# ─────────────────────────────────────────────────────────────────────
# When set, all of discord.py's traffic (REST calls + gateway WebSocket)
# is routed through this proxy. We set it on Render to bypass the shared
# egress IP pool that keeps eating Discord rate limits. On a VPS or any
# other host with a dedicated IP, leave the env vars unset and the bot
# behaves exactly like v1.0.2.
#
# Recognised env var names, in priority order:
#   QUOTAGUARDSTATIC_URL  -- Render's QuotaGuard add-on
#   FIXIE_URL             -- Render's Fixie add-on
#   HTTPS_PROXY           -- generic Unix convention; useful for local testing
#   HTTP_PROXY            -- generic Unix convention; useful for local testing
#
# Supported schemes (v1.0.4):
#   http://, https://             -- HTTP CONNECT-style proxy. Works for
#                                    REST. Often unreliable for the
#                                    gateway WebSocket (silent message
#                                    drop) -- see v1.0.4 changelog.
#   socks5://, socks5h://,        -- SOCKS proxy. Tunnels at TCP layer,
#   socks4://, socks4a://            handles long-lived WebSockets cleanly.
#                                    Recommended for Discord bots.
#
# Expected URL format: scheme://user:pass@host:port
PROXY_URL_RAW = (
    os.environ.get("QUOTAGUARDSTATIC_URL")
    or os.environ.get("FIXIE_URL")
    or os.environ.get("HTTPS_PROXY")
    or os.environ.get("HTTP_PROXY")
)

# Parsed-and-ready values consumed by _build_bot. Exactly one of
# PROXY_URL_FOR_SOCKS or PROXY_NETLOC is set when a proxy is configured;
# both are None when no proxy / parse failed.
PROXY_NETLOC = None              # str: "http(s)://host:port" (HTTP path)
PROXY_AUTH = None                # aiohttp.BasicAuth or None (HTTP path)
PROXY_URL_FOR_SOCKS = None       # full URL incl. creds (SOCKS path).
                                 # Stored as URL rather than connector
                                 # because aiohttp_socks ProxyConnector
                                 # instances are single-use; the retry
                                 # loop rebuilds the connector each time.
PROXY_HOST_DISPLAY = "(none)"    # logged on startup; never includes password

_SOCKS_SCHEMES = {"socks5", "socks5h", "socks4", "socks4a"}

if PROXY_URL_RAW:
    try:
        _parsed = urlparse(PROXY_URL_RAW)
        if not _parsed.scheme or not _parsed.hostname:
            print(
                "[discord_bot] WARNING: proxy URL is malformed (missing "
                "scheme or host); proceeding WITHOUT a proxy.",
                flush=True,
            )
            PROXY_HOST_DISPLAY = "(parse failed)"
        else:
            _scheme = _parsed.scheme.lower()
            _port_part = f":{_parsed.port}" if _parsed.port else ""
            PROXY_HOST_DISPLAY = f"{_scheme}://{_parsed.hostname}{_port_part}"

            if _scheme in _SOCKS_SCHEMES:
                # SOCKS path. Need aiohttp_socks for the connector.
                if not _HAS_AIOHTTP_SOCKS:
                    print(
                        "[discord_bot] WARNING: proxy URL is SOCKS but "
                        "aiohttp_socks is not installed. Add 'aiohttp-socks' "
                        "to requirements.txt and redeploy. Proceeding "
                        "WITHOUT a proxy.",
                        flush=True,
                    )
                    PROXY_HOST_DISPLAY = "(socks dep missing)"
                else:
                    # Store the full URL; ProxyConnector is built lazily
                    # in _build_bot() because the connector is consumed
                    # when its owning aiohttp session closes (which
                    # happens at the end of each bot.run() call).
                    PROXY_URL_FOR_SOCKS = PROXY_URL_RAW
            else:
                # HTTP/HTTPS path (v1.0.3 behaviour). Strip credentials
                # from the URL we hand to discord.py -- auth goes via the
                # separate proxy_auth kwarg.
                PROXY_NETLOC = f"{_scheme}://{_parsed.hostname}{_port_part}"
                if _parsed.username and _parsed.password:
                    PROXY_AUTH = aiohttp.BasicAuth(
                        unquote(_parsed.username),
                        unquote(_parsed.password),
                    )
    except Exception as e:
        # Don't crash on a misconfigured env var -- warn and fall back to
        # no-proxy behaviour. The v1.0.2 retry would otherwise mask the
        # misconfiguration as a stream of transient HTTP errors.
        print(
            f"[discord_bot] WARNING: could not parse proxy URL ({e}); "
            f"proceeding WITHOUT a proxy.",
            flush=True,
        )
        PROXY_NETLOC = None
        PROXY_AUTH = None
        PROXY_URL_FOR_SOCKS = None
        PROXY_HOST_DISPLAY = "(parse failed)"


# ─────────────────────────────────────────────────────────────────────
# v1.1.0: Read-only log API config
# ─────────────────────────────────────────────────────────────────────
# After the bot moved off Render onto a VPS, the Streamlit portal can no
# longer share a filesystem with the bot. This API exposes the bot's log
# file over HTTP so the portal's admin dashboard / digest can fetch new
# Discord conversation rows. The portal-side counterpart lives in
# support_portal_v2.py v2.24.0+ (look for BOT_API_URL / BOT_API_SECRET
# and get_merged_log()).
#
# Auth: a single shared secret in the Authorization: Bearer header.
# Compared in constant time. If LOG_API_SECRET is unset/empty, the API
# is disabled entirely (no listener bound) -- this is the safe default
# so the API doesn't accidentally serve unauthenticated reads in dev.
#
# Bind: 0.0.0.0:8080 by default. The bind interface and port are both
# overridable via env vars, primarily for running multiple bots on one
# host or for binding to localhost-only when fronted by a reverse proxy
# (Caddy/nginx with TLS termination -- recommended follow-up).
LOG_API_SECRET = os.environ.get("LOG_API_SECRET", "") or ""
try:
    LOG_API_PORT = int(os.environ.get("LOG_API_PORT", "8080") or "8080")
except ValueError:
    LOG_API_PORT = 8080
LOG_API_BIND = os.environ.get("LOG_API_BIND", "0.0.0.0") or "0.0.0.0"


# ─────────────────────────────────────────────────────────────────────
# Startup validation
# ─────────────────────────────────────────────────────────────────────
def _fatal(msg):
    print(f"[discord_bot] FATAL: {msg}", flush=True)
    sys.exit(1)


if not TOKEN:
    _fatal(
        "DISCORD_BOT_TOKEN env var is not set. Edit /etc/cosmic-bot.env on "
        "the VPS to set it, then `systemctl restart cosmic-bot`."
    )
if not ANTHROPIC_KEY:
    _fatal("ANTHROPIC_API_KEY env var is not set.")
if not SUPPORT_CHANNEL_ID:
    print(
        "[discord_bot] WARNING: DISCORD_SUPPORT_CHANNEL_ID not set -- "
        "will only respond to @mentions, not to messages in any specific channel.",
        flush=True,
    )

print(f"[discord_bot] starting v{__version__}", flush=True)
print(f"[discord_bot]   support channel id : {SUPPORT_CHANNEL_ID or '(not set)'}", flush=True)
print(f"[discord_bot]   guild id           : {GUILD_ID or '(not set)'}", flush=True)
print(f"[discord_bot]   reply to DMs       : {REPLY_TO_DMS}", flush=True)
print(f"[discord_bot]   log file           : {LOG_FILE_PATH or '(disk persistence off)'}", flush=True)
print(f"[discord_bot]   proxy              : {PROXY_HOST_DISPLAY}", flush=True)
print(
    f"[discord_bot]   log API            : "
    f"{LOG_API_BIND}:{LOG_API_PORT} (auth: {'enabled' if LOG_API_SECRET else 'DISABLED -- API will not start'})",
    flush=True,
)


# ─────────────────────────────────────────────────────────────────────
# Cross-process-safe append to the shared JSONL log
# ─────────────────────────────────────────────────────────────────────
# The web portal uses threading.Lock for its own appends. That guards
# *intra-process* races (multiple Streamlit threads handling concurrent
# requests), but it does NOT protect against a second process (this bot)
# writing to the same file. fcntl.flock() does -- it's a kernel-level
# advisory lock that both processes should honour.
#
# Trade-off: the portal's existing _append_log_to_disk doesn't currently
# use fcntl, so there's still a small window where a portal append and a
# bot append could interleave. In practice the portal's threading.Lock
# serialises writes within its own process, and the bot's fcntl.flock
# locks the file for its own write -- so the worst case is one corrupted
# line if both flush in the same millisecond. _load_log_from_disk
# already handles JSONDecodeError by skipping the bad line and warning,
# so a corrupted line never crashes the portal. Acceptable for v1; a
# future bump can extract a shared cb_log.py.
def _append_log_to_disk_locked(row):
    """Append `row` (a dict) as one JSON line to the shared log file.
    Cross-process-safe via fcntl.flock. No-op if the disk isn't mounted."""
    if LOG_FILE_PATH is None:
        return
    try:
        # Lazy import: fcntl is Linux/Mac only. Render is Linux so this is fine.
        import fcntl
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            finally:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
    except Exception as e:
        print(f"[discord_bot] WARNING: log append failed: {e}", flush=True)


def log_discord_conversation(session_id, product, user_msg, ai_response, user_tag=""):
    """Write one row to the shared support log with Source='discord'.
    Schema matches support_portal_v2.py's log_conversation() exactly."""
    now = datetime.now()
    row = {
        "Date": now.strftime("%d %b %Y"),
        "Time": now.strftime("%H:%M"),
        "Session ID": session_id,
        "Source": "discord",
        "Product": product,
        "Customer Message": user_msg,
        "AI Response": ai_response,
        "Feedback": "",
        "Feedback Note": "",
        "Image Thumbnails": "",
        # Repurpose the Client IP column to store the Discord user tag for
        # forensics. Keeps the schema rectangular for the admin CSV export.
        "Client IP": user_tag,
    }
    _append_log_to_disk_locked(row)


# ─────────────────────────────────────────────────────────────────────
# v1.1.0: Read-only log API
# ─────────────────────────────────────────────────────────────────────
# A small aiohttp web app that exposes the bot's log file to the
# Streamlit portal over HTTP. Runs in the same asyncio event loop as
# the Discord client.
#
# This module-level definition only declares the handlers. The aiohttp
# AppRunner / TCPSite are started inside _run_bot_async() and torn
# down in its finally block, so the API's lifetime is tied to the
# bot's. The retry loop in __main__ rebuilds both on each retry,
# which is fine -- aiohttp.web.Application is stateless from our
# perspective.
import hmac as _hmac  # for constant-time secret comparison


def _read_recent_log_lines(limit):
    """Synchronously read the last `limit` valid JSON-line rows from the
    log file. Called from asyncio.to_thread inside the API handler so
    we don't block the event loop on disk I/O.

    Coordinates with _append_log_to_disk_locked via fcntl: the writer
    holds LOCK_EX while appending, and we hold LOCK_SH while reading,
    so a read won't catch a half-written line and a write won't block
    on long reads. If fcntl is unavailable (non-Linux dev env) we fall
    back to lock-free reads -- the JSONDecodeError-skip path in the
    parser already tolerates a torn last line.
    """
    if LOG_FILE_PATH is None:
        return []
    if not os.path.exists(LOG_FILE_PATH):
        return []
    try:
        import fcntl
        _has_fcntl = True
    except ImportError:
        _has_fcntl = False
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            if _has_fcntl:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                except Exception:
                    # Lock failed -- proceed unlocked. Worst case is a
                    # torn last line which the parser will skip.
                    pass
            try:
                lines = f.readlines()
            finally:
                if _has_fcntl:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except Exception:
                        pass
    except Exception as e:
        print(f"[discord_bot] log API: read failed: {e}", flush=True)
        return []
    rows = []
    for line in lines[-limit:]:
        s = line.strip()
        if not s:
            continue
        try:
            rows.append(json.loads(s))
        except json.JSONDecodeError:
            continue
    return rows


async def _api_handle_log_recent(request):
    """GET /log/recent?limit=N -- return the last N rows as JSON.
    Auth: Authorization: Bearer <LOG_API_SECRET>. Constant-time compare."""
    expected = f"Bearer {LOG_API_SECRET}" if LOG_API_SECRET else ""
    provided = request.headers.get("Authorization", "")
    if not expected or not _hmac.compare_digest(provided, expected):
        return web.json_response({"error": "unauthorized"}, status=401)
    try:
        limit = int(request.query.get("limit", "1000"))
    except (TypeError, ValueError):
        limit = 1000
    limit = max(1, min(limit, 10000))
    try:
        rows = await asyncio.to_thread(_read_recent_log_lines, limit)
    except Exception as e:
        print(f"[discord_bot] log API: handler crashed: {e}", flush=True)
        return web.json_response({"error": "internal"}, status=500)
    return web.json_response({
        "rows": rows,
        "count": len(rows),
        "version": __version__,
    })


async def _api_handle_health(request):
    """GET /health -- liveness probe. No auth required so monitoring
    tools can ping it without sharing the secret. Returns minimal info
    to avoid leaking anything sensitive."""
    return web.json_response({
        "ok": True,
        "version": __version__,
        "log_api_enabled": bool(LOG_API_SECRET),
    })


async def _start_log_api_server():
    """Build and start the aiohttp web app for the log API. Returns the
    AppRunner so the caller can clean it up on shutdown. Returns None
    if the API is disabled (no secret configured) or if the bind fails
    -- in either case the bot continues running without the API rather
    than crashing the Discord client."""
    if not LOG_API_SECRET:
        print(
            "[discord_bot] log API disabled (LOG_API_SECRET not set)",
            flush=True,
        )
        return None
    try:
        app = web.Application()
        app.router.add_get("/log/recent", _api_handle_log_recent)
        app.router.add_get("/health", _api_handle_health)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, LOG_API_BIND, LOG_API_PORT)
        await site.start()
        print(
            f"[discord_bot] log API listening on http://{LOG_API_BIND}:{LOG_API_PORT}",
            flush=True,
        )
        return runner
    except Exception as e:
        # Don't let an API bind failure kill the Discord bot. The bot
        # is the priority; the API is an add-on.
        print(
            f"[discord_bot] WARNING: log API failed to start ({e}); "
            f"Discord bot will continue without it.",
            flush=True,
        )
        return None


# ─────────────────────────────────────────────────────────────────────
# Anthropic client
# ─────────────────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


def _build_api_messages_from_chain(chain, bot_user_id):
    """Given a chronological list of Discord Messages (oldest first),
    convert into the {role, content} format Anthropic expects.

    - Bot messages -> role="assistant"
    - Anyone else  -> role="user"
    - Strips bot @mention from the text so the AI doesn't see it.
    - Drops empty messages.
    """
    api_messages = []
    for m in chain:
        text = (m.content or "").strip()
        # Strip the bot @mention. Discord uses both <@ID> and <@!ID> formats
        # depending on whether it was a nickname mention.
        text = text.replace(f"<@{bot_user_id}>", "").replace(f"<@!{bot_user_id}>", "").strip()
        if not text:
            continue
        role = "assistant" if m.author.id == bot_user_id else "user"
        api_messages.append({"role": role, "content": text})
    # Anthropic requires the conversation to start with a user message.
    # If the bot somehow ended up first (it shouldn't, but be defensive),
    # drop leading assistant messages.
    while api_messages and api_messages[0]["role"] != "user":
        api_messages.pop(0)
    return api_messages


async def _walk_reply_chain(message, bot_user_id):
    """Walk up the Discord reply chain to reconstruct conversation context.
    Returns a list of Messages in chronological order (oldest first), with
    the triggering `message` last. Caps at MAX_REPLY_DEPTH ancestors."""
    chain = [message]
    current = message
    depth = 0
    while depth < MAX_REPLY_DEPTH and current.reference is not None:
        ref = current.reference
        # ref.resolved is sometimes pre-populated by discord.py; if not, fetch.
        parent = None
        if isinstance(ref.resolved, discord.Message):
            parent = ref.resolved
        elif ref.message_id:
            try:
                parent = await message.channel.fetch_message(ref.message_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                # Parent deleted or inaccessible -- stop walking.
                break
        if parent is None:
            break
        chain.append(parent)
        current = parent
        depth += 1
    chain.reverse()  # oldest first
    return chain


def _split_for_discord(text):
    """Split a long string into chunks that each fit in one Discord message
    (<=DISCORD_MSG_LIMIT chars). Prefer splitting on \\n\\n, then \\n, then
    hard-cut. Never returns an empty list, and never returns an empty
    string in the list -- Discord 400s on empty messages.

    v1.0.1: skip empty chunks produced when the cut lands inside a run of
    whitespace and rstrip() empties the slice. Fall back to a single
    "(no response)" placeholder if every chunk turns out to be empty.
    """
    if not text:
        return ["(no response)"]
    if len(text) <= DISCORD_MSG_LIMIT:
        return [text]

    chunks = []
    remaining = text
    while len(remaining) > DISCORD_MSG_LIMIT:
        # Try to split on a paragraph break first.
        cut = remaining.rfind("\n\n", 0, DISCORD_MSG_LIMIT)
        if cut < DISCORD_MSG_LIMIT // 2:
            # No paragraph break in the second half -- try a single newline.
            cut = remaining.rfind("\n", 0, DISCORD_MSG_LIMIT)
        if cut < DISCORD_MSG_LIMIT // 2:
            # Still no good break -- hard-cut at the limit.
            cut = DISCORD_MSG_LIMIT
        candidate = remaining[:cut].rstrip()
        if candidate:
            chunks.append(candidate)
        remaining = remaining[cut:].lstrip()
    if remaining:
        chunks.append(remaining)
    # Defensive: if every slice rstrip'd to empty (pathological all-whitespace
    # input larger than DISCORD_MSG_LIMIT), return a placeholder so the
    # caller has something non-empty to send.
    if not chunks:
        return ["(no response)"]
    return chunks


def _should_respond(message, bot_user_id):
    """Decide whether this bot should reply to this message.

    Rules (in order):
      1. Skip our own messages (no infinite loops).
      2. Skip other bots (DM bot wars are not a thing we want to start).
      3. DMs: respond iff REPLY_TO_DMS is true.
      4. Guild messages: respond iff @mentioned OR in the support channel.
      5. Else: ignore.
    """
    if message.author.id == bot_user_id:
        return False
    if message.author.bot:
        return False
    # DM check. discord.DMChannel covers 1:1 DMs; group DMs are deprecated
    # for bots so we don't worry about them.
    if isinstance(message.channel, discord.DMChannel):
        return REPLY_TO_DMS
    # Guild message.
    is_mentioned = any(u.id == bot_user_id for u in message.mentions)
    in_support_channel = (
        SUPPORT_CHANNEL_ID and message.channel.id == SUPPORT_CHANNEL_ID
    )
    return is_mentioned or in_support_channel


# ─────────────────────────────────────────────────────────────────────
# Discord client + event handlers
# ─────────────────────────────────────────────────────────────────────
# v1.0.2: bot creation was extracted into a function so the startup-retry
# loop in __main__ could rebuild the Client on each retry (discord.py's
# Client can't be reused once bot.run() returns/raises).
#
# v1.0.5: bot creation moved INSIDE an async function (`_run_bot_async`)
# rather than the previous synchronous `_build_bot`. Reason: the SOCKS
# code path constructs an aiohttp_socks.ProxyConnector, whose parent
# class (aiohttp.TCPConnector) calls asyncio.get_running_loop() in its
# __init__. That raises `RuntimeError: no running event loop` when
# called outside an asyncio context. v1.0.4 hit this on Render at
# module-load time; v1.0.5 defers the construction until inside
# asyncio.run(), where the loop exists.
#
# The on_ready / on_message coroutines stay at module level (they
# reference `bot` via global lookup at call time, so they always see
# whichever instance is currently bound to that name) and are
# registered onto the fresh Client via bot.event() inside
# _run_bot_async.
intents = discord.Intents.default()
intents.message_content = True  # Required to read message text. Already
                                # enabled in the Discord Developer Portal.

bot = None  # Set by _run_bot_async() on the first iteration of the
            # retry loop in __main__. Declared here so the event handlers'
            # module-global `bot` references resolve at function-definition
            # time (Python doesn't evaluate the lookup until call time, so
            # leaving it None pre-connection is fine).


async def _run_bot_async():
    """Build a fresh discord.Client + (optional) connector inside the
    running asyncio event loop, register handlers, and run the bot until
    disconnect or error. Caller is responsible for the retry loop.

    Why async: aiohttp_socks.ProxyConnector calls
    asyncio.get_running_loop() in its constructor, so it must be built
    inside a coroutine. Doing all of bot construction here keeps the
    SOCKS path and HTTP path symmetric.

    Re-builds `bot` (module-level) each call so the v1.0.2 retry-on-
    HTTPException pattern still works -- discord.py's Client cannot be
    reused after its session closes, and aiohttp_socks.ProxyConnector
    cannot be reused after its session closes either, so each retry
    gets entirely fresh objects.
    """
    global bot
    client_kwargs = {"intents": intents}
    if PROXY_URL_FOR_SOCKS is not None:
        # SOCKS path. Connector built inside the loop -- this is the
        # specific bug v1.0.5 fixes vs v1.0.4.
        client_kwargs["connector"] = _SocksProxyConnector.from_url(PROXY_URL_FOR_SOCKS)
    elif PROXY_NETLOC:
        # HTTP/HTTPS path. No connector needed; aiohttp uses default.
        client_kwargs["proxy"] = PROXY_NETLOC
        if PROXY_AUTH is not None:
            client_kwargs["proxy_auth"] = PROXY_AUTH
    bot = discord.Client(**client_kwargs)
    bot.event(on_ready)
    bot.event(on_message)
    # v1.1.0: start the read-only log API alongside the Discord bot.
    # Returns None if disabled (no LOG_API_SECRET) or if bind fails;
    # in either case the Discord bot still runs. We tear down the
    # API runner in the finally block below so a retry rebuild gets
    # a clean port.
    api_runner = await _start_log_api_server()
    try:
        # discord.Client is an async context manager that handles session
        # setup/teardown. bot.start() does login + gateway connection.
        # Together this is exactly what bot.run() does internally, minus
        # the wrapping asyncio.run() which our caller already provides.
        async with bot:
            await bot.start(TOKEN)
    finally:
        if api_runner is not None:
            try:
                await api_runner.cleanup()
            except Exception as e:
                # Cleanup failures shouldn't mask the real exit reason.
                print(f"[discord_bot] log API cleanup failed: {e}", flush=True)


async def on_ready():
    print(f"[discord_bot] connected as {bot.user} (id={bot.user.id})", flush=True)
    if GUILD_ID:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            print(f"[discord_bot] in guild: {guild.name}", flush=True)


async def on_message(message: discord.Message):
    bot_user_id = bot.user.id if bot.user else 0
    if not _should_respond(message, bot_user_id):
        return

    # Walk reply chain for conversation context, then build API messages.
    try:
        chain = await _walk_reply_chain(message, bot_user_id)
    except Exception as e:
        print(f"[discord_bot] reply chain walk failed: {e}", flush=True)
        chain = [message]

    api_messages = _build_api_messages_from_chain(chain, bot_user_id)
    if not api_messages:
        # Nothing useful to send (e.g. user just @mentioned with no text).
        try:
            await message.reply(
                "Hi! I'm Cosmic Byte's AI support bot. Ask me about any of our "
                "products and I'll do my best to help. For example: "
                "*\"How do I pair my Lumora controller with iPhone?\"*",
                mention_author=False,
            )
        except discord.HTTPException as e:
            print(f"[discord_bot] greeting send failed: {e}", flush=True)
        return

    # Pull the user's most recent message text for product detection
    # and for logging.
    user_question = api_messages[-1]["content"] if api_messages else ""

    # Detect product(s) the user is asking about. Same logic as the web
    # portal's "All Products" branch (since Discord has no page-title
    # context). detect_products_from_message returns:
    #   (matched_list, is_recommendation_query)
    try:
        matched, is_rec = detect_products_from_message(api_messages)
    except Exception as e:
        print(f"[discord_bot] product detection failed: {e}", flush=True)
        matched, is_rec = [], False

    if matched:
        knowledge = "\n\n".join(
            f"=== {p} ===\n{KNOWLEDGE_BASE[p]}" for p in matched if p in KNOWLEDGE_BASE
        )
        product_label = matched[0] if len(matched) == 1 else f"Multi: {', '.join(matched)}"
    elif is_rec:
        knowledge = CATALOGUE_ALL
        product_label = "All Products"
    else:
        knowledge = ""
        product_label = "All Products"

    # Wrap the latest user message with PRODUCT SELECTED + KB framing.
    # Mirrors the web portal's call site exactly (minus the page-buy-link
    # block, which the web portal injects when a specific product is
    # selected via dropdown -- not applicable here).
    last = api_messages[-1]
    original_text = last["content"]
    if knowledge:
        last["content"] = (
            f"PRODUCT(S) DETECTED: {product_label}\n\n"
            f"KNOWLEDGE BASE (product manuals):\n{knowledge}\n\n"
            f"CUSTOMER MESSAGE: {original_text}"
        )
    else:
        # No KB hit and not a recommendation. Tell the model to ask which
        # product, instead of guessing -- matches the web portal's behaviour
        # in the equivalent branch.
        last["content"] = (
            f"CUSTOMER MESSAGE: {original_text}\n\n"
            f"(NOTE: We couldn't auto-detect which Cosmic Byte product they're "
            f"asking about. If their question is product-specific, ask them to "
            f"clarify which model. If it's a general question, answer normally.)"
        )

    # Third-party brand handling: same logic as the web portal.
    #
    # v1.2.0: build the full system text as a string first (same logic
    # as before), then wrap it in a single cache_control text block so
    # Anthropic caches the system prompt across calls. Cache reads cost
    # 10% of base input -- 90% savings on the bulk of input tokens.
    # Cache write costs 1.25x base, breaking even after ~1.25 reuses
    # within the 5-minute TTL. Bot traffic is typically multi-customer
    # within short windows (Discord support channel), which is exactly
    # the pattern caching is designed for.
    third_party = detect_third_party_brand(user_question)
    system_text = SYSTEM_PROMPT + "\n\nPRODUCT KNOWLEDGE:\n" + knowledge

    api_kwargs = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=api_messages,
    )
    if third_party:
        brand_manual = THIRD_PARTY_BRAND_MANUALS.get(third_party)
        if brand_manual:
            system_text += (
                f"\n\n=== THIRD-PARTY BRAND MANUAL: {third_party} ===\n"
                f"The customer is asking about {third_party}, a third-party brand "
                f"sold on thecosmicbyte.com. Use the manual below as your "
                f"AUTHORITATIVE source for what CB sells, compatibility, variants, "
                f"pricing ranges and policies. Do NOT contradict it with outside "
                f"info. For questions outside this manual's scope, refer to the "
                f"brand site URL listed in the manual or to the CB product page. "
                f"Always link back to thecosmicbyte.com for purchasing.\n\n"
                f"{brand_manual}"
            )
        else:
            api_kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]
            system_text += (
                f"\n\nThe customer is asking about {third_party} -- a third-party "
                f"brand sold on thecosmicbyte.com. Use web search to find accurate "
                f"specs, compatibility and support info. Always link back to "
                f"thecosmicbyte.com for purchasing."
            )

    # v1.2.0: wrap the assembled system text in a single cached text
    # block. Anthropic caches everything up to and including this block
    # (tools + system + the implicit prefix), so the first call about
    # each (product, brand) combo writes the cache and every subsequent
    # call within the 5-minute TTL hits the cache.
    #
    # Haiku 4.5's cache minimum is 4096 tokens. Our system_text
    # (SYSTEM_PROMPT + product manual slice + optional brand manual)
    # reliably exceeds this for any production query.
    #
    # Output quality is unaffected: the model still processes the full
    # input identically, the cache only reuses the pre-computed KV
    # cache for the cached prefix.
    api_kwargs["system"] = [
        {
            "type": "text",
            "text": system_text,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    # Show typing indicator while we wait on the API. async with handles the
    # stop-typing correctly even if an exception is raised inside.
    try:
        async with message.channel.typing():
            # The Anthropic SDK is sync; run it in a worker thread so we don't
            # block the event loop. asyncio.to_thread is the standard pattern
            # for this on Python 3.9+.
            try:
                response = await asyncio.to_thread(client.messages.create, **api_kwargs)
            except Exception as e:
                print(f"[discord_bot] Anthropic API call failed: {e}", flush=True)
                await message.reply(
                    "Sorry — I hit an error reaching our AI service. Please try "
                    "again in a minute, or email us at cc@thecosmicbyte.com.",
                    mention_author=False,
                )
                return

            # Extract text from the response. Anthropic returns a list of
            # content blocks; tool_use blocks have no .text attr, so guard.
            answer = ""
            for block in response.content:
                if hasattr(block, "text"):
                    answer += block.text
            if not answer:
                answer = (
                    "I wasn't able to get a response. Please try again, or "
                    "email us at cc@thecosmicbyte.com."
                )

        # Send the response. Split into chunks if too long. First chunk is a
        # reply (preserves the Discord conversation thread for context next
        # turn); follow-on chunks are plain channel messages.
        chunks = _split_for_discord(answer)
        try:
            await message.reply(chunks[0], mention_author=False)
            for c in chunks[1:]:
                await message.channel.send(c)
        except discord.HTTPException as e:
            print(f"[discord_bot] message send failed: {e}", flush=True)

        # Log to the shared support log. Use the message ID as the session ID
        # so the admin dashboard can group related Discord messages by
        # eyeballing the prefix; per-user state isn't tracked.
        try:
            user_tag = f"{message.author} (id={message.author.id})"
            session_id = f"discord-{message.id}"
            log_discord_conversation(
                session_id=session_id,
                product=product_label,
                user_msg=user_question,
                ai_response=answer,
                user_tag=user_tag,
            )
        except Exception as e:
            print(f"[discord_bot] log write failed: {e}", flush=True)
    except Exception as e:
        # Last-resort guard so a single bad message doesn't crash the bot.
        print(f"[discord_bot] unhandled error in on_message: {e}", flush=True)


# Module-level: no eager bot construction. _run_bot_async builds the
# Client (and its connector, when SOCKS) inside the running asyncio
# event loop on each retry. Until then `bot` is None -- the event
# handlers reference it by global lookup at call time, so they only
# need it bound by the time discord.py actually fires events.


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import time
    import asyncio

    # v1.0.2: retry on HTTPException at startup so a Discord rate-limit
    # (most commonly a 429 on GET /users/@me from a noisy shared egress IP)
    # doesn't permanently kill the bot. Each redeploy is a fresh
    # /users/@me hit; previously a single rate-limited startup would
    # FATAL-exit the process, leaving no way to recover without manual
    # redeploy -- which often hit the same rate limit again. The retry
    # converts "permanently dead" into "offline for a while, then
    # auto-recovers when Discord lifts the rate limit."
    #
    # v1.0.5: also catch aiohttp.ClientError and asyncio.TimeoutError as
    # retryable. Proxy hiccups, transient gateway disconnects during
    # login, and SOCKS server momentary unreachability all manifest as
    # one of those rather than as discord.HTTPException, and we'd
    # rather retry them than fatal-exit.
    #
    # Backoff: 60s, 2m, 4m, 8m, 16m, 30m (capped). 12 attempts total.
    # Wall-clock budget ~3.7 hours, which matches the typical duration of
    # a Discord 40062 "scaled" rate limit. If we're still rate-limited
    # after the full budget, the IP is likely persistently flagged --
    # exit with an operator-actionable message so the runner (Render /
    # systemd) can decide what to do.
    MAX_STARTUP_RETRIES = 12
    BASE_BACKOFF_S = 60
    MAX_BACKOFF_S = 30 * 60

    for attempt in range(1, MAX_STARTUP_RETRIES + 1):
        try:
            # asyncio.run sets up a fresh event loop, runs the coroutine
            # to completion, and tears the loop down. Each retry gets a
            # completely fresh asyncio context -- which is what we want,
            # because both discord.Client and aiohttp_socks.ProxyConnector
            # are tied to the loop they were created in and can't outlive
            # it.
            asyncio.run(_run_bot_async())
            # Coroutine returned cleanly (graceful shutdown, e.g. SIGTERM
            # that discord.py handled). Anything bad raises.
            print("[discord_bot] _run_bot_async returned -- shutting down cleanly.", flush=True)
            break
        except discord.LoginFailure:
            # Token problem -- retrying won't help, this needs a human.
            _fatal(
                "Discord login failed -- token is invalid or expired. "
                "Regenerate it in the Developer Portal and update the env var."
            )
        except (
            discord.HTTPException,    # Discord-level errors incl. 429s
            aiohttp.ClientError,      # network/proxy errors (e.g. ServerDisconnectedError)
            asyncio.TimeoutError,     # network timeouts during login or gateway connect
            ConnectionError,          # OS-level connection refused, etc.
        ) as e:
            # Most common case: 429 rate-limited (sometimes with error
            # code 40062, "Service resource is being rate limited"), or
            # an aiohttp ServerDisconnectedError from a flaky proxy.
            # discord.py's internal retry-after backoff gives up after a
            # few attempts and raises HTTPException here; we catch it
            # and retry the whole runner with our own (longer) backoff.
            status = getattr(e, "status", "?")
            err_type = type(e).__name__
            if attempt >= MAX_STARTUP_RETRIES:
                _fatal(
                    f"bot crashed after {MAX_STARTUP_RETRIES} startup retries "
                    f"(last error: {err_type} status={status} {e}). The VPS "
                    f"egress IP ({os.environ.get('HOSTNAME', 'unknown host')}) "
                    f"may be persistently rate-limited by Discord -- check "
                    f"`journalctl -u cosmic-bot` for the full error history. "
                    f"If the rate limit looks permanent, options are: wait "
                    f"longer (Discord 40062 flags can take 24h+ to lift), "
                    f"contact Discord support with the bot's application ID, "
                    f"or migrate the bot to a fresh VPS with a different IPv4."
                )
            backoff = min(BASE_BACKOFF_S * (2 ** (attempt - 1)), MAX_BACKOFF_S)
            print(
                f"[discord_bot] {err_type} on startup "
                f"(attempt {attempt}/{MAX_STARTUP_RETRIES}, status={status}): {e}",
                flush=True,
            )
            print(
                f"[discord_bot] Sleeping {backoff}s before next attempt. "
                f"This is usually a Discord per-IP rate limit or a transient "
                f"network hiccup; the bot will come back online automatically "
                f"once the window clears.",
                flush=True,
            )
            time.sleep(backoff)
        except Exception as e:
            # Anything else (OOM, programmer error, etc) -- not a retry case.
            _fatal(f"bot crashed: {e}")
