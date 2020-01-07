import requests
import csv
import sys

# When given an api-key, make a csv of all 2019 B1G games
# Providing game level detail
# string -> csv
def mainloop():
    args = sys.argv
    key = args[1]
    
    params = get_params(key)
    teams = get_teams("Big Ten", params)
    games = get_games(teams, params)
    output = game_level_data(games, params)

    with open('game_level_results.csv', 'w', newline ='') as f:
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

def get_teams (name, params):
    teams = []
    r = requests.get('https://api.profootballfocus.com/v1/ncaa/2019/teams', headers = params)
    for team in r.json()['teams']:
        for group in team['groups']:
            if group['name'] == name:
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
            if game['season'] == 2019:
                if game['away_team_score'] > game['home_team_score']:
                    winner = game['away_team']
                    loser = game['home_team']
                else:
                    loser = game['away_team']
                    winner = game['home_team']
                games.append([str(game['id']),winner,loser])
    return games

# For a list of games, return game level data for each
# listof str, str -> {listof str}
def game_level_data (games, params):
    fields = ["Sacks"]
    header = ['Game ID', 'Winner', 'Loser']
    for field in fields:
        new_cols = ['Winner ' + field,
                    'Loser ' + field,
                    'Winner ' + field + ' Dif',
                    'Loser ' + field + ' Dif']
        header += new_cols
    results = [header]
    
    for game in games:
        row = game
        r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game[0]+'/plays', headers = params)
        plays = r.json()['plays']
        row += count_sacks(plays, game[1], game[2])
        results.append(row)
    return results

# For a list of plays and the winning team and losing team
# count the sacks for each
def count_sacks(plays, winner, loser):
    sacks = [0, 0]
    for play in plays:
        if play['pass_result'] == 'SACK':
            if play['defense'] == winner:
                sacks[0] = sacks[0] + 1
            else:
                sacks[1] = sacks[1] + 1
    return get_differentials(sacks)

# For a list of two items, calculate
# the first minus the second and the second minus the first
# then append those to the original list and return the list of four
# listof 2 num -> listof 4 num
def get_differentials(pair):
    quartet = pair
    quartet.append(pair[0] - pair[1])
    quartet.append(pair[1] - pair[0])
    return quartet
mainloop()
