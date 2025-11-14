from __future__ import annotations
from typing import Dict, List

VALID_MEDIA_TYPES: Dict[str, str] = {
    "all": "𝙰𝚕𝚕 𝚖𝚎𝚜𝚜𝚊𝚐𝚎𝚜",
    "text": "𝙵𝚘𝚛𝚠𝚊𝚛𝚍 𝚃𝚊𝚐",
    "document": "𝙳𝚘𝚌𝚞𝚖𝚎𝚗𝚝𝚜",
    "video": "𝚅𝚒𝚍𝚎𝚘𝚜",
    "photo": "𝙿𝚑𝚘𝚝𝚘𝚜",
    "audio": "𝙰𝚞𝚍𝚒𝚘𝚜",
    "voice": "𝚅𝚘𝚒𝚌𝚎𝚜",
    "sticker": "𝚂𝚝𝚒𝚌𝚔𝚎𝚛𝚜",
    "animation": "𝙰𝚗𝚒𝚖𝚊𝚝𝚒𝚘𝚗𝚜",
}

MEDIA_FILTER_OPTIONS: List[str] = [key for key in VALID_MEDIA_TYPES if key != "all"]

START_PANEL_IMAGE = "https://ibb.co/s9vsZvTh"

START_TXT = """𝙷𝚎𝚕𝚕𝚊𝚘𝚠 <b>{}</b>,
𝙸’𝚖 𝚢𝚘𝚞𝚛 𝚏𝚛𝚒𝚎𝚗𝚍𝚕𝚢 <a href="https://t.me/{}">{}</a>.

• 𝙰𝚞𝚝𝚘–𝚏𝚘𝚛𝚠𝚊𝚛𝚍 𝚂𝚘𝚞𝚛𝚌𝚎 ➜ 𝚃𝚊𝚛𝚐𝚎𝚝 (𝚛𝚎𝚊𝚕–𝚝𝚒𝚖𝚎)
• 𝚁𝚎𝚙𝚕𝚒𝚎𝚜, 𝚖𝚎𝚍𝚒𝚊 & 𝚎𝚍𝚒𝚝𝚜 𝚜𝚝𝚊𝚢 𝚒𝚗 𝚜𝚢𝚗𝚌
• 𝙵𝚒𝚕𝚝𝚎𝚛𝚜: 𝚝𝚢𝚙𝚎 + 𝚜𝚒𝚣𝚎 | 𝙲𝚞𝚜𝚝𝚘𝚖 𝚌𝚊𝚙𝚝𝚒𝚘𝚗𝚜 ⚡

<i>𝙲𝚛𝚎𝚊𝚝𝚎 𝚢𝚘𝚞𝚛 𝚏𝚒𝚛𝚜𝚝 𝚝𝚊𝚜𝚔 𝚘𝚛 𝚊𝚍𝚍 𝚖𝚎 𝚝𝚘 𝚊 𝚌𝚑𝚊𝚗𝚗𝚎𝚕.</i> 🔥"""

TASK_CARD = """📌 <b>𝚃𝚊𝚜𝚔 #{id}</b>

✯ <b>𝙵𝚛𝚘𝚖</b>: {source_title} ({source_id})  
✯ <b>𝚃𝚘</b>: {target_title} ({target_id})

- <b>𝙼𝚎𝚍𝚒𝚊</b>: {media}
- <b>𝚂𝚒𝚣𝚎</b>: {size_limit}
- <b>𝚂𝚔𝚒𝚙 𝙳𝚞𝚙𝚕𝚒𝚌𝚊𝚝𝚎𝚜</b>: {skip_status}
- <b>𝚁𝚎𝚖𝚘𝚟𝚎 𝙻𝚒𝚗𝚔𝚜</b>: {link_status}
- <b>𝙲𝚊𝚙𝚝𝚒𝚘𝚗</b>: {caption}

⚙️ 𝚄𝚜𝚎 𝚋𝚞𝚝𝚝𝚘𝚗𝚜 𝚋𝚎𝚕𝚘𝚠 𝚝𝚘 𝚖𝚊𝚗𝚊𝚐𝚎.
"""

