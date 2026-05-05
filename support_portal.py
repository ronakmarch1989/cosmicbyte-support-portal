import streamlit as st
import anthropic
from datetime import datetime

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cosmic Byte Support",
    page_icon="🎮",
    layout="centered"
)

# ─────────────────────────────────────────────
#  COSMIC BYTE BRAND STYLING
#  Colors from thecosmicbyte.com:
#  Orange accent: #FF6B00
#  Dark background: #0D0D0D
#  Card surface: #1A1A1A
#  Text: #FFFFFF / #CCCCCC
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500&display=swap');

html, body, [class*="css"] {
    background-color: #0D0D0D !important;
    color: #FFFFFF;
}

.stApp {
    background-color: #0D0D0D;
}

.main .block-container {
    max-width: 760px;
    padding-top: 1.5rem;
    padding-bottom: 4rem;
}

/* Header */
.cb-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 1.25rem 0 1rem;
    border-bottom: 1px solid #2A2A2A;
    margin-bottom: 1.5rem;
}
.cb-logo-text {
    font-family: 'Rajdhani', sans-serif;
    font-size: 26px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.04em;
}
.cb-logo-text span { color: #FF6B00; }
.cb-tagline {
    font-size: 11px;
    color: #888;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 2px;
}
.cb-support-badge {
    margin-left: auto;
    background: #FF6B00;
    color: #000;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 3px;
}

/* Product selector */
.cb-product-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 8px;
    margin-bottom: 1.5rem;
}
.cb-product-chip {
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 6px;
    padding: 10px 12px;
    cursor: pointer;
    transition: all 0.15s;
    font-size: 13px;
    font-weight: 500;
    color: #CCC;
    text-align: center;
}
.cb-product-chip:hover { border-color: #FF6B00; color: #FF6B00; }
.cb-product-chip.active { border-color: #FF6B00; background: rgba(255,107,0,0.1); color: #FF6B00; }

/* Chat messages */
.chat-wrap {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-bottom: 1rem;
}
.msg-user {
    align-self: flex-end;
    background: #FF6B00;
    color: #000;
    padding: 11px 16px;
    border-radius: 16px 16px 3px 16px;
    max-width: 80%;
    font-size: 14px;
    line-height: 1.55;
    font-weight: 500;
}
.msg-bot {
    align-self: flex-start;
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    color: #E8E8E8;
    padding: 13px 16px;
    border-radius: 3px 16px 16px 16px;
    max-width: 85%;
    font-size: 14px;
    line-height: 1.65;
}
.msg-bot-label {
    font-size: 11px;
    color: #FF6B00;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.msg-meta {
    font-size: 11px;
    color: #555;
    margin-top: 6px;
    text-align: right;
}

/* Quick questions */
.quick-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 1rem;
}
.quick-btn {
    background: #1A1A1A;
    border: 1px solid #333;
    border-radius: 16px;
    padding: 6px 12px;
    font-size: 12px;
    color: #AAA;
    cursor: pointer;
}
.quick-btn:hover { border-color: #FF6B00; color: #FF6B00; }

/* Input area */
.stTextInput input {
    background: #1A1A1A !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: #FFF !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
}
.stTextInput input:focus {
    border-color: #FF6B00 !important;
    box-shadow: 0 0 0 1px #FF6B00 !important;
}
.stTextInput input::placeholder { color: #555 !important; }

/* Buttons */
.stButton button {
    background: #FF6B00 !important;
    color: #000 !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.04em !important;
    padding: 10px 20px !important;
}
.stButton button:hover { background: #E55A00 !important; }

/* Select box */
.stSelectbox > div > div {
    background: #1A1A1A !important;
    border: 1px solid #333 !important;
    color: #FFF !important;
    border-radius: 6px !important;
}

/* Divider */
hr { border-color: #2A2A2A !important; }

/* Escalation box */
.escalate-box {
    background: #1A1A1A;
    border: 1px solid #FF6B00;
    border-radius: 8px;
    padding: 14px 16px;
    margin-top: 1rem;
    font-size: 13px;
    color: #CCC;
    line-height: 1.6;
}
.escalate-box strong { color: #FF6B00; }

/* Status indicator */
.status-dot {
    width: 8px; height: 8px;
    background: #22C55E;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
}

/* Scrollable chat area */
.chat-container {
    max-height: 520px;
    overflow-y: auto;
    padding: 4px 0;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ANTHROPIC CLIENT
# ─────────────────────────────────────────────
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# ─────────────────────────────────────────────
#  PRODUCT KNOWLEDGE BASE
#  All manual content stored here as context
#  Add new products by adding to KNOWLEDGE_BASE
# ─────────────────────────────────────────────
KNOWLEDGE_BASE = {

    "Lumora": """
COSMIC BYTE LUMORA — TRI-MODE CONTROLLER — FULL MANUAL

CONNECTIVITY:
- 2.4GHz Wireless: Insert USB dongle into PC. Press and hold PAIRING (P) button for 3 seconds until LED flashes purple. Controller auto-connects to dongle. Best for PC — lowest latency, 1000Hz polling rate.
- Bluetooth Android: Hold PAIRING (P) + A for 3 seconds until green LED flashes rapidly. Find "Cosmic Byte Lumora" in Bluetooth settings.
- Bluetooth iOS: Hold PAIRING (P) + B for 3 seconds until blue LED flashes rapidly.
- Bluetooth PC (Gyro mode): Hold Y + P for 3 seconds. Device appears as "Pro Controller" in Windows Bluetooth — NOT as "Cosmic Byte Lumora".
- Wired USB-C: Plug cable into controller and PC. Auto-detects. Default is X-Input mode. Yellow LED = X-Input. Red LED = D-Input. Toggle with Back + Start held 3 seconds.
- Software (Cosmic Byte PC app): Only works in Wired or 2.4GHz mode. Does NOT work via Bluetooth.
- Auto sleep: 5 minutes of inactivity. Press HOME to wake.
- Range: 2.4GHz up to 7-10 meters. Bluetooth up to 8 meters.

PLATFORM COMPATIBILITY:
- Designed EXCLUSIVELY for Windows PC use.
- NOT compatible with PlayStation, Xbox, Nintendo Switch or any console.
- No warranty or support for console use.
- Android support is limited and not covered under warranty.

POWER:
- Power ON: Press HOME button once.
- Power OFF: Hold HOME button for 5 seconds.
- Battery: 1300mAh, up to 10 hours with LED off.
- Charging: USB-C. Use 5V/1A adapter or PC USB port. Avoid fast chargers above 10W.
- Charging LED: HOME LED breathes slowly = charging. LED off = fully charged. LED flashes quickly = low battery.
- Battery check: Press Macro + RB. LED shows: Red=1-25%, Yellow=26-50%, Blue=51-75%, Green=76-100%.

TURBO:
- Enable: Press Turbo + [button].
- Disable: Repeat same combination.
- Clear all turbo: Hold TURBO + START for 2 seconds. Controller vibrates once.

MACROS:
- Record: Hold Macro (M) + ML/MR/LK/RK for 2 seconds until LED flashes. Press button sequence. Press M again to save.
- Clear: Hold Macro (M) + ML/MR/LK/RK for 2 seconds. Press M to clear.

GYRO:
- Native gyro: Bluetooth mode (Y+P pairing). Shows as "Pro Controller".
- Software gyro (works in any game): Connect via Wired or 2.4GHz. Open Cosmic Byte software. Assign gyro to any button. Choose mode: Always On, Press to Activate, or Toggle. Map gyro to mimic Left or Right joystick. Works in any game even without native gyro support.

JOYSTICK:
- Calibration: Turn off. Hold Back + X + Home for 1 second. Rotate both joysticks clockwise 3 times. Press both triggers 3 times. Press Start to complete.
- Range modes: Press L3/R3 + Macro to toggle — Full Circle (default), Small Circle (precision), Square Mode (tight angles).

TRIGGERS (Hall Effect):
- Analog mode: Smooth gradual input.
- Digital mode: Instant button-like actuation.
- Press PAIRING key to cycle: 30% range → 60% range → 100% range. Controller vibrates once each change.

D-PAD / JOYSTICK SWAP:
- If D-pad and joystick roles appear swapped, this is caused by the swap setting in the Cosmic Byte software. Open software, find swap setting, toggle back to default.

VIBRATION:
- Increase: R3 + Left Stick Up for 3 seconds.
- Decrease: R3 + Left Stick Down for 3 seconds.
- Levels: 100% → 70% → 30% → Off.

RGB LIGHTING:
- Toggle: Cycles through Pattern RGB → Joystick RGB → Off → All Lighting.
- Cycle effects: Turbo + R3.
- Change color: Turbo + L3.
- Toggle on/off: Hold Turbo + R3 for 3 seconds.

FIRMWARE UPDATE:
- Step 1: Uninstall existing Cosmic Byte software completely.
- Step 2: Download latest software from thecosmicbyte.com.
- Step 3: Connect controller via USB-C wired mode.
- Step 4: Install software — firmware flashes automatically during installation.
- Wired mode is required for firmware update.

RESET:
- Hardware reset: Insert pin into RESET hole on back. Hold 2 seconds. Pairing data may clear. Macros are NOT deleted.

AUDIO:
- 3.5mm audio jack works in 2.4GHz and Wired mode only. NOT available in Bluetooth mode.

WARRANTY:
- 1 year against manufacturing defects only.
- Physical damage, water damage, tampered products NOT covered.
- Console use NOT covered.
""",

    "Stellaris": """
COSMIC BYTE STELLARIS — TRI-MODE WIRELESS CONTROLLER — FULL MANUAL

CONNECTIVITY:
- Wired USB-C (PC XInput): Plug in and press HOME. LED2 stays on.
- Wired USB-C (PC DInput): Under XInput, long-press HOME. LED3 stays on.
- Wired USB-C (Android DInput): Plug into Android, press HOME. LED3 stays on.
- 2.4GHz PC XInput: Press X + HOME for 3 seconds. LED2 stays on.
- 2.4GHz PC DInput: Under XInput, long-press SELECT + HOME. LED3 stays on.
- 2.4GHz Android XInput: Press X + HOME for 3 seconds. LED2 stays on.
- Bluetooth PC XInput: Hold B + HOME for 3 seconds. LED2 stays on.
- Bluetooth PC DInput: Hold A + HOME for 3 seconds. LED3 stays on.
- Bluetooth PC Gyro: Hold Y + HOME for 3 seconds. LED4 stays on.
- Bluetooth Android XInput: Hold B + HOME. LED2 stays on.
- Bluetooth Android DInput: Hold A + HOME. LED3 stays on.
- Bluetooth Android Gyro: Hold Y + HOME. LED4 stays on.
- Bluetooth iOS DualShock: Hold Turbo + HOME. LED1 stays on.
- Bluetooth iOS XInput: Hold B + HOME. LED2 stays on.
- Bluetooth iOS Gyro: Hold Y + HOME. LED4 stays on.
- Gyro mode is EXCLUSIVELY available in Bluetooth mode only.
- iOS support is limited and varies by game.
- Software (Cosmic Byte PC app): Only works in Wired or 2.4GHz mode.

GYRO ON-THE-FLY (works in any game):
- Connect via Wired or 2.4GHz.
- Open Cosmic Byte software.
- Assign gyro to any button.
- Choose activation mode: Always On, Press to Activate, or Toggle.
- Map gyro output to mimic Left or Right joystick.
- This makes gyro work in ANY game even without native gyro support.

PLATFORM COMPATIBILITY:
- Designed for PC (Windows XInput/DInput).
- Multi-device: PC, Android, iOS, macOS.
- NOT supported on any gaming console. No warranty for console use.

TRIGGER MODES:
- Physical trigger mode switch on controller body.
- Analog mode (switch flipped inward): Longer travel, pressure-sensitive, gradual input. Best for racing and simulation games.
- Digital mode (switch flipped outward): Shorter travel, instant button-like response. Best for FPS and competitive games.

TURBO:
- Enable: Hold TURBO + [button].
- Speed levels: Level 1 = 5/sec, Level 2 = 12/sec (default), Level 3 = 20/sec.
- Adjust speed: TURBO + Right Stick Right (increase), TURBO + Right Stick Left (decrease).
- Clear all: Hold TURBO for 5 seconds.

MACROS (ML/MR back buttons):
- Record: Hold TURBO then hold ML/MR for 2 seconds. Press button sequence (up to 22 inputs). Press same M button to save. Vibrates once to confirm.
- Clear: Enter macro mode, press same M button with no inputs. Vibrates once to confirm deletion.

ABXY SWAP:
- Hold TURBO + R3 for 3 seconds. Motor vibration confirms. A swaps with B and X with Y simultaneously.

D-PAD AND LEFT STICK SWAP (PC MODE):
- Hold START + L3 for 3 seconds. Motor vibration confirms swap.

JOYSTICK ANGLE MODE:
- Hold L3 + TURBO for 3 seconds. Toggles between Circle mode and Square (45°) mode for better diagonal accuracy.

D-PAD 4-WAY / 8-WAY:
- Hold SELECT + RIGHT (D-pad) for 3 seconds. Single vibration = 4-Way. Continuous = 8-Way (default).

STEAM MODE (Wired only):
- Power OFF controller. Hold R3, connect USB-C cable. Release R3. Auto-enters Steam Mode.
- To exit: disconnect and reconnect normally.

VIBRATION:
- Increase: TURBO + Right Stick UP.
- Decrease: TURBO + Right Stick DOWN.
- Levels: 100% → 70% → 40% → OFF. Default: 70%.

RGB LIGHTING:
- Toggle all ON/OFF: Hold LB + RB simultaneously for 5 seconds.
- Cycle RGB modes: Press TURBO + SELECT.
- Change color: Press TURBO + RIGHT (D-pad).
- Brightness increase: Hold TURBO + UP (D-pad).
- Brightness decrease: Hold TURBO + DOWN (D-pad).
- Modes: Rainbow (default), Color Cycle, Breathing, Fixed Color Manual.

BATTERY:
- Check battery: Press CAPTURE + START. LEDs show level for 3 seconds. LED1=1-25%, LED2=26-50%, LED3=51-75%, LED4=76-100%.

POWER MANAGEMENT:
- Auto sleep: 30 seconds not connected, 5 minutes inactive.
- Wake: Press HOME.
- Manual sleep: Hold HOME for 5 seconds.
- Power off: Press RESET button.

HARDWARE RESET:
- Press and hold RESET button next to USB-C port for 1 second.
- Fixes unresponsive behavior and connection issues.
- Does NOT delete user settings.

FACTORY RESET:
- Hold SELECT + L3 + R3 simultaneously for 5 seconds while powered ON.
- Clears ALL settings: turbo, macros, RGB, vibration, button swaps, stick modes.
- Re-pairing with devices required after factory reset.

AUDIO:
- 3.5mm jack works in PC mode via 2.4GHz wireless or wired USB only.
- NOT functional in Bluetooth mode or on mobile devices.

FIRMWARE UPDATE:
- Step 1: Uninstall existing Cosmic Byte software completely.
- Step 2: Download latest from thecosmicbyte.com.
- Step 3: Connect via USB-C wired mode.
- Step 4: Install — firmware updates automatically.

WARRANTY:
- 1 year against manufacturing defects only.
- Physical damage, water damage, tampered products NOT covered.
- Console use NOT covered.
""",

    "Drakon": """
COSMIC BYTE DRAKON — WIRELESS CONTROLLER — FULL MANUAL

KEY FEATURES:
- TMR joysticks (drift resistant)
- Mechanical switch buttons
- 3-level trigger lock system
- Magnetic replaceable top covers with dongle storage
- Charging dock support
- Mouse Mode via 2.4GHz
- FNL and FNR function buttons

CONNECTIVITY:
- Wired PC XInput: Plug in, press HOME. LED2 on.
- Wired PC DInput: Under XInput, press FNR + HOME. LED3 on.
- Wired Android DInput: Plug in, press HOME. LED3 on.
- 2.4GHz PC XInput: Press X + HOME for 3 seconds. LED2 on.
- 2.4GHz PC DInput: Hold FNR + HOME for 3 seconds. LED3 on.
- 2.4GHz Android: Press X + HOME. LED2 on.
- 2.4GHz Mouse Mode: Press CAPTURE + R3 for 5 seconds. LED3 + LED4 on. A = Left Click, B = Right Click.
- Bluetooth PC XInput: Hold B + HOME for 3 seconds. LED2 on.
- Bluetooth PC DInput: Hold A + HOME for 3 seconds. LED3 on.
- Bluetooth PC Gyro: Hold Y + HOME for 3 seconds. LED4 on.
- Bluetooth Android XInput: Hold B + HOME. LED2 on.
- Bluetooth Android DInput: Hold A + HOME. LED3 on.
- Bluetooth Android Gyro: Hold Y + HOME. LED4 on.
- Bluetooth iOS XInput: Hold B + HOME. LED2 on.
- Bluetooth iOS Gyro: Hold Y + HOME. LED4 on.
- iOS support limited.
- Gyro ONLY available in Bluetooth mode (native).
- Software only works in Wired or 2.4GHz mode.

GYRO ON-THE-FLY (works in any game):
- Connect via Wired or 2.4GHz.
- Open Cosmic Byte software.
- Assign gyro to any button.
- Choose mode: Always On, Press to Activate, or Toggle.
- Map gyro to mimic Left or Right joystick.
- Works in ANY game even without native gyro support.

PLATFORM:
- Designed for PC (Windows). NOT compatible with any gaming console.
- No warranty or support for console use.

3-LEVEL TRIGGER LOCK SYSTEM:
- Independent physical switch per trigger (LT and RT can be set differently).
- Position 1 (shortest travel): Digital signal, ON/OFF like button. Best for FPS.
- Position 2 (medium travel): Analog signal, ~50% travel. Mixed gaming.
- Position 3 (longest travel): Analog signal, 100% travel. Best for racing and simulation.

MOUSE MODE (2.4GHz only):
- Activate: CAPTURE + R3 for 5 seconds.
- LED3 + LED4 confirm Mouse Mode.
- A = Left Click. B = Right Click. Right joystick = cursor movement.
- To exit: disconnect and reconnect normally.

TURBO:
- Semi-auto: Press TURBO then press desired button once.
- Full-auto: Repeat same input again.
- Disable: Repeat same input.
- Adjust speed: FNL + Turbo, then Right Joystick Right (faster) or Left (slower).
- Speeds: Slow=5/sec, Medium=15/sec, Fast=25/sec.
- Clear all: Hold FNR + Turbo for 5 seconds. Vibration confirms.
- Supported buttons: A, B, X, Y, LB, RB, LT, RT.

MACROS (ML/MR back buttons):
- Enter recording mode for ML: FNL + ML.
- Enter recording mode for MR: FNR + MR.
- Record sequence (up to 22 inputs including delays).
- Press same M button to save. Vibrates once to confirm.
- Clear: Enter macro mode, press same M button with no inputs. Vibrates once.
- Stop macro during playback: Press any non-macro button.
- Factory reset clears all macros: Hold L1 + R1 + L2 + R2 + L3 + R3 simultaneously. Vibrates 1 second.

CUSTOMISATION:
- Joystick Round/Square angle: Hold L3 + TURBO for 2 seconds.
- D-pad / Left Stick swap: Hold L3 + CAPTURE for 2 seconds.
- ABXY swap: Hold TURBO + R3 for 2 seconds.
- D-pad 4-Way/8-Way: Hold SELECT + D-pad Right for 3 seconds.

JOYSTICK CALIBRATION (TMR system):
- Turn OFF controller.
- Hold CAPTURE, then press HOME to power ON. LED1 blinks.
- Press A to begin. LED2 blinks.
- Rotate both joysticks 3 full circles.
- Press LT and RT 3 times each.
- Press A to save and exit. LED returns to normal.

VIBRATION:
- Hold FNL + Right Joystick Up/Down to cycle.
- Levels: Off, Low, Medium, High. Default: 70%.

RGB:
- Change mode: Press FNL + SELECT. Cycles: Rainbow, 7-color gradient, Breathing, Fixed color.
- Change color (Fixed mode): Press FNR + START.
- Brightness increase: FNR + D-pad Up.
- Brightness decrease: FNR + D-pad Down.
- Turn off all RGB: Hold LT + RT for 5 seconds.

CHARGING:
- Dock: Connect dock to USB power. Place controller on magnetic contacts. Dock LED On = charging. Dock LED Off = fully charged.
- Cable: USB-C to any 5V USB source. LED Blinking = charging. LED Steady = fully charged.
- Use 5V adapters only. Avoid fast chargers.
- RGB turns off automatically when battery is low (normal behavior).
- Battery life: 8-20 hours depending on usage.

MAGNETIC COVERS AND DONGLE STORAGE:
- Remove cover: Locate lift point near front edge, insert finger, pull upward gently. Magnets release.
- Install cover: Align with frame, lower gently, magnets auto-lock.
- Dongle storage: Under the top cover is a dedicated slot. Insert 2.4GHz dongle, clicks into place securely.
- Package includes: 3 magnetic top covers, 2 extra D-pads (Precision and Disc), 2 extra joystick tops.

RESET:
- Hardware reset (unresponsive/frozen): Insert pin into RESET hole, hold 1 second. No settings deleted.
- Factory reset (clears turbo/vibration/macros): Hold L1 + R1 + L2 + R2 + L3 + R3 simultaneously. Vibrates 1 second.

SLEEP:
- Auto sleep: No activity for 5 minutes, or disconnected from dongle for 30 seconds.
- Wake: Press HOME.

AUDIO:
- 3.5mm jack works in 2.4GHz wireless and wired USB mode only.
- NOT functional in Bluetooth mode or on mobile devices.

WARRANTY:
- 1 year against manufacturing defects only.
- Physical damage, water damage, tampered products NOT covered.
- Console use not supported.
""",

    "Stellaris": """
[Already defined above]
""",

    "Ares Pro": """
COSMIC BYTE ARES PRO — TRI-MODE CONTROLLER — FULL MANUAL

IMPORTANT — SOFTWARE SUPPORT MODEL CHECK:
- Software support is ONLY available on newer Ares Pro models.
- Check the back label of the controller — if it says "App Support" in the top left corner, the model supports software.
- If "App Support" text is NOT present on back label, the model does NOT support the software.
- Older models work fine as controllers but cannot use software customization features.

FIRMWARE UPDATE — CRITICAL WARNING:
- TWO different firmware versions exist.
- Models WITH "App Support" label: update firmware ONLY through the Cosmic Byte software (connect wired, press firmware update in software). NEVER use the standalone firmware file.
- Models WITHOUT "App Support" label: use the separate standalone firmware file from thecosmicbyte.com.
- Mixing these up can cause serious issues.
- Software v1.2.11 (released Jan 2026) added auto shutdown adjustment and updated vibration shortcut.

LED COLOR INDICATORS:
- Orange LED = X-Input mode (PC).
- Red LED = Direct Input / DInput mode (PC).
- Green LED = Android mode.
- Blue LED = iOS mode.

CONNECTIVITY:
- Wireless Dongle (PC): Plug dongle into PC. Hold HOME for 3 seconds when controller is off. Motor vibrates once, LED blinks, stays solid when connected.
- Wired USB-C: Connect cable. Auto-switches to X-Input mode (Orange LED).
- Bluetooth PC XInput: Hold X + Home for 3 seconds. Orange LED.
- Bluetooth Android: Hold A + Home for 3 seconds. Green LED.
- Bluetooth iOS: Hold B + Home for 3 seconds. Blue LED.
- Switch X-Input/DInput in wireless or wired: Hold Back + Start for 3 seconds. Orange=XInput, Red=DInput.
- No need to switch modes for Android — connection is automatic.
- Windows defaults to X-Input mode.
- Android requires OTG support. Android compatibility not covered under warranty.
- Turn off controller: Hold Back + B for 3 seconds.

PLATFORM COMPATIBILITY:
- Designed EXCLUSIVELY for Windows PC.
- NOT compatible with PlayStation, Xbox, Nintendo Switch or any console.
- No warranty or support for console use.

TURBO:
- Enable: Press desired button + Turbo.
- Disable: Press same button + Turbo again.
- Adjust speed increase: Turbo + Right Joystick Up (vibrates once).
- Adjust speed decrease: Turbo + Right Joystick Down (vibrates once).
- Supported buttons: A, B, X, Y, L1, L2, R1, R2.

M1/M2 MACRO SETUP:
- To set up: Hold M1/M2 + TURBO simultaneously for 3 seconds. Purple LED starts flashing.
- Press the key to assign (A, B, X, Y, L1, R1, L2, R2, etc.). Cannot assign to Back, Start, Turbo, or Home.
- Press M1/M2 again to save. Controller vibrates once, LED stops flashing.
- To activate: Press M1/M2 during gameplay.
- To cancel: Hold M1/M2 + TURBO for 3 seconds until purple LED flashes. Press M1/M2 once. Vibrates once confirming cancellation.

LED CONTROLS:
- ABXY LED toggle: Press X + Back.
- V LED (V-shape light) toggle: Press A + Back.
- Two independent LED groups.
- If LEDs won't toggle, check if battery is low — charge first.

JOYSTICK AND D-PAD TOGGLE:
- Press L3 + Back to switch between left joystick and D-pad functions.

D-PAD 4-WAY / 8-WAY MODE:
- Toggle: Hold D-pad Up, then press Back button.
- 4-Way: Only pure directional inputs (up/down/left/right). Eliminates diagonal inputs. Best for fighting games.
- 8-Way (default): All 8 directions including diagonals.

JOYSTICK RANGE SELECTION:
- Activate with R3/L3 + Turbo.
- Full Circle (default): Full joystick movement. Medium vibration confirms.
- Small Circle: Reduced range for precision control. Small vibration confirms.
- Square Mode: Square-style input for tight angles. Strong vibration confirms.

JOYSTICK CALIBRATION:
- Power off controller completely.
- Hold Back + X + Home for 1 second. LEDs flash green and blue, vibrates once.
- Rotate both joysticks clockwise 3 times.
- Press both triggers fully 3 times.
- Press Start to finish. Green LED lights up, vibrates once to confirm.

VIBRATION CONTROL (v1.2.11 update):
- Increase: HOLD R3 + Left Joystick Up for 3 seconds (must hold — not just tap).
- Decrease: HOLD R3 + Left Joystick Down for 3 seconds.
- Updated to prevent accidental changes during gameplay.
- Auto shutdown time can be adjusted via software on supported models.

HEADSET JACK:
- Works in wireless dongle and wired modes only.
- NOT supported in Bluetooth mode.
- Supports audio output and microphone input.

BATTERY:
- Low battery: LED flashes. Vibration automatically disabled to save power.
- Charging: LED flashes slowly. Fully charged: LED turns off.

POLLING RATE:
- 1000Hz polling rate available on 2026 manufacturing batch only.
- Older models cannot be upgraded to 1000Hz.

WARRANTY:
- 1 year against manufacturing defects only.
- Physical damage, water damage, tampered products NOT covered.
- Regular wear and tear from battery usage NOT covered (unique to Ares Pro).
- Console use NOT covered.
""",

    "All Products": ""  # Filled dynamically
}

# Combine all knowledge for "All Products" queries
KNOWLEDGE_BASE["All Products"] = "\n\n".join([
    f"=== {k} ===\n{v}" for k, v in KNOWLEDGE_BASE.items() if k != "All Products"
])

PRODUCTS = ["All Products", "Lumora", "Stellaris", "Drakon", "Ares Pro"]

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
}

SYSTEM_PROMPT = """You are the official Cosmic Byte customer support assistant. You ONLY help with Cosmic Byte products.

STRICT RULES — you must ALWAYS follow these:
1. NEVER mention, compare or reference any competitor brands (Sony, Microsoft, Nintendo, Razer, SteelSeries, Logitech, Xbox, PlayStation, etc.) in your answers — except to clearly state Cosmic Byte controllers are NOT compatible with those consoles when relevant.
2. ONLY answer questions about Cosmic Byte products using the provided product manual content.
3. If a question is not related to Cosmic Byte products, politely say: "I can only assist with Cosmic Byte product queries. For other questions please visit thecosmicbyte.com"
4. Be friendly, clear and concise. Use simple language — customers may not be technical.
5. If you cannot find the answer in the provided manual content, say: "I don't have specific information on that. Please contact our support team at cc@thecosmicbyte.com or call +91 7351615161 (Mon-Sat 10am-6pm)."
6. Always recommend customers visit thecosmicbyte.com for downloads, firmware, and software.
7. For warranty issues involving physical damage or water damage, clearly explain these are not covered.
8. Never make up features or specifications not mentioned in the manual content provided.
9. Keep answers focused and easy to follow — use numbered steps for procedures.
10. End complex troubleshooting answers by offering further help or escalation contact details."""

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_product" not in st.session_state:
    st.session_state.selected_product = "All Products"
if "input_key" not in st.session_state:
    st.session_state.input_key = 0

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="cb-header">
    <div>
        <div class="cb-logo-text">Cosmic<span>Byte</span></div>
        <div class="cb-tagline">switch to god mode</div>
    </div>
    <div class="cb-support-badge">
        <span class="status-dot"></span>Support Live
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PRODUCT SELECTOR
# ─────────────────────────────────────────────
st.markdown("<p style='font-size:12px;color:#888;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px'>Select your product</p>", unsafe_allow_html=True)

cols = st.columns(len(PRODUCTS))
for i, product in enumerate(PRODUCTS):
    with cols[i]:
        if st.button(
            product,
            key=f"prod_{product}",
            type="primary" if st.session_state.selected_product == product else "secondary"
        ):
            st.session_state.selected_product = product
            st.session_state.messages = []
            st.session_state.input_key += 1
            st.rerun()

st.divider()

# ─────────────────────────────────────────────
#  WELCOME MESSAGE (if no chat yet)
# ─────────────────────────────────────────────
if not st.session_state.messages:
    product = st.session_state.selected_product
    if product == "All Products":
        welcome = "👋 Hi! I'm the Cosmic Byte support assistant. I can help you with troubleshooting, setup, connectivity, warranty queries and more for all Cosmic Byte controllers. What can I help you with today?"
    else:
        welcome = f"👋 Hi! I'm here to help you with your Cosmic Byte **{product}**. Ask me anything about setup, connectivity, troubleshooting, features or warranty. What's your question?"

    st.markdown(f"""
    <div class="msg-bot">
        <div class="msg-bot-label">Cosmic Byte Support</div>
        {welcome}
    </div>
    """, unsafe_allow_html=True)

    # Quick questions
    st.markdown("<p style='font-size:11px;color:#666;margin-top:12px;margin-bottom:6px'>Common questions:</p>", unsafe_allow_html=True)
    quick_qs = QUICK_QUESTIONS.get(product, QUICK_QUESTIONS["All Products"])
    q_cols = st.columns(len(quick_qs))
    for i, qq in enumerate(quick_qs):
        with q_cols[i]:
            if st.button(qq, key=f"qq_{i}_{product}"):
                st.session_state.messages.append({"role": "user", "content": qq})
                st.session_state.input_key += 1
                st.rerun()

# ─────────────────────────────────────────────
#  CHAT HISTORY
# ─────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div style="display:flex;justify-content:flex-end;margin:10px 0">
            <div class="msg-user">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="margin:10px 0">
            <div class="msg-bot">
                <div class="msg-bot-label">Cosmic Byte Support</div>
                {msg["content"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  GENERATE AI RESPONSE
# ─────────────────────────────────────────────
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_question = st.session_state.messages[-1]["content"]
    product = st.session_state.selected_product
    knowledge = KNOWLEDGE_BASE.get(product, KNOWLEDGE_BASE["All Products"])

    with st.spinner(""):
        try:
            context_message = f"""PRODUCT SELECTED BY CUSTOMER: {product}

PRODUCT MANUAL AND KNOWLEDGE BASE:
{knowledge}

CUSTOMER QUESTION: {user_question}

Please answer the customer's question using ONLY the information in the manual above. Be helpful, clear and concise."""

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": context_message}
                ]
            )

            answer = response.content[0].text
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

        except Exception as e:
            st.error("Unable to connect to support service. Please try again or contact us at cc@thecosmicbyte.com")

# ─────────────────────────────────────────────
#  INPUT BOX
# ─────────────────────────────────────────────
st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)

col_input, col_btn = st.columns([5, 1])
with col_input:
    user_input = st.text_input(
        "Ask a question",
        placeholder=f"Ask about your {st.session_state.selected_product}...",
        label_visibility="collapsed",
        key=f"chat_input_{st.session_state.input_key}"
    )
with col_btn:
    send = st.button("Send →", use_container_width=True)

if send and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})
    st.session_state.input_key += 1
    st.rerun()

# Also handle Enter key
if user_input and user_input.strip() and not send:
    if len(st.session_state.messages) == 0 or st.session_state.messages[-1]["content"] != user_input.strip():
        pass

# ─────────────────────────────────────────────
#  CLEAR CHAT
# ─────────────────────────────────────────────
if st.session_state.messages:
    st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Clear chat", key="clear"):
            st.session_state.messages = []
            st.session_state.input_key += 1
            st.rerun()

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
st.divider()
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
    <div style="font-size:12px;color:#555">
        Can't find your answer?
        <a href="mailto:cc@thecosmicbyte.com" style="color:#FF6B00;text-decoration:none">cc@thecosmicbyte.com</a>
        &nbsp;·&nbsp;
        <a href="tel:+917351615161" style="color:#FF6B00;text-decoration:none">+91 7351615161</a>
        <span style="color:#444">&nbsp;(Mon-Sat 10am-6pm)</span>
    </div>
    <div style="font-size:11px;color:#444">
        <a href="https://www.thecosmicbyte.com" target="_blank" style="color:#555;text-decoration:none">thecosmicbyte.com</a>
    </div>
</div>
""", unsafe_allow_html=True)
