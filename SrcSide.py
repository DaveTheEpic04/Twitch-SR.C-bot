import requests
import sys
import os

SRC_API = 'https://www.speedrun.com/api/v1'
TWITCH_API = 'https://api.twitch.tv'

ClientID = os.environ['CLIENT_ID']
SecretID = os.environ['SECRET_ID']
OAuth = requests.post(f"https://id.twitch.tv/oauth2/token?client_id={ClientID}&client_secret={SecretID}&grant_type=client_credentials").json()['access_token'] # Required for the twitch category check

def conv_to_time(time): # Better formatting for time
	hours = int(time / 3600)
	time = time - hours*3600
	minutes = int(time / 60)
	time = round(time - minutes*60, 3)
	seconds = int(time)
	milliseconds = int(round((time - seconds)*1000, 0))
	if len(str(minutes)) == 1 and hours != 0:
		minutes = "0" + str(minutes)
	if len(str(seconds)) == 1:
		seconds = "0" + str(seconds)
	if len(str(milliseconds)) == 1:
		milliseconds = "00" + str(milliseconds)
	elif len(str(milliseconds)) == 2:
		milliseconds = "0" + str(milliseconds)
	if hours == 0:
		if len(str(minutes)) == 1:
			minutes = "0" + str(minutes)
		return str(minutes) + ":" + str(seconds) + "." + str(milliseconds)
	return str(hours) + ":" + str(minutes) + ":" + str(seconds) + "." + str(milliseconds)

def get_games(name):
	games = []
	broad_id = requests.get(f"{TWITCH_API}/helix/users?login={name}", headers={"Authorization":f"Bearer {OAuth}", "Client-Id":ClientID}).json()['data'][0]['id'] # Gets the broadcasters id
	category = requests.get(f"{TWITCH_API}/helix/channels?broadcaster_id={broad_id}", headers={"Authorization":f"Bearer {OAuth}", "Client-Id":ClientID}).json()['data'][0]['game_name'] # Gets the twitch category
	twitch = requests.get(f"{SRC_API}/games?name={category}").json()['data'] # Gets games with the right name
	for game in twitch:
		if game['names']['twitch'] == category:
			games.append(game['id'])
	return games

def get_pb(src, twitch, category, variables=[]):
	games = get_games(twitch) # Gets the list of games connected to the users twitch category
	for game in games:
		runs = requests.get(f"{SRC_API}/users/{src}/personal-bests?game={game}&embed=category.variables,game&max=200").json()['data']
		for run in runs:
			if category.lower() == run['category']['data']['name'].lower() and run['category']['data']['type'] == 'per-game': # Gets the correct category for full-game runs only
				vars = []
				for i, var in enumerate(run['category']['data']['variables']['data']): # gets the variable data for each variable
					for j, value in enumerate(var['values']['choices'].values()):
						if value in variables:
							vars.append({'variable':var['name'], 'var_id':var['id'], 'value':value, 'val_id':list(var['values']['choices'].keys())[j]})
							break
					if len(vars) != i+1 and var['values']['default'] != None: # Adds a
						vars.append({'variable':var['name'], 'var_id':var['id'], 'value':var['values']['choices'][str(var['values']['default'])], 'val_id':var['values']['default']})
					elif len(vars) != i+1:
						vars.append(None)
				count = 0
				for k, id in enumerate(vars):
					if id == None or run['run']['values'][id['var_id']] == id['val_id']: # Checks the run to see if it fits the specified variables
						count += 1
				var_str = ''
				for v in vars:
					if v != None:
						var_str = f"{var_str} {v['variable']}: {v['value']}," # Gets the variables in the correct format (may be changed for twitch)
				if vars == [] or count == k+1: # Part of the variable check
					return f"Position: {run['place']}, Game: {run['game']['data']['names']['international']}, Category: {run['category']['data']['name']}, {var_str} Time: {conv_to_time(run['run']['times']['primary_t'])}"

def get_opb(src, game, category, variables=[]):
	runs = requests.get(f"{SRC_API}/users/{src}/personal-bests?game={game}&embed=category.variables,game&max=200").json()['data']
	for run in runs:
		if category.lower() == run['category']['data']['name'].lower() and run['category']['data']['type'] == 'per-game': # Gets the correct category for full-game runs only
			vars = []
			for i, var in enumerate(run['category']['data']['variables']['data']): # gets the variable data for each variable
				for j, value in enumerate(var['values']['choices'].values()):
					if value in variables:
						vars.append({'variable':var['name'], 'var_id':var['id'], 'value':value, 'val_id':list(var['values']['choices'].keys())[j]})
						break
				if len(vars) != i+1 and var['values']['default'] != None: # Adds a
					vars.append({'variable':var['name'], 'var_id':var['id'], 'value':var['values']['choices'][str(var['values']['default'])], 'val_id':var['values']['default']})
				elif len(vars) != i+1:
					vars.append(None)
			count = 0
			for k, id in enumerate(vars):
				if id == None or run['run']['values'][id['var_id']] == id['val_id']: # Checks the run to see if it fits the specified variables
					count += 1
			var_str = ''
			for v in vars:
				if v != None:
					var_str = f"{var_str} {v['variable']}: {v['value']}," # Gets the variables in the correct format (may be changed for twitch)
			if vars == [] or count == k+1: # Part of the variable check
				return f"Position: {run['place']}, Game: {run['game']['data']['names']['international']}, Category: {run['category']['data']['name']}, {var_str} Time: {conv_to_time(run['run']['times']['primary_t'])}"

def get_wr(twitch, category, variables=[]):
	games = get_games(twitch) # Gets the list of games connected to the users twitch category
	for game in games:
		cats = requests.get(f"{SRC_API}/games/{game}/categories?embed=variables&max=200").json()['data']
		for cat in cats:
			if cat['name'].lower() == category.lower():
				vars = []
				for i, var in enumerate(cat['variables']['data']): # gets the variable data for each variable
					for j, value in enumerate(var['values']['choices'].values()):
						if value in variables:
							vars.append({'variable':var['name'], 'var_id':var['id'], 'value':value, 'val_id':list(var['values']['choices'].keys())[j]})
							break
					if len(vars) != i+1 and var['values']['default'] != None:
						vars.append({'variable':var['name'], 'var_id':var['id'], 'value':var['values']['choices'][str(var['values']['default'])], 'val_id':var['values']['default']})
					elif len(vars) != i+1:
						vars.append(None)
				var_str = ''
				var_req = ''
				for v in vars:
					if v != None:
						var_str = f"{var_str} {v['variable']}: {v['value']}," # Gets the variables in the correct format (may be changed for twitch)
						var_req = f"{var_req}&var-{v['var_id']}={v['val_id']}"
				run = requests.get(f"{SRC_API}/leaderboards/{game}/category/{cat['id']}?top=1{var_req}").json()['data']
				game = requests.get(f"{SRC_API}/games/{game}").json()['data']['names']['international']
				players = ""
				for player in run['runs'][0]['run']['players']:
					players = f"{players} {requests.get(player['uri']).json()['data']['names']['international']},"
				return f"Game: {game}, Players: {players} Category: {cat['name']}, {var_str} Time: {conv_to_time(run['runs'][0]['run']['times']['primary_t'])}"