# Buttons
BTN_ADD_TASK = "⚡ 𝙰𝚍𝚍 𝚃𝚊𝚜𝚔"
BTN_SHOW_TASKS = "📋 𝚂𝚑𝚘𝚠 𝚃𝚊𝚜𝚔𝚜"
BTN_HELP = "🛠 𝙷𝚎𝚕𝚙"
BTN_ABOUT = "ℹ️ 𝙸𝚗𝚏𝚘"
BTN_BOT_MODE = "🤖 𝙱𝚘𝚝 𝙼𝚘𝚍𝚎"
BTN_USER_MODE = "👥 𝚄𝚜𝚎𝚛 𝚂𝚎𝚜𝚜𝚒𝚘𝚗"
BTN_BACK = "⬅️ 𝙱𝚊𝚌𝚔"
BTN_HOME = "🏠 𝙷𝚘𝚖𝚎"
BTN_USER_GUIDE = "📖 𝚄𝚜𝚎𝚛 𝙶𝚞𝚒𝚍𝚎"
BTN_CAPTION_VARS = "🔵 𝚅𝚊𝚛𝚜"
BTN_CAPTION_FORMATS = "🎨 𝚂𝚝𝚢𝚕𝚎𝚜"
BTN_BACK_TASK = "⬅️ 𝙱𝚊𝚌𝚔"

# Target Menus
ADD_TASK_TARGET_MENU_EMPTY = """🎯 <b>𝚃𝚊𝚛𝚐𝚎𝚝 𝙲𝚑𝚊𝚗𝚗𝚎𝚕𝚜</b>  

𝙽𝚘 𝚝𝚊𝚛𝚐𝚎𝚝𝚜 𝚊𝚍𝚍𝚎𝚍 𝚢𝚎𝚝.  
𝚃𝚊𝚙 <b>𝙰𝚍𝚍 𝙲𝚑𝚊𝚗𝚗𝚎𝚕</b> 𝚝𝚘 𝚜𝚎𝚝 𝚊 𝚍𝚎𝚜𝚝𝚒𝚗𝚊𝚝𝚒𝚘𝚗.
"""

ADD_TASK_TARGET_MENU_SELECTED = """🎯 <b>𝚃𝚊𝚛𝚐𝚎𝚝 𝙲𝚑𝚊𝚗𝚗𝚎𝚕</b>  

✅ 𝙳𝚎𝚜𝚝𝚒𝚗𝚊𝚝𝚒𝚘𝚗: <b>{title}</b>  
<code>{chat_id}</code>  

𝚃𝚊𝚙 <b>𝙰𝚍𝚍 𝙲𝚑𝚊𝚗𝚗𝚎𝚕</b> 𝚝𝚘 𝚌𝚑𝚊𝚗𝚐𝚎 𝚒𝚝.
"""

ADD_TASK_TARGET_PROMPT = """➕ <b>𝙰𝚍𝚍 𝚃𝚊𝚛𝚐𝚎𝚝</b>  

𝚂𝚎𝚗𝚍 𝚝𝚑𝚎 @𝚞𝚜𝚎𝚛𝚗𝚊𝚖𝚎 𝚘𝚛 𝚌𝚑𝚊𝚝 𝙸𝙳.  
𝙾𝚛 𝚏𝚘𝚛𝚠𝚊𝚛𝚍 𝚊 𝚖𝚎𝚜𝚜𝚊𝚐𝚎 𝚏𝚛𝚘𝚖 𝚝𝚑𝚊𝚝 𝚌𝚑𝚊𝚝.  

{access_note}
"""

ADD_TASK_TARGET_ACCESS_NOTE_BOT = (
    "🤖 𝙴𝚗𝚜𝚞𝚛𝚎 𝚝𝚑𝚒𝚜 𝚋𝚘𝚝 𝚌𝚊𝚗 𝚙𝚘𝚜𝚝 𝚒𝚗 𝚝𝚑𝚎 𝚌𝚑𝚊𝚗𝚗𝚎𝚕 — 𝚊𝚍𝚍 𝚒𝚝 𝚊𝚜 𝚊𝚗 𝚊𝚍𝚖𝚒𝚗 𝚒𝚏 𝚗𝚎𝚎𝚍𝚎𝚍."
)

