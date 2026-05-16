# 🦖 Pteero Bot

A Discord bot built with [Python](https://www.python.org/) and [disnake](https://disnake.dev/) for my friends and me. It helps manage your self-hosted game server using the [Pterodactyl API](https://pterodactyl.io/).

## ✨ Features

- 📊 **Dashboards**: Create live control panels with real-time display of CPU, RAM, disk, and network usage and power buttons (Start, Stop, Restart, Kill).
- 🛡️ **Permissions System**: Configure permissions (e.g., who can start/stop a specific server) for individual users or Discord roles.

## 🚀 Installation & Setup

### 1. Using [Pterodactyl](https://pterodactyl.io/) (Recommended)

1. Create a new Nest in your Pterodactyl Panel settings.
2. Download the [egg-minecraft-bot.json](https://github.com/Skrriply/pteero-bot/blob/main/egg-pteero-bot.json) file.
3. Import the downloaded file into Pterodactyl and assign it to the Nest you just created.
4. Create a new server using this Egg.
5. After the server installing create a copy of the `.env.example` file in the root directory, rename it to `.env`, then fill in the required variables.
6. Start the server.

### 2. Manual

#### 1. Clone the repository

```bash
git clone https://github.com/Skrriply/pteero-bot.git
cd pteero-bot
```

#### 2. Install dependencies

It's recommended to use [uv](https://docs.astral.sh/uv/).

```bash
python -m pip install uv
python -m uv sync --no-dev
```

#### 3. Configure environment variables

Create a copy of the `.env.example` file in the root directory and rename it to `.env`, then fill in the required variables.

#### 4. Run the bot.

```bash
python -m uv run ./src/bot/main.py
```

---

## 📜 Discord Slash Commands

| Command                                      | Description                                                                                 |
| -------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `/dashboard [server_id]`                     | 📊 Spawns a live control panel for the specified server identifier                          |
| `/permissions grant [user/role] [server_id]` | 🛡️ Grants specific server access permissions (start, stop, etc.) to a user or Discord role. |

## ⚖️ License

Distributed under the [GPL-3.0 License](https://github.com/Skrriply/pteero-bot/blob/main/LICENSE).
