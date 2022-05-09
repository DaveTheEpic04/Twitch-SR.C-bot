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

def check_cats(game, category, scope):
	cats = requests.get(f"{SRC_API}/games/{game}/categories?embed=variables").json()['data']
	cat_list = []
	for cat in cats:
		if category.lower() == cat['name'].lower() and cat['type'] == scope:
			return cat
		if category.lower() == cat['name'][:len(category)].lower() and cat['type'] == scope:
			cat_list.append(cat)
	if len(cat_list) != 0:
		return cat_list[0]

def get_pb(src, twitch, category, scope, variables, level=""):
	games = get_games(twitch) # Gets the list of games connected to the users twitch category
	for game in games:
		cat = check_cats(game, category, scope)
		if cat == None:
			return None
		runs = requests.get(f"{SRC_API}/users/{src}/personal-bests?game={game}&embed=category,game,level&max=200").json()['data']
		for run in runs:
			if cat['id'] == run['category']['data']['id'] and (scope == 'per-game' or level.lower() == run['level']['data']['name'].lower()):
				vars = []
				for i, var in enumerate(cat['variables']['data']): # gets the variable data for each variable
					for j, value in enumerate(var['values']['choices'].values()):
						if value.lower() in [x.lower() for x in variables]:
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
				level_str = ''
				if scope == 'per-level':
					level_str = f"Level: {run['level']['data']['name']}, "
				if vars == [] or count == k+1: # Part of the variable check
					return f"Position: {run['place']}, Game: {run['game']['data']['names']['international']}, {level_str}Category: {cat['name']}, {var_str} Time: {conv_to_time(run['run']['times']['primary_t'])}"

def get_opb(src, game, category, scope, variables, level=""):
	runs = requests.get(f"{SRC_API}/users/{src}/personal-bests?game={game}&embed=category,game,level&max=200").json()['data']
	for run in runs:
		cat = check_cats(game, category, scope)
		if cat == None:
			return None
		if cat['id'] == run['category']['data']['id'] and (scope == 'per-game' or level.lower() == run['level']['data']['name'].lower()):
			vars = []
			for i, var in enumerate(cat['variables']['data']): # gets the variable data for each variable
				for j, value in enumerate(var['values']['choices'].values()):
					if value.lower() in [x.lower() for x in variables]:
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
			level_str = ''
			if scope == 'per-level':
				level_str = f"Level: {run['level']['data']['name']}, "
			if vars == [] or count == k+1: # Part of the variable check
				return f"Position: {run['place']}, Game: {run['game']['data']['names']['international']}, {level_str}Category: {cat['name']}, {var_str} Time: {conv_to_time(run['run']['times']['primary_t'])}"

def get_run(twitch, category, pos, scope, variables, level=""):
	games = get_games(twitch) # Gets the list of games connected to the users twitch category
	for game in games:
		cat = check_cats(game, category, scope)
		if cat == None:
			return None
		game_info = requests.get(f"{SRC_API}/games/{game}?embed=categories,levels&max=200").json()['data']
		levels = game_info['levels']['data']
		if scope == 'per-level':
			for lev in levels:
				if lev['name'].lower() == level.lower():
					vars = []
					for i, var in enumerate(cat['variables']['data']): # gets the variable data for each variable
						for j, value in enumerate(var['values']['choices'].values()):
							if value.lower() in [x.lower() for x in variables]:
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
					runs = requests.get(f"{SRC_API}/leaderboards/{game}/level/{lev['id']}/{cat['id']}?top={pos}{var_req}").json()['data']
					game = requests.get(f"{SRC_API}/games/{game}").json()['data']['names']['international']
					for k, place in enumerate(runs['runs']):
						if pos == place['place']:
							break
					if pos != 1:
						Position = f"Position: {pos}, "
					else:
						Position = ""
					players = ""
					for player in place['run']['players']:
						players = f"{players} {requests.get(player['uri']).json()['data']['names']['international']},"
					return f"{Position}Game: {game}, Players: {players} Level: {lev['name']}, Category: {cat['name']}, {var_str} Time: {conv_to_time(place['run']['times']['primary_t'])}"
		elif scope == 'per-game':
			vars = []
			for i, var in enumerate(cat['variables']['data']): # gets the variable data for each variable
				for j, value in enumerate(var['values']['choices'].values()):
					if value.lower() in [x.lower() for x in variables]:
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
			runs = requests.get(f"{SRC_API}/leaderboards/{game}/category/{cat['id']}?top={pos}{var_req}").json()['data']
			game = requests.get(f"{SRC_API}/games/{game}").json()['data']['names']['international']
			for place in runs['runs']:
				if int(pos) == place['place']:
					break
			if int(pos) != 1:
				Position = f"Position: {pos}, "
			else:
				Position = ""
			players = ""
			for player in place['run']['players']:
				players = f"{players} {requests.get(player['uri']).json()['data']['names']['international']},"
			return f"{Position}Game: {game}, Players: {players} Category: {cat['name']}, {var_str} Time: {conv_to_time(place['run']['times']['primary_t'])}"