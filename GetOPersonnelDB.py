import requests
import csv
import sys
import os

def mainloop():
    # no arguments - fetch key from os

    key = os.environ['PFF_API_KEY']

    team = sys.argv[1]

    players = sys.argv[2:]

    params = get_params(key)

    games = get_games(team, params)

    plays = get_plays(games, team, params)

    output = get_o_personnel(plays, players)
    save_to_txt(output, team)

def get_params(key):
    params = {'x-api-key':key}
    r = requests.post('https://api.profootballfocus.com/auth/login', headers = params)
    jwt = r.json()['jwt']
    params = {'Authorization':'Bearer ' + jwt}
    return params

def get_games(team, params):
    r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games', headers=params)
    games = []
    for game in r.json()['games']:
        if game['season'] >= 2020:
            if game['away_team'] == team or game['home_team'] == team:
                games.append(str(game['id']))
    return games

def get_plays(games, team, params):
	plays = []
	for game in games:
		r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params) # all the plays from the game
		for play in r.json()['plays']:
			if play['defense'] == team and play['run_pass']:
				plays.append(play)
	return plays

def get_players(plays, positions):
	players = []
	for play in plays:
		if play['defensive_players'] is not None:
			defplayers = play['defensive_players'].split('; ')
		else:
			defplayers = []
		for player in defplayers:
			player = player.split(" ")
			player_num = player[1]
			player_posn = player[2][1:-1]
			if player_posn in positions and player_num not in players and player_num[0] == "D":
				players.append(player_num)
	return players

def check_play(player, play, positions):
	return_play = False
	defplayers = []
	if play['defensive_players']:
		defplayers = play['defensive_players'].split('; ')
	for defplayer in defplayers:
		defplayer = defplayer.split(" ")
		if player == defplayer[1] and defplayer[2][1:-1] in positions:
			if play['pass_breakup'] and player in play['pass_breakup']:
				return_play = True
			elif play['interception'] and player in play['interception']:
				return_play = True
			elif play['sack'] and player in play['sack']:
				return_play = True
			elif play['forced_fumble'] and player in play['forced_fumble']:
				return_play = True
			elif is_solo_tackle(player, play):
				return_play = True
	return return_play

def is_solo_tackle(player, play):
	if not play['tackle']:
		return False
	elif player not in play['tackle']:
		return False
	elif len(player) + 5 == len(play['tackle']):
		return True
	return False

def get_o_personnel(plays, players):
	positions = ["FS", "FSL", "FSR", "SS", "SSL", "SSR", "LCB", "RCB", "SCBL", "SCBR", "SCBiL", "SCBiR", "SCBoL", "SCBoR"]
	if players == []:
		players = get_players(plays, positions)
	players = sorted(players)
	player_play_dict = {}
	for player in players:
		player_play_dict[player] = []
		for play in plays:
			if check_play(player, play, positions):
				player_play_dict[player].append(str(play['play_id']))
	return player_play_dict

def save_to_txt(output, team):
	filename = "{}_DB_O_personnel.txt".format(team)
	header = ['Player','Play Id']
	txt_string = 'Player \t Play Ids\n'
	for player in output:
		txt_string += reformat(player, team) + '\t' + ','.join(output[player]) + '\n\n'

	with open(filename, 'w', newline ='') as f:
		f.write(txt_string)

def reformat(player, team):
	return team + " " + str(player)[1:]


mainloop()