ADD_TASK_TARGET_ACCESS_NOTE_USER = (
    "👥 𝙴𝚗𝚜𝚞𝚛𝚎 𝚢𝚘𝚞𝚛 𝚞𝚜𝚎𝚛 𝚜𝚎𝚜𝚜𝚒𝚘𝚗 𝚌𝚊𝚗 𝚙𝚘𝚜𝚝 𝚒𝚗 𝚝𝚑𝚎 𝚌𝚑𝚊𝚝."
)

# Source Menus
ADD_TASK_SOURCE_MENU = """📡 <b>𝚂𝚘𝚞𝚛𝚌𝚎 𝙲𝚑𝚊𝚝</b>  

𝚂𝚎𝚕𝚎𝚌𝚝 𝚝𝚑𝚎 𝚌𝚑𝚊𝚝 𝚝𝚘 𝚖𝚘𝚗𝚒𝚝𝚘𝚛.  

🎯 𝙵𝚘𝚛𝚠𝚊𝚛𝚍𝚒𝚗𝚐 𝚝𝚘: <b>{title}</b>  
<code>{chat_id}</code>  

𝚃𝚊𝚙 <b>𝚄𝚜𝚎 𝚂𝚘𝚞𝚛𝚌𝚎</b> 𝚝𝚘 𝚌𝚘𝚗𝚝𝚒𝚗𝚞𝚎.
"""

ADD_TASK_SOURCE_PROMPT = """📥 <b>𝙰𝚍𝚍 𝚂𝚘𝚞𝚛𝚌𝚎</b>  

𝚂𝚎𝚗𝚍 𝚝𝚑𝚎 @𝚞𝚜𝚎𝚛𝚗𝚊𝚖𝚎 𝚘𝚛 𝚌𝚑𝚊𝚝 𝙸𝙳.  
𝙾𝚛 𝚏𝚘𝚛𝚠𝚊𝚛𝚍 𝚊 𝚖𝚎𝚜𝚜𝚊𝚐𝚎 𝚏𝚛𝚘𝚖 𝚝𝚑𝚊𝚝 𝚌𝚑𝚊𝚝.  

{access_note}
"""

ADD_TASK_SOURCE_ACCESS_NOTE_BOT = (
    "🤖 𝙴𝚗𝚜𝚞𝚛𝚎 𝚝𝚑𝚒𝚜 𝚋𝚘𝚝 𝚌𝚊𝚗 𝚛𝚎𝚊𝚍 𝚖𝚎𝚜𝚜𝚊𝚐𝚎𝚜 𝚒𝚗 𝚝𝚑𝚎 𝚜𝚘𝚞𝚛𝚌𝚎 — 𝚒𝚗𝚟𝚒𝚝𝚎 𝚘𝚛 𝚐𝚛𝚊𝚗𝚝 𝚊𝚌𝚌𝚎𝚜𝚜."
)

ADD_TASK_SOURCE_ACCESS_NOTE_USER = (
    "👥 𝙴𝚗𝚜𝚞𝚛𝚎 𝚢𝚘𝚞𝚛 𝚞𝚜𝚎𝚛 𝚜𝚎𝚜𝚜𝚒𝚘𝚗 𝚌𝚊𝚗 𝚛𝚎𝚊𝚍 𝚖𝚎𝚜𝚜𝚊𝚐𝚎𝚜 𝚒𝚗 𝚝𝚑𝚎 𝚜𝚘𝚞𝚛𝚌𝚎 𝚌𝚑𝚊𝚝."
)

