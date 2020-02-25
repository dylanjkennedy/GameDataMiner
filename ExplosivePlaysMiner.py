import requests
import csv
import sys
import os

# When given an api-key, make a csv of all 2019 B1G games
# Providing game level detail
# string -> csv
def mainloop():
    args = sys.argv
    key = os.environ['PFF_API_KEY']

    params = get_params(key)
    teams = get_teams(["Big Ten"], params)
    games = get_games(teams, params)
    output = play_level_data(games, params)

    #return output
    with open('all_gainloss.csv', 'w', newline ='') as f:
        writer = csv.writer(f)
        writer.writerows(output)

# Turn an api key into a jwt key and format as header
# str -> {str: str}
def get_params (key):
    params = {'x-api-key':key}
    r = requests.post('https://api.profootballfocus.com/auth/login', headers = params)
    jwt = r.json()['jwt']
    params = {'Authorization':'Bearer ' + jwt}
    return params

# Grab all team names that are part of a given group
# str, {str: str} -> listof str
def get_teams (names, params):
    teams = []
    r = requests.get('https://api.profootballfocus.com/v1/ncaa/2019/teams', headers = params)
    for team in r.json()['teams']:
        for group in team['groups']:
            if group['name'] in names:
                teams.append(team['gsis_abbreviation'])
    return teams

# For B1G opponents, return all game ids in which they played in 2019
# And report the id first, then winning team, then the losing team
# str, {str: str} -> listof str
def get_games (opponents, params):
    r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games', headers = params)

    games = []
    for game in r.json()['games']:
        if game['away_team'] in opponents and game['home_team'] in opponents:
            if game['season'] >= 2015:
                if game['away_team_score'] > game['home_team_score']:
                    winner = game['away_team']
                    loser = game['home_team']
                else:
                    loser = game['away_team']
                    winner = game['home_team']
                games.append([str(game['id']),winner,loser])
    return games

# For a list of games, return game level data for each
# listof str, {str: str} -> listof listof any
def play_level_data (games, params):
    header = ['Play Id',
              'Game ID',
              'Winner',
              'Loser',
              'Offense',
              'Run/Pass',
              'Sack',
              'Penalty',
              'Gain/Loss']
    results = [header]

    for game in games:
        print(game)
        r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game[0]+'/plays', headers = params)
        plays = r.json()['plays']
        for play in plays:
            results += [[play['play_id'],
                         play['game_id'],
                         game[1],
                         game[2],
                         play['offense'],
                         play['run_pass'],
                         play['sack'],
                         play['penalty'],
                         play['gain_loss']]]
    return results

a = mainloop()
            
