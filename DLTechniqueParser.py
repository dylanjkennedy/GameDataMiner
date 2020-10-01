import requests
import csv
import os
import sys

## DL techniques

## Given play ID, get quarter, down, distance, time, and the 3-6 players on the DL

def mainloop():
    # no arguments - fetch key from os

    key = os.environ['PFF_API_KEY']

    params = get_params(key)

    games = get_games(params)

    output = dl_tech_data(games, params)

    with open('dl_techniques.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(output)

# Turn an api key into a jwt key and format as header
# str -> {str: str}
def get_params(key):
    params = {'x-api-key':key}
    r = requests.post('https://api.profootballfocus.com/auth/login', headers = params)
    jwt = r.json()['jwt']
    params = {'Authorization':'Bearer ' + jwt}
    return params

def get_play_ids():
    play_ids = []
    with open('play_ids.csv') as play_ids_file:
        for row in csv.reader(play_ids_file):
            play_ids.append(row[0])
    return play_ids[1:]

def get_games(params):
    teams = ['MDUN','LATU']
    r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games', headers=params)
    games = []
    for game in r.json()['games']:
        if game['season'] == 2019:
            if game['away_team'] in teams or game['home_team'] in teams:
                games.append(str(game['id']))
    return games

def find_play(plays, play_id):
    for play in plays:
        if play['play_id'] == play_id:
            return play

def dl_tech_data(games, params):
    play_ids = get_play_ids()
    play_ids = list(map(int, play_ids))
    plays = []
    plays2 = []
    fields = ['Play ID', 'Quarter', 'Down', 'Clock', 'Distance', 'DL1', 'DL2', 'DL3', 'DL4', 'DL5', 'DL6']
    results = [fields]

    # for each game - find which plays in play_ids are from that game
    for game in games:
        r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params) # all the plays from the game
        for play in r.json()['plays']:
            plays.append(play)

    for play_id in play_ids:
        plays2.append(find_play(plays, play_id))

    plays = plays2

    for play in plays:
        row = [play['play_id']]
        row.append(play['quarter'])
        row.append(play['down'])
        row.append(play['clock'])
        row.append(play['distance'])
        dl_players = get_dl_players(play)
        dl_players = list(map(int, dl_players))
        while len(dl_players) < 6:
            dl_players.append(None)
        for player in dl_players:
            row.append(player)
        results.append(row)
    return results

def get_dl_players(play):
    dl_formation = play['dl_techniques']
    if dl_formation is None:
        print(play['play_id'])
        return []
    dl_formation = dl_formation.split('(')[1:]
    for i in range(len(dl_formation)):
        dl_formation[i] = dl_formation[i][:2]
    return dl_formation

mainloop()