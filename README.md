# ⚡ BEN — Next-Generation Professional Discord Bot

<p align="center">
  <b>The all-in-one Discord community management, automation, and entertainment powerhouse.</b><br>
  <i>Designed with modern Discord UI Components and the signature Transparent Embed aesthetic (<code>#2B2D31</code>).</i>
</p>

---

## 🎨 Visual Philosophy: The "Transparent Embed"
Unlike traditional bots that use bright, loud borders that clash with Discord's dark mode, **BEN** employs the acclaimed **`#2B2D31` Dark Theme Hex Color**.
* In Discord dark mode, `#2B2D31` matches the client's native message canvas.
* This removes harsh outer embed borders, making cards feel **floating, integrated, borderless, and native to Discord**.
* Paired with clean Unicode dividers, minimalistic status indicators (`◈`, `›`, `•`), and persistent interactive UI buttons & modals.

---

## 🚀 Key Feature Matrix

| Feature | Description | Interactive UI Components |
| :--- | :--- | :--- |
| **👋 Welcome & Leave** | Dynamic greetings and farewells with member counts, account age, and custom placeholders | Transparent Arrival Cards |
| **📜 Audit & Security Logs** | Real-time logging of message deletions, edits (before vs after), role changes, and voice movement | Diff Embeds & User Avatars |
| **📢 Broadcast Announcements** | Dispatch official server announcements with optional `@everyone`/`@here` pings and banner images | Discord Modal Popup Form |
| **🎫 Enterprise Tickets** | Persistent support panels, automatic private ticket channel creation, claim workflows, and transcript exports | Persistent Buttons & Confirm Modals |
| **📝 Staff Applications** | 5-question recruitment modal with staff review channel, Accept/Deny buttons, notes, and auto-roles | Interactive Modals & Staff Action Bar |
| **🎭 Component Roles** | Modern alternative to emoji reaction roles using native Discord UI buttons and multi-select dropdown menus | Interactive Buttons & Select Menus |
| **🎵 Audio & Music** | High-fidelity voice streaming powered by `yt-dlp` with playlist queue management | Interactive Dashboard (Play, Skip, Stop, Queue) |
| **🎮 Interactive Games** | In-chat multiplayer and solo games with rich visual feedback | 3x3 Button Grid (Tic-Tac-Toe), RPS, Trivia, Slots |
| **⚡ Telemetry & Diagnostics** | Deep system metrics, round-trip API ping, server and member profile dossiers | Categorized Dropdown Directory (`/help`) |

---

## 📁 Project Architecture

```
BEN-Bot/
├── .env.example              # Environment variables template
├── .env                      # Active token configuration
├── .gitignore                # Git ignore configuration
├── requirements.txt          # Python dependencies
├── start.bat                 # One-click Windows launch script
├── config.py                 # Bot branding, transparent colors, and emojis
├── main.py                   # Bot entrypoint, presence rotator & error handling
├── utils/
│   ├── database.py           # Asynchronous SQLite storage engine (aiosqlite)
│   └── embeds.py             # Transparent embed builder (#2B2D31)
└── cogs/
    ├── general.py            # /help (interactive dropdown), /ping, /botinfo, /serverinfo
    ├── welcome.py            # /welcome & /leave setup, preview test & event handlers
    ├── logs.py               # Audit security logger (edits, deletes, roles, voice)
    ├── announcement.py       # Modal-based announcement broadcast engine
    ├── tickets.py            # Ticket panel, private channels, claim & transcripts
    ├── application.py        # Staff recruitment questionnaire & review workflow
    ├── reaction_roles.py     # Modern button & dropdown role assigners
    ├── games.py              # Tic-Tac-Toe, Rock-Paper-Scissors, Trivia, Slots, Coinflip
    └── music.py              # Music stream player with interactive control buttons
```

---

## 🛠️ Step-by-Step Setup Guide

### 1. Create Your Bot on Discord Developer Portal
1. Navigate to the **[Discord Developer Portal](https://discord.com/developers/applications)**.
2. Click **New Application**, name it **BEN**, and accept the terms.
3. In the sidebar, select **Bot**:
   * Click **Reset Token** and copy your **Bot Token**.
4. Scroll down to **Privileged Gateway Intents** and enable:
   * ✅ **Presence Intent**
   * ✅ **Server Members Intent** *(Mandatory for Welcome, Leave, and Role events)*
   * ✅ **Message Content Intent** *(Mandatory for Audit Logs and commands)*
5. Click **Save Changes**.

### 2. Generate Bot Invite Link
1. Go to **OAuth2** ➔ **URL Generator**.
2. Select scopes:
   * ✅ `bot`
   * ✅ `applications.commands`
3. Under **Bot Permissions**, select:
   * ✅ `Administrator` (or select: Manage Channels, Manage Roles, Send Messages, Embed Links, Attach Files, Read Message History, Connect, Speak)
4. Copy the generated URL and open it in your browser to invite **BEN** to your server.

### 3. Configure `.env`
Open the `.env` file in the project folder and paste your bot token:
```env
DISCORD_TOKEN=your_bot_token_here
BOT_PREFIX=!
```

### 4. Run the Bot
Double-click **`start.bat`** on Windows.
* The script will automatically create a Python virtual environment (`.venv`), install all required dependencies from `requirements.txt`, and boot up **BEN**.

*Or run manually via terminal:*
```powershell
pip install -r requirements.txt
python main.py
```

---

## 📖 Slash Command Reference

### ⚙️ General & Telemetry
* `/help` — Opens the interactive categorized command directory with dropdown menus.
* `/ping` — Measures WebSocket latency and API round-trip time.
* `/botinfo` — Displays RAM usage, Python version, server count, and uptime stats.
* `/serverinfo` — Displays detailed statistics about the current guild.

### 👋 Welcome & Farewell
* `/welcome setup <channel> [message]` — Configures the arrival greeting channel.
  * *Placeholders*: `{user}`, `{name}`, `{mention}`, `{server}`, `{member_count}`
* `/welcome test` — Dispatches a live preview of your welcome card.
* `/welcome toggle <enabled>` — Enables or disables the welcome system.
* `/leave setup <channel> [message]` — Configures the member departure channel.
* `/leave test` — Dispatches a live preview of the departure card.

### 📜 Audit Logs
* `/logs setup <channel>` — Designates the channel for audit logging.
* `/logs toggle <enabled>` — Turns audit logging on or off.

### 📢 Announcements
* `/announce <channel> [mention] [theme]` — Opens an interactive popup form where you type Title, Content, Banner URL, and Footer. Supports pinging `@everyone`, `@here`, or `none`.

### 🎫 Tickets & Support
* `/ticket panel <channel> [category] [support_role] [title] [desc]` — Deploys a persistent **[ Create Ticket ]** button panel.
  * Clicking opens a private channel `ticket-0001` restricted to the user and support team.
  * In the ticket channel, provides **[ Close Ticket ]**, **[ Claim Ticket ]**, and **[ Save Transcript ]** buttons.
* `/ticket log_channel <channel>` — Sets the destination channel where transcripts are archived upon ticket closure.

### 📝 Staff Applications
* `/application panel <channel> <review_channel> [award_role] [title]` — Deploys a recruitment panel.
  * Clicking **[ Submit Application ]** launches a 5-question modal form.
  * When submitted, it delivers a dossier to the review channel with **[ Accept ]** and **[ Deny ]** buttons.
  * Admins can enter feedback; the bot sends a direct DM to the applicant and awards the staff role automatically upon acceptance.

### 🎭 Component Roles
* `/reactionrole button_panel <channel> <title> <role1> [role2]...` — Deploys up to 5 role toggle buttons.
* `/reactionrole select_panel <channel> <title> <role1> [role2]...` — Deploys a multi-select dropdown menu for choosing roles.

### 🎵 Music & Audio
* `/music play <query>` — Search and stream audio into your current voice channel.
* `/music skip` — Skip to the next track in the queue.
* `/music stop` — Disconnect and clear the playlist.
* `/music queue` — Inspect the queue of upcoming songs.
* *Control dashboard included with Play/Pause, Skip, Stop, and Queue buttons on every track.*

### 🎮 Interactive Games
* `/tictactoe <opponent>` — 3x3 interactive button grid duel against another member.
* `/rps [opponent]` — Play Rock-Paper-Scissors with buttons against BEN AI or a friend.
* `/trivia` — 4-choice multiple choice trivia covering Tech, Science, and History.
* `/slots [bet]` — High-roller slot machine with spinning reels and multiplier payouts.
* `/coinflip` — Fair weighted 50/50 coin toss.
* `/dice [sides]` — Roll a polyhedral die (e.g. d6, d20, d100).
