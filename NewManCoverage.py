import requests
import sys
import os

def mainloop():
    key = os.environ['PFF_API_KEY']

    team = sys.argv[1]

    params = get_params(key)

    games = get_games(team, params)
    
    plays = get_plays(games, team, params)
    
    output = manCoverage(plays)
    
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
        r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params)
        for play in r.json()['plays']:
            if play['defense'] == team:
                if str(play['pass_coverage']) in ['2M', '0', '1', '1D']:
                    plays.append(play)
    return plays

def manCoverage(plays):
	play_ids = []
	non_routes = ["k", "n", "h0", "h1", "ff", "z", "0"]
	for play in plays:
		positions = ["HB", "HB-R", "HB-iR", "HB-oR", "HB-L", "HB-iL", "HB-oL"]
		oddity = parse_oddity(play)
		for o in oddity:
			positions.append(o)
		routes = fetch_routes(play, positions)
		for pos in routes:
			route = routes[pos]
			if not any(map(lambda s: s in route, non_routes)) and route != "r" and route != "fl" and route != "fr":
				play_ids.append(str(play['play_id']))
	return play_ids


def fetch_routes(play, positions):
	routes = {}
	if play['pass_pattern'] is None:
		return routes
	pass_pattern = play['pass_pattern'].split('; ')
	for receiver in pass_pattern:
		receiver = receiver.split(' ')
		if receiver[0] in positions:
			routes[receiver[0]] = receiver[1]
	return routes

def parse_oddity(play):
	oddity = play['offensive_oddities']
	if oddity == None:
		return []
	else:
		positions = []
		oddities = oddity.split('; ')
		for o in oddities:
			pos = o.split('>')
			if pos[0] in ["HB", "HB-R", "HB-iR", "HB-oR", "HB-L", "HB-iL", "HB-oL"]:
				positions.append(pos[1])
		return positions

def save_to_txt(output, team):
    filename = "{}_Man_Coverage.txt".format(team)
    txt_string = ','.join(output)

    with open(filename, 'w', newline ='') as f:
        f.write(txt_string)

mainloop()
