#!/usr/bin/env python3
from pyrogram import Client, Filters, errors
from time import sleep, localtime, strftime
from math import ceil
from re import sub
import sqlite3
import sys
import os

#	Бот для индекса файлов в либе
#
#	[x] Прикрутить pyrogram
#	[x] Прикрутить прогресс выгрузки
#	[X]	Отловить FloodWait
#	[x] Проверить путь перед добавлениеем в БД
#	[x] Экранировать текст запроса -- % и _ просто удаляет из запроса :-)
#	[x] Добавить логи
#	[*] Поработать с UI (добавить кнопки?)

choise, cnt = {}, 1
logging = False

def init(args):
	# Here we have both options handling and client init
	# It is logically better

	global logging

	if '--updatedb' in args:
		def updateDB(directory):
			
			connect = sqlite3.connect('files.db')
			c = connect.cursor()
			# Once again, if the table does not exist, create it
			# Take a look on PRIMARY KEY mark for each full path
			c.execute('CREATE TABLE IF NOT EXISTS Files (path TEXT PRIMARY KEY, file_name TEXT);')

			for base, subfolder, files in os.walk(directory):
				for file in files:
					row = ('{}/{}'.format(base, file), file)
					# If the file is in DB, ignore it
					c.execute('INSERT OR IGNORE INTO Files (path, file_name) VALUES (?, ?);', row)

			connect.commit()
			connect.close()

		path = input('ENTER THE FULL PATH TO STORE IT\'S ENTITIES\n> ')
		
		if os.path.exists(path) and os.path.isdir(path):
			updateDB(path)
		else:
			sys.exit('GIVEN PATH IS NOT A DIRECTORY OR DOES NOT EXIST')

		sys.exit('DATABASE HAS BEEN UPDATED')

	if '--logging' in args:
		logging = True

	if not os.path.exists('files.db'):
		sys.exit('No database found. Generate it with --updatedb')

	return Client('archive', config_file="config.ini")

def searchFile(file_name):
	# We can't get on without globals
	# /search needs to get data somehow

	global choise, cnt

	# For each entrance in function we override previous values

	if choise != {} and cnt != 1:
		choise, cnt = {}, 1

	out = ''

	connect = sqlite3.connect('files.db')
	c = connect.cursor()

	for entity in c.execute('SELECT path FROM Files WHERE file_name LIKE "%" || ? || "%";', (file_name,)):
		# Entity[0] is because we pass a tuple, not string!
		choise.update({cnt: entity[0]})
		out += '`{}. {}`\n'.format(cnt,choise[cnt])
		cnt += 1
	
	if choise != {}:

		# IDK actually whether it works
		# Cutting on chunks by 4096 chars on each is needed as the lognest Telegram message is so
		# Also I have to keep search output entities strings unbroken

		chunks = []

		for count in range(0, ceil(len(out) / 4096)):
			chunks.append(out[:out[:4096].rindex('\n')])
			out = out[out[:4096].rindex('\n'):]

		if len(chunks[-1] + out) >= 4096:
			chunks.append(out)
		else:
			# This is made as we always have last chunk left
			chunks[-1] += out

		return chunks
	else:
		# indexFiles() below works with lists so we have to return the same type
		return ['Nothing found!']

def log(UID, action, UNIX_date):

	conn = sqlite3.connect('actions.db')
	c = conn.cursor()

	# If the table does not exist, let it be. Otherwise ignore it
	# Pretty simple
	c.execute('''CREATE TABLE IF NOT EXISTS Actions (
		ID INTEGER PRIMARY KEY AUTOINCREMENT,
		UID INTEGER,
		action STRING,
		date STRING
		);''')


	date = strftime('%d-%m-%Y [%H:%M:%S]', localtime(UNIX_date))

	c.execute('INSERT INTO Actions (UID, action, date) VALUES (?, ?, ?)',\
		(UID, action, date))

	conn.commit()
	conn.close()

app = init(sys.argv)

# For each command we call message handling decorator
# Then we pass a filter to work with commands only

@app.on_message(Filters.command('search'))
def indexFiles(client, message):

	if logging:
		log(message.from_user.id, message.text, message.date)

	# To avoid SQLite's wildcarting % and _ in queries are deleted
	arg = sub('%|_', '', message.text[len('/search '):])

	if arg != '':
		for chunk in searchFile(arg):
			try:
				message.reply(chunk)
			# If there are too many entities to post, Telegram can throw a FloodWait
			# Handler worked but who knows? 
			except errors.exceptions.FloodWait as e:
				print('FloodWait has been caught: sleeping for ', e.x)
				sleep(e.x)
	else:
		# Can't you be more polite?
		message.reply('Fuck you')

@app.on_message(Filters.command('choose'))
def chooseFile(client, message):

	try:
		# Take a look: we try to make an integer from
		# rest of the message after the command itself
		option = int(message.text[len('/choose '):])
	except ValueError:
		# That doesn't mean that I'm rude.
		# I'm just tired of users typing /choose '); DROP DATABASE ... 
		message.reply('Fuck you')
		return

	# User can't choose unlisted option
	if option > cnt or option < 1:
		message.reply('Fuck you')
	# Even if he didn't search
	elif choise == {}:
		message.reply('Fuck you')
	else:
		msg = message.reply('Uploading:\n')

		def progress(current, total):
			# Callback modifies the message with uploading status
			nonlocal msg
			try:
				msg.edit_text('Uploading:\n{:.1f}'.format(current * 100 / total))
			# Sometimes if throws this.
			# Maybe because callback is called for each uploaded chunk
			# Anyway, handle it
			except errors.exceptions.bad_request_400.MessageNotModified:
				msg.delete()
			# Handle it twice
			if current == total: msg.delete()

		message.reply_document(choise[option], progress=progress)
		
		if logging:
			log(message.from_user.id, '{} ({})'.format(message.text, choise[option]), message.date)


@app.on_message(Filters.command('help'))
def helpMessage(client,message):
	message.reply("""**This bot is made to index library's unsorted folders.**

**USAGE**:
`/help` - Print this message
`/search ENTITY` - Search for ENTITY. You will be given some choose options then.
`/choose OPTION` - Choose specified option.

**SOURCES AND ISSUES**:
[[Github]](https://github.com/asciid/robinHood), [[Author]](tg://user?id=298686852)""",\
	disable_web_page_preview=True)

app.run()