# Customize Panel
CUSTOMIZE_PANEL_TEXT = """⚙️ <b>𝙲𝚞𝚜𝚝𝚘𝚖𝚒𝚣𝚎 𝙵𝚘𝚛𝚠𝚊𝚛𝚍𝚒𝚗𝚐</b>  

• 𝙴𝚍𝚒𝚝 𝚌𝚊𝚙𝚝𝚒𝚘𝚗𝚜, 𝚏𝚒𝚕𝚝𝚎𝚛𝚜, 𝚘𝚛 𝚜𝚒𝚣𝚎 𝚕𝚒𝚖𝚒𝚝𝚜.  
• 𝙴𝚗𝚊𝚋𝚕𝚎 <b>𝚂𝚔𝚒𝚙 𝙳𝚞𝚙𝚕𝚒𝚌𝚊𝚝𝚎𝚜</b> 𝚝𝚘 𝚊𝚟𝚘𝚒𝚍 𝚛𝚎𝚙𝚘𝚜𝚝𝚜.  
• 𝚄𝚜𝚎 𝙷𝚃𝙼𝙻/𝙼𝚊𝚛𝚔𝚍𝚘𝚠𝚗 𝚏𝚘𝚛 𝚋𝚛𝚊𝚗𝚍𝚎𝚍 𝚌𝚊𝚙𝚝𝚒𝚘𝚗𝚜.  
• 𝙿𝚊𝚞𝚜𝚎 𝚏𝚘𝚛𝚠𝚊𝚛𝚍𝚒𝚗𝚐 𝚋𝚢 𝚍𝚒𝚜𝚊𝚋𝚕𝚒𝚗𝚐 𝚊𝚕𝚕 𝚖𝚎𝚍𝚒𝚊 𝚝𝚢𝚙𝚎𝚜.  

⬅️ 𝚄𝚜𝚎 𝚝𝚑𝚎 𝚋𝚞𝚝𝚝𝚘𝚗𝚜 𝚋𝚎𝚕𝚘𝚠 𝚝𝚘 𝚛𝚎𝚝𝚞𝚛𝚗.
"""

# Caption Help
CAPTION_INSTRUCTIONS = """📝 <b>𝙲𝚞𝚜𝚝𝚘𝚖 𝙲𝚊𝚙𝚝𝚒𝚘𝚗𝚜</b>  

✨ 𝚄𝚜𝚎 𝚟𝚊𝚛𝚒𝚊𝚋𝚕𝚎𝚜 𝚝𝚘 𝚊𝚞𝚝𝚘–𝚏𝚒𝚕𝚕.  
💡 𝙴𝚡𝚊𝚖𝚙𝚕𝚎:  
<code>🎬 {file_name} | {file_size}</code>  

👉 𝚁𝚎𝚗𝚍𝚎𝚛𝚜 𝚊𝚜:  
🎬 <b>𝙼𝚘𝚟𝚒𝚎.𝚖𝚙4</b> | 1.5 𝙶𝙱  

𝚂𝚎𝚗𝚍 <code>-</code> 𝚝𝚘 𝚌𝚕𝚎𝚊𝚛 𝚌𝚞𝚜𝚝𝚘𝚖 𝚌𝚊𝚙𝚝𝚒𝚘𝚗.
"""

CAPTION_VARIABLES_HELP = """🧿 <b>𝙵𝚒𝚕𝚎 𝚅𝚊𝚛𝚒𝚊𝚋𝚕𝚎𝚜</b>  

<code>{file_name}</code> → 𝙵𝚒𝚕𝚎 𝚗𝚊𝚖𝚎  
<code>{file_size}</code> → 𝙵𝚒𝚕𝚎 𝚜𝚒𝚣𝚎  
<code>{duration}</code> → 𝙳𝚞𝚛𝚊𝚝𝚒𝚘𝚗  
<code>{dc_id}</code> → 𝙳𝚊𝚝𝚊 𝚌𝚎𝚗𝚝𝚎𝚛 𝙸𝙳  
<code>{caption}</code> → 𝙾𝚛𝚒𝚐𝚒𝚗𝚊𝚕 𝚌𝚊𝚙𝚝𝚒𝚘𝚗
"""

