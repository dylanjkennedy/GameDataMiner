import requests
import csv
import sys
import os

def mainloop():
    # no arguments - fetch key from os

    key = os.environ['PFF_API_KEY']

    team = sys.argv[1]

    params = get_params(key)

    games = get_games(team, params)

    output = game_data(games, team, params)

    with open('one_season.csv', 'w', newline='') as f:
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
        if game['season'] >= 2020:
            if game['away_team'] == team or game['home_team'] == team:
                games.append(str(game['id']))
    return games

def game_data(games, team, params):
    plays = []
    for game in games:
        r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params) # all the plays from the game
        for play in r.json()['plays']:
            plays.append(play)
    fields = ["Game Date", "Team", "Drive", "Drive Play", "Down", "Field Pos", "Drive End Play #", "Drive End Field Pos", "Drive End Event", "Run/Pass", "Gain/Loss", "Pass Result", "Garbage Time", "NoPlay", "Penalty", "Sack"]
    results = [fields]
    for play in plays:
        results.append([play['game_date'], play["offense"], play['drive'], play['drive_play'], play['down'], play['field_position'], play['drive_end_play_number'], play['drive_end_field_position'], play["drive_end_event"], play['run_pass'], play['gain_loss'], play['pass_result'], play['garbage_time'], play['no_play'], play['penalty'], play['sack']])
    return results

mainloop()