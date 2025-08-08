# 🌐 BDO Patch Intelligence Bot

An AI-powered Discord bot that monitors both Korean and Global Labs Black Desert Online patch notes, processes them using advanced Gemini language models, and posts detailed strategic intelligence reports as downloadable `.txt` files in Discord. Designed with competitive players and guilds in mind.

---

## ⚙️ Features

- ✅ Dual-source monitoring: Korean notice board & Global Lab patch updates
- ✅ Automatic patch detection every 15 minutes
- ✅ AI-generated strategic summaries using Google Gemini
- ✅ In-depth intelligence reports saved as `.txt` files
- ✅ Real-time Discord notifications with professional embeds
- ✅ Seamless historical access via `!history` and `!archive`
- ✅ Per-server configuration for announcement channels and language
- ✅ Supports multi-language translation output (en, ko, es, fr, de, ja)
- ✅ Docker-ready deployment, SQLite database, and clean architecture

---

## ▶️ How It Works

1. **Monitoring**  
   Every 15 minutes, the bot scrapes selected sources for new patch updates.

2. **Detection**  
   If a new patch is detected (not found in the database), it is queued for processing.

3. **AI Analysis**  
   The patch content is fed into Gemini AI for summarization and strategic insights.

4. **Archiving**  
   A `.txt` intelligence report is generated and saved to the `/patch_reports/` folder.

5. **Notification**  
   A professional embed message with a download link is sent to your configured Discord channel.

6. **Access Later**  
   Users can retrieve previous reports using intuitive commands or browse via archive pagination.

---

## 📡 Invite Link

➡️ **Invite the Bot to Your Server:**  
🔗 [Click Here to Invite the Bot]([https://discord.com/oauth2/authorize?client_id=1402636721279205508](https://discord.com/oauth2/authorize?client_id=1402636721279205508&permissions=8&integration_type=0&scope=bot))

> Required permissions:  
> - `Send Messages`  
> - `Embed Links`  
> - `Attach Files`  
> - `Add Reactions`

---

## 🖥️ Commands Overview

### 📊 Live Reports

| Command            | Description                                               |
|--------------------|-----------------------------------------------------------|
| `!latest`          | Shows the latest reports for both Korean & Global Labs    |
| `!latest gl`       | Just the latest Global Labs report                        |
| `!latest ko`       | Just the latest Korean live patch report                  |

### 📚 Report History

| Command               | Description                                             |
|------------------------|---------------------------------------------------------|
| `!history gl`          | Show all GL reports (most recent first)                 |
| `!history gl 3`        | Get the 3rd latest GL report                            |
| `!history ko 1`        | Get the most recent Korean report                       |
| `!archive gl`, `ko`    | Show paginated archive of older reports                 |

### 🧾 Files & Status

| Command       | Description                                     |
|---------------|-------------------------------------------------|
| `!reports`    | List available `.txt` files                     |
| `!status`     | Show database status for debugging              |

### ⚙️ Configuration

| Command                | Description                                        |
|------------------------|----------------------------------------------------|
| `!usepatch`            | Set the current channel for auto notifications     |
| `!bdolan <lang>`       | Set your preferred language for translations       |
| `!config`              | Show your server's current bot configuration       |

### 🧠 Help & Info

| Command      | Description                      |
|--------------|----------------------------------|
| `!help`      | Show detailed help about all commands |
| `!examples`  | Show practical usage examples     |

---

## 🗂️ Intelligence Reports

Each AI-generated `.txt` report includes:

- 📌 Executive Summary  
- ⚔️ PvP/PvE Combat Meta Analysis  
- 🛠️ Class Changes  
- 🌍 Content Breakdown  
- 🧠 Player Recommendations  
- 📈 Strategic Outlook  

Stored in `/patch_reports/` for long-term reference.

---

## 🌍 Supported Languages (Under Dev)

Use `!bdolan <lang_code>` to set the language output:

- 🇺🇸 English (`en`)
- 🇰🇷 Korean (`ko`)
- 🇪🇸 Spanish (`es`)
- 🇫🇷 French (`fr`)
- 🇩🇪 German (`de`)
- 🇯🇵 Japanese (`ja`)
