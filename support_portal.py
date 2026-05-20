"""
==============================================================================
COSMIC BYTE SUPPORT PORTAL  —  app version: 2.29.0
==============================================================================

What this file is:
  - Streamlit chat UI for customer support (deployed at the company's URL)
  - Claude Haiku 4.5 backend with web search enabled for third-party brands
  - Per-product knowledge base loaded into the system prompt based on product
    detection (page title -> product name -> manual)
  - Logging, feedback capture, admin dashboard

Key dicts (search for these to navigate):
  - PRODUCT_URLS           -> buy links per product
  - PRODUCT_MANUALS        -> full per-product manual blob (the big one)
  - THIRD_PARTY_BRANDS     -> keyword -> brand-name (powers web-search trigger)
  - THIRD_PARTY_BRAND_URLS -> brand -> brand-site URL
  - THIRD_PARTY_BRAND_MANUALS -> brand -> manual blob. Wired into the
                                  system prompt at the API call site: when
                                  detect_third_party_brand matches and a
                                  manual exists, it's injected directly
                                  (web search is skipped). For brands with
                                  no manual on file, web search is used as
                                  fallback. Keys are bare brand names
                                  matching detect_third_party_brand output
                                  (Gateron, Kailh, Outemu, Moza, Cammus).

------------------------------------------------------------------------------
DEPLOYMENT (current as of v2.24.1, 2026-05-09)
------------------------------------------------------------------------------
This file runs on Render. The Discord bot (discord_bot.py) runs on a
SEPARATE Hetzner VPS as of 2026-05-09 and writes its OWN log file there;
the portal fetches new Discord conversations from the bot's HTTP API.

Where it runs:
  Host          : Render web service
  Primary URL   : https://ai.thecosmicbyte.com
  Process       : Streamlit on Render's $PORT, launched by run.py.
                  run.py also patches Streamlit's X-Frame-Options for
                  embedding and injects OG meta tags. As of 2026-05-09
                  it no longer launches the Discord bot subprocess --
                  the bot is on the VPS.
  Persistent disk: /var/data on Render (CB_DATA_DIR env var, defaults
                  here). Holds support_log.jsonl + chat_history.json
                  + digest_state.json. Survives restarts/redeploys.

Required env vars on Render:
  ADMIN_PASSWORD       -- admin dashboard login
  ANTHROPIC_API_KEY    -- AI responses on the web side
  GMAIL_APP_PASSWORD   -- daily digest email auth
  GMAIL_SENDER         -- daily digest email from-address
  CB_DATA_DIR          -- /var/data (persistent disk mount path)
  BOT_API_URL          -- e.g. http://5.223.52.60:8080
                          (the VPS bot's log API URL).
                          If unset, portal falls back to local-only
                          and silently misses new Discord rows.
  BOT_API_SECRET       -- shared secret matching VPS env var
                          LOG_API_SECRET. Sent as Bearer header.

Optional env vars (have sane defaults):
  BOT_API_TIMEOUT_S    -- 10 (HTTP timeout for bot API fetch)
  BOT_API_CACHE_TTL_S  -- 30 (how long portal caches a fetch result)
  BOT_API_FETCH_LIMIT  -- 1000 (max rows per fetch)

Vars that USED to be required but no longer are (delete from Render
if still present):
  DISCORD_BOT_TOKEN          -- bot moved to VPS
  DISCORD_GUILD_ID           -- bot moved to VPS
  DISCORD_SUPPORT_CHANNEL_ID -- bot moved to VPS
  DISCORD_BOT_REPLY_TO_DMS   -- bot moved to VPS
  QUOTAGUARDSTATIC_URL       -- proxy not needed; QuotaGuard cancelled

How Ronak deploys changes to this file:
  1. Push to GitHub main branch.
  2. Render auto-deploys (~3-5 minutes).
  3. Watch Render dashboard's Logs tab for build status. Look for
     "Build successful" -> "Your service is live". The startup
     banner ("[support_portal_v2] starting up - app version X.Y.Z",
     "bot API merge enabled -> ..." etc.) appears the first time
     someone visits the page after deploy, NOT during the deploy
     itself, because of stdout buffering across os.execvp.

There is no manual deploy. Everything goes through GitHub -> Render.

How Ronak deploys env-var changes:
  1. Render dashboard -> service -> Environment.
  2. Add/edit/delete the variable.
  3. Save Changes -- Render auto-redeploys with the new env.

Companion service:
  discord_bot.py runs on a Hetzner VPS at 5.223.52.60 (NOT here).
  See discord_bot.py's DEPLOYMENT section for the bot side. As of
  v2.24.0 the portal fetches new Discord conversation rows from the
  bot's GET /log/recent endpoint (Bearer-auth, BOT_API_SECRET) and
  merges them with the local log for admin dashboard / digest views.

------------------------------------------------------------------------------
ASSISTANT EDIT PROTOCOL  (READ THIS BEFORE EDITING THE FILE)
------------------------------------------------------------------------------
The user does NOT edit this file manually -- only the assistant edits it.
Therefore every edit you make is the only record of what changed. If you skip
the changelog, the change is lost from history.

PRE-EDIT CHECKLIST (run through these before saving):
  [ ] 1. Confirm you can ast.parse the file as-is (input is valid Python).
  [ ] 2. Read the latest 1-2 changelog entries to see what was just done.
  [ ] 3. Decide your version bump:
            X (major)  - rewrite, breaking change, restructure
            Y (minor)  - new section, new product, new feature
            Z (patch)  - bug fix, wording tweak, small addition
  [ ] 4. Make your code edits.

POST-EDIT CHECKLIST (run through these before delivering the file):
  [ ] 1. Bump __version__ on the line below this docstring to the new vX.Y.Z.
  [ ] 2. Update "app version: X.Y.Z" on the title line of this docstring.
  [ ] 3. Add a new entry at the TOP of the changelog with today's actual date
         (not a placeholder), the new version, "-- Claude", and 1-N bullets
         describing what changed and why.
  [ ] 4. Run ast.parse again. If it fails, fix and re-run. Do not deliver a
         file that doesn't parse.
  [ ] 5. When delivering the file to the user, mention the new version
         number explicitly so they know it's been logged.

NOTES ON THE FORMAT:
  - The docstring uses triple-double-quotes. Do NOT type a literal sequence
    of three double-quote characters anywhere inside this docstring -- it
    will close the docstring early and break the file. If you need to refer
    to triple-quoted strings, use the words "triple-quote" or "the closing
    quotes" in prose.
  - If the user appears to have made manual edits between sessions despite
    saying they don't, add a "(undated, between sessions)" entry above
    yours to capture whatever you can infer from a diff.

CHANGELOG FORMAT:
  vX.Y.Z (YYYY-MM-DD) -- author
       - bullet describing change

------------------------------------------------------------------------------
CHANGELOG (newest entry first)
------------------------------------------------------------------------------

v2.35.0 (2026-05-20) -- Claude
  - DARK variant of the v2.34.0
    brand reskin. Operator chose
    dark over light for mobile
    readability (OLED, glare, eye
    strain, battery). Kept every
    brand upgrade -- Bricolage /
    Sora / JetBrains Mono fonts,
    orange #FF9E1B accent, rounded
    PILL buttons, soft-shadow cards
    -- but on a dark blue-charcoal
    canvas (#0d1319) with dark
    surfaces (#18212b) and light
    text (#eef1f5 / #c4c9d4). The
    website footer is already dark
    #101820, so this stays on-brand.
  - Text-on-orange (buttons, user
    bubble, badges, live pill) uses
    a fixed dark --on-accent #101820
    so it never goes low-contrast
    when --cb-ink flipped to light.
  - Button hover brightens to
    #ffb347 (was darken-to-#cc7a14
    on light) keeping dark text.
  - Disclaimer box -> dark soft-
    orange alert; brought back faint
    static orange atmosphere glows.
  - Still a pure CSS reskin: no
    logic / HTML / class names
    changed; v2.34.0 light theme was
    never deployed.
  NOTE: cannot render live Streamlit
  here -- visual review after deploy.

v2.34.0 (2026-05-20) -- Claude
  - Y-bump: full VISUAL RESKIN of
    the portal to match the new
    Cosmic Byte LIGHT website brand
    (cb-brand-light.css). Pure CSS
    change -- NO logic, NO HTML
    structure, NO class names were
    altered, so all functionality
    (chat, product picker, photo
    upload, feedback, digest, admin
    OTP login from v2.32-2.33) is
    untouched.
  - Palette: dark #060606 canvas ->
    light #f7f8fa; near-black cards
    -> white #ffffff surfaces with
    1px #e1e4ea lines + soft shadow;
    ink #101820 text; brand orange
    #FF9E1B (was #FFB020).
  - Typography: Rajdhani/Inter ->
    Bricolage Grotesque (display) +
    Sora (body/UI) + JetBrains Mono
    (labels, badges, buttons).
  - Components: angular clip-path
    cut-corner buttons -> rounded
    PILL buttons (radius 100px) with
    hover lift + orange glow; inputs
    radius 8px with orange focus
    ring; chat bubbles on white;
    orange pill scrollbar; light
    cream alert/disclaimer box; the
    dark "gaming" glows replaced by
    a faint static warm atmosphere.
  - Legacy CSS var aliases kept
    (--orange,--bg,--s1,...) mapped
    to the new palette so any stray
    reference still resolves.
  - Inline dark-hex bits (CSV link,
    Raise-a-ticket badge, feedback /
    helper text, disclaimer, footer,
    version stamp) recoloured to the
    light brand by hand.
  NOTE: I cannot render live
  Streamlit here -- visual review
  needed after deploy.

v2.33.0 (2026-05-20) -- Claude
  - Y-bump: admin OTP emails now
    send via BREVO (the
    transactional email service
    already used by the Cosmic
    Byte website and the Reverse
    Pickup portal), with the
    existing Gmail SMTP path kept
    as an automatic fallback.
    Operator-requested — keeps all
    Cosmic Byte email on one
    service.

  Why:
    v2.32.0 delivered the admin
    OTP via Gmail SMTP (the path
    the daily digest already
    used). The operator asked to
    use Brevo instead, since the
    website and the pickup portal
    already run on Brevo.
    Consolidating onto one email
    service simplifies sender-
    domain verification,
    deliverability monitoring,
    and credentials management.

  Implementation:
    send_otp_email() rewritten to
    match the pickup portal's
    Brevo integration exactly
    (app/email_brevo.py
    send_login_code), via the
    Brevo transactional HTTP API:
      POST https://api.brevo.com/v3/smtp/email
      headers: api-key, content-type,
               accept
      json: {sender:{name,email},
             to:[{email}], subject,
             htmlContent, textContent}
      success = HTTP 200/201
    The OTP email is a small clean
    HTML body with the code shown
    prominently, plus a plain-text
    alternative.

  Fallback behaviour (resilience):
    * If BREVO_API_KEY is set -> send
      via Brevo.
    * If the Brevo call fails (non-
      2xx or exception) -> automatically
      fall through to Gmail SMTP.
    * If BREVO_API_KEY is NOT set ->
      go straight to Gmail SMTP (the
      v2.32.0 behaviour).
    This means the switch can never
    break OTP delivery: worst case it
    silently uses the already-working
    Gmail path. The operator gets Brevo
    the moment BREVO_API_KEY is present
    in the environment.

  Env vars (same names as the pickup
  portal, so the values can be reused
  verbatim):
    BREVO_API_KEY    -- Brevo API key.
                        If unset, OTP
                        falls back to
                        Gmail.
    BREVO_URL        -- endpoint
                        (default
                        https://api.brevo.com/v3/smtp/email)
    EMAIL_FROM       -- verified Brevo
                        sender (default
                        no-reply@thecosmicbyte.com)
    EMAIL_FROM_NAME  -- sender display
                        name (default
                        "Cosmic Byte Support")

  Operator action on deploy:
    Add BREVO_API_KEY to the support
    portal's Render environment (the
    same key the website / pickup
    portal use). EMAIL_FROM defaults
    to the already-verified
    no-reply@thecosmicbyte.com sender,
    so no further setup is needed. If
    BREVO_API_KEY is left unset, OTP
    keeps working via Gmail.

  Reused unchanged: the rate limiting,
  whitelist, OTP hashing, verify cap,
  and 8h session cookie from v2.32.0 /
  v2.32.1 are untouched — only the
  email transport changed.

------------------------------------------------------------------------------

v2.32.1 (2026-05-20) -- Claude
  - Z-bump: set the default admin
    OTP whitelist to the
    operator's address,
    ronak.gupta@thecosmicbyte.com
    (was the two support
    addresses). Now the email+OTP
    login (v2.32.0) works
    out-of-the-box on deploy with
    no Render env-var setup
    needed. Additional admins can
    still be authorised by setting
    ADMIN_EMAILS (comma-separated).

------------------------------------------------------------------------------

v2.32.0 (2026-05-20) -- Claude
  - Y-bump: replaced the single
    shared-password admin login
    with EMAIL + ONE-TIME-CODE
    (OTP) authentication, plus
    rate limiting to deter spam
    and bots. Operator-requested
    security hardening of the
    admin panel.

  Why:
    The admin panel was gated by
    a single shared password
    (ADMIN_PASSWORD). A shared
    password is a weak control:
    it can be guessed, shared,
    leaked, or reused, and there
    was no rate limiting on the
    login form, so it was open
    to automated guessing. The
    operator asked for email +
    OTP login with rate limiting.

  What the new flow does:
    1. Operator enters their
       admin email.
    2. If the email is on the
       whitelist, a 6-digit
       one-time code is emailed
       to them (via the existing
       Gmail SMTP path — no new
       email provider needed).
    3. Operator enters the code.
       On success they're logged
       in, and the existing 8h
       HMAC session cookie is
       set (so the
       stay-logged-in behaviour
       is unchanged).

  Security properties:
    * WHITELIST: only emails in
      the ADMIN_EMAILS env var
      can receive a code. A bot
      can't request a code to an
      address it controls.
    * EMAIL-ENUMERATION
      RESISTANCE: the form
      behaves identically for
      whitelisted and non-
      whitelisted emails (same
      messaging, same stage
      transition), so it never
      reveals which addresses
      are valid admins.
    * OTP HASHED AT REST: the
      code is stored as an HMAC
      (keyed by ADMIN_PASSWORD +
      email), never in
      plaintext. A leaked state
      file is useless.
    * SHORT TTL: codes expire
      after 10 minutes and are
      single-use (burned on
      successful verify).
    * VERIFY-ATTEMPT CAP: max 5
      wrong guesses before the
      code is invalidated —
      stops brute-forcing the
      6-digit space.
    * PER-EMAIL SEND LIMIT: max
      3 code requests per email
      per 15 minutes.
    * GLOBAL SEND LIMIT: max 20
      codes sent across all
      emails per 60 minutes
      (defence-in-depth against
      a flood even though the
      whitelist already caps
      targets).

  State storage:
    OTP + rate-limit state lives
    in admin_otp_state.json on
    the persistent disk
    (/var/data), using the same
    pattern + disk lock as the
    digest state. If no
    persistent disk is mounted,
    falls back to an in-memory
    cache_resource store (lost
    on restart, which is fine —
    OTPs and rate-limit windows
    are short-lived). State is
    pruned of expired entries on
    every load so the file stays
    small.

  New env vars:
    ADMIN_EMAILS
      Comma-separated whitelist
      of emails allowed to
      request an admin OTP.
      Defaults to
      "cc@thecosmicbyte.com,
      thecosmicbyte2017@gmail.com"
      if unset, so the panel
      isn't accidentally locked
      out on first deploy.
      RECOMMENDED: set this
      explicitly in Render to
      the exact admin addresses.
    ADMIN_ALLOW_PASSWORD_FALLBACK
      "true" re-enables the old
      shared-password login as
      an emergency break-glass
      (shown as a collapsed
      "Trouble receiving the
      code?" expander). Default
      OFF. Intended for the case
      where email delivery breaks
      and the operator would
      otherwise be locked out.
      Enable temporarily in
      Render env, log in, fix
      email, then disable again.

  Reused, unchanged:
    * Gmail SMTP (GMAIL_SENDER +
      GMAIL_APP_PASSWORD) — the
      same path the daily digest
      uses. send_otp_email()
      mirrors send_email_with_csv().
    * The 8h HMAC session cookie
      (_make_admin_auth_token /
      _verify_admin_auth_token,
      keyed by ADMIN_PASSWORD).
      ADMIN_PASSWORD is still
      used as the cookie + OTP
      HMAC key; it's just no
      longer a login method by
      itself (unless the
      break-glass is enabled).

  New code (all additive except
  the login-gate rewrite):
    * import secrets (for
      cryptographically-secure
      OTP generation).
    * ADMIN_OTP_* constants.
    * _admin_allowed_emails(),
      _otp_memory_store(),
      _load_otp_state(),
      _save_otp_state(),
      _prune_otp_state(),
      _otp_send_allowed(),
      _generate_otp(),
      _hash_otp(),
      send_otp_email().
    * Admin login gate rewritten
      from a one-field password
      form into the two-stage
      email -> code flow, with
      the optional break-glass
      expander.

  Operator action required on
  deploy:
    1. (Recommended) Set
       ADMIN_EMAILS in Render to
       the exact admin email
       address(es).
    2. Confirm GMAIL_SENDER and
       GMAIL_APP_PASSWORD are
       set (they already are —
       the digest uses them).
    3. Leave
       ADMIN_ALLOW_PASSWORD_FALLBACK
       unset (OFF) unless email
       delivery is broken.

  Reversibility:
    Setting
    ADMIN_ALLOW_PASSWORD_FALLBACK=true
    restores the old password
    login alongside OTP. Full
    revert is a git revert of
    this version.

------------------------------------------------------------------------------

v2.31.0 (2026-05-19) -- Claude
  - Y-bump: max_tokens for the
    Anthropic Messages API call
    bumped from 600 to 1500
    (line ~7478). Coordinated
    with discord_bot.py v1.4.0
    (same bump) and cb_kb.py
    v1.10.25 (new Rule 17
    markdown-only / no-HTML
    output format).

  Audit context (2026-05-19,
  ~17:30 IST):
    Customer (Ares Wireless
    dropdown) asked for "all
    possible troubleshoot" for
    a button-registration issue.
    Bot generated a
    comprehensive 4-5 step
    response, hit the
    max_tokens=600 cap mid-
    Step-3, and the truncation
    left the customer with:
    (a) STEP 4 missing
        entirely
    (b) HTML divs visible as
        literal `</div></div>`
        text in the chat
        (the bot was
        generating HTML for
        styling and the
        wrapper's closing
        divs became visible
        when the truncation
        broke the nesting).

  Why 600 was too low:
    A comprehensive multi-
    step troubleshooting
    response with intro,
    clarifying question,
    4-5 STEP blocks with
    sub-bullets, and a
    closing call-to-action
    runs ~450-600 words ≈
    600-800 tokens. The
    600-token cap was at
    the lower edge of
    actual response sizes
    needed for the
    "give all possible
    troubleshoot" type of
    request, leaving zero
    margin and causing
    truncation on
    comprehensive flows.

  Why 1500 (not higher,
  not lower):
    1500 tokens ≈ 1200
    words. Comfortably
    fits 5-6 steps of
    multi-line
    troubleshooting plus
    headroom. Higher
    values (e.g. 4096)
    would be wasteful —
    Cosmic Byte's
    customer questions
    rarely warrant a
    1000-word response,
    and giving the bot
    too much rope
    encourages padding.
    1500 is the
    smallest-safe ceiling.

  Cost impact:
    Output tokens are a
    small fraction of
    total cost. Per the
    post-v1.10.18 cache
    analysis (cache_read_
    ratio 85-95%, daily
    cost ~$10/day), input
    dominates. Bumping
    max_tokens caps the
    OUTPUT side of each
    response — even if
    every response now
    used the full 1500
    tokens (which they
    don't — most are
    100-400 tokens),
    the increase would
    add ~$1-2/day. In
    practice, only the
    "give all possible
    troubleshoot" type
    of comprehensive
    flows approach the
    new limit, so the
    actual incremental
    cost is well under
    $1/day.

  Coordination with
  cb_kb.py v1.10.25:
    The max_tokens bump
    alone is insufficient
    — even with more
    headroom, the bot
    would still generate
    HTML divs that cause
    visual pollution in
    the chat. Rule 17 in
    cb_kb.py v1.10.25
    locks down "markdown
    only, no HTML" so
    the bot stops
    generating divs in
    the first place.
    Together: max_tokens
    bump prevents
    truncation, Rule 17
    prevents the HTML
    leak.

  Coordination with
  discord_bot.py v1.4.0:
    Discord bot has the
    same max_tokens
    setting (MAX_TOKENS
    constant at line
    ~795). Bumped to
    1500 to match.
    Discord also benefits
    from Rule 17 — even
    more strictly than
    the portal, since
    Discord renders only
    markdown and shows
    raw HTML as literal
    text in every case,
    not just on
    truncation.

  Reversibility:
    Single-line change.
    Trivial to revert by
    changing 1500 back to
    600 (or any other
    value).

------------------------------------------------------------------------------

v2.30.0 (2026-05-14) -- Claude
  - Y-bump: switch the Anthropic
    prompt-cache TTL from the
    default 5 minutes to 1 hour.
    Single-line code change inside
    the system-prompt cache_control
    breakpoint construction (line
    ~7378). Zero behavior change for
    customers; this is a cost /
    cache-amortization optimization
    only.

  Background:
    The Anthropic API supports two
    prompt-cache lifetimes:
      - 5-minute TTL (the default):
        cache write costs 1.25x
        base input price; cache
        read costs 0.1x.
      - 1-hour TTL: cache write
        costs 2x base input price;
        cache read costs 0.1x.
    The 5-minute default expires
    quickly enough that during low-
    volume hours (and during rapid
    deploy cycles that invalidate
    the cached prefix), the cache
    writes don't amortize
    efficiently — write
    amortization in the API console
    was sitting at 1.08x
    (essentially "one read per
    write"), which leaves
    significant cost savings on
    the table.
    Operator review on 2026-05-13
    showed cb_kb v1.10.x daily
    cost at $14.14 for 328
    conversations on Claude Haiku
    4.5 ($0.043 per conversation,
    ~Rs 3.58). Modelled cost at
    1-hour TTL with the same
    14-conversations-per-hour
    average is $5-7/day (~Rs 14k-
    19k/month vs current
    Rs 35k/month run-rate).

  Why this is safe:
    1. Pure config change — the
       Anthropic API handles the
       new TTL transparently; no
       SDK upgrade needed, no
       beta header required for
       Claude Haiku 4.5 (1-hour
       TTL is GA for Claude 4.5
       family per docs.claude.com
       /en/build-with-claude/
       prompt-caching).
    2. Cache content does NOT
       change — the same system-
       prompt text is cached; it
       just lives 12x longer
       between writes.
    3. Worst-case downside is
       paying 2x cache-write cost
       on a write that gets only
       one read (still cheaper
       than 5-min cache in that
       scenario? actually
       slightly worse: 2x write
       vs 1.25x write for the
       same single read). But
       the dominant case at
       Cosmic Byte's traffic
       volume (~14 conv/hour
       averaged across the day,
       peaks of 30-40/hour) is
       many reads per write,
       where 1-hour is decisively
       better.
    4. Reversible in one line if
       it causes any unexpected
       issue — change "1h" back
       to default by removing
       the ttl key. Single-block
       cache_control means the
       blast radius is contained.

  Verification path:
    - After deploy, watch the
      API console Caching
      dashboard (console
      .anthropic.com) over
      48 hours.
    - Expected: cache_creation
      tokens drop, cache_read
      tokens stay roughly steady
      (same content cached
      longer), write amortization
      climbs from 1.08x toward
      5-7x.
    - Expected: daily cost on
      the Cost dashboard drops
      from ~$14/day to
      ~$5-7/day at current
      traffic levels.
    - If write amortization
      hasn't improved by
      2026-05-17, investigate
      whether the cached prefix
      is being invalidated by
      something else (e.g. a
      cb_kb.py update, a session
      ID accidentally landing
      in the cached portion of
      the system prompt).

  Coordinated change:
    discord_bot.py v1.3.0 ships
    the same one-line edit on
    its parallel cache_control
    breakpoint (discord_bot.py
    line ~1429). Both files
    must be deployed together
    to apply the change across
    the full support surface
    (portal + Discord bot).
    discord_bot.py and
    support_portal.py reference
    DIFFERENT API call sites
    but use the same cache_
    control pattern; both need
    the ttl update.

  Documentation reference:
    Anthropic prompt caching
    docs:
    https://docs.claude.com/en/
    docs/build-with-claude/
    prompt-caching
    1-hour TTL syntax (current
    GA):
      "cache_control": {
        "type": "ephemeral",
        "ttl": "1h"
      }

v2.29.0 (2026-05-11) -- Claude
  - Y-bump: admin dashboard timestamps
    now display in India Standard Time
    (IST, UTC+5:30) instead of UTC.

  Background:
    Log rows are stored on disk with
    Date/Time fields in the server's
    local timezone (UTC -- the default
    for both the Render container and
    the Hetzner Cloud VPS that hosts
    the Discord bot). The admin dash-
    board was showing those raw UTC
    strings, forcing the operator (in
    Pune) to mentally add 5h30m to
    every timestamp -- annoying and
    a frequent source of "when did
    this actually happen" confusion.

  Fix architecture:
    Conversion happens at the read
    layer (get_merged_log), not at
    each display site. This means:
      - Sort by Date+Time still works
        (IST is monotonic with UTC).
      - Calendar week/month/day
        grouping aligns with IST
        naturally -- a row at 23:45
        UTC on May 11 is now correctly
        grouped under May 12 (IST).
      - Expander labels show IST.
      - CSV export of displayed values
        shows IST.
      - Daily digest aggregation uses
        IST-aligned day boundaries.
      - No per-display-site edits
        required.

  Storage is unchanged:
    The on-disk log file (support_log.
    jsonl) still contains UTC strings.
    This keeps existing log entries
    valid, avoids any migration step,
    and crucially means the Discord
    bot does NOT need a code change
    -- saving an extra bot restart in
    today's already-busy deploy queue.
    Conversion is purely a read-side
    transformation.

  Implementation pieces:
    1. New `IST` timezone constant
       (`timezone(timedelta(hours=5,
       minutes=30))`) at module load.
    2. New `_convert_row_to_ist(row)`
       helper that parses the stored
       UTC `"%d %b %Y %H:%M"` strings,
       attaches a UTC tzinfo, converts
       to IST via `.astimezone()`, and
       writes the IST strings back into
       the row. Idempotent via a
       `_tz_converted` marker so it's
       safe to call repeatedly. Silent-
       fail on malformed rows so one
       bad row can't crash the dash-
       board.
    3. `get_merged_log()` now applies
       this converter to every row
       before returning, on both the
       local-only path and the merged
       local+remote path. Conversion
       happens BEFORE the sort so the
       sort key compares IST values
       consistently across local and
       remote rows.
    4. Imported `timezone` from
       `datetime` (was just `datetime,
       timedelta` before).
    5. Small caption at the top of
       `render_admin()` reading
       "🕒 Timestamps shown in IST
       (UTC+5:30). Storage on disk
       remains in UTC." so the
       operator has a one-line
       reminder of the convention.

  Assumption + caveat:
    Both servers (Render container
    and Hetzner VPS) are assumed to
    be running in UTC -- the cloud
    default. If either ever gets
    moved to a non-UTC timezone (rare;
    would require explicit TZ env var
    or container config), this
    conversion will produce wrong
    values for rows logged from that
    server. The fix is to either set
    the offending host back to UTC or
    change the storage code to use
    `datetime.utcnow()` (or `datetime.
    now(timezone.utc)`) explicitly.
    For now, this is documented inline
    so a future you can spot it
    quickly.

  Verification after deploy:
    The screenshot of the admin
    dashboard showed entries at
    timestamps like "11 May 2026
    10:46" (UTC). After this fix,
    those should show "11 May 2026
    16:16" (IST, 5h30m later). If
    a row shows the wrong-by-5h30m
    time, conversion isn't running.
    If a row shows the wrong-by-
    some-other-offset time, the
    server isn't actually in UTC.

  No changes to:
    - cb_kb.py
    - discord_bot.py
    - Storage format on disk
    - Any read/write code outside
      get_merged_log

  ast.parse before/after.

v2.28.1 (2026-05-11) -- Claude
  - Z-bump: log hygiene. The six module-
    level print() calls used for startup
    banners (version banner, persistent-
    disk OK/WARNING, bot API merge enabled
    /WARNING/disabled) were firing on
    every Streamlit script rerun, not
    just on actual worker-process startup.

  Observed symptom:
    Render log stream showed ~30+ copies
    of the same three startup banners in
    a 75-second window during normal
    concurrent traffic (~1 user action
    every 2.2s). The banners themselves
    are useful on real startup but the
    duplicates were burying real events
    (errors, OOM restarts, deploy
    transitions) under repetitive noise,
    making the logs effectively unusable
    for triage.

  Root cause:
    Streamlit's execution model re-runs
    the entire script top-to-bottom on
    every user interaction. Any plain
    `print()` at module scope therefore
    fires on every rerun, not once per
    process as one might assume. Module-
    level globals reset each rerun too,
    so a simple "did_log = True" flag
    wouldn't work as a guard.

  Fix:
    Added a small helper
    `_log_once_per_process(msg: str)`
    decorated with `@st.cache_resource`,
    placed right after `import streamlit
    as st` so it's defined before any
    module-level print site. The decorator
    caches the function's return value
    across reruns AND across sessions,
    meaning the body (which prints)
    executes exactly ONCE per worker
    process for each unique `msg` string.

    Then routed all 6 startup print
    sites through the helper:
      1. Version banner ("starting up
         — app version X.Y.Z")
      2. Persistent disk OK banner
      3. Persistent disk WARNING (when
         /var/data is not mounted)
      4. Bot API merge enabled
      5. Bot API merge HALF-CONFIGURED
         warning
      6. Bot API merge disabled

  Behaviour:
    Identical at the application level.
    Render logs are now cleaner -- each
    startup banner appears exactly once
    per worker process, then never again
    until the worker is replaced (deploy,
    crash, OOM restart, scale event).

    Side benefit: future OOM restart
    cycles will now show up as distinct
    fresh banner blocks in the logs,
    making them immediately diagnosable
    (today's incident took several
    minutes to identify because the
    legitimate restart banner was lost
    in 30+ duplicate banners from normal
    traffic in the same window).

  Code paths NOT changed:
    The surrounding module-level setup
    code (env var parsing, disk-write
    probe, BOT_API_URL/SECRET reading)
    still runs on every rerun -- that's
    needed to keep module-level globals
    like LOG_FILE_PATH, BOT_API_URL etc.
    in scope for the rest of the script.
    Streamlit's design assumes this is
    cheap, which it is. Only the print
    calls were generating user-visible
    noise, so only the prints were
    moved behind the cache.

  ast.parse before/after.

v2.28.0 (2026-05-10) -- Claude
  - Y-bump: added QUICK_QUESTIONS entries
    for 7 products that were previously
    missing keyed entries and falling
    through to the controller-themed
    "All Products" default. Customer
    landing on any of these product pages
    was being shown irrelevant starter
    chips like "Controller not detected
    in game" and "Button keeps auto-
    pressing", which was both confusing
    and a missed opportunity to surface
    the right starter questions.

  Products added to QUICK_QUESTIONS:
    1. Helios Mouse (mouse) -- inserted
       in the mouse cluster before
       Hypernova Mouse, matching the
       order in PRODUCTS.
    2. CryoCore (USB-only wired headset)
    3. Proteus (dual-input headset --
       USB + 3.5mm)
    4. Immortal (tri-mode wireless
       headset)
    5. CosmoBuds X220 (TWS earbuds)
    6. Cyclone RGB (laptop cooling pad)
    7. Dragonfly (keyboard + mouse combo,
       CB-GKM-19)
    Trailing 6 (CryoCore through Dragonfly)
    appended after Astra at the end of the
    dict, in the same order as their
    appearance in PRODUCTS.

  Question selection method:
    For each product I read the first
    ~18 lines of its KNOWLEDGE_BASE entry
    to identify the actual category and
    distinguishing features, then drafted
    5 starter questions (the standard count
    used elsewhere in the dict) emphasising:
      - the most likely real customer issue
        (e.g. "One earbud not working" for
        TWS, "Mic not working" for headsets)
      - the product-specific feature most
        likely to confuse new customers
        (e.g. "GOD Mode" for CosmoBuds,
        "USB vs 3.5mm" for Proteus)
      - basic onboarding (pairing, software,
        mode switching)

  Coverage check:
    Pre-v2.28.0: 31 of 38 non-"All Products"
    entries in PRODUCTS had QUICK_QUESTIONS
    coverage. Post-v2.28.0: 38 of 38 (full
    coverage). The "All Products" default
    is now only used in its actual intended
    role -- when the customer hasn't
    selected a product yet -- not as a
    silent fallback.

  ast.parse before/after.

v2.27.1 (2026-05-09) -- Claude
  - Z-bump HOT-FIX: the v2.26.0 jump-to-page
    feature broke Prev/Next pagination on
    production. Every Prev or Next click
    raised StreamlitAPIException:
      "st.session_state.<jump_widget_key>
      cannot be modified after the widget with
      key <jump_widget_key> is instantiated."

  Root cause:
    The v2.26.0 implementation tried to keep
    the number_input's displayed value in sync
    with the actual page state by manually
    writing to st.session_state[jump_widget_key]
    inside the Prev/Next button click handlers.
    Streamlit does NOT allow this -- once a
    widget has been instantiated in any prior
    run, its session_state key is "owned" by
    Streamlit and external writes throw
    StreamlitAPIException, even after
    st.rerun(). The previous version's "if
    jump_widget_key in st.session_state:" guard
    prevented the error on the FIRST page-load
    (when the key didn't exist yet) but not on
    subsequent navigations once the user had
    interacted with the input or seen it
    rendered.

    My v2.26.0 changelog had a comment about
    "Streamlit gotcha: widget state takes
    precedence over the value= parameter once
    the widget has been interacted with" -- but
    I picked the wrong fix for that gotcha
    (manually writing to widget state) instead
    of the correct fix (recreating the widget
    with a new key when external state
    changes). My bad on the v2.26.0 review --
    should have caught this in pre-deploy
    testing.

  Fix:
    Replaced the static jump_widget_key with a
    DYNAMIC key that includes the current page
    number:
      jump_widget_key = f"{page_key}__jump_at_p{current_page}"

    When current_page changes via Prev/Next +
    st.rerun(), the widget gets a brand-new key
    that has no prior session_state, so
    Streamlit honours the value=current_page+1
    parameter on first instantiation. No
    manual session_state manipulation needed
    anywhere -- the widget re-renders with the
    correct value automatically because it's
    effectively a "new" widget at the new page.

    Side effect: old widget keys accumulate in
    session_state as the operator paginates
    (one per page visited within a session),
    but this is bounded -- no operator
    paginates more than a few dozen pages per
    session, and Streamlit's session_state is
    cleared on browser tab close. Acceptable
    cost for a clean fix.

    The Prev/Next click handlers no longer
    touch any widget state -- they just update
    page_key and call st.rerun(), and the
    natural widget-recreation handles the
    rest.

  Risk-flagging code from v2.26.0 is unaffected
  by this hot-fix -- only the jump-to-page
  pagination control was broken.
  ast.parse before/after.

v2.27.0 (2026-05-09) -- Claude
  - Y-bump: companion to cb_kb.py v1.8.0 -- new
    product (Cosmic Byte Hypernova Tri-Mode
    Gaming Mouse) added to the QUICK_QUESTIONS
    dict so the in-portal starter-question
    chips render correctly when a customer
    arrives via the Hypernova product page.

  Quick questions added (5, the standard count
  for mouse products):
    - "How to pair the dongle?" -- routes to
      the Hypernova-specific Left+Middle+Right
      mouse buttons + Spacebar pairing combo.
    - "8000Hz polling system requirements" --
      surfaces the i7 9700K / 240Hz / GTX 1080
      / 16GB minimum specs documented in the
      Hypernova manual.
    - "Can I use a fast charger?" -- this is
      the highest-stakes Hypernova-specific
      question (warranty void if damaged by
      fast charger). Surfacing this proactively
      is exactly the kind of thing the
      starter-chip UX is for.
    - "How to charge the spare battery?" --
      Hypernova ships with TWO removable
      batteries; the spare has its own USB-C
      port, which is unusual.
    - "Mouse cursor stuttering at 8000Hz" --
      common-by-construction issue when 8000Hz
      polling is enabled on a PC that doesn't
      meet the manual's minimum specs.

  No code change beyond the dict addition.
  ast.parse before/after.

v2.26.0 (2026-05-09) -- Claude
  - Y-bump: review-risk flagging on the admin
    conversation list + jump-to-page input on the
    pagination control. Two related portal-only
    UX improvements driven by the day's KB-quality
    work.

  Why:
    Today's 15 KB fixes all came from individual
    bad responses Ronak surfaced manually --
    either by random scroll of the admin list, or
    by customer escalation. There's no efficient
    way today to ASK the question "which of the
    last 200 conversations might be problematic?"
    -- the operator has to expand each row and
    judge for themselves. v2.26.0 adds:

  Risk flagging:
    A new `_score_conversation_risk()` helper
    runs at row-render time over each
    (customer_msg, ai_response) pair and applies
    9 heuristics derived from the fabrication
    patterns observed in today's cb_kb.py
    changelog (v1.4.1 Eclipse calibration,
    v1.5.1 Ares Pro back label, v1.5.2 warranty
    advocacy, v1.6.2 Ares dongle, v1.7.0 Ares
    XInput, plus the cross-product Rule #14
    violations).

    The 9 heuristics, with point values:
      H1  Button-combo with timing pattern
          ("Hold X + Y for N seconds")     -> +2
      H2  LED color claim with high specificity
          ("Orange LED = XInput")          -> +1
      H3  Short customer question (<= 4 words)
          + multi-step response (>= 3
          numbered items) - the Rule #14
          violation pattern                -> +3
      H4  Warranty advocacy patterns
          (drafted email subject, coaching
          language, fabricated root causes
          like "inadequate solder joint") -> +3
      H5  Categorical warranty pre-judgment
          ("you'll be covered", "definitely
          a manufacturing defect")
            ... un-hedged                  -> +3
            ... with neutral framing nearby -> +1
      H6  Severity rating language
          ("Severity: HIGH")               -> +2
      H7  Drafted email template (Subject +
          Body within response)            -> +3
      H8  Specific known fabrications by
          exact phrase ("turbo + y for 3
          seconds", etc.) -- regression
          safety net                       -> +4
      H9  Customer-stated framing inconsistent
          with detected product (Ares
          Wireless + "wired USB cable")    -> +2

    Score thresholds and badges:
      0     -> no badge (clean)
      1-2   -> 🟡 (low risk, possibly worth
                 a glance)
      3-4   -> 🟠 (medium, likely worth review)
      5+    -> 🔴 (high, almost certainly
                 review-worthy)

    The badge appears at the START of the row
    label so the operator can scan a long list
    and spot risky rows without expanding each
    one. Inside an expanded row, a "🚩 Flagged
    for review" callout lists exactly which
    heuristics matched, so the operator
    immediately knows which part of the
    response is suspicious.

    A new "Review risk" filter (6th column in
    the existing filter row) lets the operator
    filter to a threshold:
      "All"           - default, show everything
      "🟡+ Any flag"   - thorough review mode
      "🟠+ Medium+"    - daily-triage mode
      "🔴 High only"   - quick spot-check

    Filter is applied AFTER the cheaper exact-
    match filters (date / product / feedback /
    source) so the regex evaluation only runs
    on rows that survived earlier filtering --
    keeps the dashboard responsive even on
    large logs.

  Jump-to-page:
    Replaced the static "Page X of Y" markdown
    indicator in `_render_paginated_rows()`
    with an editable st.number_input. The
    operator can now jump directly to a
    specific page number instead of click-
    spamming Next on long days. The widget
    state is synced bidirectionally:
      - Typing a new page number updates the
        page state.
      - Clicking Prev/Next also updates the
        widget value (otherwise the input
        keeps showing the old page after a
        button click -- known Streamlit gotcha
        where widget state takes precedence
        over the value= parameter once the
        widget has been interacted with).

  Implementation notes:
    - Pure portal-only change. No bot impact.
      No cb_kb.py impact.  Zero cache
      invalidation (the system prompt content
      is unchanged).
    - Risk scoring is idempotent and side-
      effect-free; safe to call repeatedly.
      Pure regex / substring matching, no LLM
      calls. Minor CPU cost per row at render.
    - `re` module added to imports (was not
      previously imported).
    - The known-fabrications list (H8) is the
      "regression safety net": if a fabrication
      we already added a guard for in cb_kb.py
      reappears in production, this heuristic
      will surface it immediately so we know
      the guard isn't holding.

  Tuning notes for future:
    The 9 heuristics + thresholds are tuned
    against today's 5 confirmed-bad responses.
    First few days of use, monitor for:
      - False positives (heuristic flags a
        correct response)
      - False negatives (heuristic misses a
        bad response)
    Adjust point values or add/remove patterns
    based on actual usage. After a week of
    operational data, decide whether to
    promote risk-scoring to server-side at
    log-write time (Tier 2 -- store score in
    log row, faster admin rendering) or to
    AI-meta-evaluation (Tier 3 -- second LLM
    call per response, most accurate but
    adds latency + API cost).

  ast.parse before/after.

v2.25.0 (2026-05-09) -- Claude
  - Y-bump: enable Anthropic prompt caching on the
    Anthropic API call, cutting input cost for the
    system prompt + product knowledge by ~90%.

  Why:
    Ronak flagged that current API spend is high.
    Looking at the call site, every call sent the
    full SYSTEM_PROMPT + product manual slice
    (+ optional third-party brand manual) as fresh
    input tokens -- typically 15-30K tokens of
    identical content per call across many calls.
    Anthropic prompt caching exists exactly for
    this pattern.

  How caching works (no quality impact):
    Anthropic stores the pre-computed key-value
    cache for the cached portion of the input
    server-side. On a subsequent request with
    matching cached content, the model reuses the
    KV cache instead of recomputing it -- but it
    still processes the full input identically.
    Output quality is unchanged. Only the per-token
    input price drops on the cached portion: 0.1x
    base for cache reads, vs 1.25x base for cache
    writes (the one-time write surcharge is
    amortised after ~1.25 reuses).

    Per Anthropic's published pricing rules
    (https://docs.claude.com/en/about-claude/
    pricing): "Cache write tokens are 1.25 times
    the base input tokens price; cache read
    tokens are 0.1 times the base input tokens
    price."

    Per Anthropic's prompt-caching docs, the
    cache covers everything up to and including
    the cache_control breakpoint (tools + system,
    in our case), and persists for 5 minutes
    (ephemeral) -- with the TTL refreshing on
    every cache hit, so an actively-used cache
    stays warm indefinitely.

  Implementation:
    Refactored the api_kwargs construction at the
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

    The change is purely structural: same model,
    same max_tokens, same content, same messages.
    The only difference is that subsequent calls
    with the same (product, brand) combo within
    the 5-minute TTL will hit the cache.

  Cache hit pattern in production:
    Each unique (product, brand) combo gets its
    own cache entry, keyed by the byte-exact
    content of the system text. Cosmic Byte's
    busy-product calls (Lumora / Stellaris /
    Drakon / Eclipse) will hit the cache often;
    cold products will pay the cache write
    overhead on first call and then hit the cache
    if a second customer asks about the same
    product within 5 minutes.

  Threshold caveat:
    Haiku 4.5 has a 4096-token minimum for
    caching to actually engage. Our system text
    reliably exceeds this for any production
    query, but if it ever falls below the
    minimum the API request still succeeds; we
    just silently pay full price on that one
    call (cache_creation_input_tokens comes back
    as 0 in the response usage object).

  Verifying it's working:
    After this deploy, check console.anthropic.com
    -> Usage. The Cache Read and Cache Write
    columns should both populate. If Cache Read
    stays at 0 across many calls, something is
    wrong (cache key keeps changing -- the most
    common cause is a non-deterministic value
    sneaking into the system text, e.g. a
    timestamp or a randomly-ordered dict).

  ast.parse before/after.

v2.24.6 (2026-05-09) -- Claude
  - Y-bump: per-day pagination on the admin
    conversation list, plus a "Reset pages" button
    and a "Per page" selector. Targeted at the
    long-page complaint that v2.24.4 (since
    reverted) tried and failed to address by
    replacing st.expander with custom buttons.

  Why:
    With 56 conversations on a single busy day,
    the admin dashboard could become a very long
    scroll, especially when several rows were
    expanded simultaneously. Streamlit's
    st.expander does not expose its open/close
    state to the host code, so we cannot enforce
    "only one open" or "collapse all" from Python.
    The only reliable lever we have is rendering
    fewer rows in the first place -- pagination.

  What's new:

  1. PAGE-SIZE SELECTOR (5th filter column):
     "Per page" -> 5 / 10 / 20 / 50. Default 10.
     Lives next to Date / Product / Feedback /
     Source so it is in the natural place an
     operator looks when narrowing a view.

  2. PAGINATION CONTROLS PER DAY:
     New helper `_render_paginated_rows()` wraps
     the existing per-row renderer with Prev /
     Next buttons and a "Page X of Y · showing
     A-B of N" centre-aligned indicator. The
     pagination UI is suppressed when a day has
     fewer rows than the page size, so quiet days
     still render as a single uninterrupted list
     (no Prev/Next clutter when not needed).

     Each day tracks its own current page in
     session_state under the key
     `_admin_page__day__<day_label>`, so paging
     forward in "09 May" does not affect "08 May"
     etc. The flat-view path also paginates
     under `_admin_page__flat`.

     Page state survives reruns (clicking inside
     a row, refresh-data, etc.) so the operator
     does not get bounced back to page 1 by
     normal interactions.

  3. "RESET PAGES" BUTTON in the top action bar
     (next to Refresh data / Sign out): clears
     every session_state key starting with
     `_admin_page__`, which jumps every day's
     pagination back to page 1 in one click.

     The button is honest about what it does NOT
     do: its tooltip explicitly says "Does NOT
     close any expanders you have open". This is
     because once a user has clicked an
     st.expander, its state is internal to
     Streamlit and cannot be programmatically
     reset from the host code. v2.24.4 tried to
     work around this by replacing st.expander
     with a custom button-based accordion; that
     was rejected on visual + performance
     grounds. So instead of pretending we can
     close expanders, we tell the operator
     plainly that they need to click each one
     themselves. With pagination active and a
     sensible page size, this rarely matters
     because the visible row count is bounded.

  Edge cases handled:
    - If page_size shrinks (operator changes
      selector from 50 to 10) and the previously
      stored page is now out of bounds, the page
      is silently clamped back to 0.
    - When a new conversation arrives and changes
      the row count, the pagination indicator
      updates correctly on the next refresh.
    - Per-row widget keys (photo download buttons
      etc.) continue to use the original
      filtered_idx, so they stay stable across
      pagination changes.

  ast.parse before/after.

v2.24.5 (2026-05-09) -- Claude
  - Z-bump: revert v2.24.4. The button-based
    accordion looked wrong and rendered slowly --
    Ronak rejected both immediately on first
    deploy.

  Two problems with v2.24.4:

  (a) VISUAL: each conversation row rendered as a
      Streamlit st.button with use_container_width.
      Streamlit buttons inherit the app's primary
      colour, which for Cosmic Byte is brand
      orange. The result: every row in the admin
      conversation list looked like an orange
      warning / call-to-action button rather than a
      neutral expandable header. Visually
      overwhelming, especially on days with many
      conversations.

  (b) PERFORMANCE: 173 st.button widgets are
      noticeably heavier to render than 173
      st.expander widgets, and every click
      triggered a full-page st.rerun() which
      re-rendered all 173 rows. The end-to-end
      latency on opening any single row became
      unacceptable.

  Fix:
    Restored the original st.expander-based
    rendering (the v2.24.3 behaviour). Multiple
    rows can again be open simultaneously -- this
    is a downside of going back to expanders, but
    it is the trade-off Ronak preferred over the
    orange-buttons-and-slow-page outcome of
    v2.24.4. The "page-too-long when many rows are
    open" concern that motivated v2.24.4 is still
    real; future work will address it via a
    different mechanism (likely pagination per
    day, smarter day-collapse defaults, or a
    "Collapse all" button), NOT by replacing
    st.expander with widgets that have these two
    properties.

  Net effect:
    The admin dashboard's conversation rows behave
    exactly as they did before v2.24.4. The
    accordion state-tracking session_state key
    (`_admin_open_row_key`) is no longer read or
    written; if it ever appears in session_state
    from a stale tab on the v2.24.4 deploy, it is
    harmless (just unused).

  ast.parse before/after.

v2.24.4 (2026-05-09) -- Claude
  - Z-bump: admin conversation list now behaves as a
    true accordion -- only ONE row is expanded at a
    time. Click another row to expand it (auto-
    closing the previously open one); click the
    already-open row to collapse it.

  Why:
    Ronak reported that opening several conversation
    rows on the admin dashboard made the page very
    long -- 173 conversations worth of cumulative
    scroll if he had multiple expanded mid-review.
    He asked for accordion behaviour: at most one
    open at a time.

  Why this needs a real fix (not a config tweak):
    Streamlit's native st.expander allows multiple
    expanders to be open simultaneously and exposes
    no API for the host code to read or override
    the open/close state. Once the user has clicked
    an expander, its state is internal to Streamlit
    and any subsequent reruns cannot collapse it
    from Python code. So accordion behaviour cannot
    be achieved by just passing `expanded=False` to
    st.expander -- that parameter is initial state
    only.

  Implementation:
    Replaced the per-row st.expander in
    _render_admin_conversation_row with a button +
    conditional content block:
      * Track the currently-open row in
        st.session_state._admin_open_row_key (a
        string derived from Session ID + Date +
        Time, content-stable across reruns).
      * Each row renders a full-width button as
        the header. The button label is prefixed
        with ▶ when collapsed and ▼ when expanded
        (visually mirroring Streamlit's native
        expander glyph).
      * Click handler: if the clicked row is
        already open, set the open-key to None
        (collapse). Otherwise, set the open-key
        to this row's state_key (auto-closing
        whichever row was previously open). Then
        st.rerun() to repaint with the new state.
      * Below the button, render the row's content
        (customer message, attached photos, AI
        response, feedback) only if this row is
        the currently-open one. Otherwise return
        immediately.
      * A divider is rendered after the open row's
        content for visual separation from the
        next collapsed header.

    Widget keys for the row buttons include the
    row index `i` for absolute uniqueness, even in
    the unlikely case that two rows share the same
    Session ID + Date + Time. Photo-download
    buttons inside the open row continue to use
    the existing `dl_{i}_{ti}` keys -- unchanged.

    The day / week / month grouping expanders
    above the conversation rows are unchanged --
    those are normal st.expander instances and
    multiple can stay open simultaneously, which
    is the desired behaviour for those (Ronak
    wants to see multiple days within a week
    without having to re-click each time).

  Side benefit:
    With at most one row's heavy content (photos,
    base64-decoded thumbnails) rendered at a time,
    the admin page also gets noticeably lighter on
    days with many image-attached rows.

  ast.parse before/after.

v2.24.3 (2026-05-09) -- Claude
  - Z-bump: actually fix admin getting kicked to the
    password form on every refresh -- v2.24.2 fixed
    the wrong side of the bug.

  Background:
    v2.24.2 added a wait-for-cookies-mount loading
    state to the admin gate, on the theory that
    `_cookies` was None on the first render after a
    refresh and the gate was dropping straight to
    the login form before the iframe had a chance
    to post the saved cookie back. That theory was
    plausible but wrong -- the actual bug is that
    no `cb_admin_auth` cookie was ever being written
    in the first place. So no amount of patience on
    the read side could ever recover an auth that
    was never persisted.

  Diagnosis:
    Confirmed with browser DevTools (Application ->
    Cookies -> ai.thecosmicbyte.com): immediately
    after a successful admin login, the cookie list
    contained `cb_bid` (browser history cookie, set
    elsewhere in the file with no immediate rerun
    after) but did NOT contain `cb_admin_auth`. The
    admin auth cookie set was failing silently every
    time.

  Root cause:
    Race condition between the cookie set and
    st.rerun(). The login success handler does
    three things in order:
        st.session_state.admin_authenticated = True
        _cookie_manager.set(name, token, expires_at)
        st.rerun()
    `_cookie_manager.set()` posts a message via
    Streamlit's component channel to its iframe,
    asking the iframe to write the cookie via
    document.cookie. The set() call returns
    immediately; the actual cookie write happens
    asynchronously on the client. `st.rerun()`
    fires the very next line, telling Streamlit to
    halt and restart the script. The rerun command
    arrives at the client before the iframe has
    had a chance to process the postMessage and
    commit the cookie. The cookie write is lost.

    The cb_bid cookie does NOT have this problem
    because it is set during a normal render with
    no immediate rerun after -- the rest of the
    page renders, control returns to Streamlit's
    render loop, and the iframe gets plenty of
    time to process the message before any further
    instruction arrives.

  Fix:
    Insert `time.sleep(0.5)` between
    `_cookie_manager.set()` and `st.rerun()`. The
    server pauses for half a second; during that
    pause the cookie set message reaches the
    client, the iframe processes it, document.cookie
    is written, and the browser commits the write.
    Then st.rerun() fires and the rerun lands on a
    state where the cookie is actually persisted.
    On a future hard refresh, the CookieManager
    iframe reads the cookie back and admin auth is
    restored cleanly via the existing v2.13.0 path.

    500ms was chosen empirically -- the smallest
    interval observed to work reliably across
    Chrome / Edge / Safari / Firefox. Shorter
    intervals (100-300ms) work most of the time
    but occasionally race on slower client machines
    or under load. The user-visible cost is a half-
    second pause on the Login click, which is
    indistinguishable from normal network latency
    on a click.

  v2.24.2's wait-for-cookies-mount logic is left in
  place. It is now defensive (guards against a
  separate read-side race that could in theory
  occur on slow first-page loads) rather than
  load-bearing, but costs nothing to keep.

  ast.parse before/after.

v2.24.2 (2026-05-09) -- Claude
  - Z-bump: fix admin getting kicked to the password
    form on every hard refresh of the AI page.

  Symptom (reported by Ronak):
    "If I refresh the AI page my admin gets logged out.
    I have to reenter password."

  Root cause:
    The cookie-based persistent admin auth introduced
    in v2.13.0/.1 has a race window on the very first
    render after a hard refresh. The CookieManager
    component (extra_streamlit_components.CookieManager)
    needs ~100ms to mount its iframe and post the
    saved cookies back to the script. During that
    window `_cookies` is None.

    The auth-restore check at the top of the admin
    gate read:

        if not st.session_state.admin_authenticated and _cookies:
            ...validate token, restore auth...

    With `_cookies = None`, the boolean falls through,
    the cookie check is skipped, and the operator
    drops straight to the login form. A few hundred
    ms later the iframe mounts and triggers a Streamlit
    rerun -- which WOULD have restored auth from the
    cookie -- but by then the operator has already
    seen the password prompt and is typing into it.

  Fix:
    Add an explicit "cookies still loading" branch
    above the auth-restore check. If a CookieManager
    exists but `_cookies is None` and we haven't
    waited yet, render an "🔐 Restoring admin
    session..." message and st.stop() -- the iframe-
    mount-triggered rerun lands the script back here
    with `_cookies` populated, and the restore
    succeeds on the second pass.

    Guarded with a `_admin_cookies_waited`
    session_state flag so the wait only happens once.
    Browsers that block the iframe entirely (third-
    party cookies disabled, ad-blocker stripping the
    component, etc.) fall through to the login form
    on the second pass -- graceful degradation, no
    infinite "Restoring..." loop.

    The wait flag is cleared on successful restore
    AND on successful password login, so a future
    sign-out + sign-back-in cycle within the same
    session gets a fresh wait window on the next
    refresh.

    No change to token format, cookie name, cookie
    duration (8h), or the embed_mode skip path.

  ast.parse before/after.

v2.24.1 (2026-05-09) -- Claude
  - Z-bump: docs only. Added DEPLOYMENT section to the
    file's top docstring covering Render setup, current
    env vars, vars that should be deleted post-migration,
    and the GitHub-only deploy flow. Lets future Claude
    sessions answer Ronak's deploy/env-var questions
    without re-deriving the topology from scratch.

  No code change. ast.parse before/after.

v2.24.0 (2026-05-09) -- Claude
  - Y-bump: portal now fetches Discord conversation rows
    from the bot's HTTP API and merges them with the
    local log for admin dashboard / digest views.

  Why:
    Today's migration moved the Discord bot off Render
    onto a Hetzner VPS to escape Render's per-IP rate
    limits with Discord. The portal stayed on Render. Side
    effect: the two services no longer share a filesystem,
    so any new Discord row the bot writes to its own log
    file (/var/lib/cosmic-bot/support_log.jsonl) is
    invisible to the portal's admin dashboard, daily
    digest emails, CSV export, and bulk photo export.

    discord_bot.py v1.1.0 added a small read-only HTTP
    API (GET /log/recent, Bearer-auth) for exactly this.
    This bump consumes it on the portal side.

  What's new:
    * Two new env vars (both optional):
        BOT_API_URL    -- e.g. http://5.223.52.60:8080
        BOT_API_SECRET -- shared secret matching the bot's
                          LOG_API_SECRET. Sent as
                          Authorization: Bearer <secret>.
      If either is unset, the merge layer is a no-op and
      v2.24 behaves exactly like v2.23 (local rows only).

    * `_fetch_remote_discord_rows(force=False, ttl=30)` --
      hits the bot's /log/recent endpoint, caches the
      result for `ttl` seconds. Cached at module level
      via @st.cache_resource, so all Streamlit sessions
      on the same Render instance share one cached fetch.
      Returns the last successful fetch on transient
      failures (network blip, bot restart) -- avoids
      blanking out the admin view on every retry-able
      error.

    * `get_merged_log()` -- returns local rows + remote
      Discord rows, deduplicated and sorted by
      Date+Time. The local row wins on overlap (so any
      pre-migration Discord rows that exist in BOTH
      logs keep whatever feedback the admin set on the
      local copy).

    * Each remote row carries a "_remote": True marker
      so the UI / write-side code can identify rows that
      live on the VPS rather than the local filesystem.

  Where it's used:
    * render_admin() -- iterates get_merged_log() instead
      of get_log() so the admin sees new Discord rows.
    * auto_daily_digest() -- aggregates over the merged
      view so Discord conversations make it into the
      daily emails, CSV, and digest stats.
    * Bulk photo export uses get_merged_log() too, but
      since Discord rows in this codebase don't carry
      attached images (Image Thumbnails always ""), this
      is mostly cosmetic correctness.

  Where it's NOT used:
    * log_conversation() and update_feedback() still use
      get_log() (local cache only). They only ever
      mutate Web rows -- log_conversation appends a new
      Web row, update_feedback updates an existing Web
      row by index. Both correct against local rows.
      Discord rows are read-only on the portal side
      because the in-chat 👍/👎 feedback widgets only
      exist in the Streamlit chat UI (Web channel),
      never on Discord.

  Failure modes:
    * Bot down / unreachable: get_merged_log returns
      local rows + last cached remote rows (which may
      be empty if cold-start). Admin sees a stale view
      until the bot comes back. No crash.
    * Bot returns garbage / wrong schema: rows that
      don't parse get skipped silently; the rest merge
      normally.
    * Wrong / missing secret: bot returns 401, fetcher
      logs a WARNING, returns last cached rows. Admin
      eventually notices missing recent Discord rows;
      operator fixes the secret on either side.

  Security note:
    BOT_API_SECRET is the only thing protecting access
    to your customers' Discord conversations over the
    public internet. Generate a long random value
    (`openssl rand -hex 32`) and never put it in git or
    in chat. The endpoint serves plain HTTP -- the data
    in transit is theoretically eavesdroppable. Putting
    Caddy + Let's Encrypt in front of the bot's port
    8080 is the recommended follow-up; it's an ops
    change with no code change.

v2.23.2 (2026-05-09) -- Claude
  - Z-bump: fixes for several issues found in a code review
    after the v2.23.0/.1 deploy.

  Bug 1: AUTO-DAILY-DIGEST STILL MISSING DISCORD ROWS
    The v2.23.0 fix to make the daily digest see Discord
    conversations set `st.session_state.log = _load_log_from_disk()`
    but then iterated `get_log()`. Those are different objects:
    `get_log()` returns the cache_resource shared list, which the
    Discord bot (separate process) never touches. Net result: the
    digest emails Ronak gets at the end of each day were silently
    dropping every Discord conversation, exactly the symptom
    v2.23.0 claimed to fix.

    Fix: refactored the disk-refresh pattern into a single helper
    `_refresh_cached_log_from_disk()` that mutates the
    cache_resource shared list IN PLACE (clear + extend) so
    every reader of `get_log()` sees the fresh data, and
    iterate that list directly instead of calling `get_log()`
    after the refresh.

  Bug 2: IN-CHAT FEEDBACK COULD LAND ON THE WRONG ROW
    `log_conversation()` returns `len(get_log()) - 1` as the
    row_num, which is then stored on the assistant message as
    `log_idx` and used by the in-chat 👍/👎 buttons. But
    `get_log()` is the stale cache_resource shared list. If any
    Discord row had landed since the portal cold-started, the
    cache was short by N rows relative to disk, so the row_num
    pointed N rows too low. A user clicking 👍 on their own
    answer would actually file feedback against a Discord
    conversation N rows back. Worst case for Ronak: feedback
    analytics would be quietly miscredited.

    Fix: `log_conversation()` now performs the full cycle
    (read disk -> sync cache to disk truth -> append new row to
    cache + disk) under a single `_log_disk_lock` acquisition.
    Two effects:
      (a) Discord rows that arrived since the last sync are
          picked up before we compute this row's index, so the
          row_num always reflects the row's true on-disk
          position.
      (b) Two concurrent web log_conversation calls can no
          longer interleave cache and disk in different orders.
          Previously the cache append was unlocked while the
          disk append was locked, so a different thread
          ordering between the two could leave cache positions
          and disk positions disagreeing -- and a feedback
          click would land on whichever row happened to share
          the cache index. (This race existed in v2.23.1 and
          earlier too, just rare enough to go unreported.)

    Implementation note: factored out a new
    `_load_log_from_disk_unlocked()` helper that does the read
    work without taking the lock, so callers that already hold
    the lock can use it directly. `_load_log_from_disk()` now
    just wraps it with the lock and the load-summary print --
    public API is unchanged.

  Bug 3: CONVERSATION-HISTORY TRIM COULD VIOLATE ROLE ALTERNATION
    The trim `all_msgs[:1] + all_msgs[-(MAX_HISTORY - 1):]` keeps
    msg 0 (always user, holds the KB) and the last 7 messages.
    Conversations always end on a user message (we just appended
    one before sending), so `len(all_msgs)` is always odd at the
    API call. For lengths 9, 11, 13, ... the slice produces two
    consecutive user messages at the head→tail seam, and Anthropic's
    API rejects the call with "messages: roles must alternate".
    Latent bug -- only triggers once a single conversation passes
    8 messages.

    Fix: when trimming, check the role at the head→tail seam and
    drop one message off the front of the tail if it would create
    a same-role adjacency. The trimmed conversation is now at most
    MAX_HISTORY messages and is guaranteed to alternate.

  Bug 4: `_save_history_to_disk` ITERATES STORE OUTSIDE THE LOCK
    The function builds the entries-list from `store.items()`
    BEFORE acquiring `_history_disk_lock`. A concurrent request
    mutating the store (any normal chat turn) trips
    "RuntimeError: dictionary changed size during iteration".
    The broad except swallows it, so customers don't see the
    error -- they just get an occasional silent save failure
    and lose history persistence for that turn.

    Fix: build the entries list inside the `with` block so the
    iteration is protected by the same lock that guards the disk
    write.

  Files changed in this release:
    * support_portal_v2.py (this file)
    * discord_bot.py (small empty-chunk guard in
      `_split_for_discord`; bumped to v1.0.1)

  No behaviour change for the customer-facing chat flow on
  the happy path. Affected paths are the daily digest email,
  in-chat feedback button accuracy, long conversations
  (>8 msgs) hitting the API, and chat history persistence
  under concurrent load.

v2.23.1 (2026-05-08) -- Claude
  - Z-bump: cosmetic fix. The hardcoded human-readable banner on
    line 3 of this file's top docstring still read "app version:
    2.21.0" even though __version__ had been bumped to 2.22.0 and
    then 2.23.0. The startup print at module load (line ~3325)
    uses an f-string with {__version__} so the actual reported
    version was always correct, but anyone opening the file in an
    editor saw "2.21.0" at the very top -- which is exactly what
    Ronak caught.

    The file already has a checklist item at line 46 saying
    "Update 'app version: X.Y.Z' on the title line of this
    docstring." -- I missed that step in both v2.22.0 and v2.23.0.

    Fix: line 3 now reads "app version: 2.23.1" matching
    __version__. No code or behaviour change. Future edits should
    follow the line-46 checklist or this drift will recur.

v2.23.0 (2026-05-08) -- Claude
  - Y-bump because cb_kb v1.1.0 (which we now require) added a new
    product (Immortal headset). Also fixes two bugs that surfaced
    after v2.22.0 went live: the admin dashboard didn't show
    Discord conversations, and the v2.22.0 KB extraction missed
    six dict-mutation entries that the Discord bot couldn't see.

  Bug 1: ADMIN DOESN'T SHOW DISCORD CONVERSATIONS
    Symptom: Ronak filtered admin -> Source = "discord" and saw
    nothing, even though @mentions and #support-channel messages
    were getting AI replies in Discord.

    Root cause: The admin renders from `st.session_state.log`,
    which the portal loads ONCE per browser session via
    _load_log_from_disk(). The Discord bot is a separate process;
    it writes to /var/data/support_log.jsonl with fcntl-locked
    appends but never touches our in-memory log. Result: web rows
    appeared in admin (because log_conversation appends both
    in-memory AND to disk), but Discord rows lived only on disk
    and were invisible in admin.

    Fix: in render_admin() and auto_daily_digest(), re-read the log
    from disk at the top, and update st.session_state.log to match.
    The admin dashboard is now fresh on every render.

    Bonus: also fixed update_feedback() to re-read disk before its
    full-rewrite step. Without that fix, giving feedback on a web
    row would have BLOWN AWAY any Discord rows that landed between
    page-render and feedback-click. (The rewrite reads in-memory ->
    overwrites disk; if in-memory was stale, disk loses data.)

    All three call sites (render_admin, update_feedback,
    auto_daily_digest) now share the same defensive pattern:
       if LOG_FILE_PATH is not None:
           log = _load_log_from_disk()
           st.session_state.log = log
       else:
           log = get_log()  # dev fallback when disk persistence is off

  Bug 2: SIX KB ENTRIES MISSING FROM DISCORD BOT
    Symptom: A Discord user asking about CryoCore / Proteus /
    CosmoBuds X220 / Cyclone RGB / Dragonfly would have gotten a
    generic-knowledge answer instead of the manual-grounded one
    the web portal gives. (Wasn't directly observed yet, found
    while diagnosing Bug 1.)

    Root cause: In v2.22.0 we extracted KNOWLEDGE_BASE from this
    file into cb_kb.py, but the original file had six dict
    mutations AFTER the literal `KNOWLEDGE_BASE = {...}` block:
        KNOWLEDGE_BASE["CryoCore"] = "..."
        KNOWLEDGE_BASE["Proteus"] = "..."
        KNOWLEDGE_BASE["CosmoBuds X220"] = "..."
        KNOWLEDGE_BASE["Cyclone RGB"] = "..."
        KNOWLEDGE_BASE["Dragonfly"] = "..."
        KNOWLEDGE_BASE["All Products"] = ""
    Those mutations stayed in support_portal_v2.py. The web portal
    saw all six (it imports the dict and then mutates it before any
    customer query), but the Discord bot, importing KNOWLEDGE_BASE
    fresh in its own process at startup BEFORE the portal's mutation
    code runs (and from a separate process where module-level state
    is not shared anyway), saw an empty entry for those products.

    Fix: cb_kb v1.1.0 absorbs all six entries into the canonical
    KB definition. This file no longer mutates KNOWLEDGE_BASE — we
    only import it.

  New product (cb_kb side): Cosmic Byte Immortal headset
    Tri-mode (Wi-Fi 2.4GHz / Bluetooth 5.3 / Wired 3.5mm),
    50mm driver, ENC detachable mic, 40hr battery, RGB LED, 20m
    range. URL added to PRODUCT_URLS, full ~9KB manual added to
    KNOWLEDGE_BASE, catalogue updated with a new "Wireless
    Headsets" section, keyword aliases wired up for product
    detection. The KB explicitly flags two manual ambiguities
    (USB-A vs USB-C dongle labelling, and Mode-button gesture
    overloading) so the AI doesn't confabulate -- it tells the
    customer the manual is unclear and to contact support, rather
    than guessing.

  Files changed in this release:
    * support_portal_v2.py (this file)
        - render_admin(): refresh log from disk
        - update_feedback(): refresh log from disk before rewrite
        - auto_daily_digest(): refresh log from disk
        - removed the six KNOWLEDGE_BASE["..."] = "..." mutations
          (now in cb_kb.py)
        - changelog entry added
    * cb_kb.py (cb_kb v1.1.0)
        - PRODUCT_URLS["Immortal"]
        - PRODUCTS list updated
        - KNOWLEDGE_BASE["Immortal"] full manual entry
        - CATALOGUE_HEADSETS updated with wireless section
        - "immortal" keyword alias in both detection tables
        - absorbed the six previously-orphan mutations
    * discord_bot.py: NO CHANGES (no rebuild needed)
    * run.py: NO CHANGES

  No deployment changes needed beyond replacing the two affected
  files. Same env vars, same requirements.txt, same Render config.

v2.22.0 (2026-05-08) -- Claude
  - Y-bump: extracted the entire knowledge-base data layer into
    a new shared module `cb_kb.py` so the new Discord bot
    (discord_bot.py) can import the same data without pulling
    in Streamlit. Single source of truth, no drift risk.

  What moved out of this file (now in cb_kb.py, imported back):
    * PRODUCT_URLS                    (37 product page URLs)
    * KNOWLEDGE_BASE                  (full per-product KB, 32 keys)
    * PRODUCTS                        (dropdown list)
    * SYSTEM_PROMPT                   (~609 lines, all policy blocks)
    * match_product_from_title()      (page-title -> product)
    * THIRD_PARTY_BRAND_MANUALS       (Cosmic Byte's distributor manuals
                                       for Logitech, Razer, etc., 6 keys)
    * CATALOGUE_CONTROLLERS / _MICE / _KEYBOARDS /
      _HEADSETS / _ACCESSORIES / _ALL
    * THIRD_PARTY_BRANDS              (10 keys)
    * THIRD_PARTY_BRAND_URLS          (7 keys)
    * detect_third_party_brand()
    * detect_products_from_message()
    * detect_product_from_message()
    -> ~3553 lines moved. File went from 8874 -> 5350 lines.

  What stayed in this file:
    * Streamlit page setup, CSS, page rendering
    * Disk-persistence layer (/var/data)
    * Admin dashboard + grouping helpers
    * Cookie/session/email/digest logic
    * Customer-facing chat UI
    * The Anthropic API call sites (still consume the
      now-imported SYSTEM_PROMPT and KNOWLEDGE_BASE).

  Standing edit protocol now extends to cb_kb.py:
    * Only Claude edits cb_kb.py (same as this file).
    * Every edit there bumps cb_kb's own __version__
      (started at v1.0.0) and adds a dated CHANGELOG entry.
    * cb_kb.py must pass ast.parse before delivery.

  Discord bot (the actual feature this enables):
    * discord_bot.py is shipped alongside this version.
    * Reads env vars: DISCORD_BOT_TOKEN (required),
      DISCORD_SUPPORT_CHANNEL_ID (= 1502355643233730610),
      DISCORD_GUILD_ID (= 1416742276322955296),
      DISCORD_BOT_REPLY_TO_DMS (default false).
    * Behaviour: replies to @mentions in any channel and to
      every message in the dedicated #support channel.
      DMs are off by default; flip the env var to enable later.
    * Logs to the same /var/data/support_log.jsonl with a new
      Source column ("web" or "discord"). Backwards-compatible:
      old rows without Source are treated as "web".

  Admin dashboard:
    * Added "Source" filter column alongside Date / Product /
      Feedback so Ronak can split web vs discord traffic.

  run.py:
    * Adds a `subprocess.Popen([sys.executable, "discord_bot.py"])`
      BEFORE the existing `os.execvp` into Streamlit, gated on
      `DISCORD_BOT_TOKEN` being set. The subprocess is reparented
      to PID 1 once Streamlit replaces this process; standard
      Linux behaviour, works fine on Render's single-instance
      web service.

  No semantic changes to the AI's behaviour. The KB, system
  prompt, and detection logic are byte-for-byte the same as
  v2.21.0 -- only their location changed.

v2.21.0 (2026-05-08) -- Claude
  - Y-bump: hierarchical Month -> Week -> Day grouping in the
    admin conversation list. Triggered immediately after
    v2.17.0 / v2.18.0 deployed disk persistence: Ronak noted
    "the conversations in the admin page will become very
    large with persistence disk. Can we have it categoried by
    each day, then week, then month? I can click on it to
    open the data?"

  Background:
    Pre-v2.17.0, the conversation log was wiped on every
    Render restart, so it never grew beyond a day's worth of
    chat traffic. The flat list in the admin dashboard was
    fine for that volume.

    Post-v2.17.0 / v2.18.0, the log persists indefinitely.
    18 conversations on day one becomes ~500 in a month and
    several thousand over a year. Scrolling through a flat
    list of all of those becomes unworkable. Hierarchical
    grouping with collapsible sections is the natural fix.

  Design choices:

    1. THREE-LEVEL HIERARCHY: Month -> Week -> Day -> conversation.
       Matches Ronak's request literally ("by each day, then
       week, then month"). Each level shows a count so the
       admin can see at a glance where the volume is.

    2. AUTO-EXPAND THE MOST RECENT PATH: when the dashboard
       loads, the most recent month / week / day are all
       expanded by default. Today's conversations are
       reachable in zero clicks. Older months/weeks/days
       stay collapsed and quiet until the admin clicks in.

    3. SMART FLAT FALLBACK: hierarchical drill-down is
       counterproductive when the dataset is small. The new
       view falls back to the original flat list when:
         (a) The user has selected a specific date in the
             existing Date filter (the filter is already
             doing the job).
         (b) The full filtered set is small (<=30 rows) AND
             all from a single calendar day -- one day's
             worth, fits on a screen, no need to make the
             admin click into a single-day expander to see
             what's already visible.
       Otherwise, the hierarchical view kicks in.

    4. WEEK BOUNDARIES: Monday-to-Sunday weeks (the more
       common convention in India where Cosmic Byte
       operates). Week label format: "Week of 04 May" --
       short, unambiguous.

    5. DAY LABEL INCLUDES WEEKDAY: e.g. "08 May 2026 (Fri)"
       -- saves the admin from having to mentally compute
       which day of the week a given calendar date was.

    6. SAME PER-CONVERSATION RENDER: the existing per-row
       expander UI (customer message, AI response, photo
       thumbnails with download buttons, feedback) is
       UNCHANGED. The grouping is purely a wrapper layer
       on top. So every existing feature -- photo download
       buttons, feedback display, session ID -- continues
       to work identically.

    7. UNDATED ROWS: rows whose Date field can't be parsed
       (corrupted log entry, format drift) are bucketed
       into a synthetic "(Undated)" group at the bottom of
       the hierarchy rather than dropped. Visible to the
       admin so they know corruption exists without losing
       access to the row.

  Code changes:

    1. New helper _group_log_for_admin(rows_with_idx) added
       just above render_admin(). Takes a list of (filtered_idx,
       row) pairs (preserving the original filtered-list index
       so per-row Streamlit widget keys stay stable). Returns
       a sorted nested structure: months -> weeks -> days ->
       (idx, row) pairs, each level reverse-chronological,
       each level annotated with a count for header display.
       Day rows within a day are sorted by Time descending.

    2. New helper _render_admin_conversation_row(idx, r) added
       just above render_admin(). Encapsulates the existing
       per-row UI -- the st.expander, customer message, photo
       grid, AI response, feedback line, plus the photo
       download buttons keyed off the row's filtered index --
       so it can be called from both the flat path and the
       grouped path without duplication.

    3. render_admin() updated:
         - Existing top action bar, filters, metrics, and
           download/email/zip sections UNCHANGED.
         - The conversation list section (previously a flat
           for-loop) now branches:
             * If selected_date != "All dates" -> flat list
               (filter is already narrowing, hierarchy adds
               friction).
             * Else if all rows are from a single date AND
               there are 30 or fewer rows -> flat list (one
               day's worth, fits on a screen).
             * Else -> hierarchical Month/Week/Day expanders,
               with the most recent path auto-expanded.

  Verification: ast.parse OK on Python 3.

  Known minor cosmetic note:
    Streamlit's nested st.expander UI works but stacks
    visually -- 4 levels deep (month/week/day/conversation)
    can look busy when many sections are expanded at once.
    The default-collapsed-except-most-recent strategy keeps
    it manageable for the common case (admin scans recent
    activity, occasionally drills into history).

  Followup notes:
    - Open: backup strategy beyond email digest.
    - Open from v2.16.0: Drakon ML/MR vs L4/R4 software
      label mismatch.
    - Open from v2.15.2: ORDER & SHIPPING POLICIES gap.

v2.20.0 (2026-05-08) -- Claude
  - Y-bump: add REFURBISHED PRODUCTS POLICY to SYSTEM_PROMPT
    after a customer interaction where the AI confidently told
    a customer "Cosmic Byte does not sell refurbished products.
    All products sold on thecosmicbyte.com are brand new" --
    which is FALSE. Cosmic Byte has a Certified Refurbished
    category live on the website with multiple pages of
    listings, in the main site navigation menu, with its own
    documented policy and warranty terms.

  Trigger:
    Customer asked "Warranty in refurbished product". The AI
    responded by denying that Cosmic Byte sells refurbished
    products at all, then implied the customer might have
    been scammed or sold a fake ("If you've purchased a
    product that you believe is refurbished or used, please
    contact our support team immediately"). For a customer
    who legitimately bought from the Certified Refurbished
    category (a real product line on the site), this answer
    would be alarming and incorrect.

  Root cause:
    Same KB-silence hallucination pattern flagged repeatedly
    in v2.12.x, v2.14.x, v2.15.x, and v2.19.0 (BGMI). The KB
    had no info on refurbished products, so the AI
    pattern-matched to a typical e-commerce
    "no-we-don't-sell-that, you've-been-scammed" frame and
    fabricated. Identical failure mode to v2.15.2's invented
    invoice download portal and v2.19.0's invented BGMI
    gamepad support.

  Reality (per Ronak, with the policy text from
  https://www.thecosmicbyte.com/product-category/certified-refurbished/
  verified live):
    - Cosmic Byte sells certified refurbished products under
      a dedicated product category in the main site
      navigation. Multiple pages of listings.
    - Packaging: refurbished products may or may not come in
      the original packaging. Replacement / similar packaging
      is acceptable per Cosmic Byte's published policy. This
      is BY DESIGN -- not a fraud indicator.
    - Condition: products are opened and tested. May have
      minimal or no signs of wear & tear. Will NOT be broken
      or damaged.
    - Warranty: 6-MONTH minimum, supplier-backed. This is
      DIFFERENT from the 1-year warranty on new products. The
      6-month figure is the operative warranty period for
      refurbished, and the 1-year figure should NOT be
      applied.

  Fix shipped in v2.20.0:

  1. NEW: REFURBISHED PRODUCTS POLICY block added to
     SYSTEM_PROMPT (placed near the WARRANTY OVERVIEW since
     warranty differs by product type). The block:
       - Affirms that Cosmic Byte sells certified refurbished
         products and gives the URL.
       - States the packaging policy (may not be original; not
         a fraud indicator).
       - States the condition policy (opened, tested, minimal
         wear, will not be broken or damaged).
       - States the warranty policy (6 months, supplier-backed,
         vs 1 year on new).
       - Provides three conversation flows the AI should
         follow:
           Case A: "Do you sell refurbished?" / "What's the
                   refurbished warranty?" -> share URL +
                   policy.
           Case B: Customer suspects their product is
                   refurbished but believes they bought new
                   -> ASK which category they bought from
                   FIRST, before treating it as fraud.
                   Non-original packaging on a refurbished
                   order is normal; same packaging on a
                   regular-category order is a real concern.
           Case C: Refurbished product has a defect ->
                   standard troubleshooting + warranty path,
                   but using the 6-month period.
       - Lists explicit DO-NOT-SAY items including the exact
         "Cosmic Byte does not sell refurbished products"
         phrase that triggered this fix.
       - Lists explicit DO items: direct refurbished-curious
         customers to the URL, state 6-month warranty
         clearly, treat refurbished as a legitimate product
         line.

  2. WARRANTY OVERVIEW block updated to mention the
     refurbished exception inline ("...except certified
     refurbished products which carry a 6-month
     supplier-backed warranty -- see REFURBISHED PRODUCTS
     POLICY below for full details"). Keeps the block as
     the single answer to "what's the warranty?" while
     pointing at the policy block for the variant.

  Followup notes:
    - Open: backup strategy beyond email digest; Drakon
      ML/MR vs L4/R4 software label mismatch; ORDER &
      SHIPPING POLICIES gap (still open from v2.15.2).

  Verification: ast.parse OK on Python 3.

v2.19.0 (2026-05-08) -- Claude
  - Y-bump: substantive correctness bundle covering THREE
    related issues all surfaced by one customer interaction
    where the AI was asked "does the Ares Pro work on iPad?"
    and then "to play games like BGMI". The AI's responses
    contained multiple compounding errors that would
    directly cost Cosmic Byte sales and trust.

  Triggers (all from the same iPad / BGMI conversation):

    (1) AI told the iPad customer "Gyro is NOT supported on
        iPad -- the motion control only works on PC, not iOS
        devices. This is an Apple limitation, not a controller
        limitation." Two problems:
          (a) The Ares Pro does NOT have gyro hardware at
              all. Confirmed by Ronak: "Ares Pro does not have
              Gyro." The AI was answering "doesn't work on
              iPad" when the truthful answer is "this
              controller doesn't have gyro period -- not on
              iPad, not on PC, not anywhere." Tracked back
              to a wrong CATALOGUE_CONTROLLERS entry that
              listed "gyro" as an Ares Pro feature.
          (b) Even for controllers that DO have gyro
              (Lumora, Drakon, Stellaris, Blitz Tri-Mode),
              when a customer asks about gyro on a
              non-Windows platform, the AI was just saying
              "doesn't work on this platform" -- missing
              the on-the-fly software gyro workaround
              that Ronak flagged: "if gamepad supports
              software you can do on the fly gyro so it
              can work even in unsupported games. Gyro
              will mimic Joystick function once assigned
              in Software." This workaround is documented
              in the Lumora / Drakon / Stellaris / Blitz
              manuals already, but the AI wasn't
              proactively surfacing it for non-Windows
              platform questions.

    (2) Follow-up turn: customer asked "to play games like
        BGMI" on iPad. AI responded "BGMI will recognize
        it as a standard gamepad for button input (aim,
        shoot, move, etc.)" -- which is FALSE. Web search
        confirms: BGMI / PUBG Mobile does NOT natively
        support gamepads on iOS or Android. The Quora /
        Cashify / Amkette product-listing sources are all
        consistent on this. The third-party workarounds
        (Mantis Gamepad Pro, Panda Gamepad Pro) are
        Android-only with rooted devices and risk Krafton
        ban; on iOS / iPad there is no working solution.
        AI fabricated game support from gamepad-shape
        priors -- the same KB-silence hallucination
        pattern flagged repeatedly in v2.12.x / v2.14.x /
        v2.15.x.

    (3) The iPad customer was specifically asking about
        BGMI. The AI's compounded errors meant: customer
        thinks gyro is a workaround that exists on PC but
        not iPad (false -- the Ares Pro has no gyro at
        all), AND BGMI works as a standard gamepad on
        iPad (false -- BGMI doesn't accept gamepads on
        iPad in any way). The customer would have bought,
        plugged in, found nothing worked, and asked for a
        refund. Worse: if they tried Mantis/Panda on
        Android, they could get their BGMI account banned.

  Fixes shipped in v2.19.0:

  1. ARES PRO -- NO GYRO correction:
     - CATALOGUE_CONTROLLERS Ares Pro line: removed "gyro"
       from the feature list. New line correctly omits
       gyro from the feature set. Description updated to
       reflect actual capability.
     - Ares Pro PRODUCT_MANUALS entry: added an explicit
       "GYRO: NONE" section near the top of the manual.
       States clearly that the Ares Pro has NO gyro
       hardware, that this is a hardware fact (not a
       platform limitation), and recommends Lumora /
       Drakon / Stellaris / Blitz Tri-Mode for customers
       who need gyro.
     - Ares Pro "COMMON FAILURE MODES TO AVOID" block:
       added a "Do NOT claim Ares Pro has gyro" rule.
       The catalog was wrong; the manual was right by
       omission. Both now consistent.
     - BUYING GUIDE: kept Ares Pro as "best all-rounder"
       since gyro removal does not change its top-level
       value prop, but customers prioritising gyro now
       get redirected to the gyro-equipped models.

  2. NEW: GAME-SPECIFIC GAMEPAD SUPPORT VERIFICATION POLICY
     block added to SYSTEM_PROMPT (placed near the existing
     CONSOLE COMPATIBILITY RULE since both deal with
     platform / game compatibility claims). The block tells
     the AI:
       - Before claiming a specific game works (or works
         well) with a CB controller, web_search the game's
         current gamepad support status. Don't trust priors;
         mobile-game gamepad support changes and many
         touch-first games have NO native support.
       - If web search confirms support: state confidently
         with the source.
       - If web search confirms no support: state THAT
         clearly, plus any third-party workarounds AND
         their risks.
       - If inconclusive: don't fabricate; recommend the
         customer check the game's official documentation
         or contact support.
       - NEVER fabricate game compatibility -- the BGMI
         "will recognize it as a standard gamepad" line
         is exactly the kind of fabrication that costs
         Cosmic Byte sales.

     Plus an explicit BGMI / PUBG Mobile sub-section with
     actual facts:
       - Does NOT natively support gamepads on iOS or
         Android.
       - Third-party Android apps (Mantis Gamepad Pro,
         Panda Gamepad Pro) work via touch-coordinate
         mapping but require rooted Android, cost money,
         and risk Krafton account ban.
       - On iOS / iPad: no working solution. iOS doesn't
         allow this kind of input-mapping app.
       - Legitimate path for BGMI + controller: PC via
         emulator (BlueStacks / GameLoop / LD Player) --
         the emulator handles input mapping at the OS
         level so the game itself doesn't need to support
         gamepads.
       - Honest answer to "will [CB controller] work for
         BGMI on iPad?" -> NO. Recommend touch controls
         on iPad, or PC + emulator.
       - Honest answer to "will [CB controller] work for
         BGMI on Android?" -> Native: NO. Workaround
         exists with caveats. Recommend PC + emulator.
       - Other potentially-problematic mobile titles
         flagged for verification: Free Fire, Call of
         Duty Mobile, Mobile Legends, Genshin Impact.
         Always web search before answering.

  3. NEW: ON-THE-FLY SOFTWARE GYRO ON NON-WINDOWS PLATFORMS
     POLICY block added to SYSTEM_PROMPT (placed near the
     v2.16.0 MAC COMPATIBILITY POLICY). The block tells
     the AI:
       - When customer asks about gyro / motion control on
         iOS / iPad / Mac / Android, do NOT just say "gyro
         doesn't work on this platform". The honest answer
         is more nuanced and useful.
       - Native gyro on Bluetooth gamepads is generally
         unavailable on iOS / iPad (MFi protocol limit),
         limited on macOS, varies on Android.
       - WORKAROUND -- ON-THE-FLY SOFTWARE GYRO: a real CB
         differentiator. Explained step by step:
           1. Configure on Windows via Cosmic Byte software
              -- assign gyro to LEFT or RIGHT joystick.
           2. Setting persists in onboard memory.
           3. Pair to iPad / Mac / Android via Bluetooth.
           4. Gyro now drives joystick movement on the new
              platform.
           5. Works in any game that supports gamepad /
              joystick input.
       - Confirmed controllers with this feature: Lumora,
         Drakon, Stellaris, Blitz Tri-Mode (manuals
         describe it explicitly).
       - EXPLICITLY NOT in this list: Ares Pro (no gyro
         hardware at all -- see fix #1 above), Ares
         (Tri-Mode), Ares Wired, Ares Wireless, Nexus,
         Eclipse, Starforge -- these models do not have
         gyro and / or do not have on-the-fly software
         gyro; the workaround does not apply.
       - Caveats: requires one-time Windows access for
         setup; the destination game must support gamepad
         / joystick input (loops back to the BGMI
         policy -- if the game doesn't accept gamepads
         at all, the gyro workaround can't help).
       - WHAT NOT TO SAY:
           * "Gyro is NOT supported on iPad" without
             checking if the controller has on-the-fly
             gyro -- this loses sales.
           * Promise the workaround works without
             confirming the controller is on the
             confirmed list.
           * Claim the workaround makes BGMI / Free Fire
             / etc. playable on iPad -- the limit there
             is the GAME, not the gyro.

  Followup notes:
    - The AI's iPad / BGMI response also said "Vibration
      works, but you can't adjust it via iPad. You'd need
      to configure vibration settings on a Windows PC ...
      using the Cosmic Byte software, and those settings
      carry over to iPad use." This part was actually
      reasonable per the v2.16.0 MAC COMPATIBILITY
      POLICY. Not changed in this version.
    - Open from earlier: backup strategy beyond email
      digest; Drakon ML/MR vs L4/R4 software label
      mismatch; ORDER & SHIPPING POLICIES gap.

  Verification: ast.parse OK on Python 3.

v2.18.0 (2026-05-08) -- Claude
  - Y-bump: persist customer-facing chat history to disk so a
    customer's previous thread is restored on revisit even
    after a Render redeploy. Triggered immediately after
    v2.17.0 was deployed: Ronak tested by sending a message,
    closing the tab, and reopening, and was surprised that
    the thread didn't restore. v2.17.0 had only persisted the
    admin-facing conversation log; the customer-facing chat
    history (the cookie-keyed in-memory store from v2.12.0)
    was still server-ephemeral by the v2.10.x design. v2.18.0
    extends disk persistence to cover that store too, since
    we now have the disk infrastructure.

  Background:
    The portal has TWO independent stores. v2.17.0 made (1)
    persistent. v2.18.0 makes (2) persistent.
      (1) Admin conversation log (admin dashboard, daily
          email digest, support records). File:
          /var/data/support_log.jsonl. Done in v2.17.0.
      (2) Per-(browser_id, product) chat history. When a
          customer comes back to the portal, their previous
          thread is rehydrated from this store via the
          cb_bid cookie. File: /var/data/chat_history.json
          (new in v2.18.0).

    Without v2.18.0, every time Render redeployed, every
    customer's open chat thread vanished. With v2.18.0, the
    thread is still there. 7-day expiry from v2.12.0 is
    preserved -- expired entries get dropped on both load
    and the existing _purge_expired sweep.

  What this version does NOT do (still ephemeral, by intent):
    - Image attachments are still stripped from history
      before storage (same as v2.12.0 -- _strip_images_for_history
      replaces image payloads with an inline placeholder). The
      original image bytes do NOT go to disk; only the customer's
      text + an "[image attached in original message]" note. This
      keeps the file small and avoids storing potentially-sensitive
      raw uploads to disk indefinitely.
    - Cross-device continuity (same customer on a different
      browser sees the same thread) is OUT OF SCOPE. The cookie
      is per-browser by design. Cross-device would need a
      server-side identity / login system, which the portal
      doesn't have.
    - Streamlit session state for the active session.

  Code changes:

  1. New constant HISTORY_FILE_PATH added to the v2.17.0 disk
     persistence block. Set to {PERSISTENT_DATA_DIR}/chat_history.json
     when the disk is mounted; None otherwise. Co-located with
     LOG_FILE_PATH and DIGEST_STATE_PATH so all on-disk file
     paths live in one place.

  2. The startup "persistent disk OK" log line updated to mention
     both stores so the operator can see at a glance that v2.18.0
     persistence covers both.

  3. New helpers in the chat history section:

       _history_disk_lock -- separate threading.Lock from the
         conversation log lock. Different files, independent
         locks; a chat-history rewrite shouldn't block a
         conversation-log append (or vice versa).

       _load_history_from_disk() -- reads the JSON file once on
         cold start. Format is {"entries": [{"bid", "product",
         "messages", "updated_at"}, ...]}. Tuple keys are
         reconstructed from the bid+product fields. Expired
         entries (older than HISTORY_EXPIRY_DAYS) are dropped
         on load -- same eviction policy as the in-memory
         _purge_expired. Malformed entries are skipped with a
         counter print, not raised; corruption in one entry
         shouldn't lose every other customer's chat. Returns
         {} on cold-start-with-no-file, parse failure, or if
         the disk isn't mounted.

       _save_history_to_disk(store) -- atomic full-rewrite
         (tmp + os.replace) under the lock. Datetimes are
         serialised via .isoformat(). No-op if disk not mounted.

  4. get_history_store() now rehydrates from disk on cold
     start (same @st.cache_resource pattern as get_shared_store
     in v2.17.0). Disk read happens once per Render instance
     lifetime; subsequent reads are served from RAM.

  5. _save_history() now calls _save_history_to_disk(store)
     after the in-memory mutation. Every chat turn = one disk
     write. At realistic volume (~100 active browsers, ~2MB
     file) this is a few-millisecond rewrite -- well within
     SSD bandwidth.

  6. _clear_history() now calls _save_history_to_disk(store)
     after dropping entries. Covers both the per-product clear
     and the full-browser-id clear paths.

  7. _purge_expired() now calls _save_history_to_disk(store)
     ONLY when something was actually evicted. Preserves the
     "no-op when nothing to do" pattern so a quiet page load
     doesn't cause a disk write.

  Test plan (for Ronak):
    1. Open https://ai.thecosmicbyte.com, send a message,
       close the tab.
    2. Trigger a Render redeploy (Manual Deploy or push any
       small change).
    3. After redeploy, reopen the same browser to the same
       product page.
    4. Expected: the previous thread re-appears.
    5. Bonus: also check the admin dashboard -- the message
       should still be there too (v2.17.0 path).

  Caveats:
    - Pre-v2.18.0 in-memory chat history will be lost on the
      deploy that adds this. From the next conversation
      onward, history persists.
    - Race window: if Render restarts mid-write (between
      tmp file write and os.replace), the live file is
      either the old version OR the new version, never a
      partial-write. os.replace is atomic on POSIX. So
      restart safety is fine; we may lose at most the last
      message that hadn't yet completed its write.
    - Disk size projection: 7 days * 100 browsers/day *
      2 products * 10KB = ~14MB worst-case at current
      volume. The 1GB disk attached in v2.17.0 has 70x
      headroom. No size action needed.

  Followup notes:
    - Open from v2.17.0: backup strategy beyond daily email
      digest (e.g. periodic rsync to S3).
    - Open from v2.16.0: Drakon trigger sensor tech still
      unspecified; Drakon ML/MR vs software's L4/R4 label
      mismatch.
    - Open from v2.15.2: no general ORDER & SHIPPING
      POLICIES section in the KB.

  Verification: ast.parse OK on Python 3.

v2.17.0 (2026-05-08) -- Claude
  - Y-bump: persist the conversation log to disk so it
    survives Render restarts and redeploys. Triggered by
    Ronak: "Lets add disk to render so we can store all
    reponses. Else with every start it disappears."

  Background:
    Until now, the conversation log lived only in the
    in-memory shared store (@st.cache_resource). Across
    Render redeploys (which happen on every code push) and
    Render's periodic restarts, the log was wiped. The
    daily email-digest CSV partially compensated -- emails
    persist -- but anything logged today and not yet
    digested was lost on the next deploy. The v2.10.x
    decision to keep the log server-ephemeral was made
    when Cosmic Byte wasn't yet on a Render plan that
    supports persistent disks. That has now changed.

  What's persisted in v2.17.0:
    - Conversation log (every row from log_conversation):
      Date, Time, Session ID, Product, Customer Message,
      AI Response, Feedback, Feedback Note, Image
      Thumbnails (base64), Client IP.
    - Daily digest "last sent date" -- so a redeploy
      mid-day doesn't trigger a duplicate digest send.

  What's NOT persisted (still ephemeral, by design):
    - Per-(browser_id, product) chat history. This
      remains intentionally server-ephemeral as decided
      in v2.10.x -- it's a UX nicety for in-session
      rehydration, not a record of customer interactions.
      Could be migrated to disk in a future version if
      desired; not in scope for v2.17.0.
    - Streamlit session state for the current request.
    - Admin auth (already restart-safe via signed cookie
      from v2.13.0; no disk needed).

  Code changes:

  1. Import threading (added). Used for a module-level
     Lock that guards all disk reads/writes so concurrent
     Streamlit reruns can't interleave writes (an issue
     mainly for rows with image thumbnails > 4KB, where
     POSIX append-mode atomicity is no longer guaranteed).

  2. New constants and helpers placed just above
     get_shared_store():

       PERSISTENT_DATA_DIR -- env var CB_DATA_DIR with
         default "/var/data" (Render's standard mount
         path for persistent disks). Can be overridden
         for local dev or alternative mount points.

       _disk_persistence_enabled() -- checks that the
         data dir exists and is writable. If both true,
         disk persistence is on. Else, the portal runs
         with in-memory-only logging and prints a LOUD
         startup warning so the operator knows the disk
         isn't mounted.

       LOG_FILE_PATH -- {data_dir}/support_log.jsonl
         (None if disk not mounted).
       DIGEST_STATE_PATH -- {data_dir}/digest_state.json
         (None if disk not mounted).

       _load_log_from_disk() -- reads the JSONL log file
         line by line. Skips corrupted lines with a
         warning rather than failing the whole startup.
         Returns [] if the file doesn't exist (cold
         start with new disk).

       _append_log_to_disk(row) -- atomically appends a
         single row as one JSON line, under the lock.
         No-op if disk not mounted.

       _rewrite_log_to_disk(all_rows) -- writes the full
         log to a tmp file then os.replace()s it onto
         the real path. Used when an existing row is
         updated (feedback). Atomic on POSIX. No-op if
         disk not mounted.

       _load_digest_state() / _save_digest_state(date)
         -- small JSON file that holds last_digest_date
         so a same-day redeploy doesn't re-send the
         digest.

  3. get_shared_store() now rehydrates from disk on
     cold start. The @st.cache_resource decorator means
     this runs once per Render instance lifetime --
     loaded into memory, then served from RAM for all
     subsequent reads. Disk reads happen ONLY on cold
     start; runtime reads stay fast.

  4. log_conversation() now also calls
     _append_log_to_disk(row) right after appending in
     memory. The on-disk log and in-memory log stay in
     lockstep.

  5. update_feedback() now calls _rewrite_log_to_disk(log)
     after mutating the in-memory row. Feedback is
     comparatively rare (one event per conversation),
     so the full-rewrite cost is negligible at our
     volume (<10K rows ~ <50MB rewrite, milliseconds).

  6. auto_daily_digest() now calls _save_digest_state()
     after sending the digest, so the timestamp survives
     restarts.

  7. Startup print now states whether disk persistence
     is on or off, so the Render deploy log shows
     immediately whether the disk is mounted correctly.

  Render dashboard side (NOT a code change -- Ronak
  does this in the Render UI):

    a) Open the Render service for the support portal.
    b) Settings -> Disks -> Add Disk.
    c) Configure:
         Name: cb-support-data (or anything descriptive)
         Mount Path: /var/data
         Size: 1 GB (more than enough for years of logs
                even with image thumbnails; can grow
                later if needed)
    d) Save. Render will restart the service with the
       disk mounted.
    e) Verify: check the Render deploy log for the
       "[support_portal_v2] persistent disk OK at
       /var/data" line on next startup. If you see
       "WARNING: persistent disk NOT mounted" instead,
       the disk wasn't picked up and persistence is
       still off -- check the mount path matches.

  Caveats / things to know:
    - Render persistent disks lock the service to a
      single instance (no horizontal scaling). The
      portal already runs single-instance, so this
      changes nothing in practice.
    - Persistent disks require a paid Render plan
      (Starter or higher) -- not free tier.
    - Render does NOT auto-backup persistent disks.
      The daily email digest already provides a
      partial backup (yesterday's CSV emailed daily);
      that's still in place. For deeper backup, a
      future version could rsync the JSONL to S3 or
      similar -- not in scope for v2.17.0.
    - Existing in-memory log on the deploy that adds
      this IS NOT migrated. v2.17.0's first startup
      with disk = empty log on disk; from there
      forward, logs persist. This is fine because the
      pre-v2.17.0 log was already going to be lost on
      this deploy anyway.

  Followup notes:
    - Open: chat history persistence (separate scope,
      not done here).
    - Open: backup strategy beyond daily email digest
      (e.g. periodic rsync of /var/data to S3).
    - Open from v2.16.0: Drakon trigger sensor tech
      still unspecified; Drakon ML/MR vs software's
      L4/R4 label mismatch.
    - Open from v2.15.2: no general ORDER & SHIPPING
      POLICIES section in the KB.

  Verification: ast.parse OK on Python 3.

v2.16.0 (2026-05-08) -- Claude
  - Y-bump: substantive multi-item correction bundle covering
    Drakon joystick tech, Drakon package contents, and a new
    cross-product Mac compatibility policy. Triggered by
    Ronak's direct feedback after reviewing an AI Mac
    compatibility response that incorrectly told a customer
    the Cosmic Byte Ares is "not officially supported on
    Mac".

  Triggers (three issues bundled per Ronak's message):
    (1) AI told a customer "the Cosmic Byte Ares is primarily
        designed for Windows PC and Android -- unfortunately,
        native Mac support is not officially supported by
        Cosmic Byte". Per Ronak: ALL CB Bluetooth controllers
        DO work with Mac for basic gamepad use (just no
        Cosmic Byte software / drivers for Mac). The AI's
        answer was a worse version of the truth -- pessimistic
        and likely to lose a sale. The KB had no centralised
        Mac compatibility policy for controllers, only
        per-mouse / per-keyboard mentions, so the AI
        defaulted to "not supported".
    (2) Ronak confirmed Drakon has TMR joysticks, NOT Hall
        Effect. This resolves the contradiction flagged in
        v2.15.4's followup notes (the Drakon manual's
        "JOYSTICK CALIBRATION (TMR)" header was correct all
        along; the Hall Effect matrix and several
        cross-references were wrong). The product page URL
        itself contains "tmr-joysticks" -- confirming the
        manual was right and the matrix was wrong.
    (3) Ronak indicated Drakon comes with more accessories
        than the existing PACKAGE line listed. Per the
        official product images: 6 swappable joystick tops
        in 3 styles (short ridged concave, tall ridged
        concave, smooth dome) -- not "2 extra" as the manual
        had it. Two pre-installed plus four spare in the
        case = six total in three style pairs.

  Fixes shipped in v2.16.0:

  1. Drakon now correctly classified as TMR joysticks across
     ALL references in the file:
     - Hall Effect / TMR matrix line: "Drakon: Hall Effect
       joysticks (older, pre-TMR generation)" rewritten to
       "Drakon: TMR joysticks (confirmed by Cosmic Byte;
       product page URL contains 'tmr-joysticks'). Trigger
       sensor type not specified in the Drakon manual --
       Drakon has a 3-position physical trigger lock for
       digital / mid-analog / full-analog modes; if a
       customer asks specifically about trigger sensor tech,
       offer to confirm with support."
     - Blitz Tri-Mode KEY FEATURES JOYSTICKS line: removed
       Drakon from "main advantage over Lumora / Drakon
       (both Hall Effect)". TMR is no longer an advantage
       over Drakon -- both Blitz and Drakon have TMR.
       Updated to "main advantage over Lumora (which has
       Hall Effect joysticks, not TMR)".
     - PRODUCT COMPARISON GUIDANCE Drakon vs Lumora line:
       updated. Drakon now wins on TMR joystick precision
       AND RGB granularity (7 zones with up to 8 keyframes
       vs Lumora's 5 zones with preset animations) AND
       dragon artwork. Lumora wins on macro count (4 vs 2),
       button mapping flexibility (gamepad/keyboard/mouse
       vs gamepad-only), replaceable accessories scope
       (joystick tops + D-pad covers vs Drakon's joystick
       tops + D-pads + face plates -- different set), and
       trigger flexibility (analog/digital switchable
       triggers vs Drakon's 3-position physical lock).
     - CATALOGUE_CONTROLLERS Drakon line: "Hall Effect
       joysticks" -> "TMR joysticks". Description expanded
       to surface package contents (carrying case, charging
       dock, swappable face plates / joystick tops / D-pads).
     - CATALOGUE_CONTROLLERS BUYING GUIDE: "Best joystick
       precision (TMR)" list now includes Drakon alongside
       Blitz Tri-Mode and Stellaris 2nd Gen. "Distinctive
       RGB design" line kept Drakon (it already won there).

  2. Drakon manual updated:
     - PACKAGE line corrected: "2 extra joystick tops" ->
       "6 swappable joystick tops in 3 styles (short ridged
       concave / tall ridged concave / smooth dome) -- 2
       pre-installed on the controller, 4 spare in the
       case". Magnetic top covers / face plates clarified
       as "3 magnetic face plates (plain black / doodle
       artwork / dragon artwork)".
     - NEW KEY FEATURES summary block added near the top
       of the Drakon manual (mirroring Lumora and Blitz
       structure). Surfaces: TMR joysticks; 3-position
       physical trigger lock; 2 dedicated macro buttons
       (ML / MR -- note: software displays them as L4 / R4,
       still flagged as a future cleanup); 7-zone RGB with
       up to 8 keyframe animations; 6-axis gyro with native
       Bluetooth gyro mode plus on-the-fly software gyro;
       6 swappable joystick tops + 2 D-pads + 3 face
       plates; charging dock + carrying case included;
       1000Hz polling on wired/2.4GHz; tri-mode connectivity;
       600mAh battery 8-20 hours. Helps the AI answer
       "what's special about Drakon?" and surface Drakon
       in cross-product comparisons.

  3. NEW: MAC COMPATIBILITY POLICY block added to
     SYSTEM_PROMPT (placed near the INVOICE POLICY /
     WARRANTY OVERVIEW area since it is a cross-product
     policy block, not per-product manual content). The
     block states:
       - All Cosmic Byte Bluetooth controllers work on Mac
         for basic gamepad use. Pair via Bluetooth from
         macOS Bluetooth settings; controller appears as
         a standard gamepad in any game that supports
         standard gamepad input.
       - There is NO Cosmic Byte software / driver for
         macOS. Software-only features (custom button
         mapping, software RGB customisation, firmware
         updates via the Cosmic Byte software, software
         deadzone / anti-deadzone configuration) are
         WINDOWS-ONLY.
       - DO NOT tell a customer "this CB Bluetooth
         controller does not work with Mac". It does --
         just without advanced configuration.
       - Wired-only or older 2.4GHz-dongle-only models
         (older Ares wired-only batch, Nexus, etc.) --
         most work plug-and-play via USB on Mac for basic
         gamepad input but software is Windows-only;
         direct customers to test plug-and-play first.
       - Specifically called out as Mac-via-Bluetooth-OK:
         Lumora, Drakon, Stellaris (Gen 1 + Gen 2), Blitz
         Tri-Mode, Ares (Tri-Mode), Ares Pro, Ares
         Wireless, Eclipse, Starforge, Nexus (wired,
         plug-and-play), Quantum, Stratos Xenon. Anything
         with Bluetooth in this catalog works for basic
         gamepad use on Mac.
       - Closing: "If the customer's primary need is
         software-driven configuration on Mac, recommend
         they use the controller in basic gamepad mode and
         configure on a Windows machine first if possible
         -- onboard profiles persist between platforms."

  Followup notes:
    - Resolved: the v2.15.4 followup flag about the Drakon
      manual saying "JOYSTICK CALIBRATION (TMR)" while the
      matrix said Hall Effect. Matrix is now updated to
      TMR; manual was always correct.
    - Still open: the v2.15.4 followup about the Drakon
      manual MACRO section saying "ML/MR" while the Drakon
      software shows the buttons labeled "L4/R4". Likely a
      software display label vs button label mismatch;
      worth Ronak's confirmation before touching. Noted in
      the new Drakon KEY FEATURES block as a flag.
    - Still open: the v2.15.2 followup gap (no general
      ORDER & SHIPPING POLICIES section). Separate sweep.
    - Still open: Drakon trigger sensor tech is not
      specified anywhere in the file. The Drakon manual
      describes only the 3-position physical trigger lock,
      not the underlying sensor type. The new TMR matrix
      entry for Drakon explicitly says trigger sensor type
      is unspecified; if Ronak confirms (Hall Effect?
      TMR? Standard?), a Z-bump can patch it.

  Verification: ast.parse OK on Python 3.

v2.15.4 (2026-05-08) -- Claude
  - Y-bump pretending to be a Z (substantial KB fix bundling
    multiple manual updates and a new SYSTEM_PROMPT block).
    Triggered by two real customer interactions:
    (1) Customer with Blitz Tri-Mode asked if Lumora would be a
        better future upgrade. AI made TWO factual errors:
        (a) Falsely claimed Ares Pro has TMR joysticks.
        (b) Mis-positioned Lumora as a downgrade from Blitz
            Tri-Mode, only comparing joystick tech and missing
            all of Lumora's actual differentiating features.
    (2) Earlier customer interactions had surfaced AI confusion
        about Lumora's joystick tech, which traced back to a
        bug in the Hall Effect matrix.

  Root causes:
    - Hall Effect matrix line for Lumora was WRONG: it stated
      "Lumora: standard joysticks (no Hall Effect on Lumora)"
      while the Lumora product manual itself correctly listed
      Hall Effect joysticks + Hall Effect analog/digital
      switchable triggers. The matrix and the manual contradicted
      each other, and the AI was getting confused. Per Ronak's
      direct confirmation and the actual Lumora software /
      hardware: Lumora has Hall Effect joysticks (NOT TMR) and
      Hall Effect analog/digital switchable triggers.
    - Blitz Tri-Mode manual incorrectly listed "Macro programming"
      as a key feature. Per Ronak's confirmation: Blitz Tri-Mode
      has NO dedicated macro buttons. The existing "MACRO" section
      in the manual described a Turbo-button-based sequence
      recording feature, which is real but should not be called
      "macro" since Blitz has no dedicated macro buttons.
    - Blitz Tri-Mode also was implicitly assumed to have RGB and
      replaceable joystick tops / D-pad covers in cross-product
      comparisons. Per Ronak: Blitz has NONE of these.
    - The AI was inferring "newer / App Support label / current
      generation = TMR joysticks" — a synthesis error. Sensor tech
      varies across current-gen products (Lumora and Ares Pro
      are current-gen with App Support but have Hall Effect, not
      TMR; Stellaris 2nd Gen and Blitz Tri-Mode have TMR).
    - The AI was performing single-dimension product comparisons
      ("Blitz has TMR therefore Blitz is better than Lumora")
      instead of multi-dimensional comparisons that would surface
      Lumora's actual strengths.

  Fixes shipped in v2.15.4:

  1. Hall Effect matrix corrected. Lumora line updated to:
     "Lumora: Hall Effect joysticks + Hall Effect analog/digital
      switchable triggers (confirmed by Cosmic Byte). Lumora is
      NOT TMR despite being a current-generation product with
      software / 'App Support' — do not infer TMR from generation
      or positioning."

  2. Lumora manual KEY FEATURES section rewritten as a
     comprehensive accurate feature list. Now surfaces:
     - 4 dedicated macro buttons (ML/MR/LK/RK, 32 inputs each)
       — explicitly contrasted with Stellaris/Drakon (2 macros)
       and Blitz Tri-Mode (0 macros).
     - Full button mapping flexibility — gamepad, keyboard, OR
       mouse mapping. Lumora-exclusive among current CB
       controllers.
     - 6 replaceable joystick tops (3 styles) and 2 replaceable
       D-pad covers (square/diamond + faceted disc).
     - Cloak RGB design — controller appears solid black when
       RGB is OFF, reveals skull/gear artwork when RGB is ON.
       Distinct from Stellaris transparent variant.
     - 5 individually-colorable RGB zones with 5 animations,
       brightness/speed sliders, granular toggles.
     - 4 onboard profiles, switchable on the controller via
       M + Right Joystick Up/Down.
     - Independent per-grip vibration intensity.
     - Per-stick deadzone, anti-deadzone, Radial Trace.
     - Per-trigger deadzone, anti-deadzone.
     - 6-axis gyro with on-the-fly software customisation.

  3. Blitz Tri-Mode manual KEY FEATURES section rewritten:
     - Removed "Macro programming" claim. Replaced with
       explicit "MACRO BUTTONS: NONE" with recommendation to
       point macro-needing customers at Lumora/Drakon.
     - Added "RGB LIGHTING: NONE" with same redirect.
     - Added "REPLACEABLE JOYSTICK TOPS / D-PAD COVERS: NONE"
       with same redirect.
     - Clarified TRIGGERS as Hall Effect ANALOG only (not
       analog/digital switchable like Lumora).
     - Clarified BUTTON MAPPING as gamepad-to-gamepad ONLY
       (no keyboard/mouse mapping like Lumora).
     - Listed full software customisation surface: Initial/Max
       range sliders for sticks/triggers, Raw mode, Swap, etc.
     - Surfaced gyro robustness as a real Blitz strength.
     The existing MACRO section in the Blitz manual was renamed
     to TURBO SEQUENCE RECORDING and now explicitly states this
     is a Turbo-button feature, not dedicated macro buttons.

  4. PRODUCT COMPARISON GUIDANCE block added to SYSTEM_PROMPT
     (placed after the HALL EFFECT / TMR VERIFICATION GUIDE).
     Five rules:
     (1) Always consult the Hall Effect / TMR matrix.
         Do NOT infer joystick tech from generation /
         positioning / "App Support" label / software
         availability. Newer doesn't mean TMR. Examples
         called out: Lumora and Ares Pro are current-gen
         with software but Hall Effect (not TMR);
         Stellaris 2nd Gen and Blitz Tri-Mode have TMR.
     (2) Compare across MULTIPLE dimensions: joystick tech,
         trigger tech, macros, RGB, button mapping, replaceable
         accessories, gyro, vibration, profiles, design,
         polling, connectivity. Single-axis comparisons miss
         actual customer-relevant tradeoffs.
     (3) Do NOT default to "newer = better". Many CB
         cross-product comparisons are SIDE-GRADES with
         different strengths. Specific guidance for
         Lumora vs Blitz Tri-Mode and Drakon vs Lumora.
     (4) When asked "what's the best CB controller?",
         do NOT pick. Ask what the customer values, then
         recommend based on stated priorities.
     (5) Do NOT invent feature comparisons. If unsure, say
         so and offer to look up — do NOT guess.

  Verification: ast.parse OK on Python 3.

  Followup notes:
    - The Drakon manual still says "JOYSTICK CALIBRATION (TMR)"
      while the Hall Effect matrix says Drakon has Hall Effect
      joysticks. This contradiction was NOT touched in this
      version — flagged for a future cleanup version once
      Ronak confirms which is correct.
    - The Drakon manual MACRO section says "ML/MR" while the
      Drakon software shows the macro buttons labeled "L4/R4".
      Likely just a software display label vs button label
      mismatch; not touched in this version. Worth confirming
      with Ronak.

v2.15.3 (2026-05-08) -- Claude
  - Z-bump: add HALL EFFECT / TMR VERIFICATION GUIDE block to
    SYSTEM_PROMPT after a real customer interaction where the
    AI gave a workable but suboptimal answer to "how do I
    confirm my Ares has Hall Effect joysticks?".

  Trigger:
     Customer wanted to verify Hall Effect status without
     opening the controller and without waiting for support.
     The AI proposed a "stress test then recheck for drift"
     methodology, which is partially valid but has known
     gaps (brand-new potentiometer joysticks pass the test,
     producing false negatives). The AI also did not surface
     the simpler back-label check, which is faster and more
     reliable.

  Reality (per Ronak, from Cosmic Byte's own testing):
     - Hall Effect and TMR joysticks on Cosmic Byte
       controllers show 0-2% circularity error on gamepad
       testing tools (max for same-model units, tested by
       the Cosmic Byte team).
     - Potentiometer joysticks typically show 10-20% error,
       especially after some use.
     - 2026 batch back labels of Hall Effect / TMR products
       mention "Hall Effect" or the relevant sensor type
       directly, providing a 5-second physical check that
       requires neither opening the controller nor running
       any software.

  Fix: New "HALL EFFECT / TMR VERIFICATION GUIDE" block
  added to SYSTEM_PROMPT (placed immediately after the
  existing Hall Effect quick-reference matrix since both
  cover the same topic). The block tells the AI:

    1. ALWAYS suggest the back-label / packaging check FIRST.
       Fastest, no software needed, no risk to the unit.
    2. If the customer wants software-based confirmation:
       direct them to https://hardwaretester.com/gamepad and
       describe the THREE specific tests:
         (a) Resting drift — 0-2% for Hall Effect / TMR;
             5-20% for potentiometer.
         (b) Corner accuracy — Hall Effect / TMR consistently
             hit close to 100% in all 4 corners; potentiometer
             often falls short (95-98%) with corner-to-corner
             variation.
         (c) Smoothness — Hall Effect / TMR shows smooth
             transitions on slow movement; potentiometer often
             shows stepped or jittery values.
    3. Caveats explicitly listed for the AI: brand-new
       potentiometer joysticks may show low drift initially;
       drift develops with use over weeks/months; resting
       drift and corner accuracy are MORE diagnostic than
       aggressive stress testing.
    4. What NOT to suggest:
       - DO NOT tell customers to open the controller — voids
         warranty, risk of damage.
       - DO NOT lead with the stress-test-then-recheck
         methodology as the primary test (false negatives
         on new units).

  Verification: ast.parse OK on Python 3.

v2.15.2 (2026-05-08) -- Claude
  - Z-bump: add INVOICE POLICY block to SYSTEM_PROMPT after a
    real customer interaction where the AI invented a
    self-service invoice download portal that does not exist.

  Trigger:
     Customer asked "how to download invoice" (All Products
     context). The AI confidently walked the customer through
     visiting "https://track.thecosmicbyte.com/", entering
     order number + email, and "downloading the invoice"
     from a non-existent self-service page. Same KB-silence
     hallucination pattern as v2.12.1 (Raptor), v2.12.2
     (Blitz dock), v2.14.0 firmware-updater, v2.14.1 Gen 1
     LED, and v2.15.1 Eclipse/Starforge software.

  Root cause:
     "How to download invoice" is a generic e-commerce
     question. The KB has no section covering order-management
     or invoice/shipping policies — only product manuals.
     With no information available, the AI pattern-matched to
     typical e-commerce flows (Amazon-style "View Order ->
     Download Invoice button") and fabricated a URL that
     sounded plausible.

  Reality (per Ronak):
     - Orders shipped through the Cosmic Byte website
       generate invoices automatically.
     - Customers receive the invoice via EMAIL once the order
       is shipped, and again on delivery.
     - Customers also receive a HARDCOPY of the invoice with
       the product (inside the package).
     - There is NO online invoice download portal. Customers
       cannot self-serve download an invoice from any URL.

  Fix:
     New INVOICE POLICY block added to SYSTEM_PROMPT (placed
     near the WARRANTY OVERVIEW section since both are
     cross-product policy content rather than per-product
     manual content). Block states the three facts above
     explicitly and tells the AI:
       - DO NOT invent a self-service download URL.
       - DO NOT direct customers to a "track.thecosmicbyte.com"
         invoice page or any other invoice download URL.
       - If customer hasn't received the email, suggest
         checking spam/promotions, confirming the email
         address on the order, and contacting support to
         have it resent.
       - Hardcopy is always inside the product package — if
         customer says they didn't receive a hardcopy, that's
         a packaging issue and should be raised with support.

  Followup gap (offered, not shipped):
     The KB has no general "ORDER & SHIPPING POLICIES" section.
     This means the AI is currently underdetermined on:
       - Order tracking (where does the customer track? does
         the website have an order tracker, or is it via a
         shipping partner like Shiprocket?)
       - Returns and refunds (process, timeline, eligibility)
       - Shipping speed expectations (delivery windows, regions)
       - Cancellation policy
       - Coupon/discount policies beyond ONLINEPAY
     Each of these is a future invention waiting to happen.
     Ronak should consider a sweep of order/shipping policies
     when convenient (separate from product manual sweep).

  Verification: ast.parse OK on Python 3.

v2.15.1 (2026-05-08) -- Claude
  - Z-bump: correct an incorrect claim shipped in v2.15.0
    affecting Eclipse and Starforge.

  Trigger:
     Customer asked how to update Eclipse firmware. The portal
     (with v2.15.0 just deployed) walked the customer through
     downloading "the Cosmic Byte companion software" and
     using its firmware-update option. WRONG — Eclipse and
     Starforge do not have any PC companion software at all.

  Root cause (my fault, not the AI's):
     When Ronak originally clarified Eclipse and Starforge in
     the v2.15.0 prep, he said: "Eclipse and Starforge also
     support Keylinker app for mobile for button mapping. No
     firmware update for these using keylinker." That was
     accurate. I assumed the unstated half ("if not Key Linker,
     then it must be the standard PC-software path") instead
     of asking. Same failure mode I keep flagging in the AI
     itself: filling a gap with a plausible synthesis instead
     of confirming.

  Reality (Ronak confirmed):
     - Eclipse and Starforge have NO PC companion software at
       all. Single-generation products. No "App Support" back
       label distinction. All controller configuration (RGB,
       turbo, vibration, macros, calibration) is done via
       gamepad button shortcuts on the controller itself.
     - Key Linker mobile app (iOS/Android) on these two
       controllers handles BUTTON REMAPPING ONLY. No firmware
       updates via Key Linker either.
     - Firmware updates: MANUAL file path. If/when a firmware
       update exists for these products, it is posted on
       thecosmicbyte.com (downloaddrivers section or the
       product page) along with instructions. Customer
       downloads the file and applies it manually following
       the on-page instructions. There may not always be a
       firmware update available — customer should check the
       website periodically if needed.

  Fixes:

  1. Eclipse manual: removed the false "firmware via companion
     software" block. Replaced with accurate statement: no PC
     software exists; firmware updates are manual via website
     when available. Key Linker scope (iOS/Android, button
     remapping only) preserved.

  2. Starforge manual: same fix as Eclipse.

  3. SYSTEM_PROMPT firmware rule: restructured to recognise
     four product categories rather than one rule with two
     exceptions:
       - Category A: Products with companion PC software
         ("App Support" generations) → firmware via software,
         wired USB.
       - Category B: Products with manual-file firmware path
         → customer goes to website, downloads file when
         available, follows on-page instructions. Examples:
         Eclipse, Starforge, Ares Pro Gen 1, older Ares
         family models.
       - Category C: Products with mobile-app firmware path
         → Stellaris Gen 1 only (Key Linker via Bluetooth).
       - Category D: Products without any user firmware
         updates → most basic / passive products.
     This makes the actual product taxonomy explicit instead
     of the AI inferring it from scattered exception phrasing.

  4. Stellaris failure-modes block: bullet about Key Linker
     scope updated again to be precise — Eclipse and
     Starforge use Key Linker for BUTTON REMAPPING ONLY (NOT
     firmware), Stellaris Gen 1 uses Key Linker for both,
     and the platform is iOS/Android (mobile-only).

  Verification: ast.parse OK on Python 3.

v2.15.0 (2026-05-08) -- Claude
  - Y-bump: KB sweep across all 36 product manual entries to find
    and fix the same hallucination patterns that produced
    v2.12.1 (Raptor), v2.12.2 (Blitz dock), v2.14.0 (Stellaris
    rewrite + universal firmware rule), and v2.14.1 (Stellaris
    Key Linker scope). Sweep was triggered after the v2.14.1
    Gen 1 LED-via-Key-Linker bug demonstrated that the same
    failure pattern was likely present elsewhere.

  Sweep methodology:
     Scanned every manual entry for four patterns -- "sold
     separately" without confirming current availability,
     "check website" without confirming the page exists,
     app/tool name references without scope boundaries, and
     multi-generation products without explicit ASK-FIRST
     guidance. Produced a triage report with answers
     requested from Ronak. Ronak responded with definitive
     answers, which this changelog entry implements.

  ──────────────────────────────────────────────────────────────
  CHANGE 1 -- SYSTEM_PROMPT: UNIVERSAL FIRMWARE RULE updated
  ──────────────────────────────────────────────────────────────
  Discovered (per real customer interaction history): the v2.14.1
  rule "no separate firmware updater tool ever exists" is too
  sweeping. There is one more legitimate exception:

  - Ares Pro Gen 1 (no "App Support" back label, older model
    without companion software) -- firmware is updated MANUALLY
    via a separate standalone firmware file from
    thecosmicbyte.com. The customer downloads the file and
    applies it manually. This is the only currently-sold
    product line where this manual-firmware-file path applies.

  The rule is updated to explicitly include this as a second
  exception alongside Stellaris Gen 1 (Key Linker mobile app).

  Also added: "App Support" back-label check guidance. Three
  product lines (Ares Pro, Stellaris, Blitz) have current-gen
  models with companion software vs older models without.
  AI is now instructed to ask the customer to check the back
  label for "App Support" text when firmware/software questions
  involve any of these three products.

  ──────────────────────────────────────────────────────────────
  CHANGE 2 -- Stellaris failure-modes block: Key Linker scope updated
  ──────────────────────────────────────────────────────────────
  v2.14.1 said "Key Linker is Stellaris Gen 1 only." That is
  incorrect. Eclipse and Starforge ALSO use the Key Linker
  mobile app -- but only for button remapping, NOT for firmware
  updates. (Stellaris Gen 1 uses Key Linker for both button
  remap AND firmware updates -- that's unique to Gen 1.)

  Updated the Stellaris failure-modes bullet covering Gen 2 and
  Key Linker to read accurately: Key Linker is used by Stellaris
  Gen 1 (button remap + firmware), Eclipse (button remap only),
  and Starforge (button remap only). It is NOT used by current
  Stellaris (Gen 2), Ares family, Blitz family, mice, or
  keyboards.

  ──────────────────────────────────────────────────────────────
  CHANGE 3 -- ARES PRO entry: ASK-FIRST + firmware contradiction fix
  ──────────────────────────────────────────────────────────────
  The Ares Pro entry contained a direct contradiction: line 2614
  said "do NOT use any other firmware files" while lines 2617-2619
  said older non-App-Support models DO use a separate standalone
  firmware file. Ronak confirmed: older models DO use a separate
  manual firmware file path. The contradiction was on the
  "current/Gen 2" side -- that line was correctly absolute for
  Gen 2 only.

  Restructured Ares Pro entry similar to the Stellaris v2.14.0
  treatment:
    - ASK-FIRST guidance at top (current Ares Pro vs Gen 1 older
      model, distinguished by "App Support" back label).
    - Section for current Ares Pro (App Support label) -- software
      handles config and firmware. The firmware update is done
      THROUGH the software, not as a separate file.
    - Section for Ares Pro Gen 1 (no App Support label) -- no
      software; firmware update is a manual file download from
      thecosmicbyte.com; customer should contact support if they
      cannot find the right file for their model.
    - Common failure modes block: do not tell Gen 1 customers to
      use software (it does not work for them); do not tell
      Gen 2 customers to download a separate firmware file
      (their firmware is in the software).

  ──────────────────────────────────────────────────────────────
  CHANGE 4 -- Eclipse and Starforge entries: KeyLinker scope clarified
  ──────────────────────────────────────────────────────────────
  Eclipse line 3081 and Starforge line 3134 said "KeyLinker app
  available for advanced customisation" without specifying scope.
  Customer asking about firmware update on Eclipse/Starforge
  could be told to use Key Linker (wrong -- Key Linker on these
  controllers does NOT update firmware; it only handles button
  remapping).

  Updated both entries to clarify:
    - Key Linker mobile app on Eclipse and Starforge handles
      BUTTON MAPPING ONLY.
    - Firmware updates on Eclipse and Starforge follow the
      universal rule (companion PC software, wired USB).
    - Do NOT direct customers to Key Linker for firmware on
      these products.

  ──────────────────────────────────────────────────────────────
  CHANGE 5 -- STRATOS XENON + QUANTUM: dongle URL added
  ──────────────────────────────────────────────────────────────
  Stratos Xenon manual mentioned "wireless dongle (sold
  separately)" without a URL. Same exact phrase pattern as the
  Blitz dock bug pre-fix. Confirmed by Ronak: the dongle IS
  currently sold and the URL is
  https://www.thecosmicbyte.com/product/cosmic-byte-stratos-xenon-gamepad-dongle-for-pc-gamepad-not-included-black/.
  ALSO confirmed: the SAME dongle works for the Quantum
  controller -- so the Quantum manual now documents this as
  well.

  ONLINEPAY (10% off online payments) applies to the dongle
  the same as any other purchase. AI is told this explicitly so
  it does not invent a separate coupon.

  ──────────────────────────────────────────────────────────────
  CHANGE 6 -- MICE: macOS support stated explicitly
  ──────────────────────────────────────────────────────────────
  Several mouse entries (Velox, Aether) said "check website for
  macOS" or "Windows-primary, check website" -- the exact
  "check website" pattern that triggered the Raptor download
  hallucination. Per Ronak: ALL Cosmic Byte mice work on macOS
  for basic plug-and-play use, but there is NO dedicated macOS
  software for any mouse. Software-only features (custom DPI
  beyond presets, button remapping, macros, polling rate
  adjustment, custom RGB) are Windows-only.

  Updated affected entries (Velox, Aether, and any others with
  ambiguous phrasing) to state this explicitly. AI is told not
  to direct macOS users to any "macOS software page" -- it does
  not exist.

  ──────────────────────────────────────────────────────────────
  CHANGE 7 -- ASTRA: switch compatibility stated precisely
  ──────────────────────────────────────────────────────────────
  Astra entry's "Confirm on thecosmicbyte.com before purchasing"
  guidance for switch compatibility was vague. Per Ronak: Astra
  works with 3-pin AND 5-pin mechanical switches (Cherry MX,
  Gateron, Kailh, Outemu in either pin format). It does NOT work
  with Optical switches (Trinity uses optical -- different
  socket). It does NOT work with Magnetic switches.

  Replaced the "confirm on website" wording with this explicit
  list.

  ──────────────────────────────────────────────────────────────
  CHANGE 8 -- DRAGONFLY: separate software clarified
  ──────────────────────────────────────────────────────────────
  Dragonfly manual mentioned "(separate software for keyboard
  and mouse)" without explaining where to find each. Updated to
  state explicitly: the Dragonfly downloads page on
  thecosmicbyte.com lists Dragonfly Keyboard software and
  Dragonfly Mouse software as two separate entries; download
  both if the customer wants to configure both peripherals.

  ──────────────────────────────────────────────────────────────
  CHANGE 9 -- ARES (basic), ARES WIRED, ARES WIRELESS: ASK-FIRST
  ──────────────────────────────────────────────────────────────
  These three Ares-family products all have a 2026 batch (Hall
  Effect joysticks + analog triggers, possibly with newer
  features) and an older batch (standard joysticks, 125Hz on
  basic Ares). The manuals describe both batches but do not
  formally tell the AI to ask the customer which batch they
  have before answering. Added ASK-FIRST guidance at the top
  of each entry.

  Hint to identify: 2026 batch generally has 1000Hz polling and
  Hall Effect; older batch has 125Hz and standard sensors.
  Customer can also check the back label or product page for
  "Hall Effect" mention.

  ──────────────────────────────────────────────────────────────
  CHANGE 10 -- ARES WIRELESS: missing warranty section restored
  ──────────────────────────────────────────────────────────────
  The Ares Wireless entry ended without a warranty section
  (the entry just stopped after the disconnections
  troubleshooting). Added a warranty section consistent with the
  rest of the Ares family.

  ──────────────────────────────────────────────────────────────
  CHANGE 11 -- SYSTEM_PROMPT: "Pro Controller" Bluetooth name guidance
  ──────────────────────────────────────────────────────────────
  Multiple Cosmic Byte controllers pair as "Pro Controller" via
  Bluetooth in their respective Gyro / Switch-protocol modes
  (Stellaris Gen 1 in PC mode, Lumora in PC Gyro mode, possibly
  others). If a customer asks about "Pro Controller" appearing
  in their Bluetooth list without context, the AI previously had
  to guess or ask vaguely.

  Added explicit guidance: "Pro Controller" is the Bluetooth
  name used by multiple Cosmic Byte controllers in Nintendo
  Switch-compatible (Gyro / NS) Bluetooth mode. Replicates the
  Switch Pro Controller protocol so Gyro works like a Switch
  controller. NOTE: triggers are NOT pressure-sensitive in this
  mode (analog triggers act as digital). If a customer mentions
  "Pro Controller" without specifying which product they own,
  ask which Cosmic Byte controller they have before answering.

  ──────────────────────────────────────────────────────────────
  CHANGE 12 -- SYSTEM_PROMPT: WARRANTY GUIDANCE
  ──────────────────────────────────────────────────────────────
  Confirmed by Ronak: all Cosmic Byte products carry 1-year
  warranty against manufacturing defects. The warranty period
  for an individual product is printed on the MRP label on the
  product packaging. AI is told this explicitly so it can guide
  customers who ask about warranty periods generally.

  ──────────────────────────────────────────────────────────────
  Verification: ast.parse confirms the file parses on Python 3.

v2.14.1 (2026-05-08) -- Claude
  - Z-bump: tighten the Stellaris Gen 1 / Gen 2 boundary in
    KNOWLEDGE_BASE["Stellaris"]. Real customer interaction
    revealed two boundary gaps in the v2.14.0 rewrite.

  Trigger:
     Customer asked "How do I change LED in Stellaris Gen 1?"
     The AI walked the customer through using the Key Linker
     mobile app to change LED color. WRONG. Key Linker on
     Gen 1 is for button remap + firmware updates only --
     RGB lighting on Gen 1 is controlled exclusively via
     gamepad button shortcuts (SELECT + D-pad Left to cycle
     modes, SELECT + D-pad Right to switch single colors,
     etc.). The AI also did not ask the customer about black
     vs transparent variant before answering, which the
     ASK-FIRST guidance specifically requires for RGB
     questions.

  Root cause:
     The v2.14.0 Gen 1 section said "Key Linker handles
     firmware" without explicitly saying what Key Linker
     does NOT handle. The AI synthesised "Gen 1 has no PC
     software, Key Linker is the only mobile app mentioned,
     therefore Key Linker is the way to do anything on
     Gen 1." Same KB-silence-fills-with-plausible-fiction
     pattern as v2.12.1 (Raptor), v2.12.2 (Blitz dock),
     v2.14.0 firmware-updater.

  Fixes:

  1. Gen 1 section: Key Linker scope now stated explicitly
     as "button remap + firmware update ONLY". The exact
     phrase "RGB and lighting on Gen 1 are NOT done through
     Key Linker -- use gamepad shortcuts" added in two
     places (lighting subsection and Key Linker subsection)
     so neither path can be reached without seeing the
     boundary. Added a step-by-step "HOW TO CHANGE LED
     COLOR ON GEN 1" procedural block so the AI has explicit
     steps to recite rather than synthesising from scattered
     shortcut references.

  2. Gen 2 section: explicit "Gen 2 does NOT support Key
     Linker -- Key Linker is Gen 1 only" line added, to
     prevent the inverse error (telling a Gen 2 customer
     to use Key Linker because that's how the AI saw
     Stellaris-and-mobile-app paired in the KB).

  3. ASK-FIRST GUIDANCE: variant question for RGB topics
     promoted from "ask if the answer would differ" to
     "ALWAYS ask before answering any RGB / lighting
     question on Stellaris", because the variant-difference
     (transparent has the outer ring) is essentially always
     material to a complete answer, and the previous
     softer phrasing let the AI skip the ask.

  4. COMMON FAILURE MODES TO AVOID block: two new bullets
     covering the Key Linker scope boundary and the variant-
     ask requirement.

  Verification:
     ast.parse on Python 3 confirms file parses. Pure KB
     content edit, no UI/data-flow changes.

v2.14.0 (2026-05-08) -- Claude
  - Y-bump: Stellaris knowledge-base restructure + universal
    firmware-update rule + duplicate-key bug fix. Three things
    bundled because they were discovered together while addressing
    a customer interaction where the AI invented a fictional
    "Stellaris 2nd Gen Firmware Updater" tool with a /downloaddrivers/
    URL.

  Trigger:
     A real Stellaris 2nd Gen support session in which the AI
     fabricated a non-existent firmware updater download and walked
     the customer through using it. Same failure pattern as v2.12.1
     (Raptor "available software" -> AI invented download URL) and
     v2.12.2 (Blitz dock "sold separately" -> AI invented coupon
     codes and accessory product URL). KB silence on a specific
     mechanism -> AI fills the gap with plausible-but-fictional
     detail.

  ──────────────────────────────────────────────────────────────
  FIX 1 -- KNOWLEDGE_BASE["Stellaris"] DUPLICATE-KEY BUG
  ──────────────────────────────────────────────────────────────
  The KNOWLEDGE_BASE dict had TWO "Stellaris" entries: the full
  manual at line 2065 (~95 lines) and a near-empty stub a few
  hundred lines later containing only "[Already defined above]"
  plus a single Bluetooth-polling-rate paragraph. Python dict-
  literal "last wins" semantics meant the stub silently
  overwrote the full manual. For however long this duplicate
  has existed, live customers have been getting an almost-empty
  Stellaris KB injected into the system prompt. Discovered by
  Claude Code during code review of the v2.14.0 prep work.

  Fix:
     Stub deleted. The stub's only unique content (Bluetooth
     polling rate detail) was already present at lines 2090-2094
     of the full manual, so the deletion is purely subtractive.
     KNOWLEDGE_BASE["Stellaris"] now resolves to the single
     restructured full manual entry described in FIX 2.

  ──────────────────────────────────────────────────────────────
  FIX 2 -- STELLARIS MANUAL ENTRY: Gen 1/Gen 2/transparent variant
  ──────────────────────────────────────────────────────────────
  The previous Stellaris entry was effectively Gen-2-only and did
  not document Gen 1 (discontinued but still under warranty for
  some customers) or the transparent variant (which has an
  additional outer RGB ring around the body that the black variant
  does not have). The entry was also organized as one flat block,
  which made it impossible for the AI to know when to ask
  clarifying questions vs. when to answer directly.

  New structure of KNOWLEDGE_BASE["Stellaris"]:
    - VARIANT/GENERATION ASK-FIRST guidance at the top
    - CURRENT STELLARIS (was "Gen 2") -- default; the AI assumes
      this unless customer signals otherwise. TMR joysticks,
      magnetic triggers, Gyro (Bluetooth-only), Analog/Digital
      trigger switch, 1000Hz wired/2.4G + 125Hz BT, multi-platform
      PC/Android/iOS/macOS, companion software, all the existing
      Gen 2 detail reorganized into a clean section.
    - LEGACY STELLARIS GEN 1 -- discontinued; warranty support
      only. Magnetic joysticks + magnetic triggers, NO Gyro, NO
      companion software (firmware via "Key Linker" mobile app
      over Bluetooth), 3 RGB modes only (vs Gen 2's 4), physical
      mode switch on back (Android/WIN PC/iOS positions),
      different RGB shortcut combos (Select+D-pad rather than
      Turbo+Select), pairing names per Gen 1 user manual:
      "Pro Controller" on PC, "CB Stellaris Controller" on
      Android, "Xbox Wireless Controller" on iOS.
    - TRANSPARENT VARIANT -- applies to both gens. Has an extra
      outer RGB ring around the controller body, controlled by
      the same shortcuts as the gen's other RGB zones. Black
      variant does not have this ring. AI is instructed to ask
      about variant when answering RGB-related questions only.
    - COMMON FAILURE MODES TO AVOID (AI-facing notes) telling
      the AI:
        * Don't say Gen 1 has no RGB. Both gens have RGB.
        * Don't say Gen 2 RGB is software-only. Gen 2 RGB has
          gamepad shortcuts AND software.
        * Don't forget the transparent variant's outer ring.
        * Don't confuse the two gens' shortcut combos.
        * Default to Gen 2; switch to Gen 1 only on customer
          signal. Don't proactively ask "Gen 1 or Gen 2?" on
          every query.

  Why default to Gen 2: Gen 1 is discontinued. New sales are all
  Gen 2. The signal-driven Gen-1-fallback approach lets the AI
  serve the common case fluently while still helping legacy
  warranty customers when their questions reveal an older unit.

  ──────────────────────────────────────────────────────────────
  FIX 3 -- SYSTEM_PROMPT: UNIVERSAL FIRMWARE-UPDATE RULE
  ──────────────────────────────────────────────────────────────
  Added a global block to SYSTEM_PROMPT (placed after the Hall
  Effect quick-reference matrix, similar shape -- a cross-product
  factual rule that overrides per-product manual assumptions).

  The rule:
    - For ANY Cosmic Byte product with software support, firmware
      updates are done THROUGH the companion software, NOT through
      a separate firmware-updater tool.
    - The process is always: download companion software from
      thecosmicbyte.com -> connect device in WIRED USB mode ->
      open the software -> use the firmware update option inside
      it.
    - There is NEVER a separate "Firmware Updater" download.
      Never a separate firmware file.
    - EXCEPTION: Stellaris Gen 1 (discontinued) used the
      "Key Linker" mobile app over Bluetooth.
    - Products without software support do not have user firmware
      updates.

  Why the global rule (rather than only Stellaris-specific): the
  same failure mode would have hit Helios, Umbra, Ignis, Phantom
  TKL, Lumora, Aether, and every other software-supported product
  the next time anyone asked about firmware. One global rule is
  cheaper and more robust than per-product KB notes.

  Verification:
     ast.parse on Python 3 confirms file parses (no syntax errors
     introduced by the dict-literal deletion or the SYSTEM_PROMPT
     append). Streamlit components untouched -- this is a pure
     content/data fix, no UI changes.

v2.13.1 (2026-05-07) -- Claude
  - Z-bump: fix StreamlitDuplicateElementKey regression introduced
    in v2.13.0. The admin auth work added three additional
    `stx.CookieManager(key="cb_cookie_mgr")` calls (auth-restore
    check, login success handler, sign-out button) on top of the
    existing one in the v2.12.0 customer history block. I had
    assumed Streamlit dedupes components by key; it does not --
    each call registers a fresh element with the same key, which
    Streamlit refuses with StreamlitDuplicateElementKey.

  Fix:
     Hoist the cookie manager to a single instantiation point
     before the admin gate. Bind the manager and its cookies dict
     to module-level names (_cookie_manager, _cookies) so all
     downstream code -- admin gate, login handler, sign-out
     button inside render_admin(), and the customer history
     block -- reads from the same instance. The original four
     instantiations are reduced to one.

  Specifics:

  1. New top-level block placed just before "# -- ADMIN LOGIN
     GATE --":
        _cookie_manager = None
        _cookies = None
        if not st.session_state.get("embed_mode"):
            _cookie_manager = stx.CookieManager(key="cb_cookie_mgr")
            _cookies = _cookie_manager.get_all()
     Skipped in embed_mode (third-party cookies unreliable in
     iframes; same gating as v2.12.0).

  2. Admin gate auth-restore check no longer creates a manager;
     it reads the shared `_cookies` dict directly. If `_cookies`
     is None (first render, or embed mode) it falls through to
     the login form, same as before.

  3. Login success handler calls `_cookie_manager.set(...)` on
     the shared instance instead of creating its own. Guarded by
     `if _cookie_manager is not None` for the embed_mode edge
     case (admin should never be entered via embed in practice,
     but the guard keeps it from crashing if it ever were).

  4. Sign-out button inside render_admin() also uses the shared
     `_cookie_manager`. Functions can read module-level names, so
     this works without parameter passing. Guarded the same way.

  5. Customer history block updated to use the already-bound
     `_cookies` and `_cookie_manager` instead of instantiating
     its own. The `if not embed_mode` gate stays; it's now only
     guarding the rehydration logic, not the component creation.

  Why this didn't break in v2.12.0 alone: there was only one
  CookieManager instantiation in the file. v2.13.0 added three
  more, and any path that crossed two of them tripped the check.

v2.13.0 (2026-05-07) -- Claude
  - Y-bump: two admin-page UX fixes that user reported:
       (a) Refreshing the admin page logged the operator out
           because admin_authenticated is in st.session_state,
           which Streamlit wipes on hard refresh.
       (b) The admin panel had no way to refresh the data view
           without going Back to Support and re-entering it.

  Fix (a) -- persistent admin auth via signed cookie:

  1. Two new constants near the existing HISTORY constants:
        ADMIN_AUTH_COOKIE_NAME = "cb_admin_auth"
        ADMIN_AUTH_DURATION_HOURS = 8
     Eight hours = roughly one work day. Long enough to avoid
     re-login during a shift; short enough that a forgotten
     browser overnight expires the session.

  2. New helpers _make_admin_auth_token() and
     _verify_admin_auth_token() use HMAC-SHA256 keyed by
     ADMIN_PASSWORD over the expiry timestamp. Token format:
        "<expiry_iso>|<hmac_hex>"
     Stateless: survives Render restart because the password
     comes from environment / secrets, so the same HMAC verifies
     after a redeploy. No server-side token store needed.

  3. Admin gate flow extended:
       - On entering the gate while not authenticated, instantiate
         the cookie manager (same key "cb_cookie_mgr" used by the
         v2.12.0 customer history flow -- Streamlit dedupes the
         component by key) and read cookies.
       - If a cb_admin_auth cookie is present, validate it. On
         success, set admin_authenticated = True and continue to
         render_admin() in the same render. No password prompt.
       - On failed validation or missing cookie, fall through to
         the existing password form.
       - On successful password login, mint a fresh token and call
         cookie_manager.set with expires_at = now + 8h. The cookie
         is what makes the auth survive page refresh.

  4. Brief login-form flash on hard refresh: the cookie manager
     component takes one render to mount (returns None from
     get_all() initially). On hard refresh you may briefly see
     the password field before the second render auto-restores
     the session. Acceptable papercut; a true loading screen
     would add complexity for marginal UX gain.

  Fix (b) -- in-panel actions:

  5. New top-of-panel action row in render_admin() with two
     buttons placed before the existing data divider:
       - "🔄 Refresh data" -- calls st.rerun(). Because
         render_admin() snapshots the log via list(get_log()) at
         the top, a rerun reads the latest store state. No auth
         change.
       - "🚪 Sign out" -- deletes the cb_admin_auth cookie, clears
         admin_authenticated and show_admin in session_state, and
         reruns. This is the explicit "I'm done" action.

  6. Behavior of the existing bottom "<- Back to Support" button
     is unchanged: it sets show_admin = False but keeps the
     auth cookie, so the operator can return to admin without
     re-login. Two distinct actions:
        Back to Support -> go back, stay logged in
        Sign out        -> clear cookie, full logout

  7. New stdlib imports near the top of the file: hmac, hashlib.
     Both are part of the Python standard library; no
     requirements.txt change needed.

  Security notes:
     The token is HMAC'd against ADMIN_PASSWORD, so a stolen
     cookie cannot be forged without the password (or a hash
     match that's astronomically unlikely with SHA-256). However,
     a stolen cookie value is replayable until expiry -- there is
     no per-cookie revocation list. For the threat model of an
     internal admin tool this is fine; if it ever needs hardening,
     options are: shorter expiry, IP binding (with the trade-off
     that it breaks on network change), or a server-side token
     store (loses the stateless-across-restart property).

v2.12.3 (2026-05-07) -- Claude
  - Z-bump: fix Raptor Mouse line in the All-Products compact
    catalogue (line ~4897 before this edit) to match its full
    manual. User confirmed the max DPI is 4800.

  Before:
     - Raptor Mouse: Wired, 3200 DPI. Budget option.
  After:
     - Raptor Mouse: Dual-mode (wired + 2.4GHz, no Bluetooth),
       4800 DPI. Entry-level wireless option.

  Two errors corrected on the same line:
     1. "Wired" -- the Raptor is dual-mode (2.4GHz + wired) per
        its full manual, not wired-only.
     2. "3200 DPI" -- the Raptor's sensor (PixArt 3212) goes from
        800 to 4800 DPI per its full manual; user confirmed.

  Why this matters operationally:
     The compact catalogue is what the AI sees in the system
     prompt when the dropdown is set to "All Products." The full
     per-product manual is only injected when a specific product
     is selected. So a customer in "All Products" mode asking
     "which budget mouse has wireless?" would have been told the
     Raptor is wired (wrong), or one asking "what DPI does the
     Raptor go up to?" would have been told 3200 (wrong by 1600
     DPI). Now both views agree.

  Note: I left the category heading "BASIC / OFFICE" unchanged.
  Strictly speaking, Raptor is now in a slightly different niche
  from Atlas and Umbra (which really are wired-only), but the
  catalogue's coarse buckets still work. Recategorising is a UX
  call, not a correctness fix, and you may want to do it
  alongside any future catalogue restructure.

v2.12.2 (2026-05-07) -- Claude
  - Z-bump: KB content fix to stop the AI claiming the Blitz Tri-Mode
    charging dock is "sold separately" and currently purchasable.
    User reported a real customer interaction where the bot said
    the dock was sold separately, gave a coupon code (ONLINEPAY,
    10% off), and linked to the Blitz Tri-Mode CONTROLLER product
    page when the customer asked where to find the charging dock.
    The dock has not yet launched.

  Root cause:
     The Blitz Tri-Mode manual described the charging dock as
     "sold separately" in three places:
       - Comparison table row: "Charging dock | Yes (sold separately)"
       - Key features list: "Charging dock support (sold separately)"
       - Charging section: "CHARGING: USB-C or Charging Dock (sold
         separately)."
     "Sold separately" reads as a real, currently-purchasable
     accessory. Claude combined that with the controller's product
     URL (the only Blitz product page that exists) and the standard
     ONLINEPAY coupon pattern from elsewhere in the system prompt,
     and produced a confident purchase journey for an item that
     does not yet exist.

  Fix:
     Inserted a "CHARGING DOCK STATUS — IMPORTANT" block right
     under the Blitz vs old-Blitz comparison table. The block:
       (a) States plainly that the dock has NOT YET LAUNCHED and
           will be available on thecosmicbyte.com on its own
           product link when released.
       (b) Explicitly tells the AI not to say "sold separately"
           or "available now," not to link the controller page
           for the dock, and not to apply a coupon code to it.
       (c) Gives the AI the correct response template for when a
           customer asks about the dock: "coming soon, here's how
           to charge in the meantime via USB-C."
     The three legacy "sold separately" mentions are reworded to
     "coming soon (not yet launched)" so the manual is internally
     consistent and the AI can't pattern-match against the old
     phrasing if the override block is partially missed.

  Same failure pattern as v2.12.1 (Raptor software). Both bugs
  are caused by KB sentences that imply a product/feature exists
  when it doesn't. A future content sweep should look for:
     - "sold separately"  (anywhere a product is not yet launched)
     - "Check the website for available X"
     - "X support" without a clear yes/no
     - Mismatches between full manuals and the All-Products
       compact catalogue (still pending: Raptor specs at line
       ~4897 contradict the full manual).

v2.12.1 (2026-05-07) -- Claude
  - Z-bump: KB content fix to stop the AI hallucinating that the
    Raptor Mouse has companion software. User reported a real
    customer interaction where the bot confidently linked
    /downloaddrivers/ for a Raptor and described software features
    (RGB customisation, DPI levels, etc.) that do not exist for
    this model.

  Root cause:
     The Raptor Mouse entry in PRODUCT_MANUALS (line ~2833 before
     this fix) ended its RGB description with:
        "Check thecosmicbyte.com for available Raptor software."
     That phrasing reads as "go check, software is available." The
     AI then pattern-matched against the ~15 other mouse / keyboard
     manuals in the KB that all legitimately point to
     thecosmicbyte.com/downloaddrivers/, and produced a confident
     answer with the URL filled in. The model was being faithful
     to its source material; the source material was the bug.

  Fix:
     Replaced the misleading sentence with an explicit "SOFTWARE:
     NONE" block that:
       (a) states clearly that the Raptor has no companion software
       (b) tells the AI not to direct customers to /downloaddrivers/
           for this model
       (c) gives the AI the correct response to use when a customer
           asks about Raptor software (configured via buttons on
           the mouse itself).
     The surrounding RGB sentence is kept but reworded to make
     hardware-only control explicit.

  Side issue NOT fixed in this bump (flagged for the user):
     The "All Products" compact catalogue at line ~4897 describes
     the Raptor Mouse as "Wired, 3200 DPI. Budget option." which
     contradicts the full manual (dual-mode 2.4GHz + wired, no BT,
     800-4800 DPI). Same product, two different specs in two
     places. Did not touch this in v2.12.1 because the user has
     better visibility on which spec is actually correct. Worth
     reconciling on a future content pass.

v2.12.0 (2026-05-07) -- Claude
  - Y-bump: per-product chat history that persists across browser
    sessions for 7 days. A returning customer on the same browser
    sees their previous conversation rehydrated automatically;
    switching products in the dropdown loads that product's history
    independently. Server-ephemeral storage -- history lives in an
    @st.cache_resource shared store that is wiped on Render restart.
    User explicitly chose this depth in preference to disk/DB
    persistence; if Render redeploys the file (which we do often),
    history is lost. Acceptable tradeoff for a 7-day window.

  Why per-product, not global, history:
     A global thread carries Lumora context into Ares conversations
     etc. The existing API call sends the entire message list plus
     the currently-selected product's manual in the system prompt.
     Mixing products in the message history confuses pronoun
     attribution ("the same on this one"), leaks stale facts (button
     combos differ per controller), and grows token cost linearly.
     Each product gets its own thread; switching products switches
     threads.

  Why server-ephemeral, not persistent:
     Render's filesystem is ephemeral by default. Disk persistence
     would require a paid persistent-disk add-on; a real DB would
     be more setup. User picked the simple option. Worst case: a
     redeploy wipes everyone's history mid-window. Acceptable.

  Implementation:

  1. New dependency: extra-streamlit-components (stx). Provides a
     CookieManager component that exposes browser cookies to
     Python. Add to requirements.txt:
         extra-streamlit-components
     Without this, the import at the top of this file fails and
     the portal will not start.

  2. Constants near the top of the helpers section:
        HISTORY_EXPIRY_DAYS = 7
        HISTORY_COOKIE_NAME = "cb_bid"

  3. New shared store get_history_store() decorated with
     @st.cache_resource. Keys are tuples of (browser_id, product
     name); values are {"messages": [...], "updated_at": datetime}.
     Same lifetime as the existing log store.

  4. Helpers:
        _strip_images_for_history(messages) -> list
            Clones messages, drops base64 image payloads, and
            appends "*[image attached in original message]*" inline
            so the rehydrated conversation flow still reads
            sensibly when the customer scrolls back.
        _load_history(browser_id, product) -> entry or None
            Returns the entry if present and within
            HISTORY_EXPIRY_DAYS; lazily evicts expired entries on
            access.
        _save_history(browser_id, product, messages)
            Persists the conversation. Called only on real state
            transitions (after each AI response, and just before
            the user switches products) -- not on every Streamlit
            rerun.
        _clear_history(browser_id, product=None)
            Drops history for one product or for the whole browser.
        _purge_expired()
            Sweeps expired entries from the store. Cheap; runs
            once per page load.

  5. Cookie + rehydration block placed AFTER the admin
     authentication st.stop() so it does not render on the admin
     page, and BEFORE the customer-facing header. Flow:
        a. Skip entirely if embed_mode is True. Cookies are
           unreliable inside iframes embedded on third-party
           domains (Chrome, Safari, Firefox block third-party
           cookies by default). Embed-mode visits are one-shot
           anyway.
        b. Instantiate CookieManager and call get_all(). On the
           very first render of a new tab, this returns None
           (component still mounting); we skip rehydration on that
           render and pick up on the next rerun. This causes a
           ~100ms delay before history appears -- standard
           behavior for any custom Streamlit component.
        c. If a cb_bid cookie exists, that is the browser ID. If
           not, mint a fresh UUID and call cookie_manager.set with
           expires_at = now + 14 days (2x the history window so a
           returning visitor whose history is alive still has a
           valid cookie).
        d. Look up history for (browser_id, current_product). If
           an entry exists and st.session_state.messages is empty
           (i.e. we're not mid-conversation), rehydrate it and
           stash the entry's updated_at timestamp in
           st.session_state._restored_from for the toast notice.
        e. Use a session_state marker keyed by (browser_id |
           product) to avoid re-rehydrating on every rerun.
        f. Sweep expired entries with _purge_expired().

  6. Toast notice on rehydrate:
        "Restored from your visit on 5 May"
     Shown once per (browser, product) combination per session,
     gated by st.session_state._restored_shown so it does not
     re-fire on every Streamlit rerun.

  7. _on_product_change extended: before switching products, save
     the current product's messages (if non-empty). After
     switching, clear the rehydration marker so the new product
     rehydrates on the next render.

  8. Save-after-response: in the main chat handler, right after
     st.session_state.messages.append({"role": "assistant", ...}),
     call _save_history(bid, product, messages) so each turn
     immediately persists. Skipped in embed mode.

  9. New "Manage history" expander rendered after the chat history,
     visible only when there are messages and not in embed mode.
     Contains a clear-history button and a one-line caption noting
     the 7-day retention. Clear-history wipes both the store and
     the in-session message list and reruns.

  Privacy notes:
     Image attachments are NOT persisted -- they are stripped at
     save time and replaced with the inline placeholder. Warranty
     photos and address-label photos are the most sensitive
     payloads in this portal; they exist only in the live
     conversation and the daily CSV/email digest, never in the
     history store. The customer's IP IS persisted via the v2.10.0
     "Client IP" column in the conversation log; that is unchanged.

v2.11.0 (2026-05-07) -- Claude
  - Y-bump: revert all of v2.9.0 (agent-name tagging). User
    decision: only IP-based identification on the support
    portal; no name capture. Reasoning -- the "Tester ID"
    expander from v2.9.0 was visible to customers (collapsed
    but present), and the value of name tagging was marginal
    once IP logging from v2.10.0 was in place. IP is captured
    without user cooperation, customers see no UI change at
    all, and cross-referencing against the test-portal email
    digest (which has agent name + IP) does not need a name
    on the support side.

  Reverts (relative to v2.10.0):

  1. Removed "Agent Name" column from CSV_COLUMNS. The CSV
     schema goes back to its v2.8.x shape plus the v2.10.0
     "Client IP" column at the end. Existing in-memory rows
     written between v2.9.0 and now have an "Agent Name" key
     that csv.DictWriter will silently drop because of
     extrasaction='ignore' default... actually DictWriter's
     default is 'raise', so we explicitly do NOT carry the
     pre-bump rows forward as-is. Practically: the in-memory
     log resets on each Render restart anyway, so this is
     fine. If you have an older CSV export sitting in email
     with an "Agent Name" column, that file is fine as-is --
     this change only affects new exports going forward.

  2. log_conversation() signature: removed the agent_name=""
     kwarg and the "Agent Name" entry from the row dict.

  3. Call site at the bottom of the chat handler: removed
     the agent_name= argument. client_ip= stays.

  4. Session_state init: removed the block that reads
     `?tester=NAME` from query_params. The param is now
     ignored (Streamlit will not error on unknown params).

  5. Header: removed the _tester_pill rendering. Header
     reverts to just the brand image and the Live badge, as
     it was before v2.9.0.

  6. Removed the entire "Tester ID (internal use)" expander
     that sat under the header. Customers no longer see any
     internal-looking control. This is the main customer-UX
     cleanup the user asked for.

  Net effect:
     The support portal is back to a pure customer-facing
     UI (no internal-only widgets visible) plus the v2.10.0
     IP logging running silently in the background.

v2.10.0 (2026-05-07) -- Claude
  - Y-bump: log the client IP for every conversation row.
    Companion change in app.py captures the test-taker's IP
    once per test session and includes it in the result
    email. Together these enable cross-referencing test
    submissions against support-portal queries by IP --
    stronger than the agent-name tagging from v2.9.0
    because it does not depend on the agent voluntarily
    identifying themselves.

  Implementation:

  1. New helper _get_client_ip() reads X-Forwarded-For from
     st.context.headers (set by Streamlit Cloud and most
     managed proxies). First entry in the comma-separated
     list is the original client. Falls back to X-Real-IP,
     then to "" if neither is present (bare-metal deploys
     without a reverse proxy, or Streamlit < 1.36). Wrapped
     in try/except so any deployment quirk degrades to ""
     rather than crashing the page.

  2. New "Client IP" column appended to CSV_COLUMNS. Placed
     at the end so the visible columns (Date, Time, Session
     ID, Agent Name, Product, Customer Message, AI Response)
     stay in the same order managers are used to seeing in
     the digest. csv.DictWriter fills missing keys with ""
     so older in-memory rows from before the bump still
     write a well-formed CSV.

  3. log_conversation() takes an optional client_ip="" kwarg
     and writes it into the row dict. The single call site
     at the bottom of the chat handler passes
     _get_client_ip() directly so we capture per query --
     this matters because a long-lived browser session can
     change networks (laptop unplugged, switched to mobile
     hotspot) and we want each query attributed correctly.

  Operational notes:
     - Office NAT means multiple agents share one public IP.
       Use IP + timestamp + test-portal email to disambiguate
       which agent was testing at the moment a portal query
       fired from the office IP.
     - Home-network IPs are usually unique per agent, which
       makes attribution clean for remote testing -- record
       each agent's test IP once and look for it in the
       portal log.
     - VPN / mobile carrier CGNAT can defeat IP attribution.
       Combine with v2.9.0 agent-name tagging and the test-
       portal timing flags for a layered signal.

v2.9.0 (2026-05-07) -- Claude
  - Y-bump: tag conversation log rows with the operator's name
    so portal usage during agent-test windows can be cross-
    referenced against test-portal submissions. Companion
    change in app.py records per-question timing -- a join on
    (agent name, timestamp) flags any test answer submitted
    within seconds of a portal query, which is the strongest
    available signal that an agent is Claude'ing the test
    instead of taking it.

  Implementation:

  1. New session_state field "agent_name" populated from a
     `?tester=NAME` query param on page load. Empty string
     for normal customer traffic -- no behavioural change in
     the customer-facing path.

  2. New "Agent Name" column inserted into CSV_COLUMNS
     between "Session ID" and "Product". csv.DictWriter fills
     missing keys with "" by default, so older in-memory rows
     from before the bump still write a well-formed CSV.

  3. log_conversation() takes an optional agent_name=""
     kwarg and writes it into the row dict. The single call
     site at the bottom of the chat handler passes
     st.session_state.get("agent_name", "").

  4. UI: when agent_name is set, a small "Tester: NAME" pill
     renders next to the Live badge in the header so the
     operator visibly knows their queries are being tagged.
     A collapsed "Tester ID" expander below the header lets
     them set/clear the name manually if the URL param was
     missed. Customer traffic without the param sees no
     change at all.

  Operational:
     Distribute per-agent URLs like
     `https://<portal-host>/?tester=Priya` before each test
     window. After the window, build the cross-reference by
     joining test-portal email digests (which now include
     per-question submission timestamps and elapsed seconds)
     against the support-portal CSV log on agent name --
     any portal query within ~60s before a test answer
     submission is the smoking gun.

v2.8.2 (2026-05-07) -- Claude
  - Y-bump: bulk photo export from the admin dashboard.
    Complements the per-thumbnail download from v2.8.1 -- when
    the team needs to grab photos from an entire week's worth
    of warranty/return queries in one go, this is the faster
    path.

  Implementation:

  1. New helper build_images_zip(rows) sits next to
     build_csv_bytes() in the helpers section. Iterates the
     filtered rows, decodes each row's "Image Thumbnails" JSON,
     and writes every photo into an in-memory ZIP file using
     Python's stdlib zipfile module (no new dependency).

  2. Folder structure inside the ZIP:
       {date}_{session_id}/
           01_<original_name_basename>.jpg
           02_<original_name_basename>.jpg
           ...
     Examples:
       07-May-2026_e30e4078/
           01_L3-stick-defect.jpg
           02_packaging-damage.jpg
       06-May-2026_b7724dda/
           01_warranty-card.jpg
     Per-session folders keep all photos from one customer
     interaction together. Folder names include the date so
     they sort chronologically when extracted, and so duplicate
     session-IDs across days never collide. Numeric prefix on
     filenames preserves the order the customer attached them.

  3. Filename sanitisation: original name's basename is used,
     extension forced to .jpg (since stored bytes are JPEG --
     same logic as v2.8.1 single-photo download), and any
     stray path separators are stripped so a malformed name
     can't write outside the intended folder.

  4. Returns (zip_bytes, image_count, conversation_count) or
     (None, 0, 0) if no photos were found across the rows.

  5. UI -- new "📦 Export Photos (ZIP)" section placed right
     below the existing "📧 Email CSV Report" section in the
     admin dashboard. Honors the existing date / product /
     feedback filters at the top -- you filter to what you
     want, then click export.

  6. Button label dynamically shows what's about to be
     exported, e.g. "📦 Download all photos (47 from 23
     conversations · 1.2 MB)" so the admin knows the scope
     and size before clicking.

  7. Empty-state handling:
     - Filters match no rows: yellow warning ("No rows match
       current filters")
     - Filters match rows but none have photos: blue info
       ("No photos in the filtered conversations -- nothing
       to export")
     - ZIP build fails: red error with exception text

  8. Output filename includes the date filter and a timestamp,
     e.g. "cb_photos_07-May-2026_20260507_1430.zip" or
     "cb_photos_all_dates_20260507_1430.zip" -- helps when
     multiple exports accumulate in the admin's downloads.

  Performance note: ZIP is generated in-memory on each render
  while the admin is on the page. With a few hundred filtered
  rows and ~25KB per thumbnail, this is fractions of a second
  -- well within Streamlit's render budget. If filter scope
  ever grows to thousands of rows, can revisit by deferring
  ZIP build until button click via a session_state flag.

v2.8.1 (2026-05-07) -- Claude
  - Z-bump: small UX win on the admin dashboard. Each thumbnail
    in the conversation expander now has a "📥 Download photo"
    button right below it. One click saves a JPEG to the admin's
    computer with the original filename (extension forced to
    .jpg since the bytes are JPEG regardless of what the
    customer originally uploaded — prevents mismatched-MIME
    issues when opening). Removes the need to manually decode
    base64 from the CSV cell when the team wants to forward an
    image to a courier (delivery damage claim) or attach to an
    internal ticket.

  Implementation:
  - Used Streamlit's native st.download_button — no extra
    dependency, no JS hacks. Each button gets a unique key
    f"dl_{row_idx}_{thumb_idx}" so multiple downloads don't
    collide in Streamlit's widget tree.
  - Filename: original name's basename + .jpg. So a customer's
    "L3-defect.png" becomes "L3-defect.jpg" on download
    (matches the actual JPEG bytes).
  - Tiny CSS extension: .stDownloadButton button now picks up
    the same orange CB button styling as .stButton and
    .stFormSubmitButton (was previously rendering as a default
    Streamlit grey button -- looked out of place in the admin
    dashboard).

  No data model changes -- thumbnails were already in the CSV
  from v2.8.0. This bump just adds the download trigger.

  Future bigger improvement still on the table if useful: a
  bulk "📦 Export images for date range" button that ZIPs all
  thumbnails from filtered rows into a single download with
  per-session subfolders. Not done in this bump -- only do
  if/when the per-thumbnail download proves insufficient.

v2.8.0 (2026-05-07) -- Claude
  - Y-bump: NEW FEATURE -- attached photos now visible in the
    Admin dashboard. User confirmed they're on Render Hobby
    (ephemeral filesystem, no persistent disk), so persistent-
    file storage was ruled out -- went with thumbnails inline
    in the CSV log instead. Defaults agreed:
      * Medium thumbnails: 400px wide, JPEG quality 75
      * Retention: natural log lifetime (no extra cleanup needed)
      * Email CSV: thumbnails included automatically
      * Disclaimer: one-line photo-retention disclosure added

  Implementation:

  1. CSV schema -- added new column "Image Thumbnails" to
     CSV_COLUMNS (now 9 columns). Existing rows with no images
     write empty for this column. csv.DictWriter handles
     missing keys gracefully -- backward compatible.

  2. Thumbnail generation -- new helper _make_thumbnails_for_log()
     above log_conversation():
        * Decodes the base64 from each uploaded image
        * Opens via PIL (already imported as _PILImage)
        * Converts to RGB if needed (so RGBA/palette/etc. can
          save as JPEG)
        * Resizes to max 400px wide, preserving aspect ratio,
          using LANCZOS resampling (best quality for downsizing)
        * Saves as JPEG quality=75, optimize=True -- typical
          output is 20-40KB per thumbnail
        * Base64-encodes the JPEG bytes
        * Returns a JSON-serialized list of {name, data} dicts
     Per-image errors are caught individually -- a single bad
     image won't break the whole log entry. If all images fail,
     returns "" so the column stays empty.

  3. log_conversation() -- new optional `images=None` parameter.
     When provided, calls _make_thumbnails_for_log and stores
     the JSON in the new column. Existing call signatures still
     work (images defaults to None).

  4. Call site -- the AI-response handler now passes
     last_user_msg.get("images") into log_conversation. If no
     images attached, this is None and the column stays empty.

  5. Admin dashboard -- the row-expander rendering now reads
     the "Image Thumbnails" column. If non-empty, JSON-decodes
     and renders thumbnails in a 4-column grid (180px wide each)
     between the customer message and the AI response, captioned
     with the original filename. Malformed JSON or old rows
     without the column are handled gracefully.

  6. Email CSV -- no changes needed. build_csv_bytes() uses
     CSV_COLUMNS and writes whatever's in each row dict.
     Thumbnails travel with the email automatically. Each row
     with 4 images is ~80-160KB heftier than text-only rows --
     still very manageable for emailed reports.

  7. Customer disclaimer -- added one line to the existing
     orange-bordered AI disclaimer at the bottom of the chat:
     "Photos you attach are retained briefly with your
      conversation for support quality review."
     Keeps things transparent without scaring customers off
     using the feature.

  Storage math: a typical customer query with 2 images of
  defects/packaging adds ~60KB to one CSV row. Even with 100
  image-attached queries per day, the daily added log size is
  ~6MB, well within Hobby tier's working memory + email-CSV
  practical limits. If volume grows materially, can revisit
  by either:
    (a) reducing thumbnail size further (200px → ~10KB each)
    (b) adding retention cleanup (auto-delete thumbnails from
        log rows older than N days)
    (c) upgrading to Render with persistent disk and switching
        to Option 2 (full images on disk).

v2.7.2 (2026-05-07) -- Claude
  - Z-bump: fix misleading "200MB per file" text on the file
    uploader. User flagged: "200MB per file?" -- the helper text
    Streamlit auto-generates was contradicting the actual 5MB
    limit my Python validation enforces. A customer could pick
    a 50MB photo, wait for it to upload, then get rejected with
    a yellow warning -- bad UX, wasted bandwidth.

  Two parts to the fix:

  1. IN CODE (this bump):
     * Updated the file_uploader label to include the actual
       limits explicitly: "📎 Attach photos of your product or
       issue (optional) -- up to 4 images, 5MB each".
       Customers now see the real constraint before they pick
       a file.
     * Added CSS rules targeting
       [data-testid="stFileUploaderDropzoneInstructions"] small
       and [data-testid="stFileUploader"] section small to
       display:none, hiding Streamlit's default "200MB per file
       • PNG, JPG, WEBP, GIF" text. The accurate limit lives in
       the label + the help tooltip now, not in conflicting
       places.

  2. ON THE SERVER (one-time setup, not a code change in this
     file):
     User should add the env var STREAMLIT_SERVER_MAX_UPLOAD_SIZE=5
     to the Render service. This makes Streamlit enforce the
     5MB limit at the upload stage itself -- the browser refuses
     to even start uploading a file over 5MB. Saves bandwidth
     and gives instant feedback rather than waiting for the
     upload to complete and then being rejected by my Python
     validation.

  No functional changes to image handling, AI processing, or
  message construction. Pure UX accuracy fix on the frontend +
  one infrastructure note for the user.

v2.7.1 (2026-05-07) -- Claude
  - Z-bump: visibility fix for the v2.7.0 image uploader.
    User reported "Where is the add image or file option?" --
    the uploader was rendered correctly but visually invisible:
    label was set to label_visibility="collapsed" and the
    default Streamlit uploader styling blended into the dark
    theme background.

  Two fixes:

  1. Restored the label. Now reads "📎 Attach photos of your
     product or issue (optional)" with a paperclip icon prefix
     so it's obvious what the widget is for. Tooltip on hover
     reads "Up to 4 images, 5MB each. PNG, JPG, WebP, or GIF."

  2. Added explicit CSS targeting [data-testid="stFileUploader"]:
     - Label rendered in the brand orange, 12px, bold.
     - Drop zone given a dashed orange border on a slightly
       lighter dark background (#0c0c0c) so it stands out
       against the page background (#060606). Hover state
       brightens to solid orange border.
     - "Browse files" button styled to match the existing CB
       button language (orange fill, black text, uppercase
       Rajdhani, slight angle, etc.) so it reads as a real
       interactive control rather than greyed-out chrome.
     - Helper text and file size info given the muted-grey
       color used elsewhere in the UI.

  No functional changes -- the uploader, validation, message
  construction, AI image-handling, and logging from v2.7.0 all
  unchanged. Pure visibility fix.

v2.7.0 (2026-05-07) -- Claude
  - Y-bump: NEW FEATURE -- image attachments. Customers can now
    attach up to 4 photos (PNG/JPG/WebP/GIF, 5MB max each) along
    with their message. The AI examines the images and integrates
    what it sees into the response.

  Implementation:

  1. UI -- file uploader added to the chat form (st.file_uploader,
     accept_multiple_files=True, type=[png/jpg/jpeg/webp/gif]).
     Caption above the form tells the customer the limits (up to
     4 photos, 5MB each, supported formats). Uploader sits below
     the text input + Send button inside the same form so files
     submit together with the text on Send / Enter.

  2. Validation -- client-side checks before sending:
     * Cap at 4 images per message (extras dropped, customer
       warned which were skipped).
     * 5MB per file (Anthropic API hard limit; oversized files
       skipped with friendly warning).
     * Media-type detection from upload header, with PIL fallback
       for files where the browser didn't set Content-Type.
     * Files that fail validation are listed back to the customer
       in a yellow st.warning so they know what got dropped --
     no silent failures.

  3. Storage -- session state messages now optionally carry
     "images": [{"data": base64, "media_type": "...", "name": "..."}].
     Backward compatible: messages without "images" key continue
     to work as plain text.

  4. Chat history rendering -- when displaying a user message
     that has attached images, small thumbnails (180px wide) are
     rendered below the message bubble in up to 4 columns, each
     captioned with the original filename. Customers can see what
     they sent in the conversation history.

  5. API call -- the message construction loop was refactored.
     Plain-text user messages still send as a content string
     (existing behaviour, no regression). User messages with
     attached images now send as a content list:
       [
         {"type": "text", "text": "..."},
         {"type": "image", "source": {"type": "base64",
                                      "media_type": "...",
                                      "data": "..."}},
         ...
       ]
     The KB/buy-info injection logic was updated to handle BOTH
     content shapes -- if the first user message is a string, it
     wraps as before; if it's a list of blocks, the wrapper is
     applied to the text block only and image blocks are left
     intact. A note is added to the wrapped text telling the AI
     "the customer attached one or more images with this message
     -- examine each one carefully" so it doesn't ignore them.

  6. System prompt -- new "VISUAL EVIDENCE HANDLING" section
     placed right above the existing PC CONTROLLER TESTING
     section. Covers concrete cases: physical damage (route to
     warranty if defect; explain non-coverage if drop/water/
     tampering); receipts/invoices/warranty cards (read date +
     serial directly); packaging damage on delivery (returns
     portal + ticket, both); keyboard switches (reseat vs
     replacement guidance); LED state photos (mode confirmation);
     Windows error dialog screenshots (read error text verbatim);
     "is this a defect?" close-ups (be honest about manufacturing
     tolerance vs real defect); cable/connector damage (cable
     swap as first step). Plus 6 general rules: reference what
     you see specifically, answer text+image together, ask for
     clearer photos if unclear, be honest about non-coverage,
     never invent image details, never ask for re-upload.

  7. Logging -- the conversation log now records "[+N image(s)
     attached]" appended to the user_question text whenever the
     message included images. Lets analytics/admin dashboard
     see which sessions used the new feature.

  Cost impact -- a typical phone photo costs roughly 1000-2000
  input tokens (depending on dimensions). Per Anthropic's pricing
  for Haiku 4.5 this is single-digit-paise per image. The
  diagnostic accuracy gain (e.g. avoiding wrongly-routed warranty
  tickets, immediate visual confirmation of a defect) is worth a
  lot more than the marginal token cost.

  Out of scope this bump:
  - Video files (Anthropic API doesn't accept video natively;
    would need ffmpeg-based frame extraction -- deferred).
  - Audio (would need separate transcription step -- deferred).
  - Server-side image resizing/compression (5MB limit + 4-image
    cap is enough for v1; can add later if real-world uploads
    hit issues).

  Diagnostic expander from v2.5.2 is still in place -- if any
  image-related API call fails, the technical-details panel will
  show the error and full traceback for fast debugging during
  initial rollout. Plan to remove the expander once image support
  has been validated in production.

v2.6.5 (2026-05-07) -- Claude
  - Z-bump: data correction + new authoritative quick-reference
    matrix for Hall Effect on Ares controllers.

    Production failure on 07 May 2026 (session b7724dda, on the
    Ares product page): customer asked "DOES THIS HAVE BOTH HALL
    EFFECT JOYSTICKS AND TRIGGERS". The AI confirmed Hall Effect
    joysticks but said "Hall Effect triggers — Not documented in
    the manual I have access to" and routed the customer to the
    product page and customer support to confirm. User flagged
    the gap directly: "Yes Ares Tri Mode also has Hall Effect
    Triggers as well as Joystick. Same for Ares Wired, Ares
    Wireless, Ares Pro."

    Root cause: the "Ares" (Tri-Mode) PRODUCT_MANUALS entry was
    the only one of the four Ares variants that didn't mention
    Hall Effect triggers. Pre-fix line read:
      "2026 model: Tri-Mode (...), Hall Effect joystick, 1000Hz
       polling rate."
    -- "joystick" only, "triggers" missing. The other three Ares
    variants (Wired, Wireless, Pro) already correctly stated both
    in their PRODUCT_MANUALS entries -- this was a gap in just one
    of the four entries.

    Fix #1 -- Ares (Tri-Mode) PRODUCT_MANUALS entry updated:
      * "Hall Effect joystick" -> "Hall Effect joysticks AND Hall
        Effect analog triggers" in the generation note.
      * Added a dedicated "HALL EFFECT (2026 BATCH)" section
        mirroring the structure of the Ares Wired and Ares Wireless
        entries -- explicit confirmation that BOTH joysticks AND
        analog triggers are Hall Effect on current models, with the
        older-batch carve-out preserved.

    Fix #2 -- new HALL EFFECT QUICK-REFERENCE MATRIX added to
    SYSTEM_PROMPT (placed right above the LIVE PRICES line, near
    the existing model-disambiguation guidance). The matrix:
      * Confirms BOTH joysticks AND triggers are Hall Effect on
        current-batch Ares (Tri-Mode), Ares Wired, Ares Wireless,
        Ares Pro -- so the AI never has to fall back on "the
        manual doesn't specify".
      * Explicit instruction NOT to hedge: "do not say 'the manual
        doesn't specify' or 'I'm not sure about the triggers' for
        these four controllers."
      * Reference rows for other CB controllers with Hall Effect:
        Quantum (HE joysticks + HE triggers), Stratos Xenon (HE
        joystick + HE triggers), Stellaris 2nd Gen (TMR joysticks
        + HE analog triggers), Blitz Tri-Mode (TMR + HE triggers),
        Drakon (HE joysticks), Lumora (standard, no HE -- be
        honest about this).
      * Safety note: for models NOT in the matrix, ask the customer
        for exact model + batch year before answering -- do NOT
        guess "yes" for models not on the confirmed list.

    The matrix is now always loaded in context, so even if a
    customer asks about Hall Effect on a different product page,
    the AI has the authoritative answer.

v2.6.4 (2026-05-07) -- Claude
  - Z-bump: behavior fix. The Gamepad Tester multi-mode test had
    been added to the system prompt back in v2.5.5 (after the user
    validated it first-hand on real Android hardware), but the AI
    was not proactively offering it when customers reported
    vibration not working on mobile. User flagged this directly:
    "You are not suggesting this option to the customer when they
    claim vibration does not work in mobile."

    Root cause: structural ordering. The "VIBRATION NOT WORKING ON
    ANDROID" section led with per-controller troubleshooting AND
    the warranty-disclaimer line ("this is an Android limitation,
    not covered under warranty"). The Gamepad Tester multi-mode
    test was buried at the end as a "pro tip". The AI was anchoring
    on the first content it saw, dismissing the issue as
    out-of-warranty, and never reaching the actually-helpful
    suggestion at the bottom.

    Fix: hard restructure of the VIBRATION NOT WORKING ON ANDROID
    section.
    1. Added a new ENFORCEMENT RULE at the very top: "your FIRST
       response must offer the multi-mode Gamepad Tester test...
       Do NOT lead with 'this is an Android limitation, not covered
       under warranty' -- that line goes at the END as context,
       after you've offered an actual solution."
    2. The Gamepad Tester multi-mode test now sits FIRST in the
       section as the primary recommendation, with full step-by-step
       instructions and an exact verbatim messaging template the AI
       should use (or come close to). The template starts with
       "I have a suggestion that's been tested first-hand by our
       team and works well..." -- frames it as a positive,
       action-oriented suggestion rather than a deflection.
    3. The warranty/limitation line is now framed as "ONLY AFTER
       you've offered the test above" -- the AI is explicitly told
       to use it as background context, not as the lead.
    4. Per-controller specific notes (Stellaris/Blitz/Drakon
       DualShock shortcut, Lumora R3 method, Ares Tri-Mode PC-only
       carve-out) are kept but moved BELOW the lead recommendation
       and clearly labelled "supplementary -- use as context AFTER
       the test recommendation, not as a substitute for it".
    5. Ares Tri-Mode special case (vibration genuinely doesn't work
       on mobile at all -- PC XInput only) gets explicit guidance:
       "Be upfront with the customer about this rather than running
       them through a test that won't work."
    6. Other supplementary tips (game vibration setting, max
       intensity, OTG, PC verification via hardwaretester.com)
       reframed as "offer these only if the multi-mode test alone
       doesn't help" -- not as the primary path.

    No data changes -- just reordering and stronger enforcement
    language so the AI surfaces the right information first.

v2.6.3 (2026-05-07) -- Claude
  - Z-bump: added 3 customer-self-service URLs that the AI now
    surfaces by trigger phrase. None were previously in the system
    prompt -- the AI had no answer when customers asked
    "where is my order" or "how do I return this".

  New rule #11 in STRICT RULES, with three sub-rules:

  a) ORDER TRACKING -- https://track.thecosmicbyte.com/
     Triggers: "track my order", "where is my order", "when will it
     arrive", "shipment status", "AWB", typo variants (trak / ordr /
     shipement), or any question with an order/tracking number.

  b) RETURNS SUBMISSION -- https://track.thecosmicbyte.com/returns
     Triggers: "I want to return", "how do I return", "send back",
     "exchange this", "wrong product received", "damaged on
     arrival", "DOA", "refund process", typo variants.

  c) SHIPPING & RETURN POLICY -- https://www.thecosmicbyte.com/?page_id=2248
     Triggers: "what is your return policy", "shipping policy",
     "how many days do I have to return", "return window",
     "return charges", "COD available", typo variants.
     Brief summary of key points included (7-day window, original
     packaging required, etc.) but with the explicit instruction to
     link the policy page as the source of truth and NOT make up
     specific clauses. The page is authoritative -- the prompt's
     summary is a quick reference only.

  Routing logic captured at the bottom of the rule:
  - "Where is my order" only -> tracking URL only.
  - Wants to send something back -> returns URL + policy mention.
  - Asks about policy itself -> policy URL + brief summary.
  - Warranty/defect/manufacturing claim -> existing raise-a-ticket
    flow (rule #6/#7), NOT the returns URL. Returns portal is for
    customer-initiated returns within the 7-day window; warranty
    claims are a separate process.
  - The three URLs are SEPARATE -- never substitute one for another.

v2.6.2 (2026-05-07) -- Claude
  - Z-bump: bug fix to AI behavior, no new features. A real customer
    interaction on 07 May 2026 (session e30e4078, on the Ares product
    page) failed badly:

    Customer asked: "Tell me some plastation certified controler"
    The AI responded:
    - Refused with "I can only assist with products available on
      thecosmicbyte.com" -- WRONG, CB sells PlayStation-compatible
      controllers (Quantum and Stratos Xenon).
    - Then explicitly redirected the customer to PlayStation's store
      and "other retailers that carry Sony controllers" -- this
      drives customers AWAY from CB to competitors.
    - Then recommended the Ares (no console support) instead of
      Quantum/Stratos Xenon (the actually-relevant products).

    Why it failed: the existing "NEVER mention competitor brands"
    rule (was rule #1) was too abstract. The AI misclassified
    "PlayStation-certified controller" as "Sony's licensed product
    that CB doesn't carry" rather than "controller that works on
    PlayStation" -- and on the Ares product page, only the Ares
    manual was loaded, so the AI didn't have Quantum/Stratos Xenon
    detail readily in context.

    Fix: inserted a NEW rule #0 at the top of STRICT RULES,
    immediately above the existing competitor rule. It includes:
    (a) Explicit list of trigger phrases ("PlayStation-certified",
        "PlayStation controller", "PS4 controller", "PS5
        controller", "Sony-compatible gamepad") that must surface
        Quantum + Stratos Xenon.
    (b) Charitable typo handling -- common typos to read past:
        plastation/playstaion/ps -> PlayStation, controler ->
        controller, campatible -> compatible.
    (c) Hard prohibition on phrases that send customers off-site
        ("check PlayStation's official store", "visit Sony's
        website", "look at other retailers", etc.).
    (d) Worked example: the EXACT wrong response from session
        e30e4078 quoted verbatim as ❌ WRONG, paired with a ✅
        CORRECT answer that surfaces both Quantum and Stratos
        Xenon with their PS4 (full) and PS5 (PS4 games only) caveats.
    (e) Generalisation note: the same rule applies to Xbox/Switch/
        Logitech/Razer queries -- never redirect to the competitor;
        recommend the closest CB equivalent instead.

    Renumbered the original rule #1 (NEVER mention competitor brands)
    as a continuation -- the new ❌/✅ example is the enforcement
    mechanism, the abstract rule alone wasn't enough.

    Existing data was already correct: Quantum (line 1460) and
    Stratos Xenon (line 1505) both have detailed PRODUCT_MANUALS
    entries flagging "GENUINE CONSOLE SUPPORT", and the
    detect_products keyword map already routes "quantum" /
    "stratos xenon" / "stratos" correctly. The fix is purely
    a routing/framing improvement at the SYSTEM_PROMPT level
    so that even when those PRODUCT_MANUALS aren't injected
    (because the customer didn't name them), the AI still
    knows to surface them for any PlayStation-related query.

v2.6.1 (2026-05-07) -- Claude
  - Z-bump: integrity correction. The v2.6.0 entries for Kailh, Outemu
    Cream variants, and ~24 of 29 Outemu Pre-Lubed switches contained
    fabricated per-variant specs — Claude wrote them from training-data
    inference (with `~` hedge marks in some places) but presented them
    confidently as fact in the manual. User flagged this directly:
    "Tell me have you searched the web for all switch specifications to
    add it? Because website does not have specifications for each color
    and each variation". Honest answer was no — most weren't verified
    from the live web. This bump fixes that.

  WHAT CHANGED:

  1. Source-tag system introduced. Every spec in every brand manual
     is now tagged inline with one of:
       [CB published]                -- spec is on the CB product page
                                        itself or a CB-hosted spec sheet.
       [Web-sourced from {source}]   -- spec is from manufacturer's
                                        official site or reseller datasheet.
       [Specs not publicly documented] -- no verifiable source found.

  2. New SYSTEM_PROMPT block "DISCLOSING WEB-SOURCED SWITCH SPECS"
     placed alongside the existing switch-related content. It tells
     the AI: when citing a [Web-sourced...] spec, ALWAYS disclose
     the source to the customer ("per Cherry's official datasheet
     at cherry.de..." rather than presenting it as a CB spec). For
     [Specs not publicly documented] switches, point the customer to
     CB customer support directly rather than guessing.

  3. Cherry MX -- previously had `45gf, 1.9mm/3.7mm` etc. presented
     without source. Now: every spec line tagged [Web-sourced from
     cherry.de official + multiple datasheets]. Notes that CB-linked
     spec PDFs return 404 and the actual source is Cherry's own
     cherry.de pages and Mouser/Farnell-hosted datasheets. Added
     full datasheet detail (operating force tolerance, IP40 rating,
     bounce time, switching voltage, MX2A generation note, etc.)

  4. Gateron -- per-variant detail dramatically expanded. Web-sourced
     from gateron.com/products/gateron-g-pro-30-switch-set and
     gateron.com/pages/g-pro-20 (the official Gateron compare pages)
     plus mechanicalkeyboards.com, kbdfans, cannonkeys, kprepublic.
     Each of the 5 G Pro variants now has actuation force tolerance,
     bottom-out, pre-travel, total travel, spring length, and lifespan.
     Notes that CB-linked spec PDFs return 404 (same as Cherry).

  5. Kailh -- the worst-affected entry from v2.6.0. Previously had
     "~60g", "~45g" with hedge marks but presented as fact. Now:
     6 variants properly sourced. Added the click-bar detail (Kailh
     blues click on both press AND release, distinctive from
     Cherry/Gateron). Box switches IP56 + 1.8mm/3.6mm. Box Brown V1
     vs V2 difference flagged (V1 mushy 50g tactile, V2 stronger
     75g tactile -- CB doesn't specify which version they stock).
     Silver Speed switch: 40gf actuation, 1.1mm pre-travel, 3.5mm
     total -- 0.1mm shorter than Cherry Speed Silver.

  6. Outemu -- biggest restructure. The 5 CB-published spec sheets
     (Silent Lemon V1, Silent Honey Peach V1, Panda, Yellow Silver,
     Transparent Crystal Linear) kept verbatim and tagged
     [CB published]. Web-sourced specs added for: standard line
     (Black/Blue/Brown/Red), and 12 of the Pre-Lubed series I could
     find sources for (Maple Leaf 55gf, Spring Breeze 40gf tactile,
     Lotus 45gf linear, Maple Cold Plum 60gf linear, Milk Blue 50gf
     clicky, Milk Peach 45gf linear, Milk Tea 45gf tactile, Ocean/
     Silent Ocean ~45gf silent linear, Red Panda tactile, Silent
     Grey 55gf tactile, Silent White 45gf linear, Silent Yellow
     45gf linear). Sources tagged per variant.

  7. Outemu obscure variants explicitly marked [Specs not publicly
     documented]: Jadeite, Jerry, Pink, Tom Silent, White Blue.
     The system prompt routes the AI to direct customers to
     CB customer support for these rather than guessing.

  8. Outemu Cream series (5-Pin pack) — TWO factual corrections to
     v2.6.0:
       - Cream Green Pro: was "tactile" in v2.6.0, actually LINEAR
         per mechkeysshop.com / chosfox official spec.
       - Cream Yellow Pro: was "linear, not pre-lubed" in v2.6.0,
         actually SILENT TACTILE with factory-lube and rubber
         stem dampeners per lumekeebs.com review + multiple
         reseller datasheets. (It's a Boba U4-style nylon switch.)
     Both now properly tagged [Web-sourced from {source}].

  9. CB Optical Switches (H&J) — type classification confirmed
     (Brown=tactile, Red=linear) per H&J Amazon/Newegg listings.
     Detailed actuation force / pre-travel / total travel: not
     published by CB OR by H&J on any verifiable source. Marked
     [Specs not publicly documented] with explicit instruction
     to route customers to CB support for exact specs. Added
     general optical-switch context (IR beam actuation, ~100M
     keystroke typical lifespan, water/dust resistant, no
     debounce delay) sourced from hirosarts.com / varmilo /
     ibuypower educational pages.

  10. Quick Picker section at end of Outemu now uses ONLY verified
      data, no fabricated feel-by-name guesses.

  Sources cross-referenced this session (web fetches):
  - cherry.de (official, Cherry MX Silent Red + Speed Silver)
  - cherryxtrfy.com (Cherry retail spec)
  - mouser.com + farnell.com (Cherry official datasheets)
  - mechanicalkeyboards.com (Cherry + Gateron G Pro 3.0 Yellow)
  - keychron.com (Cherry guide, Kailh guide, G Pro 3.0)
  - deskthority.net wiki (Cherry MX Silent Red + Speed Silver)
  - kailhswitch.com FAQ + guide pages
  - switchandclick.com (Kailh + Outemu deep dives)
  - thekeyboardco.com (Kailh introduction)
  - thegamingsetup.com (Kailh + Outemu guides)
  - mechkeybs.com (Kailh + Outemu)
  - gateron.com official product pages and compare pages
  - gateron.co (Gateron G Pro 2.0 + 3.0 sets)
  - kprepublic.com (Outemu Four Seasons, OTM line, Pro V2)
  - kbdfans.com (Gateron G Pro 3.0 Yellow)
  - cannonkeys.com (Gateron G Pro 2.0 Yellow)
  - mtnkbd.com (Gateron G Pro 2.0/3.0 Yellow)
  - milktooth.com (Outemu switch comparisons)
  - lumekeebs.com (Outemu Cream Yellow Silent Tactile review)
  - mechkeysshop.com / mechkeys.com (Outemu Cream Pro specs)
  - thekapco.com (Outemu Cream Blue spec sheet)
  - chosfox.com (Outemu Cream + Milk + Silent series specs)
  - goblintechkeys.com (Outemu Milk Blue, Milk Peach)
  - thoccexchange.com (Outemu Maple Leaf)
  - ymdkey.com (Outemu Four Seasons spec)
  - hirosarts.com (Outemu guide, optical switch info)
  - varmilo, ibuypower (general optical switch info)
  - newegg.com / Amazon (H&J Optical listings, type confirm)

  All four CB-linked spec-sheet PDFs (Cherry Silent Red, Cherry
  Speed Silver, Gateron G Pro 2.0 Yellow, Gateron G Pro 2.0 Silver)
  return 404 as of last check -- fact noted in each entry.

v2.6.0 (2026-05-06) -- Claude
  - Y-bump: added 5 switch products under the Option B workflow.
    User sent 5 product URLs covering the entire Keyboard Mechanical
    Switches category. Each page was fetched live; data below is from
    the actual product pages (not search snippets, not training data).

  NEW ENTRIES:
  - Cherry MX added to THIRD_PARTY_BRAND_MANUALS (between Outemu and Moza).
    SKU CHERRYMX, 5-Pin, Pack of 10, ₹449. Only 2 variants on CB:
    MX Silent Red and MX Speed Silver (both linear). Per-variant
    spec-sheet references included. Now auto-routes via the v2.5.7
    wiring -- Cherry MX queries skip web search and use this manual.
    This was the last brand in the THIRD_PARTY_BRANDS keyword list
    that fell back to web search; only Brook, Fanatec, Thrustmaster
    remain on web-search fallback now.
  - Cosmic Byte Optical Switches added as a CB product (NOT a third-
    party brand — manufactured by H&J for CB, fits only the Trinity
    Optical keyboard). Added entry to PRODUCT_URLS and a dedicated
    section in SYSTEM_PROMPT placed near the existing switch-related
    content. SKU OPTICALSWITCHES, Pack of 20, ₹145. Only 2 variants:
    Brown and Red. CRITICAL routing rule captured in the section:
    these are NOT compatible with any other CB keyboard -- they use
    a different (light-based) actuation mechanism and only fit the
    Trinity socket. Customers with non-Trinity keyboards must be
    redirected to mechanical switches (Outemu/Gateron/Kailh/Cherry MX).

  CORRECTIONS TO EXISTING ENTRIES (live page data overrode prior info):
  - Gateron: replaced entry with authoritative variant list. The OLD
    entry claimed "3-pin and 5-pin variants available" and listed
    "Milky Yellow" and "Brown" as variants -- NEITHER is on the
    actual product page. Correct: 5-Pin only, 7 actual variants
    (Blue, Red, G Pro 3.0 Blue/Red/Yellow Pre-Lubed, G Pro 2.0
    Yellow/Silver Pre-Lubed). Spec sheets exist for G Pro 2.0
    Yellow and Silver only. 50M keystroke rating retained.
  - Kailh: replaced entry. Old entry mentioned generic "Speed
    switches"; the actual page lists "Silver Switch" specifically
    (Kailh's Speed line). Old entry also missing Box Brown.
    Correct: 6 actual variants -- Blue, Brown, Red, Box Brown,
    Box Red, Silver. Box variants are typically 5-pin (CB lists
    them all under one SKU but the box housing may indicate 5-pin).
  - Outemu: kept the rich 3-Pin Pack of 20 detail (29 variants,
    5 detailed spec sheets). Filled in the previously-empty 5-Pin
    Pack of 20 section with its actual 4 Cream variants (Cream
    Blue/Green/Pink Pre-Lubed + Cream Yellow). Added a critical
    note that the 3-Pin and 5-Pin Outemu packs have COMPLETELY
    different switch lineups -- previously the entry implied they
    were the same product in different pin counts, which is wrong.

  Source URLs (each fetched live from thecosmicbyte.com):
  - https://www.thecosmicbyte.com/product/cherry-mx-mechancial-5-pin-switches-compatible-with-hot-swappable-keyboards-pack-of-10/
  - https://www.thecosmicbyte.com/product/cosmic-byte-optical-switches-pack-of-20/
  - https://www.thecosmicbyte.com/product/gateron-mechanical-switches-compatible-with-cosmic-byte-hot-swappable-keyboards-qty-1pc/
  - https://www.thecosmicbyte.com/product/kailh-mechanical-switches-for-swappable-keyboards-pack-of-10/
  - https://www.thecosmicbyte.com/product/outemu-mechanical-switches-for-hot-swappable-keyboards-5-pin-pack-of-20/

v2.5.7 (2026-05-06) -- Claude
  - User chose Option A: wire THIRD_PARTY_BRAND_MANUALS into the system
    prompt at runtime so the structured manuals we collect actually get
    used. Previously the dict was defined but unused.
  - Renamed three dict keys for direct lookup against detect_third_party_brand
    output: "Gateron Switches" -> "Gateron", "Kailh Switches" -> "Kailh",
    "Outemu Switches" -> "Outemu". "Moza" and "Cammus" already matched.
    Lookup is now a single dict.get() call, no mapping layer needed.
  - Modified the API call site in the AI-response block. New behavior:
      * detect_third_party_brand returns brand name (unchanged).
      * If THIRD_PARTY_BRAND_MANUALS has a manual for that brand:
          - Inject the manual directly into the system prompt under a
            "=== THIRD-PARTY BRAND MANUAL: {brand} ===" header.
          - Tell the AI it's authoritative for what CB sells.
          - DO NOT enable web search (faster + cheaper response, manual
            covers everything we know about the brand on CB).
          - For off-catalog questions, AI is told to direct customers
            to the brand site URL or CB product page.
      * If no manual exists (Cherry MX, Brook, Fanatec, Thrustmaster):
          - Keep current behavior: enable web search + brand addendum.
    This means Outemu/Gateron/Kailh/Moza/Cammus queries no longer trigger
    a web search call -- they get answered from the structured manuals.
  - Updated the docstring "Key dicts" map to reflect that
    THIRD_PARTY_BRAND_MANUALS is now consumed at runtime.

v2.5.6 (2026-05-06) -- Claude
  - First product variant addition under the user's "Option B" workflow
    (one product per turn, scraped from the live thecosmicbyte.com page).
  - Added new entry "Outemu Switches" to THIRD_PARTY_BRAND_MANUALS,
    placed between Kailh and Moza so all switch-brand entries stay
    grouped before the sim racing brands. Captures:
      * 3 SKUs sold on CB: 3-Pin Pack of 20, 5-Pin Pack of 20, and
        Certified Refurbished Pack of 20 (with all 3 product URLs).
      * Compatibility rules: 3-pin fits all CB hot-swap keyboards;
        5-pin fits Astra/Phantom TKL/Phantom TKL Wired only.
      * Full list of all 29 switch-type variants as published on the
        Pack of 20 (3-Pin) product page: 4 standard (Blue/Brown/Red/
        Black) plus 25 Pre-Lubed (incl. silent variants, fruit/tea
        themed names, Yellow Silver, Transparent Crystal, etc).
      * Detailed published spec sheets for the 5 switches CB publishes
        data for: Silent Lemon V1, Silent Honey Peach V1, Panda,
        Yellow Silver, Transparent Crystal Linear (operating force,
        bottom-out, travel distances, materials, lube status).
      * Price range (₹145–₹325 for new 3-Pin, ₹75–₹140 for refurbished).
      * No-warranty / no-return policy reiterated.
      * "Quick picker" section grouping switches by use-case so the AI
        can recommend appropriately based on what the customer wants
        (quiet typing / gaming linear / tactile bump / clicky / RGB).
  - Source URL: https://www.thecosmicbyte.com/product/outemu-mechanical-switches-for-swappable-keyboards-pack-of-20/
  - Note: THIRD_PARTY_BRAND_MANUALS is still not consumed at runtime --
    third-party brand queries continue to use web search via
    detect_third_party_brand(). This entry is reserved for a future
    merge into the system prompt OR direct lookup; either way, the
    structured knowledge is now in the file.

v2.5.5 (2026-05-06) -- Claude
  - User confirmed v2.5.4 fixes resolved the "Unable to connect" error.
    Portal is now responding to queries.
  - User shared first-hand validation that the Android Bluetooth-mode
    gamepad-tester approach actually works on real hardware. Reinforced
    the existing PRO TIP section in the system prompt:
      * Added "✅ VALIDATED BY THE COSMIC BYTE TEAM" line at the top of
        the section so the AI can recommend the approach confidently
        rather than tentatively.
      * Updated the customer-facing messaging template to use the user's
        own empathetic phrasing -- "customers might need to try different
        things to find what works for their specific phone — that's
        normal, not a fault." This shifts tone from purely technical
        ("compatibility variation, not hardware fault") to acknowledging
        the customer's effort.
  - Diagnostic expander from v2.5.2/v2.5.3 is INTENTIONALLY KEPT for now
    as a safety net. Will be removed in a future patch once the user has
    run several successful queries and confirms nothing else is broken.

v2.5.4 (2026-05-06) -- Claude
  - ROOT CAUSE FOUND. The "Unable to connect" error has been failing for
    every query because of two pre-existing variable-name bugs in the
    AI-response code block (lines 3710 + 3714 of the previous version).
    Neither was introduced by recent edits -- both have been in the file
    from the original version, on the main API-call code path.
      Bug 1: line 3710 referenced `user_input`, which is only defined in
        the form block FURTHER DOWN in the file (line 3768). Streamlit
        runs the script top-to-bottom on every interaction, so when the
        AI-response block executes, the form below it hasn't run yet --
        `user_input` doesn't exist in scope. Fix: use `user_question`,
        which IS defined just above the block at line 3655.
      Bug 2: line 3714 referenced `kb_content`, which is never defined
        anywhere in the file. The correct variable from the surrounding
        code is `knowledge` (defined at lines 3665/3671/3673/3675).
        This bug would have triggered immediately after fixing Bug 1.
    Both fixed in this version. The portal should now respond to queries
    once v2.5.4 is deployed and the footer reads v2.5.4.
  - Diagnostic expander from v2.5.2/v2.5.3 is intentionally KEPT for now,
    so if anything else fails post-deploy, we still see the traceback.
    A future v2.5.5 patch can remove it once we confirm the portal works
    cleanly across multiple test queries.

v2.5.3 (2026-05-06) -- Claude
  - Deployment-verification patch. After v2.5.2 added a diagnostic expander,
    user reported the same "Unable to connect" error twice with no expander
    visible in the screenshots -- strongly suggesting the deployed code was
    still an older version. To make this impossible to misdiagnose:
      * Added "v2.5.3" label to the bottom-right of the page footer using
        the __version__ constant. Now the user can see at a glance which
        version is actually live.
      * Set the diagnostic expander to expanded=True so the error details
        appear automatically when the API call fails -- no clicking needed.
      * Added a startup print of the version to server logs (visible in
        Streamlit Cloud / deployment logs) so deploys can be confirmed
        without opening the UI.
    Once deployed, the footer should read "v2.5.3" and the next failed
    request will show the full traceback inline. That traceback is what
    we need to identify the root cause of the "Unable to connect" error.

v2.5.2 (2026-05-06) -- Claude
  - DIAGNOSTIC PATCH. The deployed app showed "Unable to connect" with no
    detail when the customer asked about Blitz vibration on Android. The
    exception handler at the API-call site was swallowing the real error.
    Modified it to:
      * Keep the existing friendly st.error for customers.
      * Add a collapsible "Technical details" expander showing error type,
        message, HTTP status (if available), response body (if available),
        and full Python traceback.
      * Print the same to server logs via print(..., flush=True) so it
        appears in Streamlit Cloud / deployment logs.
    Once the root cause is identified and fixed, this expander block can
    be removed in a future patch (it's marked with a comment).

v2.5.1 (2026-05-06) -- Claude
  - Replaced the soft "when you share this file" paragraph in the docstring
    with a hard ASSISTANT EDIT PROTOCOL block: pre-edit checklist, post-edit
    checklist, format notes, and an explicit warning not to type literal
    triple-quote sequences inside this docstring (which would close it).
    Goal: reduce the risk that future Claude instances forget to log
    changes when editing the file.
  - No code changes -- documentation/protocol only.

v2.5.0 (2026-05-06) -- Claude
  - Added "PC CONTROLLER TESTING" section to the system prompt, recommending
    https://hardwaretester.com/gamepad as the first-line diagnostic for PC
    vibration / input issues. Framed as a warranty-deflection step: if the
    controller works there, the issue is game-side, not hardware.
    Inserted just before the "ANDROID VIBRATION & DUALSHOCK MODE GUIDE"
    section so the AI sees it as the PC counterpart to the Android test.
    Includes a Hindi/Hinglish messaging template.
  - Fixed 5 pre-existing parse errors that were preventing the file from
    running at all (Python ast.parse failed before the app could load):
      * "Ignis Mouse" URL in PRODUCT_URLS was split mid-string by an
        accidentally-pasted keyboard-manual line. Rejoined.
      * Closing triple-quote of "Ares Wireless" entry and opening of the
        next dict key for "Blitz Tri-Mode" had been merged into a single
        bullet line. Restored as a proper dict-entry boundary.
      * Orphan duplicate CHARGING/WARRANTY fragment (with leading
        "Charging Dock" chopped to "g Dock") after Blitz Tri-Mode entry.
        Removed.
      * Third-party brand manuals (Gateron / Kailh / Moza / Cammus) were
        sitting outside any dict, indented as if inside detect_product()
        but after its `return` statement, plus a duplicate copy of
        Moza+Cammus right after. Wrapped the legitimate copy in a proper
        module-level dict named THIRD_PARTY_BRAND_MANUALS; deleted the
        duplicate.
      * Orphan "BLUETOOTH POLLING RATE: ..." paragraph at module scope
        after all the Streamlit code. Removed.
  - Named the recovered third-party-brand manuals dict
    THIRD_PARTY_BRAND_MANUALS (NOT THIRD_PARTY_BRANDS) to avoid silently
    overwriting the existing keyword-lookup dict that powers
    detect_third_party_brand() and the web-search trigger.

v2.4.x (prior to 2026-05-06, undated) -- User
  - Added "PRO TIP -- GAMEPAD MODE COMPATIBILITY TEST" section inside the
    "ANDROID VIBRATION & DUALSHOCK MODE GUIDE". Tells customers to use
    gamepad-tester.com in a mobile browser to find which Bluetooth mode
    (DInput / DualShock / iOS) makes vibration work on their specific
    phone, and to use that mode for gaming. Framed as compatibility
    variation, not warranty.

v2.x (earlier, undated) -- User
  - Original support portal: Streamlit UI, Claude Haiku 4.5 integration,
    PRODUCT_MANUALS for the full Cosmic Byte catalog (controllers, mice,
    keyboards, headsets, accessories, cables, sim racing), product
    detection from page title, web search for third-party brands
    (Gateron, Kailh, Outemu, Cherry MX, Moza, Cammus, Brook, Fanatec,
    Thrustmaster), feedback logging via Google Sheets, email transcripts,
    admin dashboard.

==============================================================================
"""

__version__ = "2.35.0"

import streamlit as st


# v2.28.1: helper to suppress per-rerun log spam.
#
# Streamlit re-executes the entire script top-to-bottom on every user
# interaction (button click, dropdown change, message send, etc.). That
# means any plain `print()` at module scope fires on every rerun — under
# modest concurrent load (~30 user actions per 75s) this floods the
# Render log stream with duplicate startup banners and makes real events
# (OOM restarts, errors) hard to spot.
#
# Routing those prints through this helper makes them fire ONCE per
# worker process for each unique message string. `@st.cache_resource`
# caches the return value across reruns AND across sessions; the first
# call with a given `msg` runs the body (which prints), subsequent calls
# with the same `msg` return the cached True without re-running.
#
# Use for startup banners and one-time config-state messages only.
# Do NOT use for per-request logging where you want every event recorded.
@st.cache_resource(show_spinner=False)
def _log_once_per_process(msg: str) -> bool:
    print(msg, flush=True)
    return True


import anthropic
import os
import hmac
import hashlib
import threading
import extra_streamlit_components as stx
from datetime import datetime, timedelta, timezone

# Print version on startup so it appears in deployment logs (Streamlit Cloud, etc.)
# Helps confirm which version is actually live after a deploy.
# v2.28.1: routed through _log_once_per_process (was bare print, fired
# on every script rerun).
_log_once_per_process(f"[support_portal_v2] starting up — app version {__version__}")

# ── PRODUCT BUY LINKS ──
import uuid
import json
import csv
import re             # v2.26.0: risk-flagging regex patterns in admin
import secrets        # v2.32.0: cryptographically-secure admin OTP generation
import base64
import io
import zipfile
import smtplib
import time          # v2.24.0: cache TTL on bot API fetch
import requests      # v2.24.0: bot API fetch (already a transitive dep)
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ============================================================================
# Knowledge base (shared with discord_bot.py via cb_kb.py).
# All product data, system prompt, catalogues, third-party brand info, and
# product-detection helpers were extracted into cb_kb.py in v2.22.0 so the
# Discord bot can import them without pulling in Streamlit. See cb_kb.py
# header for the full move list and standing edit protocol.
# ============================================================================
from cb_kb import (
    PRODUCT_URLS,
    KNOWLEDGE_BASE,
    PRODUCTS,
    SYSTEM_PROMPT,
    match_product_from_title,
    THIRD_PARTY_BRAND_MANUALS,
    CATALOGUE_CONTROLLERS,
    CATALOGUE_MICE,
    CATALOGUE_KEYBOARDS,
    CATALOGUE_HEADSETS,
    CATALOGUE_ACCESSORIES,
    CATALOGUE_ALL,
    THIRD_PARTY_BRANDS,
    THIRD_PARTY_BRAND_URLS,
    detect_third_party_brand,
    detect_products_from_message,
    detect_product_from_message,
)

# Decode CB logo for use as favicon
import io as _io, base64 as _b64
from PIL import Image as _PILImage
_favicon_bytes = _b64.b64decode("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")
_favicon_img = _PILImage.open(_io.BytesIO(_favicon_bytes))
st.set_page_config(page_title="Cosmic Byte Support", page_icon=_favicon_img, layout="centered")

CB_LOGO = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA7EAAAOxCAYAAAAjIyBZAAEAAElEQVR4nOz9eZykZX3v/7+u67qXquqejc0FWRRlViAg7keNC2IEBhCGAVFAcc3vnCwneXwfjxxBE2MUg4AmOX5PQAUOSIAZBSIqosk3J8tJNCKrLAqzdE/vPWtPd1fVfd/X5/dH1X13dU93z97dM/N5+ih7HequrvVdn+v6fEAppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSimllFJKKaWUUkoppZRSSs2CV73qVTLbx6CUUkoppZRSSu3W17/+denq6pJLL71Ug6xSSimllFJKqbnr61//unR0dMimTZtk/fr1smrVKg2ySimllFJKKaXmnq997WvS09MjmzZtkg0bNkhHR4e8+OKL8t/+23/TIKuUUkodIGa2D0AppZQ6HNxxxx3y7ne/G+cc1lq891SrVay1JEnCd7/7Xf7kT/5En3eVUkqp/WRn+wCUUkqpQ9kxxxwjjzzyiLzvfe8jDEOCIMAYgzGG9vZ2kiQhCALOP/98vvCFL2hFVimllNpP+o6wUkoptR9+8IMfyOtf/3oAwjBERAiCAICdO3ciIiRJQq1Ww3vPgw8+yGc/+1l9/lVKKaX2kT6JKqWUUvvoRz/6kZx11lmICM45oijCOUeaplhrybKMer3O6Ogo9Xqd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iLxAeiAVERFZB7fffru74ooraNuWMAz7AU4Ao9GIb33rW9x666163BUREXmBohN9BURERE4HH/3oRw3grrjiCpqm6ffENk3Dv/yX/5I/+qM/UoAVERERERGRk8v73/9+993vftd997vfdf/1v/5X9/a3v92d6OskIiIiIiIiclDbt2933/3ud90VV1yhACsiIiIiIiInv/POO08BVkREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREROSE+P8A4MqX4QEg1S8AAAAASUVORK5CYII="



st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Sora:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');
:root{
  --cb-bg:#0d1319;--cb-bg-soft:#111a23;--cb-surface:#18212b;--cb-surface-2:#1f2a35;
  --cb-line:#2b3744;--cb-line-soft:#232e39;
  --cb-ink:#eef1f5;--cb-ink-2:#c4c9d4;--cb-ink-3:#8a92a3;
  --cb-accent:#FF9E1B;--cb-accent-2:#ffb347;--cb-accent-soft:rgba(255,158,27,0.12);
  --on-accent:#101820;
  /* legacy aliases — any leftover var() reference resolves to the dark palette */
  --orange:#FF9E1B;--orange-dim:rgba(255,158,27,0.12);--orange-border:#2b3744;
  --bg:#0d1319;--s1:#18212b;--s2:#1f2a35;--border2:#2b3744;--text:#eef1f5;--muted:#8a92a3;
}
html,body,[class*="css"],[data-testid="stAppViewContainer"],[data-testid="stApp"],.stApp{
  background-color:var(--cb-bg)!important;color:var(--cb-ink);
  font-family:'Sora',-apple-system,BlinkMacSystemFont,sans-serif;
  padding-top:0!important;margin-top:0!important;}
h1,h2,h3,h4,h5,h6{font-family:'Bricolage Grotesque',serif!important;font-weight:700!important;color:var(--cb-ink)!important;letter-spacing:-0.02em!important;}
.main .block-container{max-width:780px;padding-top:0!important;padding-bottom:4rem;margin-top:0!important;position:relative;z-index:1;}
[data-testid="stHeader"]{display:none!important;height:0!important;min-height:0!important;visibility:hidden!important;}
section[data-testid="stMain"] > div:first-child{padding-top:0!important;}
div[data-testid="stVerticalBlock"] > div:first-child{padding-top:0!important;}
.appview-container .main .block-container{padding-top:0!important;}
[data-testid="stSidebar"]{background:var(--cb-bg-soft)!important;}

.cb-header{display:flex;align-items:center;justify-content:space-between;padding:0.5rem 0 0.7rem;border-bottom:1px solid var(--cb-line);margin-bottom:0.8rem;position:relative;}
.cb-header::after{content:'';position:absolute;bottom:-1px;left:0;width:64px;height:3px;background:var(--cb-accent);border-radius:100px;}
.cb-brand{display:flex;align-items:center;gap:14px;}
.cb-logo-text{display:none;}
.cb-tagline{display:none;}
.cb-live-badge{background:var(--cb-accent);color:var(--on-accent);font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;padding:6px 16px;border-radius:100px;}
.status-dot{width:7px;height:7px;background:#22C55E;border-radius:50%;display:inline-block;margin-right:6px;box-shadow:0 0 8px rgba(34,197,94,0.7);animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.4;}}

.cb-label{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;color:var(--cb-accent);margin-bottom:6px;display:flex;align-items:center;gap:10px;}
.cb-label::after{content:'';flex:1;height:1px;background:linear-gradient(to right,var(--cb-line),transparent);}

.msg-user{display:flex;justify-content:flex-end;margin:10px 0;}
.msg-user-bubble{background:var(--cb-accent);color:var(--on-accent);font-weight:500;padding:11px 18px;border-radius:18px 18px 4px 18px;max-width:78%;font-size:14px;line-height:1.55;font-family:'Sora',sans-serif;box-shadow:0 2px 12px rgba(255,158,27,0.22);}
.msg-bot{display:flex;gap:10px;align-items:flex-start;margin:10px 0;}
.msg-bot-icon{width:34px;height:34px;flex-shrink:0;background:var(--cb-accent-soft);border:1px solid var(--cb-line);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;margin-top:2px;}
.msg-bot-bubble{background:var(--cb-surface);border:1px solid var(--cb-line);border-left:3px solid var(--cb-accent);color:var(--cb-ink-2);padding:13px 17px;border-radius:4px 14px 14px 14px;max-width:85%;font-size:14px;line-height:1.72;font-family:'Sora',sans-serif;box-shadow:0 2px 10px rgba(0,0,0,0.25);}
.msg-bot-bubble strong{color:var(--cb-ink)!important;}
.msg-bot-name{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:var(--cb-accent);margin-bottom:7px;}

.stTextInput input{background:var(--cb-surface)!important;border:1px solid var(--cb-line)!important;border-radius:8px!important;color:var(--cb-ink)!important;font-size:14px!important;padding:12px 16px!important;font-family:'Sora',sans-serif!important;}
.stTextInput input:focus{border-color:var(--cb-accent)!important;box-shadow:0 0 0 3px rgba(255,158,27,0.18)!important;}
.stTextInput input::placeholder{color:var(--cb-ink-3)!important;}
.stSelectbox > div > div{background:var(--cb-surface)!important;border:1px solid var(--cb-line)!important;border-radius:8px!important;color:var(--cb-ink)!important;}
.stSelectbox > div > div:focus-within{border-color:var(--cb-accent)!important;box-shadow:0 0 0 3px rgba(255,158,27,0.18)!important;}
.stSelectbox svg{fill:var(--cb-accent)!important;}

.stButton button,.stFormSubmitButton button,.stDownloadButton button{background:var(--cb-accent)!important;color:var(--on-accent)!important;border:1px solid var(--cb-accent)!important;border-radius:100px!important;font-weight:700!important;font-size:11px!important;letter-spacing:0.1em!important;text-transform:uppercase!important;font-family:'JetBrains Mono',monospace!important;padding:11px 22px!important;clip-path:none!important;box-shadow:none!important;transition:all 0.2s!important;}
.stButton button:hover,.stFormSubmitButton button:hover,.stDownloadButton button:hover{background:var(--cb-accent-2)!important;color:var(--on-accent)!important;border-color:var(--cb-accent-2)!important;transform:translateY(-2px)!important;box-shadow:0 6px 22px rgba(255,158,27,0.4)!important;}
[data-testid="stForm"]{border:none!important;padding:0!important;}

/* File uploader — dark dashed dropzone */
[data-testid="stFileUploader"] label{color:var(--cb-accent)!important;font-size:12px!important;font-weight:600!important;font-family:'Sora',sans-serif!important;margin-bottom:6px!important;}
[data-testid="stFileUploader"] section{background:var(--cb-bg-soft)!important;border:1px dashed var(--cb-line)!important;border-radius:10px!important;padding:8px 12px!important;}
[data-testid="stFileUploader"] section:hover{border-color:var(--cb-accent)!important;background:var(--cb-accent-soft)!important;}
[data-testid="stFileUploader"] section button{background:var(--cb-accent)!important;color:var(--on-accent)!important;border:none!important;border-radius:100px!important;font-weight:700!important;font-size:11px!important;letter-spacing:0.08em!important;text-transform:uppercase!important;padding:6px 14px!important;clip-path:none!important;font-family:'JetBrains Mono',monospace!important;}
/* Hide Streamlit's default "200MB per file" helper text — it's wrong (we enforce 5MB). */
[data-testid="stFileUploaderDropzoneInstructions"] small,[data-testid="stFileUploader"] section small{display:none!important;}
[data-testid="stFileUploader"] section > div:first-child{color:var(--cb-ink-3)!important;font-size:12px!important;}

button[kind="secondary"],div[data-testid="stHorizontalBlock"] button{background:var(--cb-surface)!important;color:var(--cb-accent)!important;border:1px solid var(--cb-line)!important;clip-path:none!important;border-radius:100px!important;font-size:16px!important;padding:4px 12px!important;letter-spacing:0!important;text-transform:none!important;}
div[data-testid="stHorizontalBlock"] button:hover{background:var(--cb-accent-soft)!important;border-color:var(--cb-accent)!important;}

hr{border-color:var(--cb-line)!important;}
.cb-footer{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;font-size:12px;color:var(--cb-ink-3);font-family:'JetBrains Mono',monospace;letter-spacing:0.04em;padding-top:0.6rem;margin-top:1rem;border-top:1px solid var(--cb-line);}
.cb-footer a{color:var(--cb-accent);text-decoration:none;}
.cb-footer a:hover{color:var(--cb-accent-2);}
.feedback-row{display:flex;align-items:center;gap:8px;margin-top:8px;padding-top:8px;border-top:1px solid var(--cb-line);}
.feedback-label{font-size:11px;color:var(--cb-ink-3);font-family:'Sora',sans-serif;}

a{transition:color 0.2s;}
a:hover{color:var(--cb-accent)!important;}
::-webkit-scrollbar{width:10px;height:10px;}
::-webkit-scrollbar-thumb{background:var(--cb-accent)!important;border-radius:100px;}
::-webkit-scrollbar-track{background:var(--cb-surface-2);}

#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
</style>
""", unsafe_allow_html=True)

# Subtle warm brand atmosphere on the dark canvas — faint, static glows
st.markdown("""
<style>
#cb-glow-bl{
    position:fixed;bottom:-180px;left:-180px;
    width:620px;height:620px;border-radius:50%;
    background:radial-gradient(circle,rgba(255,158,27,0.10) 0%,transparent 70%);
    pointer-events:none;z-index:0;
}
#cb-glow-tr{
    position:fixed;top:-150px;right:-150px;
    width:520px;height:520px;border-radius:50%;
    background:radial-gradient(circle,rgba(255,158,27,0.07) 0%,transparent 70%);
    pointer-events:none;z-index:0;
}
</style>
<div id="cb-glow-bl"></div>
<div id="cb-glow-tr"></div>
""", unsafe_allow_html=True)


def get_secret(key, default=""):
    """Read from env vars (Render) or st.secrets (Streamlit Cloud)."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        return st.secrets[key]
    except Exception:
        return default

client = anthropic.Anthropic(api_key=get_secret("ANTHROPIC_API_KEY"))

# ── CONSTANTS ──
CSV_COLUMNS = ["Date", "Time", "Session ID", "Source", "Product", "Customer Message", "AI Response", "Feedback", "Feedback Note", "Image Thumbnails", "Client IP"]
DIGEST_EMAIL = "thecosmicbyte2017@gmail.com"

# ── DISK PERSISTENCE (v2.17.0) ──────────────────────────────────────────
# Conversation log persists across Render restarts/redeploys via a
# Render persistent disk mounted at PERSISTENT_DATA_DIR (default
# /var/data). If the disk isn't mounted, the portal still runs but
# logs only in memory and prints a loud startup warning.
#
# File layout on disk:
#   {PERSISTENT_DATA_DIR}/support_log.jsonl   -- one JSON row per line
#   {PERSISTENT_DATA_DIR}/digest_state.json   -- last digest send date
#
# JSONL was chosen over CSV/SQLite because:
#   - Append-only writes are simple and atomic under a lock.
#   - Each line is a self-contained JSON record (easy to inspect/grep).
#   - The Image Thumbnails column already stores JSON, so no double
#     encoding gymnastics.
#   - Schema changes don't require migration (new fields = new keys
#     on new rows; missing keys = .get() with default on read).
PERSISTENT_DATA_DIR = os.environ.get("CB_DATA_DIR", "/var/data")

def _disk_persistence_enabled():
    """True iff the persistent data dir exists and is writable.
    Checked once at module load to set LOG_FILE_PATH / DIGEST_STATE_PATH."""
    try:
        return os.path.isdir(PERSISTENT_DATA_DIR) and os.access(PERSISTENT_DATA_DIR, os.W_OK)
    except Exception:
        return False

if _disk_persistence_enabled():
    LOG_FILE_PATH = os.path.join(PERSISTENT_DATA_DIR, "support_log.jsonl")
    DIGEST_STATE_PATH = os.path.join(PERSISTENT_DATA_DIR, "digest_state.json")
    HISTORY_FILE_PATH = os.path.join(PERSISTENT_DATA_DIR, "chat_history.json")  # v2.18.0
    # v2.28.1: routed through _log_once_per_process to avoid per-rerun spam.
    _log_once_per_process(f"[support_portal_v2] persistent disk OK at {PERSISTENT_DATA_DIR} -- conversation log and chat history will survive restarts")
else:
    LOG_FILE_PATH = None
    DIGEST_STATE_PATH = None
    HISTORY_FILE_PATH = None  # v2.18.0
    _log_once_per_process(f"[support_portal_v2] WARNING: persistent disk NOT mounted at {PERSISTENT_DATA_DIR} -- conversation log AND chat history will be LOST on restart. To enable persistence, attach a Render persistent disk at this mount path (Render dashboard -> Settings -> Disks -> Add Disk).")

# v2.24.0: optional fetch of new Discord rows from the bot's HTTP API.
# Set both to enable; leave either unset to fall back to local-only
# behaviour (identical to v2.23.x).
BOT_API_URL = (os.environ.get("BOT_API_URL", "") or "").rstrip("/")
BOT_API_SECRET = os.environ.get("BOT_API_SECRET", "") or ""
BOT_API_TIMEOUT_S = float(os.environ.get("BOT_API_TIMEOUT_S", "10") or "10")
BOT_API_CACHE_TTL_S = float(os.environ.get("BOT_API_CACHE_TTL_S", "30") or "30")
BOT_API_FETCH_LIMIT = int(os.environ.get("BOT_API_FETCH_LIMIT", "1000") or "1000")
if BOT_API_URL and BOT_API_SECRET:
    # v2.28.1: routed through _log_once_per_process to avoid per-rerun spam.
    _log_once_per_process(f"[support_portal_v2] bot API merge enabled -> {BOT_API_URL}")
elif BOT_API_URL or BOT_API_SECRET:
    # Half-configured: log loudly because partial config silently disables
    # the merge layer and is easy to miss.
    _log_once_per_process(
        "[support_portal_v2] WARNING: bot API merge is HALF-CONFIGURED. "
        "Set BOTH BOT_API_URL and BOT_API_SECRET, or NEITHER. "
        "Discord rows from the VPS bot will NOT be visible in the admin "
        "dashboard until this is fixed."
    )
else:
    _log_once_per_process("[support_portal_v2] bot API merge disabled (BOT_API_URL/BOT_API_SECRET not set)")

# Lock guarding ALL disk reads/writes for the log files. Concurrent
# Streamlit reruns can call log_conversation / update_feedback at the
# same time; without this lock, a row with image thumbnails (>4KB)
# could be split across an interleaved append.
_log_disk_lock = threading.Lock()

def _load_log_from_disk_unlocked():
    """Read the full log file into a list of dicts WITHOUT acquiring
    _log_disk_lock. The caller is responsible for holding the lock.

    v2.23.2: factored out so log_conversation can do an atomic
    read-modify-write cycle (load → sync cache → append new row to cache
    and disk) under a single lock acquisition. Without this, two
    concurrent log_conversation calls could refresh-then-append in
    interleaved order and produce a cache vs disk row-position mismatch
    -- which would point the in-chat 👍/👎 buttons at the wrong row.

    Returns [] for missing/unmounted/unreadable file. Backfills missing
    Source="web" on pre-v2.22.0 rows. Does NOT print a load summary --
    that's _load_log_from_disk's job (and would spam the logs if printed
    on every log_conversation call)."""
    if LOG_FILE_PATH is None:
        return []
    if not os.path.exists(LOG_FILE_PATH):
        return []
    rows = []
    skipped = 0
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    skipped += 1
                    continue
        # v2.22.0: backfill Source on pre-v2.22.0 rows.
        for r in rows:
            if "Source" not in r:
                r["Source"] = "web"
        if skipped:
            print(f"[support_portal_v2] WARNING: skipped {skipped} corrupted line(s) while loading log from {LOG_FILE_PATH}", flush=True)
    except Exception as e:
        print(f"[support_portal_v2] WARNING: log file read failed: {e} -- starting with empty log", flush=True)
        return []
    return rows

def _load_log_from_disk():
    """Read the full log file into a list of dicts. Skip corrupted
    lines with a warning rather than failing module import. Returns
    [] if the file doesn't exist (cold start with new disk) or if
    disk persistence is off.

    v2.23.2: now wraps _load_log_from_disk_unlocked() with the disk
    lock and the load-summary print. Behaviour is identical to the
    pre-v2.23.2 version from the caller's perspective."""
    if LOG_FILE_PATH is None:
        return []
    if not os.path.exists(LOG_FILE_PATH):
        return []
    with _log_disk_lock:
        rows = _load_log_from_disk_unlocked()
    print(f"[support_portal_v2] loaded {len(rows)} conversation row(s) from {LOG_FILE_PATH}", flush=True)
    return rows

def _append_log_to_disk(row):
    """Append a single row as one JSON line. No-op if disk persistence
    is off. Errors are logged but never raised -- the portal must keep
    serving customers even if the disk write fails."""
    if LOG_FILE_PATH is None:
        return
    try:
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with _log_disk_lock:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(line)
    except Exception as e:
        print(f"[support_portal_v2] WARNING: log append failed: {e}", flush=True)

def _rewrite_log_to_disk(all_rows):
    """Rewrite the full log file (used when an existing row is updated
    in place, e.g. for feedback). Writes to a tmp file then os.replace
    onto the real path -- atomic on POSIX."""
    if LOG_FILE_PATH is None:
        return
    try:
        tmp_path = LOG_FILE_PATH + ".tmp"
        with _log_disk_lock:
            with open(tmp_path, "w", encoding="utf-8") as f:
                for r in all_rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            os.replace(tmp_path, LOG_FILE_PATH)
    except Exception as e:
        print(f"[support_portal_v2] WARNING: log rewrite failed: {e}", flush=True)

def _load_digest_state():
    """Return the last digest-sent date as a date object, or today's
    date if the state file doesn't exist or can't be parsed."""
    if DIGEST_STATE_PATH is None or not os.path.exists(DIGEST_STATE_PATH):
        return datetime.now().date()
    try:
        with _log_disk_lock:
            with open(DIGEST_STATE_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
        iso = d.get("last_digest_date")
        if iso:
            return datetime.fromisoformat(iso).date()
    except Exception as e:
        print(f"[support_portal_v2] WARNING: digest state read failed: {e}", flush=True)
    return datetime.now().date()

def _save_digest_state(date):
    """Persist the last-digest-sent date so a same-day Render restart
    doesn't trigger a duplicate digest send."""
    if DIGEST_STATE_PATH is None:
        return
    try:
        tmp_path = DIGEST_STATE_PATH + ".tmp"
        with _log_disk_lock:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump({"last_digest_date": date.isoformat()}, f)
            os.replace(tmp_path, DIGEST_STATE_PATH)
    except Exception as e:
        print(f"[support_portal_v2] WARNING: digest state save failed: {e}", flush=True)

# ── SHARED LOG (cache_resource = shared across ALL sessions/iframes) ──

@st.cache_resource
def get_shared_store():
    """Single shared store — survives across all sessions on the same
    Render instance. As of v2.17.0, also rehydrates from disk on cold
    start so the log survives Render restarts/redeploys.

    The @st.cache_resource decorator means this runs ONCE per Render
    instance lifetime. Subsequent reads are served from RAM."""
    return {
        "log": _load_log_from_disk(),
        "last_digest_date": _load_digest_state(),
    }

def get_log():
    return get_shared_store()["log"]

def _refresh_cached_log_from_disk():
    """v2.23.2: Rehydrate the cache_resource shared log from disk in place
    so all in-memory readers (callers of get_log()) see Discord-bot-written
    rows that arrived after the portal cold-started.

    Atomic: load + cache-sync happen under a single _log_disk_lock
    acquisition so a concurrent disk write can't slip in between the read
    and the cache update.

    The cached list is mutated in place (clear + extend) rather than
    rebound, so any concurrent caller that already grabbed a reference to
    the list still appends into the shared object instead of an orphaned
    copy.

    Returns the refreshed cached list, or None if disk persistence is off
    (caller should fall back to get_log()).
    """
    if LOG_FILE_PATH is None:
        return None
    cached = get_shared_store()["log"]
    with _log_disk_lock:
        fresh = _load_log_from_disk_unlocked()
        cached.clear()
        cached.extend(fresh)
    return cached


# ── v2.24.0: REMOTE DISCORD-ROW FETCH FROM THE BOT ─────────────────
# After the discord bot moved off Render onto a Hetzner VPS, the
# portal can no longer read the bot's log file directly. The bot
# exposes GET /log/recent (Bearer auth) and we fetch from it whenever
# admin / digest code wants the unified view. Cached for ~30s to
# avoid hammering the bot per-rerun (Streamlit reruns the script on
# every interaction).
#
# Caching strategy: single-entry @st.cache_resource holder. Stores
# (rows, fetched_at, last_error). On expiry, attempts a re-fetch; on
# failure, returns the previously cached rows (potentially stale)
# with the error logged. This avoids blanking out the admin view on
# every transient hiccup.
@st.cache_resource
def _bot_api_fetch_cache():
    """Single-instance cache holder for the bot API fetch.
    Lives for the Render container's lifetime."""
    return {"rows": [], "fetched_at": 0.0, "last_error": None}


def _fetch_remote_discord_rows(force=False):
    """Fetch recent rows from the bot's /log/recent endpoint.

    Returns a list of row dicts (each with `_remote: True` set so
    callers can distinguish them from local rows). Returns the
    previously-cached rows on transient errors -- a single bot blip
    shouldn't blank out the admin dashboard.

    No-op (returns []) when BOT_API_URL or BOT_API_SECRET is unset:
    portal behaves identically to v2.23.x.

    Cached: refreshed at most once per BOT_API_CACHE_TTL_S seconds
    unless `force=True`.
    """
    if not BOT_API_URL or not BOT_API_SECRET:
        return []
    cache = _bot_api_fetch_cache()
    now = time.time()
    if not force and (now - cache["fetched_at"]) < BOT_API_CACHE_TTL_S:
        return cache["rows"]
    try:
        resp = requests.get(
            f"{BOT_API_URL}/log/recent",
            params={"limit": BOT_API_FETCH_LIMIT},
            headers={"Authorization": f"Bearer {BOT_API_SECRET}"},
            timeout=BOT_API_TIMEOUT_S,
        )
        if resp.status_code == 401:
            # Wrong secret -- log and bail. Don't update the cache so
            # the operator's misconfiguration is visible (admin view
            # silently misses Discord rows until fixed).
            print(
                "[support_portal_v2] WARNING: bot API returned 401 -- "
                "BOT_API_SECRET on portal does not match LOG_API_SECRET on bot. "
                "Discord rows from VPS will not appear until this is fixed.",
                flush=True,
            )
            cache["last_error"] = "auth"
            cache["fetched_at"] = now  # back off retries to TTL cadence
            return cache["rows"]
        resp.raise_for_status()
        data = resp.json() or {}
        raw_rows = data.get("rows", [])
        if not isinstance(raw_rows, list):
            raise ValueError(f"bot returned non-list rows ({type(raw_rows).__name__})")
        # Mark each row as remote so write-side code can identify it.
        # Mutating the dicts here is safe: we just decoded them from
        # JSON; nothing else holds a reference.
        for r in raw_rows:
            if isinstance(r, dict):
                r["_remote"] = True
        # Keep only valid dict rows. Anything else is bot bug or schema
        # mismatch; skip silently rather than crashing the admin view.
        rows = [r for r in raw_rows if isinstance(r, dict)]
        cache["rows"] = rows
        cache["fetched_at"] = now
        cache["last_error"] = None
        return rows
    except Exception as e:
        # Network/parse error. Log and return whatever we had cached
        # (could be empty on cold start). DON'T overwrite cache["rows"]
        # so a brief outage doesn't drop us back to no-Discord-data.
        print(
            f"[support_portal_v2] WARNING: bot API fetch failed: {type(e).__name__}: {e} "
            f"(returning {len(cache['rows'])} cached row(s))",
            flush=True,
        )
        cache["last_error"] = str(e)
        cache["fetched_at"] = now  # back off retries to TTL cadence
        return cache["rows"]


def _row_dedup_key(row):
    """Stable identity for a conversation row, used to deduplicate
    when local + remote logs overlap (e.g. pre-migration Discord rows
    that exist in BOTH the portal's local /var/data file AND the
    bot's VPS log if the bot was started with carried-over history).

    Session ID + Date + Time + first 50 chars of customer message.
    Different rows could in theory hash the same if the same session
    sent two identical messages in the same minute -- vanishingly
    rare, and the merge gracefully drops the duplicate either way."""
    return (
        row.get("Session ID", ""),
        row.get("Date", ""),
        row.get("Time", ""),
        (row.get("Customer Message", "") or "")[:50],
    )


# ── IST DISPLAY TIMEZONE (v2.29.0) ──────────────────────────────────
# All log rows are stored on disk with Date/Time in the server's local
# timezone (UTC -- the default for the Render container and for the
# Hetzner Cloud VPS that hosts the Discord bot). For the admin dashboard
# display we want India Standard Time (UTC+5:30) so the operator (in
# Pune) doesn't have to do mental arithmetic on every timestamp.
#
# Strategy: convert UTC -> IST at the get_merged_log() read layer.
# Storage on disk stays in UTC -- this keeps existing log rows valid,
# avoids a migration step, and means the bot doesn't need a code change
# (so no extra Discord-bot restart). All downstream code (sort, calendar
# week/month/day grouping, expander labels, CSV export of displayed
# values) automatically operates in IST because Date/Time fields are
# already IST by the time anything reads them.
#
# If the server ever runs in a non-UTC timezone, this conversion will
# silently produce wrong values. As a defensive measure each converted
# row gets a `_tz_converted` marker so the function is idempotent even
# if get_merged_log() is called multiple times within a single Streamlit
# rerun.
IST = timezone(timedelta(hours=5, minutes=30))

def _convert_row_to_ist(row):
    """Convert one row's Date/Time fields from server-UTC to IST, in place.
    Idempotent: sets `_tz_converted = True` so re-application is a no-op.
    Defensive: silently leaves the row unchanged on any parse error so a
    single malformed row can't crash the dashboard."""
    if row.get("_tz_converted"):
        return row
    date_str = row.get("Date", "")
    time_str = row.get("Time", "")
    if not date_str or not time_str:
        row["_tz_converted"] = True
        return row
    try:
        utc_dt = datetime.strptime(f"{date_str} {time_str}", "%d %b %Y %H:%M")
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        ist_dt = utc_dt.astimezone(IST)
        row["Date"] = ist_dt.strftime("%d %b %Y")
        row["Time"] = ist_dt.strftime("%H:%M")
    except Exception:
        pass
    row["_tz_converted"] = True
    return row


def _row_sort_key(row):
    """Key for chronological sort. Date format is `dd Mon YYYY`,
    Time is `HH:MM`. Falls back to datetime.min on any parse error
    so a malformed row sorts to the top instead of crashing the sort."""
    try:
        return datetime.strptime(
            f"{row.get('Date','')} {row.get('Time','')}",
            "%d %b %Y %H:%M",
        )
    except Exception:
        return datetime.min


def get_merged_log(force_remote=False):
    """Return local rows + remote Discord rows from the VPS bot,
    deduplicated and sorted chronologically. Used by the admin
    dashboard, daily digest, CSV export, and bulk photo export
    starting in v2.24.0.

    Local rows win on overlap (so pre-migration Discord rows keep
    whatever feedback Ronak set on them via the chat-side 👍/👎).

    Note: this is for READ paths. WRITE paths (log_conversation
    appending a Web row, update_feedback updating a Web row by
    index) continue to use get_log() against the local cache --
    they only ever mutate local rows, so they don't need remote
    data. Never pass an index from get_merged_log() into
    update_feedback() -- the local-cache index won't match.
    """
    local = list(get_log())
    remote = _fetch_remote_discord_rows(force=force_remote)
    if not remote:
        # v2.29.0: convert each row's stored UTC Date/Time to IST for display.
        for r in local:
            _convert_row_to_ist(r)
        return local  # no merge needed; preserves identity
    seen_keys = set()
    merged = []
    for r in local:
        key = _row_dedup_key(r)
        seen_keys.add(key)
        merged.append(r)
    for r in remote:
        if _row_dedup_key(r) in seen_keys:
            continue
        merged.append(r)
    # v2.29.0: convert each merged row's stored UTC Date/Time to IST.
    # MUST happen BEFORE the sort so the sort key compares IST values
    # consistently across local + remote rows.
    for r in merged:
        _convert_row_to_ist(r)
    merged.sort(key=_row_sort_key)
    return merged


# ── BROWSER-PERSISTENT CHAT HISTORY (v2.12.0) ──
# Server-ephemeral; per-product; 7-day expiry. See the v2.12.0 changelog
# entry at the top of this file for the full design rationale.
HISTORY_EXPIRY_DAYS = 7
HISTORY_COOKIE_NAME = "cb_bid"

# ── ADMIN AUTH PERSISTENCE (v2.13.0) ──
# Cookie-based admin auth so a hard refresh doesn't kick the operator out.
# Token is an HMAC-SHA256 of the expiry timestamp, keyed by ADMIN_PASSWORD.
# Stateless: the same HMAC re-verifies after a Render restart because
# ADMIN_PASSWORD lives in env/secrets, not in-memory state.
ADMIN_AUTH_COOKIE_NAME = "cb_admin_auth"
ADMIN_AUTH_DURATION_HOURS = 8

def _make_admin_auth_token(password):
    """Mint a signed token. Format: '<expiry_iso>|<hmac_hex>'."""
    expiry = datetime.now() + timedelta(hours=ADMIN_AUTH_DURATION_HOURS)
    expiry_iso = expiry.isoformat()
    sig = hmac.new(
        password.encode(),
        expiry_iso.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{expiry_iso}|{sig}"

def _verify_admin_auth_token(token, password):
    """Return True iff `token` is well-formed, unexpired, and HMAC-valid
    against `password`. Defensive against any parse error."""
    if not token or "|" not in token:
        return False
    try:
        expiry_iso, sig = token.split("|", 1)
        expiry = datetime.fromisoformat(expiry_iso)
        if datetime.now() > expiry:
            return False
        expected_sig = hmac.new(
            password.encode(),
            expiry_iso.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False

@st.cache_resource
def get_history_store():
    """Per-(browser_id, product) chat history. As of v2.18.0, persists
    across Render restarts via a JSON file on the persistent disk
    (chat_history.json), so a customer's previous thread is restored
    on revisit even after a redeploy. Each entry:
        {"messages": list[dict], "updated_at": datetime}
    The @st.cache_resource decorator means the disk read happens once
    per Render instance lifetime; subsequent reads are served from RAM."""
    return _load_history_from_disk()

# ── CHAT HISTORY DISK PERSISTENCE (v2.18.0) ──
# Lock guarding chat_history.json reads/writes. Separate from
# _log_disk_lock (which guards support_log.jsonl + digest_state.json)
# so a chat-history rewrite doesn't block a conversation-log append.
_history_disk_lock = threading.Lock()

def _load_history_from_disk():
    """Return the in-memory store dict, rehydrated from disk. Empty dict
    on cold-start with no file, on parse failure, or if disk is not
    mounted. Tuple keys (bid, product) are reconstructed from the bid +
    product fields stored in each entry. Expired entries (older than
    HISTORY_EXPIRY_DAYS) are dropped on load -- matches the eviction
    policy of _purge_expired so we don't restore stale threads."""
    if HISTORY_FILE_PATH is None or not os.path.exists(HISTORY_FILE_PATH):
        return {}
    try:
        with _history_disk_lock:
            with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
        out = {}
        skipped = 0
        evicted = 0
        for entry in d.get("entries", []):
            try:
                bid = entry["bid"]
                product = entry["product"]
                updated_at = datetime.fromisoformat(entry["updated_at"])
            except (KeyError, ValueError, TypeError):
                skipped += 1
                continue
            if datetime.now() - updated_at >= timedelta(days=HISTORY_EXPIRY_DAYS):
                evicted += 1
                continue
            out[(bid, product)] = {
                "messages": entry.get("messages", []),
                "updated_at": updated_at,
            }
        if skipped:
            print(f"[support_portal_v2] WARNING: skipped {skipped} malformed chat history entry(s) on load", flush=True)
        print(f"[support_portal_v2] loaded {len(out)} chat history entry(s) from {HISTORY_FILE_PATH} (evicted {evicted} expired)", flush=True)
        return out
    except Exception as e:
        print(f"[support_portal_v2] WARNING: chat history file read failed: {e} -- starting with empty history", flush=True)
        return {}

def _save_history_to_disk(store):
    """Persist the entire chat history store to disk (atomic full
    rewrite via tmp + os.replace, under the lock). No-op if disk is
    not mounted. Errors are logged but never raised -- the portal must
    keep serving customers even if a disk write fails.

    v2.23.2: build the entries list INSIDE the lock. Previously the
    `for (bid, product), v in store.items()` iteration happened before
    the `with _history_disk_lock:` block, which meant a concurrent
    request mutating the store mid-iteration could trip
    `RuntimeError: dictionary changed size during iteration`. The
    broad except below caught it, so customers never saw the error,
    but every such race silently dropped a chat-history save.
    """
    if HISTORY_FILE_PATH is None:
        return
    try:
        tmp_path = HISTORY_FILE_PATH + ".tmp"
        with _history_disk_lock:
            entries = []
            for (bid, product), v in store.items():
                updated_at = v.get("updated_at", datetime.now())
                entries.append({
                    "bid": bid,
                    "product": product,
                    "messages": v.get("messages", []),
                    "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
                })
            payload = {"entries": entries}
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp_path, HISTORY_FILE_PATH)
    except Exception as e:
        print(f"[support_portal_v2] WARNING: chat history disk save failed: {e}", flush=True)

def _strip_images_for_history(messages):
    """Clone the message list with image payloads removed. If a message had
    images attached, append a small inline placeholder so the rehydrated
    conversation still reads coherently when the customer scrolls back.
    log_idx is preserved when present so feedback widget keys remain stable."""
    out = []
    for m in messages:
        if not m.get("content"):
            continue
        clean = {"role": m["role"], "content": m["content"]}
        if m.get("images"):
            clean["content"] = clean["content"] + "\n\n*[image attached in original message]*"
        if "log_idx" in m:
            clean["log_idx"] = m["log_idx"]
        out.append(clean)
    return out

def _load_history(browser_id, product):
    """Return the entry for (browser_id, product) if alive (within
    HISTORY_EXPIRY_DAYS), else None. Lazily evicts expired entries on access."""
    store = get_history_store()
    entry = store.get((browser_id, product))
    if not entry:
        return None
    age = datetime.now() - entry.get("updated_at", datetime.min)
    if age >= timedelta(days=HISTORY_EXPIRY_DAYS):
        store.pop((browser_id, product), None)
        return None
    return entry

def _save_history(browser_id, product, messages):
    """Persist the conversation. No-op for empty message lists.
    v2.18.0: also persists to disk so the thread survives Render restarts."""
    if not messages:
        return
    store = get_history_store()
    store[(browser_id, product)] = {
        "messages": _strip_images_for_history(messages),
        "updated_at": datetime.now(),
    }
    _save_history_to_disk(store)

def _clear_history(browser_id, product=None):
    """Drop history for one product (if `product` given) or for the entire
    browser_id. v2.18.0: also persists the cleared state to disk."""
    store = get_history_store()
    if product is None:
        for k in list(store.keys()):
            if k[0] == browser_id:
                store.pop(k, None)
    else:
        store.pop((browser_id, product), None)
    _save_history_to_disk(store)

def _purge_expired():
    """Sweep expired entries from the store. Runs once per page load. Cheap
    because the store is small (one entry per active (browser, product)).
    v2.18.0: persists to disk only if something was actually evicted, so a
    quiet page load does not cause a disk write."""
    store = get_history_store()
    cutoff = datetime.now() - timedelta(days=HISTORY_EXPIRY_DAYS)
    expired = [k for k, v in store.items() if v.get("updated_at", datetime.min) < cutoff]
    if not expired:
        return
    for k in expired:
        store.pop(k, None)
    _save_history_to_disk(store)

def _get_client_ip():
    """Best-effort client IP from request headers. Reads X-Forwarded-For from
    st.context.headers (set by Streamlit Cloud and most managed proxies); the
    first entry in the comma-separated list is the original client. Falls back
    to X-Real-IP, then to "". Wrapped in try/except so any Streamlit version
    quirk or bare-metal deployment without a reverse proxy degrades to "".
    """
    try:
        ctx = getattr(st, "context", None)
        if ctx is None:
            return ""
        headers = getattr(ctx, "headers", None)
        if headers is None:
            return ""
        for key in ("X-Forwarded-For", "x-forwarded-for"):
            v = headers.get(key)
            if v:
                return v.split(",")[0].strip()
        for key in ("X-Real-IP", "x-real-ip"):
            v = headers.get(key)
            if v:
                return v.strip()
        return ""
    except Exception:
        return ""

def _make_thumbnails_for_log(images):
    """Resize each uploaded image to a 400px-wide JPEG (quality 75), base64-encode,
    and return a JSON-serializable list of {name, data} dicts.
    Used to persist a viewable thumbnail in the conversation log so admin can
    review what customers attached. Skips silently on per-image errors so a
    bad image never breaks logging."""
    if not images:
        return ""
    thumbs = []
    MAX_W = 400
    for img in images:
        try:
            raw = base64.b64decode(img["data"])
            with _PILImage.open(_io.BytesIO(raw)) as pil:
                # Convert RGBA / palette / etc. to RGB so we can save as JPEG.
                if pil.mode != "RGB":
                    pil = pil.convert("RGB")
                w, h = pil.size
                if w > MAX_W:
                    new_h = int(h * MAX_W / w)
                    pil = pil.resize((MAX_W, new_h), _PILImage.LANCZOS)
                out = _io.BytesIO()
                pil.save(out, format="JPEG", quality=75, optimize=True)
                thumbs.append({
                    "name": img.get("name", "image"),
                    "data": base64.b64encode(out.getvalue()).decode("ascii"),
                })
        except Exception:
            # Bad image -- skip the thumbnail but don't break logging
            continue
    if not thumbs:
        return ""
    return json.dumps(thumbs)

def log_conversation(session_id, product, user_msg, ai_response, images=None, client_ip="", source="web"):
    now = datetime.now()
    row = {
        "Date": now.strftime("%d %b %Y"),
        "Time": now.strftime("%H:%M"),
        "Session ID": session_id,
        "Source": source,
        "Product": product,
        "Customer Message": user_msg,
        "AI Response": ai_response,
        "Feedback": "",
        "Feedback Note": "",
        "Image Thumbnails": _make_thumbnails_for_log(images),
        "Client IP": client_ip,
    }
    # v2.23.2: do the full read-modify-write cycle under a single
    # _log_disk_lock acquisition so:
    #   (a) any Discord rows that arrived since cache cold-start are
    #       picked up before we compute this row's index, and
    #   (b) two concurrent web log_conversation calls can't interleave
    #       cache and disk in different orders, which would mis-point
    #       the row_num returned to the in-chat 👍/👎 button (stored on
    #       the assistant message as msg["log_idx"], passed to
    #       update_feedback as row_idx).
    # The lock is contended for microseconds at our row volume, so the
    # serialization cost is invisible.
    if LOG_FILE_PATH is not None:
        try:
            line = json.dumps(row, ensure_ascii=False) + "\n"
            cached = get_shared_store()["log"]
            with _log_disk_lock:
                # 1) Pick up anything Discord wrote since our last sync.
                disk_rows = _load_log_from_disk_unlocked()
                cached.clear()
                cached.extend(disk_rows)
                # 2) Append the new row to cache and disk. Order: cache
                #    first (cheap, in-memory), then disk (the durable record).
                cached.append(row)
                with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                    f.write(line)
        except Exception as e:
            # Mirror the pre-v2.23.2 behaviour: never raise from the
            # logging path. The portal must keep serving customers even
            # if the disk write fails. The cache still got the row, so
            # the assistant response renders correctly; the row is just
            # not durably persisted for this turn.
            print(f"[support_portal_v2] WARNING: log append failed: {e}", flush=True)
    else:
        # Dev fallback: no persistent disk. Same as pre-v2.23.2.
        get_log().append(row)
    return len(get_log()) - 1

def update_feedback(row_idx, feedback, note=""):
    # v2.23.0: re-read the log from disk before mutating, so we don't blow
    # away Discord-bot-written rows that landed between the admin's last
    # page render and this feedback click. Discord rows live on disk only
    # (the bot is a separate process), and a naive _rewrite_log_to_disk()
    # from our stale in-memory copy would delete them.
    #
    # Index stability: row_idx came from the last admin render. New rows
    # (web or discord) are always appended to the END of the JSONL file,
    # so existing indices still point to the same rows even after appends.
    # The disk-truth read here picks up any new appends and preserves them
    # through the rewrite.
    #
    # v2.23.2: use _refresh_cached_log_from_disk() so the cache_resource
    # shared list (returned by get_log()) is also updated. The previous
    # `st.session_state.log = log` only updated per-session state; readers
    # of get_log() -- in particular log_conversation's row_num computation --
    # were left looking at a stale list. Mutating the cached list in place
    # also means the feedback we apply below lands on the SAME object the
    # cache exposes, so subsequent get_log() reads see it without another
    # disk roundtrip.
    #
    # No-op fallback: if disk persistence is off (LOG_FILE_PATH is None,
    # e.g. dev environment without /var/data), _refresh_cached_log_from_disk
    # returns None -- in that case fall back to the in-memory log so we
    # don't silently drop the feedback.
    refreshed = _refresh_cached_log_from_disk()
    if refreshed is not None:
        log = refreshed
        st.session_state.log = log
    else:
        log = get_log()
    if row_idx is not None and 0 <= row_idx < len(log):
        log[row_idx]["Feedback"] = feedback
        log[row_idx]["Feedback Note"] = note
        # v2.17.0: rewrite the on-disk log so the feedback persists too.
        # Full rewrite is fine at our volume (<10K rows = milliseconds).
        # No-op if persistent disk isn't mounted.
        _rewrite_log_to_disk(log)

# ── EMAIL HELPERS ──
def build_csv_bytes(rows):
    # v2.24.0: extrasaction='ignore' so v2.24.0+ rows tagged with the
    # internal _remote marker (added by _fetch_remote_discord_rows) don't
    # break CSV export with a ValueError. Default 'raise' would crash on
    # any extra key. CSV_COLUMNS is explicit, so future internal markers
    # also stay out of the CSV without further changes here.
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")

def build_images_zip(rows):
    """Bundle every thumbnail in `rows` into an in-memory ZIP.
    Folder structure inside the archive: {date}_{session_id}/{NN}_{name}.jpg
    where NN is the per-conversation image index (zero-padded 2 digits).
    Returns (zip_bytes, image_count, conversation_count). If no images are
    found across the rows, returns (None, 0, 0)."""
    buf = io.BytesIO()
    image_count = 0
    convo_count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in rows:
            thumbs_raw = r.get("Image Thumbnails", "")
            if not thumbs_raw:
                continue
            try:
                thumbs = json.loads(thumbs_raw)
            except (json.JSONDecodeError, TypeError):
                continue
            if not thumbs:
                continue
            convo_count += 1
            # Folder name: "07-May-2026_e30e4078"  -> sorts chronologically
            # when extracted, sessions stay grouped.
            date_str = r.get("Date", "unknown").replace(" ", "-")
            session = r.get("Session ID", "unknown") or "unknown"
            folder = f"{date_str}_{session}"
            for idx, t in enumerate(thumbs, start=1):
                try:
                    img_bytes = base64.b64decode(t["data"])
                    name = t.get("name", f"image_{idx}")
                    base_name = os.path.splitext(name)[0] or f"image_{idx}"
                    # Sanitise: strip path separators in case any slipped in.
                    base_name = base_name.replace("/", "_").replace("\\", "_")
                    arcname = f"{folder}/{idx:02d}_{base_name}.jpg"
                    zf.writestr(arcname, img_bytes)
                    image_count += 1
                except Exception:
                    # Bad image -- skip it but keep going on the rest
                    continue
    if image_count == 0:
        return None, 0, 0
    return buf.getvalue(), image_count, convo_count

def send_email_with_csv(csv_bytes, subject, recipient=DIGEST_EMAIL):
    try:
        gmail_user = get_secret("GMAIL_SENDER")
        gmail_app_pw = get_secret("GMAIL_APP_PASSWORD")
        msg = MIMEMultipart()
        msg["From"] = gmail_user
        msg["To"] = recipient
        msg["Subject"] = subject
        body = f"Hi,\n\nPlease find the Cosmic Byte support log attached.\n\nGenerated: {datetime.now().strftime('%d %b %Y %H:%M')}\nRows: {len(csv_bytes.splitlines()) - 1}\n\n- Cosmic Byte Support Bot"
        msg.attach(MIMEText(body, "plain"))
        part = MIMEBase("application", "octet-stream")
        part.set_payload(csv_bytes)
        encoders.encode_base64(part)
        filename = f"cosmic_byte_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_app_pw)
            server.sendmail(gmail_user, recipient, msg.as_string())
        return True
    except Exception as e:
        return False

def auto_daily_digest():
    today = datetime.now().date()
    # v2.23.0: refresh log from disk so Discord conversations land in
    # the daily digest email. Without this, the digest would only contain
    # web conversations -- the Discord bot writes to disk only and never
    # touches the in-memory log.
    #
    # v2.23.2: the v2.23.0 fix was incomplete -- it set
    # `st.session_state.log = _load_log_from_disk()` but then iterated
    # `get_log()`, which returns the cache_resource shared list (a
    # different object). The shared list still didn't contain Discord
    # rows, so digest emails were dropping every Discord conversation.
    # Switch to the helper that mutates the cached list in place, and
    # iterate that list directly.
    #
    # v2.24.0: the local refresh is still needed (it picks up
    # historical Discord rows from /var/data on Render and any Web
    # rows the portal wrote), but the new Discord rows now live on
    # the VPS bot. Use get_merged_log() to combine local + remote.
    # When BOT_API_URL is unset, get_merged_log() degrades to local-
    # only and behaviour is identical to v2.23.2. We keep the local
    # cache refresh because (a) it makes st.session_state.log
    # accurate for any same-render Web feedback path, and (b)
    # get_merged_log() reads from the cache so the cache must be
    # current.
    refreshed = _refresh_cached_log_from_disk()
    if refreshed is not None:
        st.session_state.log = refreshed
    rows_source = get_merged_log()
    if today > get_shared_store()["last_digest_date"] and rows_source:
        yesterday = get_shared_store()["last_digest_date"].strftime("%d %b %Y")
        rows = [r for r in rows_source if r.get("Date") == yesterday]
        if rows:
            csv_bytes = build_csv_bytes(rows)
            send_email_with_csv(csv_bytes, f"Cosmic Byte Support Log - {yesterday}")
        get_shared_store()["last_digest_date"] = today
        # v2.17.0: persist the new digest date so a Render restart
        # later today doesn't trigger a duplicate digest send.
        # No-op if persistent disk isn't mounted.
        _save_digest_state(today)





QUICK_QUESTIONS = {
    "All Products": [
        "How do I connect to PC?",
        "Controller not detected in game",
        "How do I update firmware?",
        "Warranty claim process",
        "Button keeps auto-pressing",
    ],
    "Lumora": [
        "How do I connect via 2.4GHz?",
        "Check battery level",
        "Reset my controller",
        "Gyro not working",
        "Charging stopped",
    ],
    "Stellaris": [
        "How to enter gyro mode?",
        "Factory reset steps",
        "Trigger mode switch",
        "Macro not working",
        "LED indicator meaning",
    ],
    "Drakon": [
        "How does trigger lock work?",
        "Mouse mode setup",
        "Change magnetic cover",
        "Dongle storage location",
        "Joystick drift fix",
    ],
    "Ares Pro": [
        "Does my model support software?",
        "How to update firmware safely?",
        "M1/M2 macro setup",
        "LED colors meaning",
        "Vibration not working",
    ],
    "Ares": [
        "How do I connect to PC?",
        "Controller not detected in game",
        "How do I claim warranty?",
        "Joystick drift fix",
        "Vibration not working",
    ],
    "Nexus": [
        "How do I connect to PC?",
        "Controller not detected in game",
        "LED colors meaning",
        "Vibration not working",
        "Battery and storage tips",
    ],
    "Ares Wired": [
        "How do I connect to PC?",
        "Old game not detecting controller",
        "Does my model have Hall Effect?",
        "ABXY LED turned off",
        "Joystick drift fix",
    ],
    "Ares Wireless": [
        "How do I connect to PC?",
        "Controller not re-pairing with dongle",
        "Charging issue - fast charger",
        "Hall Effect - which batch?",
        "Controller keeps disconnecting",
    ],
    "Blitz Tri-Mode": [
        "How do I connect via Bluetooth?",
        "How to activate Steam mode?",
        "Gyro not working in 2.4GHz",
        "Macro setup",
        "Battery level check",
    ],
    "Blitz Wireless": [
        "How do I connect to PC?",
        "Old game not detecting controller",
        "How do I re-pair the dongle?",
        "Turbo setup and auto-turbo",
        "Is the Blitz Wireless discontinued?",
    ],
    "Eclipse": [
        "How do I connect to PC?",
        "Joystick resistance adjustment",
        "Gyro calibration",
        "Turbo setup",
        "Trigger travel switch",
    ],
    "Starforge": [
        "How do I connect to PC?",
        "How to replace joystick modules?",
        "Stick calibration after module swap",
        "What is NS mode?",
        "Gyro calibration",
    ],
    "Quantum": [
        "How to connect to PS4?",
        "Does it work on PS5?",
        "How to connect to PC?",
        "ML/MR macro setup",
        "Charging - what adapter to use?",
    ],
    "Stratos Xenon": [
        "How to connect to PS4?",
        "Does it work on PS5?",
        "Back button not working on PC",
        "How to connect wirelessly to PC?",
        "Mic not working",
    ],
    "Velox": [
        "How do I connect via 2.4GHz?",
        "DPI colors meaning",
        "Mouse cursor lagging",
        "Bluetooth device name to look for",
        "Battery draining fast",
    ],
    "Helios Mouse": [
        "How do I pair the dongle?",
        "Bluetooth pairing steps",
        "DPI adjustment",
        "Software download",
        "Mouse not detected",
    ],
    "Hypernova Mouse": [
        "How to pair the dongle?",
        "8000Hz polling system requirements",
        "Can I use a fast charger?",
        "How to charge the spare battery?",
        "Mouse cursor stuttering at 8000Hz",
    ],
    "Atlas Mouse": [
        "How do I connect via 2.4GHz?",
        "Bluetooth polling rate vs wired",
        "Software download",
        "DPI adjustment",
        "Mouse not detected",
    ],
    "Aether Mouse": [
        "How do I swap the battery?",
        "How do I connect via 2.4GHz?",
        "Does it support fast charging?",
        "DPI adjustment",
        "Mouse not detected",
    ],
    "Umbra Mouse": [
        "How do I connect via 2.4GHz?",
        "Bluetooth polling rate limitation",
        "DPI adjustment",
        "Mouse not detected",
        "Software download",
    ],
    "Firestorm Mouse": [
        "Is the Firestorm wireless?",
        "How do I change DPI?",
        "RGB not working",
        "Software download",
        "Buttons not responding",
    ],
    "Ignis Mouse": [
        "Does Ignis have RGB?",
        "How do I connect via 2.4GHz?",
        "Battery life - how long?",
        "DPI above 12000 - how?",
        "Mode switch not working",
    ],
    "Raptor Mouse": [
        "Does Raptor have Bluetooth?",
        "How do I connect via 2.4GHz?",
        "How do I change DPI?",
        "RGB setup",
        "Mouse cursor lagging",
    ],
    "Phantom TKL": [
        "How to connect via Bluetooth?",
        "How to switch between 3 Bluetooth devices?",
        "2.4G not connecting — how to re-pair?",
        "Battery draining fast",
        "How to change backlight effect?",
    ],
    "Phantom TKL Wired": [
        "How to swap switches?",
        "How to change backlight effects?",
        "FN key shortcuts list",
        "Windows key locked — how to unlock?",
        "WASD and arrows swapped — how to fix?",
    ],
    "Pandora": [
        "How to swap switches?",
        "How to change backlight?",
        "Windows key locked — how to unlock?",
        "Game mode shortcuts",
        "Custom backlight recording",
    ],
    "Vanth": [
        "How to swap switches?",
        "How to change backlight?",
        "Windows key locked — how to unlock?",
        "Game mode shortcuts",
        "Custom backlight recording",
    ],
    "Artemis Wireless": [
        "How to connect via Bluetooth?",
        "How to pair 2.4G dongle?",
        "How to check battery level?",
        "Keyboard not detected in wireless mode",
        "LED not working — software fix",
    ],
    "Artemis": [
        "How to swap switches?",
        "Backlight not working",
        "Software not detecting keyboard",
        "Windows key locked — how to unlock?",
        "LED stopped working after software update",
    ],
    "Firefly TKL": [
        "How to swap switches?",
        "How to adjust keyboard height?",
        "Backlight not working",
        "Software setup",
        "Windows key locked — how to unlock?",
    ],
    "Trinity": [
        "How to connect via Bluetooth?",
        "How to pair 2.4G dongle?",
        "Software not working in wireless mode",
        "Can I use Outemu switches to replace?",
        "How to check battery level?",
    ],
    "Astra": [
        "How to pair Bluetooth?",
        "Can I use Cherry MX switches?",
        "Software not working in Bluetooth mode",
        "Battery LED blinking red — what to do?",
        "How to switch between Windows and Mac mode?",
    ],
    "CryoCore": [
        "Headset not detected on PC",
        "Mic not working",
        "How does 7.1 surround work?",
        "How do I mute the mic?",
        "Warranty claim process",
    ],
    "Proteus": [
        "USB vs 3.5mm — which should I use?",
        "Mic not working",
        "RGB lighting control",
        "On-cable controller buttons",
        "Volume dial not working",
    ],
    "Immortal": [
        "How do I switch between modes?",
        "Bluetooth pairing steps",
        "Mic not working",
        "Battery life and charging",
        "Using on PS5 / Xbox",
    ],
    "CosmoBuds X220": [
        "How do I pair to my phone?",
        "How do I activate GOD Mode (low-latency)?",
        "Battery life and charging time",
        "One earbud not working",
        "Reset and re-pair earbuds",
    ],
    "Cyclone RGB": [
        "How do I control fan speed?",
        "Change RGB lighting effects",
        "Which laptop sizes are supported?",
        "USB hub ports not working",
        "Adjusting height / angle",
    ],
    "Dragonfly": [
        "How do I change RGB lighting?",
        "Software download for customisation",
        "Mouse DPI adjustment",
        "Phone holder and hotkeys",
        "Keyboard not detected",
    ],
}






# ── SESSION STATE ──
if "messages" not in st.session_state:
    st.session_state.messages = []


# ── COMPACT CATALOGUE for recommendation/comparison queries ──
# Sent when a customer asks "which should I buy?" with no specific product.
# ~2K tokens — far cheaper than the full 27K concatenated KB.





CATALOGUE_ALL = CATALOGUE_CONTROLLERS + CATALOGUE_MICE + CATALOGUE_KEYBOARDS + CATALOGUE_HEADSETS + CATALOGUE_ACCESSORIES




if "selected_product" not in st.session_state:
    _params = st.query_params
    # Support both ?page_title=... (new plugin — raw WooCommerce title)
    # and ?product=... (direct/legacy embed) for backwards compatibility
    _page_title = _params.get("page_title", "")
    _url_product = _params.get("product", "")
    if _page_title:
        st.session_state.selected_product = match_product_from_title(_page_title)
    elif _url_product and _url_product in PRODUCTS:
        st.session_state.selected_product = _url_product
    else:
        st.session_state.selected_product = "All Products"
if "embed_mode" not in st.session_state:
    _params = st.query_params
    st.session_state.embed_mode = _params.get("embed", "false").lower() == "true"
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "row_nums" not in st.session_state:
    st.session_state.row_nums = []
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = {}
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "show_admin" not in st.session_state:
    st.session_state.show_admin = False

# ── AUTO DAILY DIGEST ──
auto_daily_digest()

# ── ADMIN PAGE ──
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "cosmicbyte_admin")

# ── ADMIN EMAIL + OTP LOGIN (v2.32.0, Brevo delivery v2.33.0) ──────────
# Replaces the single shared-password admin login with email + one-time
# code (OTP), delivered via Brevo (the transactional email service already
# used by the website + pickup portal), with automatic Gmail SMTP fallback.
# Includes rate limiting (per-email + global) to deter spam/bots, a verify-
# attempt cap to stop brute-forcing the 6-digit code, and email-enumeration
# resistance (the form behaves identically for whitelisted and non-
# whitelisted emails).
#
# New env vars:
#   ADMIN_EMAILS                  -- comma-separated whitelist of emails
#                                    allowed to request an admin OTP.
#                                    Defaults to
#                                    ronak.gupta@thecosmicbyte.com if
#                                    unset. Add more (comma-separated) to
#                                    authorise additional admins.
#   ADMIN_ALLOW_PASSWORD_FALLBACK -- "true" re-enables the old shared-
#                                    password login as an emergency
#                                    break-glass (default OFF). Use only
#                                    if email delivery breaks; disable
#                                    again afterwards.
#
# ADMIN_PASSWORD is still used as the HMAC key for the session cookie and
# for hashing OTPs at rest, so the existing 8h cookie-persistence keeps
# working unchanged.
ADMIN_OTP_LENGTH = 6
ADMIN_OTP_TTL_MINUTES = 10
ADMIN_OTP_MAX_VERIFY_ATTEMPTS = 5       # wrong-code tries before the code is burned
ADMIN_OTP_MAX_SENDS_PER_EMAIL = 3       # OTP requests per email...
ADMIN_OTP_SEND_WINDOW_MINUTES = 15      # ...within this rolling window
ADMIN_OTP_GLOBAL_MAX_SENDS = 20         # total OTP sends across all emails...
ADMIN_OTP_GLOBAL_WINDOW_MINUTES = 60    # ...within this rolling window (defence in depth)

ADMIN_OTP_STATE_PATH = (
    os.path.join(PERSISTENT_DATA_DIR, "admin_otp_state.json")
    if (PERSISTENT_DATA_DIR and os.path.isdir(PERSISTENT_DATA_DIR))
    else None
)

def _admin_allowed_emails():
    """Whitelist of emails permitted to request an admin OTP.
    Comma-separated env var ADMIN_EMAILS; falls back to the operator's
    admin address so the panel works out-of-the-box without env setup."""
    raw = get_secret("ADMIN_EMAILS", "ronak.gupta@thecosmicbyte.com")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}

@st.cache_resource
def _otp_memory_store():
    """In-memory OTP/rate-limit store, used only when no persistent disk is
    mounted. Shared across all sessions on this instance; lost on restart
    (acceptable — OTPs are short-lived and rate-limit windows are short)."""
    return {"_data": {}}

def _load_otp_state():
    if ADMIN_OTP_STATE_PATH is None:
        return dict(_otp_memory_store()["_data"])
    if not os.path.exists(ADMIN_OTP_STATE_PATH):
        return {}
    try:
        with _log_disk_lock:
            with open(ADMIN_OTP_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[support_portal_v2] WARNING: otp state read failed: {e}", flush=True)
        return {}

def _save_otp_state(state):
    if ADMIN_OTP_STATE_PATH is None:
        _otp_memory_store()["_data"] = dict(state)
        return
    try:
        tmp_path = ADMIN_OTP_STATE_PATH + ".tmp"
        with _log_disk_lock:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(state, f)
            os.replace(tmp_path, ADMIN_OTP_STATE_PATH)
    except Exception as e:
        print(f"[support_portal_v2] WARNING: otp state save failed: {e}", flush=True)

def _prune_otp_state(state):
    """Drop expired per-email entries and out-of-window send timestamps so
    the state file stays small and rate-limit windows roll correctly."""
    now = datetime.now()
    send_cutoff = now - timedelta(minutes=ADMIN_OTP_SEND_WINDOW_MINUTES)
    for email in list(state.keys()):
        if email == "_global_sends":
            continue
        ent = state.get(email) or {}
        kept = []
        for s in ent.get("sends", []):
            try:
                if datetime.fromisoformat(s) > send_cutoff:
                    kept.append(s)
            except Exception:
                pass
        ent["sends"] = kept
        exp = ent.get("expires")
        try:
            otp_expired = (not exp) or datetime.fromisoformat(exp) < now
        except Exception:
            otp_expired = True
        if otp_expired and not kept:
            del state[email]
        else:
            state[email] = ent
    g_cutoff = now - timedelta(minutes=ADMIN_OTP_GLOBAL_WINDOW_MINUTES)
    gkept = []
    for s in state.get("_global_sends", []):
        try:
            if datetime.fromisoformat(s) > g_cutoff:
                gkept.append(s)
        except Exception:
            pass
    state["_global_sends"] = gkept
    return state

def _otp_send_allowed(email, state):
    """Return (allowed: bool, message: str). Enforces per-email and global
    send rate limits."""
    now = datetime.now()
    ent = state.get(email, {})
    sends = ent.get("sends", [])
    if len(sends) >= ADMIN_OTP_MAX_SENDS_PER_EMAIL:
        try:
            oldest = min(datetime.fromisoformat(s) for s in sends)
            wait = int((oldest + timedelta(minutes=ADMIN_OTP_SEND_WINDOW_MINUTES) - now).total_seconds() // 60) + 1
        except Exception:
            wait = ADMIN_OTP_SEND_WINDOW_MINUTES
        return False, f"Too many code requests for this email. Please wait about {max(wait,1)} minute(s) and try again."
    if len(state.get("_global_sends", [])) >= ADMIN_OTP_GLOBAL_MAX_SENDS:
        return False, "The login system is temporarily busy. Please try again in a few minutes."
    return True, ""

def _generate_otp():
    return "".join(secrets.choice("0123456789") for _ in range(ADMIN_OTP_LENGTH))

def _hash_otp(otp, email):
    """HMAC the OTP keyed by ADMIN_PASSWORD + email, so the stored value is
    useless to an attacker even if the state file leaks."""
    return hmac.new(
        ADMIN_PASSWORD.encode(),
        f"{email.lower()}:{otp}".encode(),
        hashlib.sha256,
    ).hexdigest()

def send_otp_email(recipient, otp):
    """Send a one-time admin login code.

    Prefers Brevo — the transactional email service already used by the
    Cosmic Byte website and the Reverse Pickup portal — via its HTTP API
    (same pattern as the pickup portal's send_login_code). Falls back to
    the existing Gmail SMTP path if BREVO_API_KEY isn't configured or the
    Brevo call fails, so OTP delivery keeps working either way.

    Brevo env vars (same names as the pickup portal, so the values can be
    reused):
      BREVO_API_KEY    -- the Brevo API key (if unset, falls back to Gmail)
      BREVO_URL        -- endpoint (default https://api.brevo.com/v3/smtp/email)
      EMAIL_FROM       -- verified sender (default no-reply@thecosmicbyte.com)
      EMAIL_FROM_NAME  -- sender display name (default "Cosmic Byte Support")
    """
    subject = "Your Cosmic Byte admin login code"
    text_body = (
        f"Your Cosmic Byte admin login code is: {otp}\n\n"
        f"This code expires in {ADMIN_OTP_TTL_MINUTES} minutes and can be used once.\n"
        f"If you didn't request this, you can safely ignore this email.\n\n"
        f"- Cosmic Byte Support"
    )

    # ---- Preferred path: Brevo transactional email API ----
    brevo_key = get_secret("BREVO_API_KEY")
    if brevo_key:
        try:
            brevo_url = get_secret("BREVO_URL", "https://api.brevo.com/v3/smtp/email")
            from_email = get_secret("EMAIL_FROM", "no-reply@thecosmicbyte.com")
            from_name = get_secret("EMAIL_FROM_NAME", "Cosmic Byte Support")
            html = (
                "<div style='font-family:Arial,Helvetica,sans-serif;max-width:480px;margin:auto'>"
                "<p>Your Cosmic Byte admin login code is:</p>"
                f"<p style='font-size:32px;font-weight:700;letter-spacing:6px;margin:16px 0'>{otp}</p>"
                f"<p>This code expires in {ADMIN_OTP_TTL_MINUTES} minutes and can be used once.</p>"
                "<p style='color:#888;font-size:13px'>If you didn't request this, you can safely ignore this email.</p>"
                "<p style='color:#888;font-size:13px'>— Cosmic Byte Support</p>"
                "</div>"
            )
            r = requests.post(
                brevo_url,
                headers={"api-key": brevo_key,
                         "content-type": "application/json",
                         "accept": "application/json"},
                json={"sender": {"name": from_name, "email": from_email},
                      "to": [{"email": recipient}],
                      "subject": subject,
                      "htmlContent": html,
                      "textContent": text_body},
                timeout=20,
            )
            if r.status_code in (200, 201):
                return True
            print(f"[support_portal_v2] WARNING: Brevo OTP send failed "
                  f"({r.status_code}: {r.text[:200]}); trying Gmail fallback", flush=True)
            # fall through to Gmail fallback
        except Exception as e:
            print(f"[support_portal_v2] WARNING: Brevo OTP send error: {e}; trying Gmail fallback", flush=True)
            # fall through to Gmail fallback

    # ---- Fallback path: Gmail SMTP (existing path the daily digest uses) ----
    try:
        gmail_user = get_secret("GMAIL_SENDER")
        gmail_app_pw = get_secret("GMAIL_APP_PASSWORD")
        if not gmail_user or not gmail_app_pw:
            print("[support_portal_v2] WARNING: OTP not sent — no Brevo key and no Gmail secrets", flush=True)
            return False
        msg = MIMEText(text_body)
        msg["From"] = gmail_user
        msg["To"] = recipient
        msg["Subject"] = subject
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_app_pw)
            server.sendmail(gmail_user, recipient, msg.as_string())
        return True
    except Exception as e:
        print(f"[support_portal_v2] WARNING: OTP email send failed (Gmail fallback): {e}", flush=True)
        return False


# ── ADMIN HIERARCHICAL GROUPING (v2.21.0) ──
# With disk persistence (v2.17.0+), the admin conversation log grows
# indefinitely. The flat list became unworkable past a few days. The
# helpers below bucket rows into Month -> Week -> Day -> conversation
# so the admin can collapse old months and drill into specific days.
def _group_log_for_admin(rows_with_idx):
    """Group (filtered_idx, row) pairs into a sorted Month -> Week -> Day
    hierarchy for the admin dashboard.

    Input:
        rows_with_idx: list of (idx, row_dict). The idx is preserved as-is
        so per-row Streamlit widget keys (photo download buttons etc.) stay
        stable when called from the grouped renderer.

    Output: a list of month dicts, each:
        {
          'month_label': 'May 2026',
          'month_count': total rows in this month,
          'weeks': [
            {
              'week_label': 'Week of 04 May',
              'week_count': total rows in this week,
              'days': [
                {
                  'day_label': '08 May 2026 (Fri)',
                  'day_count': total rows on this day,
                  'rows': [(idx, row), ...],   # sorted by Time desc
                },
                ...   # most-recent day first
              ],
            },
            ...   # most-recent week first
          ],
        },
        ...   # most-recent month first

    Rows whose Date can't be parsed (corrupt log entry, format drift) are
    bucketed into a synthetic '(Undated)' group at the bottom rather than
    dropped, so the admin still sees them."""
    from collections import defaultdict

    by_day = defaultdict(list)  # date_obj or None -> [(idx, row)]
    for idx, r in rows_with_idx:
        date_str = r.get("Date", "")
        try:
            d = datetime.strptime(date_str, "%d %b %Y").date()
        except (ValueError, TypeError):
            d = None
        by_day[d].append((idx, r))

    # Sort each day's rows by Time desc (lex sort works for "HH:MM")
    for d in by_day:
        by_day[d].sort(key=lambda ir: ir[1].get("Time", ""), reverse=True)

    # Group days into (month, week)
    grouped = defaultdict(lambda: defaultdict(list))
    # ^ {(year, month): {week_start_date: [(day_date, items), ...]}}
    undated_items = []
    for d, items in by_day.items():
        if d is None:
            undated_items.extend(items)
            continue
        month_key = (d.year, d.month)
        week_start = d - timedelta(days=d.weekday())  # Monday-of-the-week
        grouped[month_key][week_start].append((d, items))

    result = []
    for month_key in sorted(grouped.keys(), reverse=True):
        year, month_num = month_key
        month_label = datetime(year, month_num, 1).strftime("%B %Y")
        weeks = grouped[month_key]
        week_data = []
        month_count = 0
        for week_start in sorted(weeks.keys(), reverse=True):
            week_label = f"Week of {week_start.strftime('%d %b')}"
            day_entries = sorted(weeks[week_start], key=lambda x: x[0], reverse=True)
            day_data = []
            week_count = 0
            for d, items in day_entries:
                day_label = d.strftime("%d %b %Y (%a)")
                day_data.append({
                    'day_label': day_label,
                    'day_count': len(items),
                    'rows': items,
                })
                week_count += len(items)
            week_data.append({
                'week_label': week_label,
                'week_count': week_count,
                'days': day_data,
            })
            month_count += week_count
        result.append({
            'month_label': month_label,
            'month_count': month_count,
            'weeks': week_data,
        })

    if undated_items:
        result.append({
            'month_label': '(Undated)',
            'month_count': len(undated_items),
            'weeks': [{
                'week_label': '(Undated)',
                'week_count': len(undated_items),
                'days': [{
                    'day_label': '(Undated)',
                    'day_count': len(undated_items),
                    'rows': undated_items,
                }],
            }],
        })

    return result


def _score_conversation_risk(customer_msg, ai_response):
    """Score a conversation pair for review-risk based on heuristics
    derived from real fabrications observed in the cb_kb.py changelog
    (2026-05-09: v1.4.1 Eclipse calibration, v1.5.1 Ares Pro back label,
    v1.5.2 warranty advocacy, v1.6.2 Ares dongle, v1.7.0 Ares XInput,
    plus Rule #14 violations across the board).

    Returns a dict:
      {'score': int, 'flags': [(label, points), ...]}

    The score is a sum of points from each heuristic that fires.
    Higher score = more likely to need operator review. Heuristic
    points are tuned against today's known fabrications -- the goal
    is for every confirmed-bad response in today's logs to score >= 3
    (yellow or higher), and for typical correct responses to score 0.

    Display thresholds (handled by the caller):
        0       -> no badge
        1-2     -> yellow (low risk, possibly worth a glance)
        3-4     -> orange (medium, likely worth review)
        5+      -> red (high, almost certainly review-worthy)

    All heuristics are pure regex / substring matching, no LLM calls.
    The function is idempotent and side-effect-free; safe to call at
    every row render.
    """
    flags = []
    customer_text = (customer_msg or "").strip()
    customer_lower = customer_text.lower()
    response_text = ai_response or ""
    response_lower = response_text.lower()
    customer_words = customer_lower.split()

    # H1: Button-combo with timing -- "Hold X + Y for N seconds" pattern.
    # Almost every fabricated procedure today included this shape (Eclipse
    # Turbo+Y, Ares Turbo+Back / Turbo+Home, etc.). Note that legitimate
    # Cosmic Byte procedures DO have these patterns too, so this is
    # informational rather than damning -- but worth a glance.
    if re.search(r"hold\s+\w+\s*\+\s*\w+(?:\s+\w+)?\s*(?:button(?:s)?)?\s*(?:together)?\s*for\s+\d+\s+second", response_lower):
        flags.append(("Button combo with timing", 2))

    # H2: LED color claim with high specificity. The Ares Pro fabrication
    # was "Orange LED = XInput" -- there is no orange LED on Ares Pro.
    # Catches both the "X LED = ..." form and "LED will turn X" form.
    if re.search(r"\b(orange|yellow|red|green|blue|white|purple|pink)\s+led\s*(?:[=:]|\bmeans\b|\bindicates\b)", response_lower) or \
       re.search(r"led\s+(?:will\s+)?(?:turn|be|become|change\s+to|light\s+up)\s+(?:solid\s+)?(orange|yellow|red|green|blue|white|purple|pink)", response_lower):
        flags.append(("LED color claim", 1))

    # H3: Vague question + multi-step response (Rule #14 violation pattern).
    # This is the highest-value heuristic -- catches the "AI generated a
    # procedure for an ambiguous question" failure mode.
    if 1 <= len(customer_words) <= 4 and len(customer_text) >= 2:
        # Count numbered list items at start of lines (markdown 1. 2. 3.)
        numbered_items = len(re.findall(r"^\s*\d+\.\s+\S", response_text, re.MULTILINE))
        if numbered_items >= 3:
            flags.append(("Short question + multi-step procedure", 3))

    # H4: Warranty advocacy patterns (the Hades headset case from v1.5.2).
    # The AI was drafting claim emails, assigning severity ratings, and
    # coaching customers on how to argue against rejection grounds.
    advocacy_patterns = [
        (r"\bsubject\s*:\s*\*?\*?warranty\s+claim", "Drafted email subject"),
        (r"\b(this|these|all\s+three).{0,40}strengthens?\s+your\s+claim", "Coaching language"),
        (r"\bmuch\s+harder\s+to\s+argue", "Coaching against rejection"),
        (r"\bpattern\s+of\s+(?:poor\s+)?manufacturing\s+(?:quality|defects?)", "Case-strength framing"),
        (r"\binadequate\s+solder\s+joint", "Fabricated root cause"),
        (r"\bloose\s+internal\s+component", "Fabricated root cause"),
        (r"\bcapacitor\s+failure", "Fabricated root cause"),
    ]
    for pattern, label in advocacy_patterns:
        if re.search(pattern, response_lower):
            flags.append((f"Warranty advocacy: {label}", 3))
            break  # one advocacy flag is enough; don't double-count

    # H5: Categorical warranty pre-judgment (Rule #11/12 violation).
    # The AI is supposed to be neutral on warranty outcomes -- only the
    # support team can determine coverage. Flag responses that pre-judge.
    cat_patterns = [
        r"\byou(?:'ll|\s+will)\s+(?:definitely\s+)?be\s+covered",
        r"\bthis\s+(?:is|qualifies)\s+(?:for|as)\s+(?:a\s+)?(?:warranty|replacement|covered)",
        r"\bdefinitely\s+(?:a\s+)?manufacturing\s+defect",
        r"\bclear\s+manufacturing\s+defect",
        r"\bthey(?:'ll|\s+will)\s+have\s+to\s+honour",
    ]
    for pattern in cat_patterns:
        if re.search(pattern, response_lower):
            # Reduce risk if the response also includes neutral framing nearby
            if "support team will evaluate" in response_lower or "support team will look" in response_lower:
                flags.append(("Coverage pre-judgment (with hedge)", 1))
            else:
                flags.append(("Coverage pre-judgment", 3))
            break

    # H6: Severity rating language (advocacy-flavoured)
    if re.search(r"\bseverity\s*[:*]+\s*\*?\*?\s*(high|medium|low|critical|severe|moderate)", response_lower):
        flags.append(("Severity rating assigned", 2))

    # H7: Drafted email template (Subject + Body shape inside the response)
    if "subject:" in response_lower and ("body:" in response_lower or "dear " in response_lower):
        flags.append(("Drafted email template", 3))

    # H8: Specific fabrication phrases we already caught today. This is
    # an "exact-match safety net" -- if any of these reappear despite the
    # anti-hallucination guards in cb_kb.py, that's a regression worth
    # surfacing immediately. Update this list as new fabrications get
    # caught and added to per-product anti-hallucination guards.
    known_fabrications = [
        ("turbo + y for 3 seconds",     "Eclipse: TURBO + Y combo"),
        ("turbo + back for 3 seconds",  "Ares: TURBO + Back combo"),
        ("turbo + home for 3 seconds",  "Ares: TURBO + Home combo"),
        ("y + home for 3 seconds",      "Lumora: Y + HOME (should be Y + P)"),
    ]
    for phrase, label in known_fabrications:
        if phrase in response_lower:
            flags.append((f"Known fabrication: {label}", 4))

    # H9: Customer-stated framing inconsistent with detected product.
    # Cheap approximation: if the response itself acknowledges the
    # customer's connection mode but the product detection in the row
    # would suggest a mismatch. We don't have product detection in
    # scope here, so we use a simpler proxy: response contains both a
    # connection-mode word AND mentions of multiple Ares variants.
    # This catches the Ares Wireless + "wired USB cable" case from v1.7.0.
    if "ares wireless" in response_lower and ("wired usb" in response_lower or "via wired" in response_lower):
        flags.append(("Possible product-mode mismatch (Ares Wireless + wired)", 2))

    score = sum(points for _, points in flags)
    return {"score": score, "flags": flags}


def _risk_badge(score):
    """Return a single-emoji badge for a risk score, suitable for inclusion
    in a row label. Returns empty string for score 0 (no clutter on
    clean rows).
    """
    if score == 0:
        return ""
    if score <= 2:
        return "🟡"
    if score <= 4:
        return "🟠"
    return "🔴"


def _render_paginated_rows(rows_with_idx, page_key, page_size):
    """Render a list of (filtered_idx, row_dict) tuples with Prev / Next
    pagination controls.

    v2.24.6: introduced to keep the admin dashboard scroll length bounded
    on days with many conversations. Without pagination, a day with 56
    conversations + several expanded rows produces an unwieldy infinite
    scroll. With pagination set to 10 per page, the worst-case scroll
    length is ~10 conversations regardless of the day's total volume.

    Parameters:
        rows_with_idx : list of (filtered_idx, row_dict)
            The rows to display. The filtered_idx is preserved so per-row
            widget keys (photo download buttons etc.) stay stable.
        page_key : str
            Unique key under which the current page is tracked in
            st.session_state. Use one key per logical pagination context
            (e.g. one per day_label, one for the flat-view list).
        page_size : int
            How many rows per page. The Prev/Next UI is suppressed when
            the total row count is <= page_size, so small days still
            render as a single uninterrupted list.

    Behaviour:
        - Pagination state survives reruns within a session, so opening
          a row does not reset the user back to page 1.
        - If page_size shrinks (user changed selector from 50 -> 10) and
          the previously stored page is now out of bounds, the page is
          clamped back to 0 silently.
        - The "Reset pages" button at the top of the dashboard clears
          every key with the `_admin_page__` prefix in one go, jumping
          all days back to page 1 simultaneously.
    """
    total = len(rows_with_idx)
    if total <= page_size:
        # Single page -- no pagination UI needed, render everything.
        for i, r in rows_with_idx:
            _render_admin_conversation_row(i, r)
        return

    total_pages = (total + page_size - 1) // page_size
    current_page = st.session_state.get(page_key, 0)
    # Clamp in case page_size shrank since the page was last set.
    if current_page < 0 or current_page >= total_pages:
        current_page = 0
        st.session_state[page_key] = 0

    start = current_page * page_size
    end = min(start + page_size, total)

    # Pagination header: Prev | "Page [N] of Y · showing A-B of N" | Next
    # v2.27.1: HOT-FIX. The v2.26.0 implementation tried to keep the
    # number_input's displayed value in sync with the actual page state
    # by manually writing st.session_state[jump_widget_key] = new_page+1
    # inside the Prev/Next button click handlers. Streamlit raises
    # StreamlitAPIException for this -- once a widget has been
    # instantiated (in any prior run), its session_state key cannot be
    # modified externally, even after st.rerun(). The previous approach
    # broke Prev/Next entirely on production.
    #
    # The fix: use a DYNAMIC widget key that includes the current page
    # number (f"...__jump_at_p{current_page}"). When current_page changes
    # via Prev/Next click + st.rerun(), the widget gets a brand-new key
    # that has no prior session_state, so Streamlit honours the
    # value=current_page+1 parameter on first instantiation. No manual
    # session_state manipulation needed -- the widget re-renders with
    # the correct value automatically because it's effectively a "new"
    # widget at the new page. Cost: old widget keys accumulate in
    # session_state as the operator paginates, but page changes within
    # a session are bounded (max ~few dozen) so this is harmless.
    p1, p2_input, p2_label, p3 = st.columns([1, 0.7, 2.3, 1])
    jump_widget_key = f"{page_key}__jump_at_p{current_page}"
    with p1:
        prev_disabled = (current_page == 0)
        if st.button(
            "← Previous",
            key=f"{page_key}__prev",
            disabled=prev_disabled,
            use_container_width=True,
        ):
            st.session_state[page_key] = current_page - 1
            st.rerun()
    with p2_input:
        # Number-input for direct page jumps. Streamlit's number_input
        # commits on blur or Enter; the value change triggers a rerun
        # and we read the new value below to update page state.
        new_page_1based = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=current_page + 1,
            step=1,
            key=jump_widget_key,
            label_visibility="collapsed",
        )
        if int(new_page_1based) - 1 != current_page:
            st.session_state[page_key] = int(new_page_1based) - 1
            st.rerun()
    with p2_label:
        st.markdown(
            f"<div style='text-align:center; padding-top:6px; opacity:0.85'>"
            f"of <b>{total_pages}</b> · "
            f"showing {start + 1}–{end} of {total}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with p3:
        next_disabled = (current_page + 1 >= total_pages)
        if st.button(
            "Next →",
            key=f"{page_key}__next",
            disabled=next_disabled,
            use_container_width=True,
        ):
            st.session_state[page_key] = current_page + 1
            st.rerun()

    # Render only the rows for this page.
    page_rows = rows_with_idx[start:end]
    for i, r in page_rows:
        _render_admin_conversation_row(i, r)


def _render_admin_conversation_row(i, r):
    """Render one conversation row's expander (customer msg, photos, AI
    response, feedback). Factored out of render_admin in v2.21.0 so both
    the flat path and the grouped Month/Week/Day path can share the same
    UI without duplication. `i` is the per-row index used for unique
    Streamlit widget keys (specifically the photo download buttons).

    History note (v2.24.4 -> v2.24.5):
    v2.24.4 briefly replaced the per-row st.expander with a button +
    conditional-content accordion to enforce "only one row open at a
    time". That worked functionally but had two problems Ronak rejected:
      (a) the buttons inherited the app's orange brand colour, making
          every row look like a warning / call-to-action rather than a
          neutral expandable header.
      (b) rendering 173 st.button widgets + a full-page st.rerun() on
          every click was significantly slower than 173 native
          st.expander widgets.
    v2.24.5 reverts to st.expander. Multiple rows can be open at once
    again -- the trade-off Ronak preferred over the button approach.
    The "too-long page" concern from the original v2.24.4 ask will be
    addressed differently (likely via pagination / smarter day-collapse
    defaults) in a future bump."""
    try:
        customer_msg = r.get("Customer Message", "")
        ai_resp      = r.get("AI Response", "")
        # v2.22.0: include the Source ("web" or "discord") in the label so
        # Ronak can see channel mix at a glance when scrolling. Pre-v2.22 rows
        # default to "web" via .get(..., "web").
        source_tag = r.get("Source", "web") or "web"

        # v2.26.0: compute review-risk score for this conversation. Score
        # is derived from heuristics that match patterns observed in
        # actual production fabrications (see _score_conversation_risk
        # docstring). The badge appears at the START of the row label
        # so the operator can scan a long list and spot risky rows
        # without expanding each one.
        risk = _score_conversation_risk(customer_msg, ai_resp)
        badge = _risk_badge(risk["score"])
        badge_prefix = f"{badge} " if badge else ""

        label = (
            f"{badge_prefix}{r.get('Date','?')} {r.get('Time','?')} "
            f"· [{source_tag}] · {r.get('Product','?')} "
            f"· {customer_msg[:55]}{'…' if len(customer_msg) > 55 else ''}"
        )
        with st.expander(label):
            # v2.26.0: if the row was flagged for review, show a callout
            # at the top of the expanded content explaining which
            # heuristics matched. This gives the operator immediate
            # context for why the row caught the filter -- instead of
            # having to guess which part of the response was suspicious.
            if risk["score"] > 0:
                flag_lines = "\n".join(
                    f"  - {label_text} *(+{points} pts)*"
                    for label_text, points in risk["flags"]
                )
                st.warning(
                    f"🚩 **Flagged for review (risk score: {risk['score']})**\n\n"
                    f"{flag_lines}\n\n"
                    f"*These heuristics are pattern-matchers, not a verdict — "
                    f"please review the response below to decide whether the AI's "
                    f"reply was actually wrong, or whether it's a false positive.*"
                )
            st.caption(f"Session: {r.get('Session ID','?')}")
            st.markdown("**Customer message**")
            st.text(customer_msg)
            # If this row has thumbnails attached, render them in a 4-column grid.
            # Stored as a JSON list of {name, data} where data is a base64 JPEG.
            thumbs_raw = r.get("Image Thumbnails", "")
            if thumbs_raw:
                try:
                    thumbs = json.loads(thumbs_raw)
                    if thumbs:
                        st.markdown(f"**Attached photos ({len(thumbs)})**")
                        cols = st.columns(min(4, len(thumbs)))
                        for ti, t in enumerate(thumbs):
                            with cols[ti % len(cols)]:
                                try:
                                    thumb_bytes = base64.b64decode(t["data"])
                                    original_name = t.get("name", f"image_{ti+1}")
                                    # Thumbnails are stored as JPEG (we convert in
                                    # _make_thumbnails_for_log), so force .jpg on
                                    # download so the file opens cleanly regardless
                                    # of what the customer originally uploaded.
                                    base_name = os.path.splitext(original_name)[0] or f"image_{ti+1}"
                                    dl_filename = f"{base_name}.jpg"
                                    st.image(thumb_bytes, caption=original_name, width=180)
                                    st.download_button(
                                        label="📥 Download photo",
                                        data=thumb_bytes,
                                        file_name=dl_filename,
                                        mime="image/jpeg",
                                        key=f"dl_{i}_{ti}",
                                        use_container_width=True,
                                    )
                                except Exception:
                                    st.caption(f"📎 {t.get('name', 'image')} (preview unavailable)")
                except (json.JSONDecodeError, TypeError):
                    # Old log row or malformed value -- skip silently
                    pass
            st.markdown("**AI response**")
            st.text(ai_resp)
            fb  = r.get("Feedback") or "No feedback"
            note = r.get("Feedback Note", "")
            st.markdown(f"**Feedback:** {fb}" + (f" — {note}" if note else ""))
    except Exception as e:
        st.warning(f"Could not display row {i}: {e}")


def render_admin():
    st.markdown("## 🎮 Cosmic Byte — Admin Dashboard")
    # v2.29.0: small operator-facing hint that all timestamps on this
    # dashboard are India Standard Time (UTC+5:30). The raw log on disk
    # is still UTC; the conversion happens in get_merged_log() so every
    # display surface (expander labels, calendar week/month grouping,
    # CSV export, daily digest) shows IST consistently.
    st.caption("🕒 Timestamps shown in IST (UTC+5:30). Storage on disk remains in UTC.")

    # v2.13.0: top action bar — refresh data without losing session, plus
    # explicit sign-out that clears the auth cookie. Distinct from the
    # bottom "Back to Support" button which keeps the session alive.
    # v2.24.6: added "Reset pages" button to jump every day's pagination
    # back to page 1 in one click, useful when the operator has been
    # paging through several days.
    _bar_c1, _bar_c2, _bar_c3, _bar_spacer = st.columns([1, 1, 1.2, 3.8])
    with _bar_c1:
        if st.button("🔄 Refresh data", key="admin_refresh", help="Reload conversation log without signing out"):
            st.rerun()
    with _bar_c2:
        if st.button("🚪 Sign out", key="admin_signout", help="Clear admin session and return to Support"):
            # v2.13.1: use the shared module-level _cookie_manager rather
            # than instantiating a new CookieManager (which would trip
            # StreamlitDuplicateElementKey). Guarded for embed_mode where
            # _cookie_manager is None.
            try:
                if _cookie_manager is not None:
                    _cookie_manager.delete(ADMIN_AUTH_COOKIE_NAME)
            except Exception:
                # Cookie delete failures shouldn't block sign-out; the
                # session_state clear below is the source of truth.
                pass
            st.session_state.admin_authenticated = False
            st.session_state.show_admin = False
            st.rerun()
    with _bar_c3:
        if st.button(
            "⊟ Reset pages",
            key="admin_reset_pages",
            help="Jump every day's pagination back to page 1. Does NOT close any expanders you have open -- Streamlit's st.expander state is internal and cannot be programmatically closed once you've interacted with it; click them yourself if needed.",
        ):
            # v2.24.6: clear every per-day / flat-view pagination key.
            # Convention: pagination keys are prefixed with
            # "_admin_page__" so they're easy to find and bulk-clear.
            keys_to_clear = [
                k for k in list(st.session_state.keys())
                if isinstance(k, str) and k.startswith("_admin_page__")
            ]
            for k in keys_to_clear:
                del st.session_state[k]
            st.rerun()

    st.divider()

    # v2.23.0: refresh the log from disk before snapshotting. The Discord
    # bot writes to /var/data/support_log.jsonl from a separate process and
    # never touches our in-memory st.session_state.log. Without this
    # refresh the admin dashboard would never show Discord conversations.
    #
    # We also overwrite st.session_state.log here so any subsequent
    # update_feedback() call in the same render gets the fresh data
    # (update_feedback also re-reads disk defensively, but keeping the
    # session cache in sync avoids confusing intermediate states).
    #
    # Fallback for dev environments without /var/data mounted: if disk
    # persistence is off, fall back to whatever's in-memory.
    #
    # v2.24.0: also merge in remote Discord rows from the bot's HTTP
    # API. The local refresh + remote fetch is wrapped in
    # get_merged_log(), which gracefully degrades to local-only when
    # BOT_API_URL/BOT_API_SECRET are unset (no behaviour change vs
    # v2.23 in that case). The merged list is for VIEW only; we keep
    # the unmerged local cache in st.session_state.log so any
    # update_feedback() call in this render (there shouldn't be one
    # from the admin path -- feedback widgets are chat-side -- but
    # belt-and-suspenders) targets a row index that's valid against
    # the local cache.
    if LOG_FILE_PATH is not None:
        fresh_log = _load_log_from_disk()
        st.session_state.log = fresh_log
    log = list(get_merged_log())

    if not log:
        st.info("No conversations logged yet.")
        if st.button("<- Back to Support", key="admin_back_empty"):
            st.session_state.show_admin = False
            st.rerun()
        return

    # ── Filters ──
    try:
        all_dates = ["All dates"] + sorted(set(r.get("Date", "") for r in log if r.get("Date")), reverse=True)
        all_products = ["All Products"] + sorted(set(r.get("Product", "") for r in log if r.get("Product")))
        # v2.22.0: Source column (web vs discord) so Ronak can split traffic.
        # The set comprehension defaults missing values to "web" -- this matches
        # the load-time backfill in _load_log_from_disk, but belt-and-suspenders.
        all_sources = ["All sources"] + sorted(set(r.get("Source", "web") or "web" for r in log))
    except Exception:
        all_dates = ["All dates"]
        all_products = ["All Products"]
        all_sources = ["All sources"]

    col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns(6)
    with col_f1:
        selected_date = st.selectbox("Date", all_dates, key="admin_date_filter")
    with col_f2:
        selected_product = st.selectbox("Product", all_products, key="admin_product_filter")
    with col_f3:
        fb_filter = st.selectbox("Feedback", ["All", "👍 Helpful", "👎 Unhelpful", "No feedback"], key="admin_fb_filter")
    with col_f4:
        selected_source = st.selectbox("Source", all_sources, key="admin_source_filter")
    with col_f5:
        # v2.24.6: per-page selector. Bounds the scroll length on days
        # with many conversations. Streamlit's st.expander state is
        # internal and cannot be programmatically closed, so the only
        # reliable way to keep the page short is to render fewer rows
        # in the first place. Default 10 strikes a balance between
        # "see enough at once" and "no infinite scroll".
        page_size = st.selectbox(
            "Per page",
            options=[5, 10, 20, 50],
            index=1,  # default 10
            key="admin_page_size",
            help="Conversations to show per page within each day. Use Prev / Next inside each day to move between pages.",
        )
    with col_f6:
        # v2.26.0: Risk filter. The 4-level filter lets the operator
        # choose how aggressive to be about surfacing potentially-risky
        # responses. "All" shows everything (current default behaviour).
        # "🟡+ Any flag" shows even low-confidence flags (good for
        # thorough review). "🟠+ Medium+" filters to medium-and-above
        # (good for daily triage). "🔴 High only" shows only the most
        # certain-looking issues (good for quick spot-check). The risk
        # score is computed by _score_conversation_risk() at render
        # time, so this filter is consistent across reruns.
        risk_filter = st.selectbox(
            "Review risk",
            options=["All", "🟡+ Any flag", "🟠+ Medium+", "🔴 High only"],
            index=0,
            key="admin_risk_filter",
            help="Filter to conversations that scored above a risk threshold. Risk score is computed from heuristics that match common fabrication patterns (button-combo with timing, LED color claims, vague-question multi-step responses, warranty advocacy language, etc.).",
        )

    # ── Apply filters ──
    try:
        filtered = list(log)
        if selected_date != "All dates":
            filtered = [r for r in filtered if r.get("Date") == selected_date]
        if selected_product != "All Products":
            filtered = [r for r in filtered if r.get("Product") == selected_product]
        if fb_filter == "No feedback":
            filtered = [r for r in filtered if not r.get("Feedback")]
        elif fb_filter != "All":
            filtered = [r for r in filtered if r.get("Feedback") == fb_filter]
        # v2.22.0: source filter. .get(..., "web") covers pre-v2.22 rows
        # that don't have the key (same default as the backfill).
        if selected_source != "All sources":
            filtered = [r for r in filtered if (r.get("Source", "web") or "web") == selected_source]
        # v2.26.0: risk-score filter. Apply AFTER the other filters so
        # the score is only computed on rows that survived the cheaper
        # exact-match filters (date, product, feedback, source) -- this
        # avoids paying for regex evaluation on rows the operator has
        # already filtered out by other criteria.
        if risk_filter != "All":
            risk_threshold = {
                "🟡+ Any flag": 1,
                "🟠+ Medium+":  3,
                "🔴 High only": 5,
            }.get(risk_filter, 0)
            filtered = [
                r for r in filtered
                if _score_conversation_risk(
                    r.get("Customer Message", ""),
                    r.get("AI Response", "")
                )["score"] >= risk_threshold
            ]
    except Exception:
        filtered = list(log)

    # ── Metrics ──
    total     = len(filtered)
    helpful   = sum(1 for r in filtered if r.get("Feedback") == "👍 Helpful")
    unhelpful = sum(1 for r in filtered if r.get("Feedback") == "👎 Unhelpful")
    sat       = f"{round(helpful / (helpful + unhelpful) * 100)}%" if (helpful + unhelpful) > 0 else "—"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", total)
    m2.metric("👍 Helpful", helpful)
    m3.metric("👎 Unhelpful", unhelpful)
    m4.metric("Satisfaction", sat)
    st.divider()

    # ── Conversation list ──
    st.markdown(f"**{total} conversation{'s' if total != 1 else ''}**")

    # v2.21.0: when the dataset spans many days/weeks/months, fall through
    # to a hierarchical Month -> Week -> Day -> conversation drill-down so
    # the page doesn't become an infinite scroll. When the dataset is
    # already narrow (specific date filter, or one day's worth), keep the
    # flat list -- the hierarchy would just add unnecessary clicks.
    rows_with_idx = list(enumerate(filtered))

    distinct_dates = {r.get("Date", "") for r in filtered if r.get("Date")}
    use_flat_view = (
        selected_date != "All dates"          # specific date filter active
        or (len(filtered) <= 30 and len(distinct_dates) <= 1)  # small one-day set
    )

    if use_flat_view:
        # v2.24.6: paginate the flat list too. Most flat-view triggers
        # (specific date filter active, or small dataset) keep the row
        # count low, but a busy single day with 50+ conversations can
        # still benefit from pagination.
        _render_paginated_rows(
            rows_with_idx,
            page_key="_admin_page__flat",
            page_size=page_size,
        )
    else:
        # Hierarchical: Month -> Week -> Day -> conversation. Auto-expand
        # the most recent path so today's conversations are visible
        # without any clicks; everything else stays collapsed.
        grouped = _group_log_for_admin(rows_with_idx)
        for m_idx, month in enumerate(grouped):
            month_expanded = (m_idx == 0)  # most recent month auto-expanded
            month_header = (
                f"📅 {month['month_label']} "
                f"· {month['month_count']} conversation"
                f"{'s' if month['month_count'] != 1 else ''}"
            )
            with st.expander(month_header, expanded=month_expanded):
                for w_idx, week in enumerate(month['weeks']):
                    week_expanded = (m_idx == 0 and w_idx == 0)
                    week_header = (
                        f"📆 {week['week_label']} "
                        f"· {week['week_count']}"
                    )
                    with st.expander(week_header, expanded=week_expanded):
                        for d_idx, day in enumerate(week['days']):
                            day_expanded = (m_idx == 0 and w_idx == 0 and d_idx == 0)
                            day_header = (
                                f"📋 {day['day_label']} "
                                f"· {day['day_count']}"
                            )
                            with st.expander(day_header, expanded=day_expanded):
                                # v2.24.6: paginate per-day. The page
                                # state key includes the day_label so
                                # each day tracks its own current page
                                # independently -- moving to page 2 of
                                # "09 May" doesn't affect "08 May".
                                _render_paginated_rows(
                                    day['rows'],
                                    page_key=f"_admin_page__day__{day['day_label']}",
                                    page_size=page_size,
                                )

    st.divider()

    # ── Email & Download ──
    st.markdown("#### 📧 Email CSV Report")
    ec1, ec2 = st.columns(2)
    with ec1:
        period_label = selected_date if selected_date != "All dates" else "All data"
        subject = f"Cosmic Byte Support Log — {period_label}"
        if st.button("📧 Send CSV to thecosmicbyte2017@gmail.com", key="admin_send_email"):
            if filtered:
                try:
                    csv_bytes = build_csv_bytes(filtered)
                    ok = send_email_with_csv(csv_bytes, subject)
                    if ok:
                        st.success(f"✅ Sent {len(filtered)} rows to thecosmicbyte2017@gmail.com")
                    else:
                        st.error("Email failed — check Gmail credentials in Render env vars.")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("No rows to send for current filters.")
    with ec2:
        if filtered:
            try:
                csv_bytes = build_csv_bytes(filtered)
                b64 = base64.b64encode(csv_bytes).decode()
                filename = f"cb_support_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                st.markdown(
                    f'''<a href="data:text/csv;base64,{b64}" download="{filename}"
                    style="display:inline-block;background:#FF9E1B;color:#101820;font-weight:700;font-family:'JetBrains Mono',monospace;
                    padding:8px 18px;border-radius:100px;text-decoration:none;font-size:12px;letter-spacing:0.06em;text-transform:uppercase;margin-top:4px">
                    ⬇️ Download CSV</a>''',
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.error(f"CSV error: {e}")

    # ── Bulk Photo Export ──
    st.markdown("#### 📦 Export Photos (ZIP)")
    st.caption("Bundles every photo attached to the filtered conversations into a single ZIP, "
               "organised in per-session folders named `{date}_{session_id}`. "
               "Useful for batch warranty/return reviews and forwarding to couriers.")
    if filtered:
        try:
            zip_bytes, n_imgs, n_convos = build_images_zip(filtered)
            if zip_bytes:
                size_kb = len(zip_bytes) / 1024
                size_label = f"{size_kb:.0f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                period_label = selected_date if selected_date != "All dates" else "all_dates"
                period_label = period_label.replace(" ", "-")
                zip_filename = f"cb_photos_{period_label}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
                st.download_button(
                    label=f"📦 Download all photos ({n_imgs} from {n_convos} conversations · {size_label})",
                    data=zip_bytes,
                    file_name=zip_filename,
                    mime="application/zip",
                    key="admin_photos_zip",
                    use_container_width=False,
                )
            else:
                st.info("No photos in the filtered conversations — nothing to export.")
        except Exception as e:
            st.error(f"ZIP build error: {e}")
    else:
        st.warning("No rows match current filters — adjust the filters above to export photos.")

    st.divider()
    if st.button("<- Back to Support", key="admin_back"):
        st.session_state.show_admin = False
        st.rerun()

# ── COOKIE MANAGER (v2.13.1: SINGLE INSTANCE PER RENDER) ──
# Streamlit does NOT dedupe components by key -- a second
# stx.CookieManager(key=...) in the same render raises
# StreamlitDuplicateElementKey. So this is the ONE place the cookie
# manager is created. Both the admin auth flow (immediately below) and
# the customer history block (further down) read from this same
# instance via the module-level _cookie_manager / _cookies bindings.
# Skipped in embed_mode where third-party cookies are unreliable in
# iframes anyway.
_cookie_manager = None
_cookies = None
if not st.session_state.get("embed_mode"):
    _cookie_manager = stx.CookieManager(key="cb_cookie_mgr")
    _cookies = _cookie_manager.get_all()

# ── ADMIN LOGIN GATE ──
if st.session_state.show_admin:
    # v2.13.0/.1: try to restore admin auth from cookie BEFORE rendering
    # the login form, so a hard refresh on the admin page reuses the
    # active session instead of dumping the operator back to the
    # password screen. Reads the shared _cookies dict (set above) --
    # never re-instantiates the manager.
    #
    # v2.24.2: handle the first-render race after a hard refresh. The
    # CookieManager iframe needs ~100ms to mount and post its cookies
    # back to the script -- during that window _cookies is None. The
    # check at line below treats None the same as "no cookie present"
    # and falls straight through to the login form, so the operator
    # sees the password prompt and types into it before the iframe-
    # mount-triggered rerun has a chance to restore auth from the
    # cookie. Fix: when _cookies is None on this path AND a cookie
    # manager exists, show a brief "restoring..." state and st.stop()
    # -- the iframe mount will trigger a rerun which lands here again
    # with _cookies populated, and the auth restore below succeeds.
    # Guard with a one-rerun-only flag so a browser that blocks the
    # iframe (cookies disabled, third-party-cookie restrictions in an
    # iframe, etc.) doesn't loop forever -- the second pass falls
    # through to the login form as a graceful degradation.
    if (not st.session_state.admin_authenticated
            and _cookie_manager is not None
            and _cookies is None
            and not st.session_state.get("_admin_cookies_waited", False)):
        st.session_state._admin_cookies_waited = True
        st.info("🔐 Restoring admin session...")
        st.stop()

    if not st.session_state.admin_authenticated and _cookies:
        _admin_token = _cookies.get(ADMIN_AUTH_COOKIE_NAME)
        if _admin_token and _verify_admin_auth_token(_admin_token, ADMIN_PASSWORD):
            st.session_state.admin_authenticated = True
            # Successful restore -- clear the wait flag so a future
            # show_admin transition (e.g. Cancel -> click Admin again)
            # gets a fresh wait window.
            st.session_state.pop("_admin_cookies_waited", None)

    if not st.session_state.admin_authenticated:
        st.markdown("### 🔒 Admin Login")
        _allowed_emails = _admin_allowed_emails()
        _otp_stage = st.session_state.get("_admin_otp_stage", "enter_email")
        # Identical wording whether or not the email is whitelisted, so the
        # form never reveals which addresses are valid admins.
        _generic_sent_msg = "If that email is authorised, a login code is on its way — check your inbox."

        def _finish_admin_login():
            """Shared success path: mark authed, set the 8h cookie, rerun."""
            st.session_state.admin_authenticated = True
            st.session_state.pop("_admin_otp_stage", None)
            st.session_state.pop("_admin_otp_email", None)
            if _cookie_manager is not None:
                _cookie_manager.set(
                    ADMIN_AUTH_COOKIE_NAME,
                    _make_admin_auth_token(ADMIN_PASSWORD),
                    expires_at=datetime.now() + timedelta(hours=ADMIN_AUTH_DURATION_HOURS),
                )
                time.sleep(0.5)  # let the cookie iframe persist before rerun (see v2.24.3)
            st.session_state.pop("_admin_cookies_waited", None)
            st.rerun()

        # ---- STAGE 1: request a code ----
        if _otp_stage == "enter_email":
            st.caption("Enter your authorised admin email. We'll send you a one-time login code.")
            email_in = st.text_input("Admin email", key="_admin_otp_email_input")
            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button("Send code"):
                    email_norm = (email_in or "").strip().lower()
                    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_norm):
                        st.error("Please enter a valid email address.")
                    else:
                        state = _prune_otp_state(_load_otp_state())
                        if email_norm in _allowed_emails:
                            ok, why = _otp_send_allowed(email_norm, state)
                            if not ok:
                                st.error(why)
                            else:
                                otp = _generate_otp()
                                now = datetime.now()
                                ent = state.get(email_norm, {})
                                ent["otp_hash"] = _hash_otp(otp, email_norm)
                                ent["expires"] = (now + timedelta(minutes=ADMIN_OTP_TTL_MINUTES)).isoformat()
                                ent["verify_attempts"] = 0
                                ent.setdefault("sends", []).append(now.isoformat())
                                state[email_norm] = ent
                                state.setdefault("_global_sends", []).append(now.isoformat())
                                _save_otp_state(state)
                                if send_otp_email(email_norm, otp):
                                    st.session_state._admin_otp_stage = "enter_code"
                                    st.session_state._admin_otp_email = email_norm
                                    st.rerun()
                                else:
                                    st.error("Couldn't send the code right now. Please try again in a moment.")
                        else:
                            # Non-whitelisted: advance to the code stage anyway so
                            # the UI gives nothing away. Any code entered will fail.
                            st.session_state._admin_otp_stage = "enter_code"
                            st.session_state._admin_otp_email = email_norm
                            st.rerun()
            with c2:
                if st.button("Cancel"):
                    st.session_state.show_admin = False
                    st.session_state.pop("_admin_otp_stage", None)
                    st.rerun()

            # Optional break-glass: only shown if explicitly enabled via env.
            if get_secret("ADMIN_ALLOW_PASSWORD_FALLBACK", "false").lower() == "true":
                with st.expander("Trouble receiving the code? (emergency password login)"):
                    pwd = st.text_input("Admin password", type="password", key="_admin_pwd_fallback")
                    if st.button("Login with password"):
                        if pwd == ADMIN_PASSWORD:
                            _finish_admin_login()
                        else:
                            st.error("Incorrect password")
            st.stop()

        # ---- STAGE 2: enter the code ----
        else:
            target = st.session_state.get("_admin_otp_email", "")
            st.caption(f"Enter the {ADMIN_OTP_LENGTH}-digit code sent to your email. "
                       f"It expires in {ADMIN_OTP_TTL_MINUTES} minutes.")
            code_in = st.text_input("Login code", max_chars=ADMIN_OTP_LENGTH, key="_admin_otp_code_input")
            c1, c2, c3 = st.columns([1, 1, 3])
            with c1:
                if st.button("Verify"):
                    state = _prune_otp_state(_load_otp_state())
                    ent = state.get(target, {})
                    if not ent or "otp_hash" not in ent:
                        st.error("No active code for that email. Please request a new one.")
                    else:
                        expired = False
                        try:
                            expired = datetime.fromisoformat(ent["expires"]) < datetime.now()
                        except Exception:
                            expired = True
                        if expired:
                            st.error("That code has expired. Please request a new one.")
                            state.pop(target, None); _save_otp_state(state)
                        elif ent.get("verify_attempts", 0) >= ADMIN_OTP_MAX_VERIFY_ATTEMPTS:
                            st.error("Too many incorrect attempts. Please request a new code.")
                            state.pop(target, None); _save_otp_state(state)
                        elif hmac.compare_digest(ent["otp_hash"], _hash_otp((code_in or "").strip(), target)):
                            state.pop(target, None); _save_otp_state(state)  # burn the code on success
                            _finish_admin_login()
                        else:
                            ent["verify_attempts"] = ent.get("verify_attempts", 0) + 1
                            remaining = ADMIN_OTP_MAX_VERIFY_ATTEMPTS - ent["verify_attempts"]
                            state[target] = ent; _save_otp_state(state)
                            if remaining > 0:
                                st.error(f"Incorrect code. {remaining} attempt(s) left.")
                            else:
                                st.error("Too many incorrect attempts. Please request a new code.")
            with c2:
                if st.button("Resend"):
                    st.session_state._admin_otp_stage = "enter_email"
                    st.rerun()
            with c3:
                if st.button("Cancel"):
                    st.session_state.show_admin = False
                    st.session_state.pop("_admin_otp_stage", None)
                    st.session_state.pop("_admin_otp_email", None)
                    st.rerun()
            st.stop()
    else:
        render_admin()
        st.stop()

# ── BROWSER-PERSISTENT HISTORY: COOKIE + REHYDRATION (v2.12.0) ──
# Skipped in embed mode -- third-party cookies are blocked by default in
# iframes on modern browsers (Chrome, Safari, Firefox), so cookie persistence
# is unreliable there. Embed-mode visits are one-shot anyway.
#
# Note on the first-render quirk: the CookieManager component returns None
# from get_all() until its iframe has mounted (one extra Streamlit rerun).
# We treat None as "not yet loaded" and skip rehydration on that pass; the
# next rerun has the cookies and rehydrates normally.
#
# v2.13.1: this block uses the module-level _cookie_manager / _cookies that
# were instantiated once before the admin gate. It does NOT create its own
# CookieManager (which would trigger StreamlitDuplicateElementKey).
if not st.session_state.get("embed_mode") and _cookie_manager is not None:
    if _cookies is not None:
        _bid = _cookies.get(HISTORY_COOKIE_NAME)
        if not _bid:
            # New visitor — mint an ID. Cookie expiry = 2x history window so
            # a returning visitor whose history is still alive has a valid
            # cookie waiting for them.
            _bid = str(uuid.uuid4())
            _cookie_manager.set(
                HISTORY_COOKIE_NAME,
                _bid,
                expires_at=datetime.now() + timedelta(days=HISTORY_EXPIRY_DAYS * 2),
            )
        st.session_state.browser_id = _bid

        # Rehydrate this product's history once per (browser_id | product)
        # combination; the marker prevents re-rehydration on every rerun.
        _current_product = st.session_state.selected_product
        _marker = f"{_bid}|{_current_product}"
        if st.session_state.get("_history_restored_for") != _marker:
            _entry = _load_history(_bid, _current_product)
            if _entry and _entry.get("messages") and not st.session_state.messages:
                st.session_state.messages = list(_entry["messages"])
                # Stash timestamp so the toast below can render once.
                st.session_state._restored_from = _entry.get("updated_at")
                st.session_state._restored_shown = False
            st.session_state._history_restored_for = _marker

        # Sweep expired entries opportunistically.
        _purge_expired()

    # One-time toast notice for the customer that history was restored.
    if st.session_state.get("_restored_from") and not st.session_state.get("_restored_shown"):
        _restored_dt = st.session_state["_restored_from"]
        if isinstance(_restored_dt, datetime):
            st.toast(
                f"💬 Restored your conversation from {_restored_dt.strftime('%d %b')}",
                icon="💬",
            )
        st.session_state._restored_shown = True

# ── HEADER ──
st.markdown(f"""
<div class="cb-header">
    <div class="cb-brand">
        <img src="{CB_LOGO}" style="width:52px;height:52px;object-fit:contain;background:var(--bg);border-radius:6px;"/>
    </div>
    <div class="cb-live-badge"><span class="status-dot"></span>Support Live</div>
</div>
""", unsafe_allow_html=True)

# ── PRODUCT SELECTOR ──
st.markdown('<div class="cb-label">Select your product</div>', unsafe_allow_html=True)

# Product change handler — only fires when user ACTUALLY changes the dropdown
def _on_product_change():
    new_product = st.session_state.get("product_dropdown", "All Products")
    if new_product != st.session_state.selected_product:
        # Save the current product's history before switching away. Skipped in
        # embed mode (cookies unreliable in iframes -> no browser_id).
        bid = st.session_state.get("browser_id")
        if bid and not st.session_state.get("embed_mode") and st.session_state.messages:
            _save_history(bid, st.session_state.selected_product, st.session_state.messages)

        st.session_state.selected_product = new_product
        st.session_state.messages = []
        st.session_state.row_nums = []
        st.session_state.feedback_given = {}
        st.session_state.input_key += 1
        st.session_state.session_id = str(uuid.uuid4())[:8]
        # Clear the rehydration markers so the new product's history loads on
        # the next render (handled by the cookie+rehydration block).
        st.session_state.pop("_history_restored_for", None)
        st.session_state.pop("_restored_from", None)
        st.session_state.pop("_restored_shown", None)

# In embed mode (iframe on product page), product is locked to URL param — no dropdown
if not st.session_state.get("embed_mode"):
    st.selectbox(
        "Product",
        PRODUCTS,
        index=PRODUCTS.index(st.session_state.selected_product),
        label_visibility="collapsed",
        key="product_dropdown",
        on_change=_on_product_change
    )

st.divider()

# ── WELCOME ──
if not st.session_state.messages:
    product = st.session_state.selected_product
    welcome = "👋 Hi! I'm the Cosmic Byte support assistant. Before I help, could you tell me which exact Cosmic Byte product you have and what issue you are facing?" if product == "All Products" else f"👋 Hi! I'm here to help with your Cosmic Byte <strong>{product}</strong>. Could you tell me what issue you are facing? I'll do my best to help you fix it right away."

    st.markdown(f"""
    <div class="msg-bot">
        <div class="msg-bot-icon">⚡</div>
        <div class="msg-bot-bubble">
            <div class="msg-bot-name">Cosmic Byte Support</div>
            {welcome}
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="cb-label" style="margin-top:14px">Common questions</div>', unsafe_allow_html=True)
    quick_qs = QUICK_QUESTIONS.get(product, QUICK_QUESTIONS["All Products"])
    q_cols = st.columns(len(quick_qs))
    for i, qq in enumerate(quick_qs):
        with q_cols[i]:
            if st.button(qq, key=f"qq_{i}_{product}"):
                st.session_state.messages.append({"role": "user", "content": qq})
                st.session_state.input_key += 1
                st.rerun()

# ── CHAT HISTORY + FEEDBACK ──
ai_response_index = 0
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="msg-user">
            <div class="msg-user-bubble">{msg["content"]}</div>
        </div>""", unsafe_allow_html=True)
        # If the customer attached images, render small thumbnails right under
        # the message bubble so the chat history reflects what was sent.
        if msg.get("images"):
            thumb_cols = st.columns(min(4, len(msg["images"])))
            for ti, img in enumerate(msg["images"]):
                with thumb_cols[ti % len(thumb_cols)]:
                    try:
                        img_bytes = base64.b64decode(img["data"])
                        st.image(img_bytes, caption=img.get("name", ""), width=180)
                    except Exception:
                        st.caption(f"📎 {img.get('name', 'attached image')}")
    else:
        st.markdown(f"""
        <div class="msg-bot">
            <div class="msg-bot-icon">⚡</div>
            <div class="msg-bot-bubble">
                <div class="msg-bot-name">Cosmic Byte Support</div>
                {msg["content"]}
            </div>
        </div>""", unsafe_allow_html=True)

        # Feedback buttons per AI response
        fb_key = f"fb_{ai_response_index}"
        if fb_key not in st.session_state.feedback_given:
            col1, col2, col3 = st.columns([1, 1, 6])
            with col1:
                if st.button("👍", key=f"up_{ai_response_index}"):
                    row = msg.get("log_idx")
                    update_feedback(row, "👍 Helpful")
                    st.session_state.feedback_given[fb_key] = "👍"
            with col2:
                if st.button("👎", key=f"dn_{ai_response_index}"):
                    st.session_state.feedback_given[fb_key] = "👎_pending"
        elif st.session_state.feedback_given.get(fb_key) == "👎_pending":
            with st.form(key=f"fb_form_{ai_response_index}", clear_on_submit=True):
                note = st.text_input("What was wrong with this answer?", placeholder="e.g. Wrong steps, missing info...")
                submitted = st.form_submit_button("Submit feedback")
                if submitted:
                    row = msg.get("log_idx")
                    update_feedback(row, "👎 Unhelpful", note)
                    st.session_state.feedback_given[fb_key] = f"👎 - {note}"
        else:
            st.markdown(f"<p style='font-size:11px;color:#8a92a3;margin:2px 0 10px'>Thanks for your feedback: {st.session_state.feedback_given.get(fb_key, '')}</p>", unsafe_allow_html=True)

        ai_response_index += 1

# ── MANAGE HISTORY (v2.12.0) ──
# Visible only when there are messages AND we're not in embed mode AND a
# browser_id has been established. Lets the customer wipe their stored
# conversation for the current product.
if (
    st.session_state.messages
    and not st.session_state.get("embed_mode")
    and st.session_state.get("browser_id")
):
    with st.expander("🕘 Manage chat history", expanded=False):
        st.caption(
            f"Your chat for **{st.session_state.selected_product}** is "
            f"remembered on this browser for {HISTORY_EXPIRY_DAYS} days. "
            f"Image attachments are not saved."
        )
        if st.button("🗑️ Clear my chat history for this product", key="clear_history_btn"):
            _clear_history(
                st.session_state.browser_id,
                st.session_state.selected_product,
            )
            st.session_state.messages = []
            st.session_state.row_nums = []
            st.session_state.feedback_given = {}
            st.session_state.pop("_restored_from", None)
            st.session_state.pop("_restored_shown", None)
            st.session_state.pop("_history_restored_for", None)
            st.toast("History cleared.", icon="🗑️")
            st.rerun()

# ── AI RESPONSE ──
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_question = st.session_state.messages[-1]["content"]
    product = st.session_state.selected_product
    # For "All Products" mode: smart KB injection to avoid sending 27K tokens.
    # 1. If specific products are mentioned → inject only those KBs (e.g. comparison)
    # 2. If recommendation/comparison intent but no specific product → inject compact catalogue
    # 3. If nothing detected yet → empty (bot will ask which product)
    if product == "All Products":
        detected_list, is_rec = detect_products_from_message(st.session_state.messages)
        if detected_list:
            # Inject KB for every mentioned product (e.g. both sides of a comparison)
            knowledge = "\n\n".join(
                f"=== {p} ===\n{KNOWLEDGE_BASE[p]}"
                for p in detected_list if p in KNOWLEDGE_BASE
            )
        elif is_rec:
            # Recommendation query with no specific product — send compact catalogue
            knowledge = CATALOGUE_ALL
        else:
            knowledge = ""  # Bot will ask which product the customer has
    else:
        knowledge = KNOWLEDGE_BASE.get(product, "")

    with st.spinner(""):
        try:
            # Trim history to last 8 messages (4 turns) to control token costs.
            # KB stays in first message; middle history is pruned on long chats.
            #
            # v2.23.2: the previous trim `all_msgs[:1] + all_msgs[-(MAX_HISTORY-1):]`
            # could produce two consecutive user messages at the head→tail seam.
            # We always reach this code with the last message being the user's
            # just-appended question, so len(all_msgs) is always odd. For odd
            # lengths > MAX_HISTORY (9, 11, 13, ...) the index `-(MAX_HISTORY-1)`
            # lands on a user message, giving us [user(msg0), user(msg-7), asst, ...]
            # and a 400 from Anthropic's API ("messages: roles must alternate").
            #
            # Fix: check the role at the head→tail seam and shave one message
            # off the front of the tail if it would create a same-role adjacency.
            # Trimmed length is therefore <= MAX_HISTORY (sometimes MAX_HISTORY-1
            # in the alternation-fix case), and alternation is guaranteed.
            MAX_HISTORY = 8
            all_msgs = st.session_state.messages
            if len(all_msgs) > MAX_HISTORY:
                head = all_msgs[:1]
                tail_size = MAX_HISTORY - 1
                # If the tail would start with the same role as the head's last
                # message, drop one to shift parity. Loop defensively in case
                # the messages list is ever non-strictly-alternating for some
                # other reason.
                while tail_size > 0 and all_msgs[-tail_size]["role"] == head[-1]["role"]:
                    tail_size -= 1
                trimmed = head + all_msgs[-tail_size:] if tail_size > 0 else head
            else:
                trimmed = all_msgs

            api_messages = []
            for m in trimmed:
                role = "user" if m["role"] == "user" else "assistant"
                # Assistant messages stay as plain text. User messages with
                # attached images become a content list with text + image blocks.
                if role == "user" and m.get("images"):
                    blocks = [{"type": "text", "text": m["content"]}]
                    for img in m["images"]:
                        blocks.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": img["media_type"],
                                "data": img["data"],
                            },
                        })
                    api_messages.append({"role": role, "content": blocks})
                else:
                    api_messages.append({"role": role, "content": m["content"]})

            # Inject KB + buy link into first user message only
            buy_link = PRODUCT_URLS.get(product, "https://www.thecosmicbyte.com/product-category/gaming-controllers/")
            buy_info = f"""
⚠️ OFFICIAL BUY LINK (use this EXACT URL — do NOT modify, do NOT search for a different one):
{buy_link}
COUPON: ONLINEPAY (10% off online payments — always mention this)
""" if product != "All Products" else ""

            # The first user message may now be either a plain string or a
            # content list (if images were attached on the very first turn).
            # Either way, we need to inject the KB + buy info around the
            # original customer text. Find the text block (or use the string)
            # and wrap it; leave any image blocks intact.
            first = api_messages[0]
            if isinstance(first["content"], str):
                original_text = first["content"]
                first["content"] = f"""PRODUCT SELECTED: {product}

KNOWLEDGE BASE (product manuals):
{knowledge}
{buy_info}

CUSTOMER MESSAGE: {original_text}"""
            else:
                # Content is a list of blocks. Find the text block, wrap it.
                for blk in first["content"]:
                    if blk.get("type") == "text":
                        original_text = blk["text"]
                        blk["text"] = f"""PRODUCT SELECTED: {product}

KNOWLEDGE BASE (product manuals):
{knowledge}
{buy_info}

CUSTOMER MESSAGE: {original_text}

(NOTE: The customer attached one or more images with this message. Examine each image carefully and incorporate what you see into your response per the VISUAL EVIDENCE HANDLING rule in your system prompt.)"""
                        break

            # Third-party brand handling:
            #   - If we have a structured manual for the brand in THIRD_PARTY_BRAND_MANUALS,
            #     inject it directly into the system prompt and skip web search. The manual
            #     is authoritative for what CB sells; no point paying for a web call.
            #   - If we don't have a manual (e.g. Cherry MX, Brook, Fanatec, Thrustmaster),
            #     fall back to web search so the AI can still answer accurately.
            #
            # v2.25.0: build the full system text as a string first (same
            # logic as before), then wrap it in a single cache_control
            # text block so Anthropic caches the system prompt across
            # calls. Cache reads cost 10% of base input -- 90% savings
            # on the system+knowledge portion, which is the bulk of input
            # tokens. Cache write costs 1.25x base, breaking even after
            # ~1.25 reuses within the 5-minute TTL window. Cosmic Byte's
            # traffic pattern (many customers asking about the same
            # product within a few minutes) hits this break-even
            # comfortably for hot products.
            third_party = detect_third_party_brand(user_question)
            system_text = SYSTEM_PROMPT + "\n\nPRODUCT KNOWLEDGE:\n" + knowledge

            api_kwargs = dict(
                model="claude-haiku-4-5-20251001",
                max_tokens=1500,
                messages=api_messages,
            )
            if third_party:
                brand_manual = THIRD_PARTY_BRAND_MANUALS.get(third_party)
                if brand_manual:
                    # We have authoritative info for this brand -- inject the manual.
                    system_text += (
                        f"\n\n=== THIRD-PARTY BRAND MANUAL: {third_party} ===\n"
                        f"The customer is asking about {third_party}, a third-party brand sold on thecosmicbyte.com. "
                        f"Use the manual below as your AUTHORITATIVE source for what CB sells, compatibility, "
                        f"variants, pricing ranges and policies. Do NOT contradict it with outside info. "
                        f"For questions outside this manual's scope (e.g. very recent product launches by the brand), "
                        f"refer the customer to the brand site URL listed in the manual or to the CB product page. "
                        f"Always link back to thecosmicbyte.com for purchasing.\n\n"
                        f"{brand_manual}"
                    )
                else:
                    # No manual on file -- fall back to web search.
                    api_kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]
                    system_text += (
                        f"\n\nThe customer is asking about {third_party} — a third-party brand sold on thecosmicbyte.com. "
                        f"Use web search to find accurate specs, compatibility and support info. "
                        f"Always link back to thecosmicbyte.com for purchasing."
                    )

            # v2.25.0: wrap the assembled system text in a single cached
            # text block. Anthropic caches everything up to and including
            # this block (tools + system + the implicit prefix), so the
            # first call about each (product, brand) combo writes the
            # cache (paying 1.25x for that portion) and every subsequent
            # call within the 5-minute TTL hits the cache (paying 0.1x).
            #
            # Haiku 4.5's cache minimum is 4096 tokens. Our system_text
            # (SYSTEM_PROMPT + product manual slice + optional brand
            # manual) reliably exceeds this for any production query.
            # If a query ever produces a system_text below 4096 tokens,
            # the API request still succeeds and we just silently pay
            # full price on that one call -- no harm done.
            #
            # Output quality is unaffected: the model still processes
            # the full input identically, the cache only reuses the
            # pre-computed key-value cache for the cached prefix.
            api_kwargs["system"] = [
                {
                    "type": "text",
                    "text": system_text,
                    "cache_control": {"type": "ephemeral", "ttl": "1h"},
                }
            ]

            response = client.messages.create(**api_kwargs)
            # Extract text from response (may contain tool use blocks)
            answer = ""
            for block in response.content:
                if hasattr(block, "text"):
                    answer += block.text
            if not answer:
                answer = "I was unable to get a response. Please try again or contact us at cc@thecosmicbyte.com."
            # Log conversation and store index directly in message
            # Annotate logged question with image count so analytics can see
            # which queries included visual evidence.
            last_user_msg = st.session_state.messages[-1]
            n_imgs = len(last_user_msg.get("images", []))
            logged_question = user_question + (f" [+{n_imgs} image(s) attached]" if n_imgs else "")
            row_num = log_conversation(
                st.session_state.session_id,
                product,
                logged_question,
                answer,
                images=last_user_msg.get("images"),
                client_ip=_get_client_ip(),
            )
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "log_idx": row_num
            })
            # v2.12.0: persist this turn so a returning customer can pick up
            # where they left off. Skipped in embed mode (no browser_id).
            _bid_save = st.session_state.get("browser_id")
            if _bid_save and not st.session_state.get("embed_mode"):
                _save_history(_bid_save, product, st.session_state.messages)
            st.rerun()

        except Exception as e:
            st.error("Unable to connect. Please try again or visit thecosmicbyte.com/raise-a-ticket/")
            # ── DIAGNOSTICS: surface the real error so we can debug ──
            # Hidden behind an expander so the customer-facing UX stays clean.
            # Remove or comment out once the underlying issue is resolved.
            import traceback
            with st.expander("🔧 Technical details (for support diagnosis)", expanded=True):
                st.write(f"**Error type:** `{type(e).__name__}`")
                st.write(f"**Error message:** {str(e)}")
                # Most common Anthropic SDK errors expose a status_code / response
                if hasattr(e, "status_code"):
                    st.write(f"**HTTP status:** `{e.status_code}`")
                if hasattr(e, "response") and hasattr(e.response, "text"):
                    st.code(e.response.text[:2000], language="json")
                st.write("**Full traceback:**")
                st.code(traceback.format_exc(), language="python")
            # Also print to server logs (visible in Streamlit Cloud / wherever deployed)
            print(f"[support_portal_v2 error] {type(e).__name__}: {e}", flush=True)
            print(traceback.format_exc(), flush=True)

# ── INPUT ──
st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
st.markdown("<p style='font-size:10px;color:#8a92a3;margin:0 0 4px'>Press Enter or click Send to submit. You can attach up to 4 photos of your product / issue (PNG/JPG/WebP, max 5MB each).</p>", unsafe_allow_html=True)
with st.form(key=f"chat_form_{st.session_state.input_key}", clear_on_submit=True):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_input("Ask", placeholder=f"Describe your issue with your {st.session_state.selected_product}...",
                                    label_visibility="collapsed")
    with col_btn:
        submitted = st.form_submit_button("Send ->", use_container_width=True)
    uploaded_files = st.file_uploader(
        "📎 Attach photos of your product or issue (optional) — up to 4 images, 5MB each",
        type=["png", "jpg", "jpeg", "webp", "gif"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.input_key}",
        help="Supported: PNG, JPG, WebP, GIF. Max 4 images, 5MB per file.",
    )
    if submitted and (user_input.strip() or uploaded_files):
        # Validate + base64-encode any attached images. Cap at 4 images, 5MB each
        # (Anthropic API limit). Skip oversized files with a friendly warning.
        image_payloads = []
        skipped = []
        if uploaded_files:
            for uf in uploaded_files[:4]:
                raw = uf.getvalue()
                if len(raw) > 5 * 1024 * 1024:
                    skipped.append(f"{uf.name} (over 5MB)")
                    continue
                # Map content_type to media_type Anthropic accepts.
                ct = (uf.type or "").lower()
                if ct in ("image/jpeg", "image/jpg"):
                    media_type = "image/jpeg"
                elif ct == "image/png":
                    media_type = "image/png"
                elif ct == "image/webp":
                    media_type = "image/webp"
                elif ct == "image/gif":
                    media_type = "image/gif"
                else:
                    # Fallback: try to detect via PIL
                    try:
                        with _PILImage.open(_io.BytesIO(raw)) as im:
                            fmt = (im.format or "").lower()
                            if fmt == "jpeg":
                                media_type = "image/jpeg"
                            elif fmt == "png":
                                media_type = "image/png"
                            elif fmt == "webp":
                                media_type = "image/webp"
                            elif fmt == "gif":
                                media_type = "image/gif"
                            else:
                                skipped.append(f"{uf.name} (unsupported format)")
                                continue
                    except Exception:
                        skipped.append(f"{uf.name} (unreadable)")
                        continue
                b64 = base64.b64encode(raw).decode("ascii")
                image_payloads.append({"data": b64, "media_type": media_type, "name": uf.name})
            if len(uploaded_files) > 4:
                skipped.append(f"{len(uploaded_files) - 4} extra file(s) — only first 4 sent")
        if skipped:
            st.warning("Some attachments were skipped: " + "; ".join(skipped))
        msg = {"role": "user", "content": user_input.strip() or "(image attached — please look at it)"}
        if image_payloads:
            msg["images"] = image_payloads
        st.session_state.messages.append(msg)
        st.session_state.input_key += 1
        st.rerun()

if st.session_state.messages:
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Clear chat", key="clear"):
            st.session_state.messages = []
            st.session_state.feedback_given = {}
            st.session_state.session_id = str(uuid.uuid4())[:8]
            st.session_state.input_key += 1
            st.rerun()

# ── DISCLAIMER ──
st.markdown("""
<div style="
    margin-top: 1.5rem;
    background: rgba(255,158,27,0.10);
    border: 1px solid #2b3744;
    border-left: 3px solid #FF9E1B;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 11px;
    color: #c4c9d4;
    line-height: 1.6;
    font-family: 'Sora', sans-serif;
">
    <span style="color:#FF9E1B;font-weight:700;">⚠ AI Disclaimer:</span>
    This support chat is powered by AI and is intended to provide general guidance based on Cosmic Byte product manuals.
    Responses may not always be accurate, complete, or up to date.
    For warranty claims, order issues, returns, or any official matter, please contact our support team directly.
    Cosmic Byte is not liable for any decisions made solely based on AI-generated responses.
    Photos you attach are retained briefly with your conversation for support quality review.
</div>
""", unsafe_allow_html=True)

# ── FOOTER ──
st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
st.divider()
st.markdown("""
<div class="cb-footer">
    <div>
        Need more help? &nbsp;
        <a href="https://www.thecosmicbyte.com/raise-a-ticket/" target="_blank"
           style="background:#FF9E1B;color:#101820;padding:5px 14px;border-radius:100px;font-weight:700;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;font-family:'JetBrains Mono',monospace;text-decoration:none">
           Raise a ticket
        </a>
        &nbsp;&nbsp;
        <a href="mailto:cc@thecosmicbyte.com">cc@thecosmicbyte.com</a>
        &nbsp;·&nbsp;
        <a href="tel:+917351615161">+91 7351615161</a>
        <span style="color:#333">&nbsp;(Mon-Sat 10am-6pm)</span>
    </div>
    <a href="https://www.thecosmicbyte.com" target="_blank" style="color:#ffb347;font-size:11px">thecosmicbyte.com</a>
</div>
<div style="text-align:right;color:#8a92a3;font-size:10px;font-family:'JetBrains Mono',monospace;letter-spacing:0.04em;margin-top:4px">
    v__VERSION_PLACEHOLDER__
</div>
""".replace("__VERSION_PLACEHOLDER__", __version__), unsafe_allow_html=True)

# Admin access link (subtle, at bottom)
st.markdown("<div style='margin-top:1.5rem;text-align:center'>", unsafe_allow_html=True)
if st.button("⚙️ Admin", key="open_admin", help="Admin dashboard"):
    st.session_state.show_admin = True
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)
