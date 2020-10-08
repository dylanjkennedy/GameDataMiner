import requests
import csv
import sys
import os

def mainloop():
    # no arguments for key - fetch key from os

    key = os.environ['PFF_API_KEY']

    params = get_params(key)

    # fetch team identifier from args

    team = sys.argv[1]

    games = get_games(team, params)

    plays = get_plays(games, team, params)

    output = cutup_pressure(plays)

    save_to_txt(output, team)

# Turn an api key into a jwt key and format as header
def get_params (key):
    params = {'x-api-key':key}
    r = requests.post('https://api.profootballfocus.com/auth/login', headers = params)
    jwt = r.json()['jwt']
    params = {'Authorization':'Bearer ' + jwt}
    return params

# For a given opponent, return all game ids in which they played in 2019
def get_games(team, params):
    r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games', headers=params)
    games = []
    for game in r.json()['games']:
        if game['season'] == 2019:
            if game['away_team'] == team or game['home_team'] == team:
                games.append(str(game['id']))
    return games

# For a given set of games, fetch the plays where team is on defense
def get_plays(games, team, params):
	plays = []
	for game in games:
		r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params) # all the plays from the game
		for play in r.json()['plays']:
			if play['defense'] == team and play['run_pass']:
				plays.append(play)
	return plays

def cutup_pressure(plays):
	players = []
	positions = ["LE", "RE", "LEO", "REO", "LOLB", "ROLB", "NLT", "NRT", "DLT", "DRT", "NT"]
	play_type_map = {"sack": 3, "hit": 2, "hurry": 1}

	for play in plays:
		pass_rushers = parse_pass_rush(play)
		for rusher in pass_rushers:
			rusher = rusher.split(" ")
			if rusher[1] not in players and rusher[2][1:-1] in positions:
				players.append(rusher[1])
	players  = sorted(players)
	results = []
	player_play_dict = {}
	for player in players:
		player_play_dict[player] = []
		for play in plays:
			play_dict = check_play(play, player, positions)
			if play_dict:
				player_play_dict[player].append(play_dict)
		player_play_dict[player] = sorted(player_play_dict[player], key = lambda x: (x['play_type'], x['game_date']), reverse=True)
		if len(player_play_dict[player]) > 25:
			print(player)
			player_play_dict[player] = player_play_dict[player][:25]
		player_play_dict[player] = [str(play['play_id']) for play in player_play_dict[player]]
	return player_play_dict

def check_play(play, player, positions):
	if not play['pass_rush_players']:
		return False
	elif player not in play['pass_rush_players']:
		return False
	else:
		pass_rushers = list(map(lambda y: [y[0], y[1][1:-1]], list(map(lambda x: x.split(" ")[1:], parse_pass_rush(play)))))
		if not any(lambda x: x[0] == player for x in pass_rushers):
			return False
		else:
			posn = ""
			for pass_rusher in pass_rushers:
				if pass_rusher[0] == player:
					posn = pass_rusher[1]
			if posn not in positions:
				return False
			else:
				play_dict = {}
				play_dict["play_id"] = play['play_id']
				play_dict["game_date"] = play['game_date']
				play_type = 0
				if play['sack'] and player in play['sack']:
					play_type = 3
				elif play['hit_players'] and player in play['hit_players']:
					play_type = 2
				elif play['hurry_players'] and player in play['hurry_players']:
					play_type = 1
				play_dict["play_type"] = play_type
				if play_type == 0:
					return False
				else:
					return play_dict


def find_player_posn(play, player):
	if play['pass_rush_players']:
		pass_rushers = play['pass_rush_players'].split("; ")[1:]

def parse_pass_rush(play):
	if play['pass_rush_players']:
		pass_rushers = play['pass_rush_players'].split("; ")[1:]
	else:
		pass_rushers = []
	return pass_rushers

def save_to_txt(output, team):
	filename = "{}_pressure_cutup.txt".format(team)
	header = ['Player','Game Id', 'Play Id']
	txt_string = 'Player \t Play Ids\n'
	for player in output:
		txt_string += reformat(player, team) + '\t' + ','.join(output[player]) + '\n\n'

	with open(filename, 'w', newline ='') as f:
		f.write(txt_string)

def reformat(player, team):
	return team + " " + player[1:]
	
mainloop()