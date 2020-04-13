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
    #teams = get_teams(["ACC"], params)
    teams = ["MABC"]
    games = get_games(teams, params)
    output = route_level_data(games, params)

    #return output
    with open('Routes.csv', 'w', newline ='') as f:
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
        if game['away_team'] in opponents or game['home_team'] in opponents:
            if game['season'] >= 2019:
                games.append(str(game['id']))
    return games

# For a list of games, return game level data for each
# listof str, {str: str} -> listof listof any
def route_level_data (games, params):
    header = ['Play Id',
              '#',
              'Formation Group',
              'Motion',
              'Pass Reciever Position Target',
              'pass_pattern']
    receiver_headers = ['Position', 'Side', 'Route Conversion', 'Depth']

    for i in range (1,6):
        header += [x + " - " + str(i) for x in receiver_headers]

    results = [header]

    counter = 0
    bad_counter = 0
    for game in games:
        print(game)
        r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params)
        plays = r.json()['plays']
        for play in plays:
            if play['pass_pattern'] is None:
                continue
            if play['offense'] != 'MABC':
                continue
            counter += 1
            row = [play['play_id'],
                   counter,
                   play['offensive_formation_group'],
                   play['shift_motion'],
                   play['pass_receiver_target_position'],
                   play['pass_pattern']]
            players = play['pass_pattern'].split('; ')
            for player in players:
                row += process_player(player)
            results += [row]
    return results

# Reformat
# str -> listof 4 str
def process_player(code):
    output = ['','','','']
    code = code.replace('(',' ')
    code = code.replace(')',' ')
    code = code + " -" # If we don't have depth add this as filler
    parts = code.split(' ')

    # Get the player position and what side of the ball they were on
    for position in ['WR', 'QB', 'TE', 'HB', 'FB']:
        if position in parts[0]:
            output[0] = position # maybe this should be parts[0] instead?
            side = parts[0].replace(position,'')
            if 'L' in side:
                output[1] = 'L'
            if 'R' in side:
                output[1] = 'R'
            if 'L' in side and 'R' in side:
                output[1] = ''

    
    # Remove blocking modifiers
    for route in ROUTE_INFO:
        if route['pff_PASSROUTE'] in parts[1] and route['Route Group'] == 'Modifiers':
            parts[1] = parts[1].replace(route['pff_PASSROUTE'],'')
            output[2] = "Block" # Note this may be overwritten later if it was a block into route
    
    # Translate the name
    for route in ROUTE_INFO:
        if (route['pff_PASSROUTE'] == parts[1]):
            output[2] = route['pff_PASSROUTENAME']
            break
        elif (route['pff_PASSROUTE'] + 'i' == parts[1] or route['pff_PASSROUTE'] + 'o' == parts[1]):
            output[2] = route['pff_PASSROUTENAME']
            break

    # Take the depth as is
    output[3] = parts[2]
    return output

with open('routeguide.csv',newline='') as csvfile:
	reader = csv.DictReader(csvfile)
	ROUTE_INFO = list(reader)
	
mainloop()
            
