from irc.bot import SingleServerIRCBot
import SrcSide
import S3Side
import shlex
import os
import asyncio
import json
import time

server = 'irc.chat.twitch.tv'
port = 6667

f = open('Streamers.json', 'r')
streamers = json.load(f)['STREAMERS']
f.close()

def file_update(streamers):
	file = open('Streamers.json', 'w')
	streamers = str(streamers).replace("\'", "\"")
	file.write('{"STREAMERS":%s}' % streamers)
	file.close()

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
		elif tag['key'] == 'user-type':
			mod_status = tag['value']
	if twitch == os.environ['BOT_NAME']:
		account = False
		for pos, stream in enumerate(streamers):
			if twitch_name.lower() == stream['TWITCH']:
				account = True
				break
		if msg.arguments[0][:5] == '!help':
			return f"@{twitch_name} Use !join to add your account, !setsrc to set your speedrun.com account and !leave if you no longer want the bot in your channel", twitch
		elif msg.arguments[0][:5] == '!join' and account == False:
			streamers.append({"TWITCH":twitch_name.lower(), "SRC":""})
			self.new_welcome(client, twitch_name.lower())
			file_update(streamers)
			return f"Added {twitch_name} to viewed chats, set your speedrun.com account using !setsrc", twitch
		elif msg.arguments[0][:7] == '!setsrc' and account == True:
			chat_message = msg.arguments[0].split(' ')
			try:
				stream['SRC'] = chat_message[1].lower()
			except IndexError:
				return f"@{twitch_name} You must enter you speedrun.com name after the command", twitch
			file_update(streamers)
			return f"Set {chat_message[1]} as {twitch_name}'s speedrun.com account", twitch
		elif msg.arguments[0][:6] == '!leave' and account == True:
			streamers.pop(pos)
			file_update(streamers)
			print("Removed:", twitch_name.lower())
			return f"@{twitch_name} has been removed from SRdotCbot's viewed chats, use !join to join back", twitch
		elif msg.arguments[0][:6] == '!count':
			return f"@{twitch_name} We currently host SRdotCbot on {len(streamers)} different streams!", twitch
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
				return f"@{twitch_name} List of commands: pb, ilpb, opb, oilpb, wr, ilwr, run, ilrun. Use !help {{command}} to find out more", twitch
			elif chat_message[1] == 'pb':
				return f"@{twitch_name} Gets the personal best of the streamer for a given category in the game they are currently playing. Usage: !pb {{Category}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'opb':
				return f"@{twitch_name} Gets the personal best of the streamer for a given category in a specified game. Usage: !opb {{Game abbreviation}} {{Category}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'wr':
				return f"@{twitch_name} Gets the world record for a given category in the game they are currently playing. Usage: !wr {{Category}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'run':
				return f"@{twitch_name} Gets the run in the specified position for a given category in the game currently being played (Moderators only). Usage: !run {{Category}} {{Position}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'ilpb':
				return f"@{twitch_name} Gets the personal best of the streamer for a given individual level category in the game they are currently playing. Usage: !ilpb {{Category}} {{Level}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'oilpb':
				return f"@{twitch_name} Gets the personal best of the streamer for a given individual level category in a specified game. Usage: !oilpb {{Game abbreviation}} {{Category}} {{Level}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'ilwr':
				return f"@{twitch_name} Gets the world record for a given individual level category in the game they are currently playing. Usage: !ilwr {{Category}} {{Level}} {{Variable1}} {{Variable2}} ...", twitch
			elif chat_message[1] == 'ilrun':
				return f"@{twitch_name} Gets the run in the specified position for a given individual level category in the game currently being played (Moderators only). Usage: Usage: !ilrun {{Category}} {{Position}} {{Level}} {{Variable1}} {{Variable2}} ...", twitch
		elif chat_message[0] == '!pb' and len(chat_message) != 1: # Gets the personal best of the streamer in the twitch category they are on for a given sr.c category (with variables)
			variables = []
			for v in range(2, len(chat_message)):
				variables.append(chat_message[v])
			try:
				message = SrcSide.get_pb(src, twitch, chat_message[1], "per-game", variables)
			except Exception as e:
				print(str(e))
				return None, twitch
			if message != None:
				print('Sending', twitch, message)
				return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!opb' and len(chat_message) != 1: # Gets the personal best of the streamer for a given game and category (with variables)
			variables = []
			for v in range(3, len(chat_message)):
				variables.append(chat_message[v])
			try:
				message = SrcSide.get_opb(src, chat_message[1], chat_message[2], "per-game", variables)
			except Exception as e:
				print(str(e))
				return None, twitch
			if message != None:
				print('Sending', twitch, message)
				return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!wr' and len(chat_message) != 1: # Gets the world record in the twitch category they are on for a given sr.c category (with variables)
			variables = []
			for v in range(2, len(chat_message)):
				variables.append(chat_message[v])
			try:
				message = SrcSide.get_run(twitch, chat_message[1], 1, "per-game", variables)
			except Exception as e:
				print(str(e))
				return None, twitch
			if message != None:
				print('Sending', twitch, message)
				return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!run' and (mod_status == 'mod' or twitch_name.lower() == twitch):
			variables = []
			for v in range(4, len(chat_message)):
				variables.append(chat_message[v])
			try:
				message = SrcSide.get_run(twitch, chat_message[1], chat_message[2], "per-game", variables)
			except Exception as e:
				print(str(e))
				return None, twitch
			if message != None:
				print('Sending', twitch, message)
				return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!ilpb' and len(chat_message) != 1: # Gets the personal best of the streamer in the twitch category they are on for a given sr.c il category (with variables)
			variables = []
			for v in range(3, len(chat_message)):
				variables.append(chat_message[v])
			try:
				message = SrcSide.get_pb(src, twitch, chat_message[1], "per-level", variables, chat_message[2])
			except Exception as e:
				print(str(e))
				return None, twitch
			if message != None:
				print('Sending', twitch, message)
				return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!oilpb' and len(chat_message) != 1: # Gets the personal best of the streamer for a given game and il category (with variables)
			variables = []
			for v in range(4, len(chat_message)):
				variables.append(chat_message[v])
			try:
				message = SrcSide.get_opb(src, chat_message[1], chat_message[2], "per-level", variables, chat_message[3])
			except Exception as e:
				print(str(e))
				return None, twitch
			if message != None:
				print('Sending', twitch, message)
				return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!ilwr' and len(chat_message) != 1: # Gets the world record in the twitch category they are on for a given sr.c il category (with variables)
			variables = []
			for v in range(3, len(chat_message)):
				variables.append(chat_message[v])
			try:
				message = SrcSide.get_run(twitch, chat_message[1], 1, "per-level", variables, chat_message[2])
			except Exception as e:
				print(str(e))
				return None, twitch
			if message != None:
				print('Sending', twitch, message)
				return f"@{twitch_name} {message}", twitch
		elif chat_message[0] == '!ilrun' and (mod_status == 'mod' or twitch_name.lower() == twitch):
			variables = []
			for v in range(4, len(chat_message)):
				variables.append(chat_message[v])
			try:
				message = SrcSide.get_run(twitch, chat_message[1], chat_message[3], "per-level", variables, chat_message[2])
			except Exception as e:
				print(str(e))
				return None, twitch
			if message != None:
				print('Sending', twitch, message)
				return f"@{twitch_name} {message}", twitch
	return None, twitch

def start_bot(parse_message):
	username = os.environ['BOT_NAME']
	password = os.environ['OAUTH']
	bot = Tmi(username, password, message_handler)
	bot.start()

if __name__ == "__main__":
	try:
		start_bot(message_handler)
	except Exception as e:
		print(str(e))
		S3Side.sigterm_handler(0, 0)