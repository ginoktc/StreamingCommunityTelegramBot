# Streaming Community Telegram Bot

The following is just a simple telegram bot to make the usage of [Streaming Community downloader](https://github.com/Lovi-0/StreamingCommunity) simpler.

## Requirements

- Docker
- Docker Compose
- Git

## Installation

1. Clone the repository

```bash
git clone https://github.com/ginoktc/StreamingCommunityTelegramBot.git
cd StreamingCommunityTelegramBot
```

2. Copy the config file from the [original repo](https://github.com/Lovi-0/StreamingCommunity):

```bash
wget -O config.json https://raw.githubusercontent.com/Lovi-0/StreamingCommunity/main/config.json
```

3. Edit the `.env` file to change the `BOT_TOKEN` value to your bot token.

4. To run the bot simply run the following command:

```bash
docker compose up -d
```

## Configuration

- To edit the default root folder for the downloads, edit the `.env` file and change the `ROOT_FOLDER` environment variable.
- To edit all the other configurations, edit the `config.json` file.
- **IMPORTANT**: do not change the default `root_path` in the `config.json` file, but change it in the `.env`.

# Disclaimer

This software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.
