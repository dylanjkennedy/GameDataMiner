import requests
import csv
import os
import sys

def mainloop():
	args = sys.argv
	key = os.environ["PFF_API_KEY"]
	opponent = args[1]
	press_plays_file = args[2]

	press_plays = get_play_ids(press_plays_file)

	params = get_params(key)
	games = get_games(opponent, params)
	plays = get_plays(games, opponent, params)

	output = parse_plays(plays, press_plays)

	with open('press_coverage_defenses.csv', 'w', newline='') as f:
		writer = csv.writer(f)
		writer.writerows(output)

def get_params(key):
	params = {'x-api-key':key}
	r = requests.post('https://api.profootbalfocus.com/auth/login', headers = params)
	jwt = r.json()['jwt']
	params = {'Authorization':'Bearer ' + jwt}
	return params

def get_games(team, params):
	r = requests.get('https://api.profootbalfocus.com/v1/video/ncaa/games', headers = params)
	games = []
	for game in r.json()['games']:
		if game['season'] >= 2019:
			if game['away_team'] == team or game['home_team'] == team:
				games.append(str(game['id']))
	return games

def find_play(plays, play_id):
	for play in plays:
		if str(play['play_id']) == play_id:
			return play

def get_play_ids(file):
	play_ids = []
	with open(file) as f:
		return f.read().split(",")

def get_plays(games, team, params):
	plays = []
	for game in games:
		r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params)
		for play in r.json()['plays']:
			if play['offense'] == team:
				plays.append(play)

def get_coverages(plays, press_plays):
	play_dict = {}
	for play_id in press_plays:
		play = find_play(plays, play_id)
		coverage = str(play['pass_coverage'])
		if coverage not in play_dict:
			play_dict[coverage] = [play_id]
		elif play_id not in play_dict[coverage]:
			play_dict[coverage].append(play_id)
	return play_dict

def parse_plays(plays, press_plays):
	coverages = get_coverages(plays, press_plays)
	fields = ["Coverage Type", "Count"]
	results = [fields]
	for key in coverages:
		row = [key]
		row.append(len(coverages[key]))
		results.append(row)
	return results

mainloop()