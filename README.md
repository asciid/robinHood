# Robin Hood

Script to share any folder as a Telegram bot.

## DEPENDENCIES

`pyrogram` is the only dependency. You can make it faster with `tgcrypto`.

## CONFIGURATION
* Go to https://my.telegram.org and register an application. Get it's `api_id` and `api_hash`.
* Go to https://t.me/botfather (@botfather in Telegram) and register a bot. Get it's `bot_token`.
* Create `config.ini` in code's base directory and write following lines:

```ini
[pyrogram]
api_id = 
api_hash = 
bot_token =
```

And insert values you have.

## USAGE

You can make it executable and run like this:

```bash
chmod +x main.py
./main.py
```

You can also call it with python:

`python3 main.py`

### OPTIONS

`./main.py --updatedb` - Update/create the file tree database `files.db`

`./main.py --logging` - Enable logging. Log is stored in `actions.db`

Feel free to modify the code, create forks and just use it.

_nullcomm, asciid_
