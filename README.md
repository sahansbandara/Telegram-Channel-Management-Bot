# Auto-Forward Bot

An easy-to-use Telegram bot powered by [Pyrofork](https://github.com/pyrogram/pyrofork)
that lets <b>anyone</b> configure message forwarding without touching the source code.
Users can add the bot to their chats, create forwarding tasks, filter by media
type, and optionally attach custom captions—all from within Telegram.

## Features

- Configure forwarding rules entirely through on-screen buttons or bot commands.
- Forward from channels, groups, or supergroups where the bot is a member.
- Choose exactly which media types (text, photos, video, etc.) to forward.
- Add custom captions that are appended to every forwarded message.
- Toggle link stripping to automatically remove URLs from forwarded text and captions.
- Reply tracking keeps threaded conversations linked in the destination chat.
- Built-in guide to walk new users through the full setup.

## Getting started

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather) and grab the
   bot token.
2. Obtain a Telegram `API_ID` and `API_HASH` from <https://my.telegram.org>.
3. Install the dependencies and start the bot:

   ```bash
   pip install -r requirements.txt
   export API_ID=123456  # replace with your API ID
   export API_HASH="0123456789abcdef0123456789abcdef"  # replace with your API hash
   export BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # replace with your bot token
   python main.py
   ```

   The bot stores user configuration in `data/config.json` so it will remember
   forwarding tasks between restarts.

## Using the bot

1. Start a private chat with your bot and send `/start`. The bot will display buttons for <b>Add Task</b>, <b>Add User Session</b>, and <b>Show Tasks</b> so you can manage everything without typing commands.
2. Tap <b>Add Task</b> and follow the prompts to choose the source and destination chats. Once both are set, you'll receive a task card with buttons for setting media filters, custom captions, or removing the task entirely.
3. Use <b>Show Tasks</b> (or `/list`) at any time to review your forwarding rules. Each task card includes the same management buttons, making adjustments quick and discoverable.
4. For public source channels or groups, simply provide their @username or invite link during setup. For private sources, add the bot as an admin (or link a user session that already has access) so it can read messages.
5. Ensure the bot or linked session has permission to post in each destination chat. Public destinations usually require promoting the bot to admin so it can send messages; private ones must also grant it access before configuring a task.
6. Run `/guide` for a step-by-step walkthrough, or fall back to the traditional commands if you prefer typing:

   - `/addforward` – interactive setup for a new forwarding rule.
   - `/list` – view your current tasks.
   - `/remove <task_id>` – delete a task you no longer need.
   - `/setfilters <task_id>` – update the media types to forward (text, photo, etc.).
   - `/setcaption <task_id>` – add or remove a custom caption.
   - `/help` – show the command list.
   - `/cancel` – abort an in-progress setup step.

Once configured, the bot forwards the selected messages automatically for each
user. Everyone can maintain their own tasks independently.
