from irc.bot import SingleServerIRCBot
import SrcSide
import shlex
import os
import asyncio
import json
import time

server = 'irc.chat.twitch.tv'
port = 6667

f = open('Streamers.json')
streamers = json.load(f)['STREAMERS']

class Tmi(SingleServerIRCBot):
	def __init__(self, username, password, message_handler):
		self.message_handler = message_handler

		super().__init__([(server, port, password)], username, username)

	def on_welcome(self, client, _):
		for i, stream in enumerate(streamers):
			client.cap('REQ', ':twitch.tv/membership')
			client.cap('REQ', ':twitch.tv/tags')
			client.cap('REQ', ':twitch.tv/commands')
			client.join("#" + stream['TWITCH'])
			print('Joined:', stream['TWITCH'])
			if (i+1) % 20 == 0:
				time.sleep(10)

	def new_welcome(self, client, twitch):
		client.cap('REQ', ':twitch.tv/membership')
		client.cap('REQ', ':twitch.tv/tags')
		client.cap('REQ', ':twitch.tv/commands')
		client.join("#" + twitch)
		print('Joined:', twitch)

	def on_pubmsg(self, client, message):
		response, channel = self.message_handler(self, message, client)
		if response:
			client.privmsg('#' + channel, response)

def message_handler(self, msg, client):
	twitch = str(msg.target)[1:] # Finds which stream to send the message
	for tag in msg.tags:
		if tag['key'] == 'display-name':
			twitch_name = tag['value']
	if twitch == 'srdotcbot':
		account = False
		for stream in streamers:
			if twitch_name.lower() == stream['TWITCH']:
				account = True
				break
		if msg.arguments[0][:5] == '!join' and account == False:
			streamers.append({"TWITCH":twitch_name.lower(), "SRC":""})
			self.new_welcome(client, twitch_name.lower())
			return f"Added {twitch_name} to viewed chats, set your speedrun.com account using !setsrc", twitch
		elif msg.arguments[0][:7] == '!setsrc' and account == True:
			chat_message = msg.arguments[0].split(' ')
			stream['SRC'] = chat_message[1].lower()
			print(stream)
			return f"Set {chat_message[1]} as {twitch_name}'s speedrun.com account", twitch
	elif msg.arguments[0][0] == '!':
		try:
			chat_message = shlex.split(msg.arguments[0]) # Splits the message to make it easier for SrcSide
		except ValueError:
			return None, twitch
		variables = chat_message[2:]
		for chat in streamers: # Finds which sr.c account to check
			if chat['TWITCH'].lower() == twitch.lower():
				src = chat['SRC']
				break
		
		if src == '':
			return "No sr.c account set", twitch
		elif chat_message[0] == '!help':
			if len(chat_message) == 1:
				return f"@{twitch_name} List of commands: pb, opb, wr. Use !help {{command}} to find out more", twitch
			elif chat_message[1] == 'pb':
				return f"@{twitch_name} Gets the personal best of the streamer for a given category in the game they are currently playing. Usage: !pb {{Category}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'opb':
				return f"@{twitch_name} Gets the personal best of the streamer for a given category in a specified game. Usage: !opb {{Game abbreviation}} {{Category}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'wr':
				return f"@{twitch_name} Gets the world record for a given category in the game they are currently playing. Usage: !wr {{Category}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'ilpb':
				return f"@{twitch_name} Gets the personal best of the streamer for a given individual level category in the game they are currently playing. Usage: !pb {{Category}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'oilpb':
				return f"@{twitch_name} Gets the personal best of the streamer for a given individual level category in a specified game. Usage: !opb {{Game abbreviation}} {{Category}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'ilwr':
				return f"@{twitch_name} Gets the world record for a given individual level category in the game they are currently playing. Usage: !wr {{Category}} {{Variable1}} {{Variable2}} ...", twitch
		elif chat_message[0] == '!pb' and len(chat_message) != 1: # Gets the personal best of the streamer in the twitch category they are on for a given sr.c category (with variables)
			variables = []
			for v in range(2, len(chat_message)):
				variables.append(chat_message[v])
			message = SrcSide.get_pb(src, twitch, chat_message[1], variables, "per-game")
			print('Sending', message)
			return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!opb' and len(chat_message) != 1: # Gets the personal best of the streamer for a given game and category (with variables)
			variables = []
			for v in range(3, len(chat_message)):
				variables.append(chat_message[v])
			message = SrcSide.get_opb(src, chat_message[1], chat_message[2], variables, "per-game")
			print('Sending', message)
			return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!wr' and len(chat_message) != 1: # Gets the world record in the twitch category they are on for a given sr.c category (with variables)
			variables = []
			for v in range(2, len(chat_message)):
				variables.append(chat_message[v])
			message = SrcSide.get_wr(twitch, chat_message[1], variables, "per-game")
			print('Sending', message)
			return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!ilpb' and len(chat_message) != 1: # Gets the personal best of the streamer in the twitch category they are on for a given sr.c il category (with variables)
			variables = []
			for v in range(2, len(chat_message)):
				variables.append(chat_message[v])
			message = SrcSide.get_pb(src, twitch, chat_message[1], variables, "per-level")
			print('Sending', message)
			return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!oilpb' and len(chat_message) != 1: # Gets the personal best of the streamer for a given game and il category (with variables)
			variables = []
			for v in range(3, len(chat_message)):
				variables.append(chat_message[v])
			message = SrcSide.get_opb(src, chat_message[1], chat_message[2], variables, "per-level")
			print('Sending', message)
			return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!ilwr' and len(chat_message) != 1: # Gets the world record in the twitch category they are on for a given sr.c il category (with variables)
			variables = []
			for v in range(2, len(chat_message)):
				variables.append(chat_message[v])
			message = SrcSide.get_wr(twitch, chat_message[1], variables, "per-level")
			print('Sending', message)
			return f"@{twitch_name} {message}", twitch
	return None, twitch

def start_bot(parse_message):
	username = "srdotcbot"
	password = os.environ['OAUTH']
	bot = Tmi(username, password, message_handler)
	bot.start()

start_bot(message_handler)
