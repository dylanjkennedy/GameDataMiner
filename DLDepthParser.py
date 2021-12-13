import requests
import csv
import os
import sys

def mainloop():
    # no arguments - fetch key from os

    key = os.environ['PFF_API_KEY']

    league = sys.argv[1].lower()

    params = get_params(key)

    games = get_games(league, params)

    plays = get_plays(league, games, params)

    output = dl_depth(plays)

    save_to_txt(output, league)

def get_params(key):
    params = {'x-api-key':key}
    r = requests.post('https://api.profootballfocus.com/auth/login', headers = params)
    jwt = r.json()['jwt']
    params = {'Authorization':'Bearer ' + jwt}
    print("Got params")
    return params

def get_games(league, params):
    r = requests.get('https://api.profootballfocus.com/v1/video/'+league+'/games', headers=params)
    games = []
    for game in r.json()['games']:
        if game['season'] == 2020:
            games.append(str(game['id']))
    print("Got " + str(len(games)) + " games")
    return games

def get_plays(league, games, params):
	plays = []
	i = 0
	for game in games:
		r = requests.get('https://api.profootballfocus.com/v1/video/'+ league + '/games/'+game+'/plays', headers = params) # all the plays from the game
		for play in r.json()['plays']:
			plays.append(play)
		i += 1
		print(i)
	print("Got " + str(len(plays)) + " plays")
	return plays

def dl_depth(plays):
	plays_to_save = []
	for play in plays:
		dl_tech = play['dl_techniques']
		lb_depth = play['linebacker_depth']
		if play['play_id'] in [3556702, 3553871, 3523552, 3754464, 3755321]:
			print(dl_tech, lb_depth, check_dl(dl_tech), check_lb(lb_depth))
		if dl_tech and lb_depth and check_dl(dl_tech) and check_lb(lb_depth) >= 2:
			plays_to_save.append(play['play_id'])
	return plays_to_save


def check_dl(techniques):
	valid = True
	players = techniques.split("; ")
	for player in players:
		num = int(player.split("(")[1].split(")")[0])
		if num >= 16 and num <= 24:
			valid = False
	return valid

def check_lb(depths):
	count = 0
	players = depths.split("; ")
	for player in players:
		player = player.split(" (")
		pos = player[0]
		num = int(player[1].split(")")[0])
		if pos in ["RILB", "LILB"] and num in [0, 1]:
			count += 1
	return count

def save_to_txt(output, league):
	filename = "{}_DL_LB_depth.txt".format(league)
	header = ['Play Id']
	txt_string = 'Play Ids\n'
	for playID in output:
		txt_string += str(playID) + ','

	with open(filename, 'w', newline ='') as f:
		f.write(txt_string)

mainloop()