CAPTION_MARKDOWN_HELP = """🎨 <b>𝙼𝚊𝚛𝚔𝚍𝚘𝚠𝚗 𝙵𝚘𝚛𝚖𝚊𝚝𝚜</b>  

<code>*bold*</code> → <b>bold</b>  
<code>_italic_</code> → <i>italic</i>  
<code>__underline__</code> → <u>underline</u>  
<code>~strike~</code> → <s>strike</s>  
<code>[link](https://example.com)</code> → <a href="https://example.com">link</a>  
<code>`code`</code> → <code>code</code>
"""

# File Size
FILE_SIZE_MSG = """📦 <b>𝙵𝚒𝚕𝚎 𝚂𝚒𝚣𝚎 𝚂𝚎𝚝𝚝𝚒𝚗𝚐𝚜</b>  

𝚂𝚎𝚝 𝚕𝚒𝚖𝚒𝚝𝚜 𝚏𝚘𝚛 𝚏𝚘𝚛𝚠𝚊𝚛𝚍𝚎𝚍 𝚏𝚒𝚕𝚎𝚜:  

🔽 <b>𝙼𝚒𝚗𝚒𝚖𝚞𝚖:</b> {min_size}  
🔼 <b>𝙼𝚊𝚡𝚒𝚖𝚞𝚖:</b> {max_size}  

{skip_notice}
"""

# No Tasks
NO_TASKS_MSG = """❌ <b>𝙽𝚘 𝚃𝚊𝚜𝚔𝚜 𝙵𝚘𝚞𝚗𝚍</b>  

𝚈𝚘𝚞 𝚑𝚊𝚟𝚎𝚗’𝚝 𝚌𝚛𝚎𝚊𝚝𝚎𝚍 𝚊𝚗𝚢 𝚝𝚊𝚜𝚔𝚜 𝚢𝚎𝚝.  
𝚃𝚊𝚙 ➕ <b>𝙰𝚍𝚍 𝚃𝚊𝚜𝚔</b> 𝚝𝚘 𝚐𝚎𝚝 𝚜𝚝𝚊𝚛𝚝𝚎𝚍.
"""

# Guide
GUIDE_TXT = """🕷️ <b>𝙰𝚞𝚝𝚘–𝙵𝚘𝚛𝚠𝚊𝚛𝚍 𝙱𝚘𝚝 — 𝚀𝚞𝚒𝚌𝚔 𝙶𝚞𝚒𝚍𝚎</b> 🔥  

❓ <b>𝙲𝚘𝚖𝚖𝚊𝚗𝚍𝚜</b>  
/start          — 𝙾𝚙𝚎𝚗 𝚖𝚎𝚗𝚞  
/list           — 𝚂𝚑𝚘𝚠 𝚝𝚊𝚜𝚔𝚜  
/cancel         — 𝙰𝚋𝚘𝚛𝚝 𝚊𝚌𝚝𝚒𝚘𝚗  
/addforward     — 𝙰𝚍𝚍 𝚝𝚊𝚜𝚔  
/remove <id>    — 𝙳𝚎𝚕𝚎𝚝𝚎 𝚝𝚊𝚜𝚔  
/setsize <id>   — 𝚂𝚎𝚝 𝚜𝚒𝚣𝚎  
/setfilters <id>— 𝙴𝚍𝚒𝚝 𝚏𝚒𝚕𝚝𝚎𝚛𝚜  
/setcaption <id>— 𝙲𝚞𝚜𝚝𝚘𝚖 𝚌𝚊𝚙𝚝𝚒𝚘𝚗  

🎉 <b>𝙵𝚎𝚊𝚝𝚞𝚛𝚎𝚜</b>  
𝚂𝚝𝚊𝚢𝚜 𝚊𝚌𝚝𝚒𝚟𝚎 𝚊𝚏𝚝𝚎𝚛 𝚛𝚎𝚜𝚝𝚊𝚛𝚝 • 𝙵𝚒𝚕𝚝𝚎𝚛𝚜 • 𝙲𝚞𝚜𝚝𝚘𝚖 𝚌𝚊𝚙𝚝𝚒𝚘𝚗𝚜 • 𝚂𝚔𝚒𝚙 𝚍𝚞𝚙𝚕𝚒𝚌𝚊𝚝𝚎𝚜 • 𝚂𝚢𝚗𝚌 𝚛𝚎𝚙𝚕𝚒𝚎𝚜/𝚎𝚍𝚒𝚝𝚜
"""

