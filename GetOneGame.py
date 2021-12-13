import requests
import csv
import sys
import os

def mainloop():
    # no arguments - fetch key from os

    key = os.environ['PFF_API_KEY']

    team = "MDUN"

    params = get_params(key)

    game = get_games(team, params)[0]

    output = game_data(game, team, params)

    with open('one_game.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(output)

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
        if game['season'] == 2019:
            if game['away_team'] == team or game['home_team'] == team:
                games.append(str(game['id']))
    return games

def game_data(game, team, params):
	plays = []
	r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params) # all the plays from the game
	for play in r.json()['plays']:
		if play['run_pass'] in ["P", "R"] and play['defense'] == team:
			plays.append(play)
	fields = ["Play ID", "Primary Pass Coverage", "Pass Coverage", "Receiver Position"]
	results = [fields]
	for play in plays:
		results.append([play["play_id"], play["primary_pass_coverage"], play["pass_coverage"], play["pass_receiver_target_position"]])
	return results

mainloop()