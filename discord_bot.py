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

CHANGELOG
---------
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

__version__ = "1.0.0"

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

import discord
import anthropic

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
# Startup validation
# ─────────────────────────────────────────────────────────────────────
def _fatal(msg):
    print(f"[discord_bot] FATAL: {msg}", flush=True)
    sys.exit(1)


if not TOKEN:
    _fatal("DISCORD_BOT_TOKEN env var is not set. Set it in Render -> Environment.")
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
    hard-cut. Never returns an empty list."""
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
        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        chunks.append(remaining)
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
intents = discord.Intents.default()
intents.message_content = True  # Required to read message text. Already
                                # enabled in the Discord Developer Portal.
bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    print(f"[discord_bot] connected as {bot.user} (id={bot.user.id})", flush=True)
    if GUILD_ID:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            print(f"[discord_bot] in guild: {guild.name}", flush=True)


@bot.event
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
    third_party = detect_third_party_brand(user_question)
    api_kwargs = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT + "\n\nPRODUCT KNOWLEDGE:\n" + knowledge,
        messages=api_messages,
    )
    if third_party:
        brand_manual = THIRD_PARTY_BRAND_MANUALS.get(third_party)
        if brand_manual:
            api_kwargs["system"] += (
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
            api_kwargs["system"] += (
                f"\n\nThe customer is asking about {third_party} -- a third-party "
                f"brand sold on thecosmicbyte.com. Use web search to find accurate "
                f"specs, compatibility and support info. Always link back to "
                f"thecosmicbyte.com for purchasing."
            )

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


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        _fatal(
            "Discord login failed -- token is invalid or expired. "
            "Regenerate it in the Developer Portal and update the env var."
        )
    except Exception as e:
        _fatal(f"bot crashed: {e}")
