# VTEX-WIZARD-TELEGRAM-BOT

## Local Installation

To run this project, you'll need to add the following environment variables to your `.env` file:

`TOKEN`

`DEVELOPER_CHAT_ID`

`BOTHOST`

`DEBUG`

Clone the project

```bash
$ git clone https://github.com/Geffrerson7/vtex-wizard-telegram-bot.git
```

Navigate to the project directory

```bash
$ cd vtex-wizard-telegram-bot
```

Create a virtual environment

```sh
$ virtualenv venv
```

Activate the virtual environment

```
# windows
$ source venv/Scripts/activate
# Linux
$ source venv/bin/activate
```

Then install the required libraries:

```sh
(venv)$ pip install -r requirements.txt
```

Once all of that is done, proceed to start the app

```bash
(venv)$ python main.py
```

## Telegram bot's menu

Shows the options menu:

```bash
  /start
```

Shows the options to cancel an operation:

```bash
  /cancel
```