# About
ABOUT_TXT = """🕷️ <b>𝙰𝚞𝚝𝚘–𝙵𝚘𝚛𝚠𝚊𝚛𝚍 𝙱𝚘𝚝</b>  
- 𝚂𝚖𝚊𝚛𝚝 𝚏𝚘𝚛𝚠𝚊𝚛𝚍𝚎𝚛 • 𝚂𝚢𝚗𝚌𝚜 𝚎𝚍𝚒𝚝𝚜 • 𝙿𝚛𝚎𝚜𝚎𝚛𝚟𝚎𝚜 𝚛𝚎𝚙𝚕𝚒𝚎𝚜  

✯ <b>𝙲𝚛𝚎𝚊𝚝𝚘𝚛</b> : <a href="https://t.me/ImSahanSBot">𝚂𝚊𝚑𝚊𝚗𝚂</a>  
✯ <b>𝙳𝚎𝚟</b> : <a href="https://t.me/imsahans">𝚂𝚊𝚑𝚊𝚗</a>  
✯ <b>𝚂𝚘𝚞𝚛𝚌𝚎</b> : 𝙿𝚛𝚒𝚟𝚊𝚝𝚎 (𝙳𝙼 𝚍𝚎𝚟)
"""

# How To
HOWTO_TXT = """📖 <b>𝚄𝚜𝚎𝚛 𝙶𝚞𝚒𝚍𝚎</b>  

1. <b>𝙿𝚕𝚊𝚗</b> — 𝚂𝚘𝚞𝚛𝚌𝚎 & 𝚝𝚊𝚛𝚐𝚎𝚝 𝚌𝚑𝚊𝚝𝚜.  
2. <b>𝙰𝚍𝚍 𝚃𝚊𝚜𝚔</b> — 𝚄𝚜𝚎 <code>/addforward</code>.  
3. <b>𝙿𝚒𝚌𝚔 𝙲𝚑𝚊𝚝𝚜</b> — 𝙲𝚑𝚘𝚘𝚜𝚎 𝚜𝚘𝚞𝚛𝚌𝚎 & 𝚝𝚊𝚛𝚐𝚎𝚝.  
4. <b>𝙲𝚞𝚜𝚝𝚘𝚖𝚒𝚣𝚎</b> — 𝙴𝚍𝚒𝚝 𝚌𝚊𝚙𝚝𝚒𝚘𝚗𝚜/𝚏𝚒𝚕𝚝𝚎𝚛𝚜.  
5. <b>𝚁𝚞𝚗</b> — 𝙺𝚎𝚎𝚙 𝚋𝚘𝚝 𝚘𝚗𝚕𝚒𝚗𝚎.

💡 𝚄𝚜𝚎 <code>/help</code> 𝚏𝚘𝚛 𝚖𝚘𝚛𝚎.
"""

# Forward Mode
FORWARD_MODE_TXT = """🔄 <b>𝙵𝚘𝚛𝚠𝚊𝚛𝚍𝚒𝚗𝚐 𝙼𝚘𝚍𝚎</b>  

𝙲𝚑𝚘𝚘𝚜𝚎 𝚑𝚘𝚠 𝚝𝚘 𝚏𝚘𝚛𝚠𝚊𝚛𝚍:  
• 𝙱𝚘𝚝 𝙼𝚘𝚍𝚎 → 𝚒𝚏 𝚋𝚘𝚝 𝚑𝚊𝚜 𝚊𝚌𝚌𝚎𝚜𝚜  
• 𝚄𝚜𝚎𝚛 𝚂𝚎𝚜𝚜𝚒𝚘𝚗 → 𝚒𝚏 𝚋𝚘𝚝 𝚌𝚊𝚗’𝚝  

👇 𝙿𝚒𝚌𝚔 𝚊 𝚖𝚘𝚍𝚎 𝚋𝚎𝚕𝚘𝚠.
"""
