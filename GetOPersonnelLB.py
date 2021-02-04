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

    #output = get_pass_rushes(output, team, params)

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
		defplayers = play['defensive_players'].split('; ')
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
		if player == defplayer[1]:
			if get_player_rating(player, play) >= 0.5 or get_player_rating(player, play) <= -0.5:
				return_play = True
			elif play['sack'] and player in play['sack']:
				return_play = True
			elif play['tackle'] and player in play['tackle'] and play['gain_loss'] < 0:
				return_play = True
			elif (play['pass_breakup'] and player in play['pass_breakup']) or (play['interception'] and player in play['interception']):
				return_play = True
	return return_play

def get_o_personnel(plays, players):
	positions = ["LOLB", "ROLB", "LLB", "RLB", "LILB", "RILB", "MLB"]
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

def get_pass_rushes(player_dict, team, params):
	last_x_games = get_last_games(team, 4, params)
	print(last_x_games)
	last_x_games = map(lambda x: x[0], last_x_games)
	plays = get_plays(last_x_games, team, params)
	for player in player_dict:
		for play in plays:
			pass_rushers = parse_pass_rush(play)
			if play['play_id'] not in player_dict[player] and player in pass_rushers:
				player_dict[player].append(play['play_id'])
	return player_dict

def get_last_games(team, num_games, params):
	r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games', headers=params)
	games = []
	for game in r.json()['games']:
		if game['season'] == 2020:
			if game['away_team'] == team or game['home_team'] == team:
				games.append([str(game['id']), game['start']])
	games = sorted(games, key = lambda i: i[1], reverse=True)
	return games[0:num_games]

def get_player_rating(player, play):
	player_w_rating = []
	defplayers = play['defensive_players_with_ratings'].split('; ')
	for defplayer in defplayers:
		defplayer = defplayer.split(" ")
		if defplayer[1] == player:
			player_w_rating = defplayer
	return float(player_w_rating[2][1:-1])

def parse_pass_rush(play):
	if play['pass_rush_players']:
		pass_rushers = play['pass_rush_players'].split("; ")[1:]
	else:
		pass_rushers = []
	return pass_rushers

def save_to_txt(output, team):
	filename = "{}_LB_O_personnel.txt".format(team)
	header = ['Player','Play Id']
	txt_string = 'Player \t Play Ids\n'
	for player in output:
		txt_string += reformat(player, team) + '\t' + ','.join(output[player]) + '\n\n'

	with open(filename, 'w', newline ='') as f:
		f.write(txt_string)

def reformat(player, team):
	return team + " " + str(player)[1:]


mainloop()