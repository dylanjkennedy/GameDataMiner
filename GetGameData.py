import requests
import csv
import sys
import os

def mainloop():
    # no arguments - fetch key from os

    key = os.environ['PFF_API_KEY']

    team = "MDUN"

    params = get_params(key)

    games = get_games(team, params)

    output = game_data(games, team, params)

    with open('{}_games_2019.csv'.format(team), 'w', newline='') as f:
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
                games.append(game)
    return games

def game_data(games, team, params):
    fields = ["Week", "Start", "Home Team", "Away Team"]
    results = [fields]
    for game in games:
        results.append([game['week'], game['start'], game['home_team'], game['away_team']])
    results = sorted(results, key = lambda game: game[1], reverse=True)
    return results

mainloop()