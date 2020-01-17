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

# Grab all team names that are part of a given group
# str, {str: str} -> listof str
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
# listof str, {str: str} -> listof listof any
def game_level_data (games, params):
    fields = ['Sacks',
              'Rushing Yards',
              'Yards per Carry',
              'Explosive Plays',
              'Red Zone Eff', 'Tite Zone Eff',
              '3rd Down Eff',
              'Havoc Rate',
              'Yards After Contact', 'Yards After Catch',
              'Missed Tackles',
              'Def Penalties',
              'Def DSSR']
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
        all_plays = r.json()['plays']
        plays = [play for play in all_plays if is_relevant_play(play)]
        row += count_sacks(plays, game[1], game[2])
        row += count_rush_yards(plays, game[1], game[2])
        row += get_ypc(plays, game[1], game[2])
        row += count_explosive_plays(plays, game[1], game[2])
        row += get_zone_efficiency(plays, game[1], game[2], 13, 25)
        row += get_zone_efficiency(plays, game[1], game[2], 1, 12)
        row += get_third_down_efficiency(plays, game[1], game[2])
        row += get_havoc_rate(plays, game[1], game[2])
        row += sum_yards_after_contact(plays, game[1], game[2])
        row += sum_yards_after_catch(plays, game[1], game[2])
        row += count_missed_tackles(plays, game[1], game[2])
        # Penalties can still be relevant for no plays
        row += sum_def_penalties(all_plays, game[1], game[2])
        row += get_def_DSSR(plays, game[1], game[2])
        
        results.append(row)
    return results

# False if they are "No Plays", special team plays, or kneels
# Useful for filtering plays
# {str: any} -> bool
def is_relevant_play(play):
    return ((play['no_play'] == 0)
            and (play['run_pass'] in ['R','P'])
            and (play['actual_poa'] != 'QB KNEEL'))

# For a list of plays and the winning team and losing team
# count the sacks for each
# listof {str: any}, str, str -> listof 4 num
def count_sacks(plays, winner, loser):
    sacks = [0, 0]
    for play in plays:
        if play['sack'] != None:
            if play['defense'] == winner:
                sacks[0] = sacks[0] + 1
            else:
                sacks[1] = sacks[1] + 1
    return get_differentials(sacks)

# For a list of plays and the winning team and losing team
# count the rushing yards for each
# listof {str: any}, str, str -> listof 4 num
def count_rush_yards(plays, winner, loser):
    rush_yards = [0, 0]
    for play in plays:
        if play['run_pass'] == 'R':
            if play['offense'] == winner:
                rush_yards[0] = rush_yards[0] + play['gain_loss_net']
            else:
                rush_yards[1] = rush_yards[1] + play['gain_loss_net']
    return get_differentials(rush_yards)

# For a list of plays and the winning team and losing team
# get the yards per carry for each
# listof {str: any}, str, str -> listof 4 num
def get_ypc(plays, winner, loser):
    carries = [0, 0]
    yards = [0, 0]
    for play in plays:
        if play['run_pass'] == 'R':
            if play['offense'] == winner:
                carries[0] = carries[0] + 1
                yards[0] = yards[0] + play['gain_loss_net']
            else:
                carries[1] = carries[1] + 1
                yards[1] = yards[1] + play['gain_loss_net']
    ypc = [round(yards[0]/carries[0], 2), round(yards[1]/carries[1], 2)]
    return get_differentials(ypc)

# For a list of plays and the winning team and losing team
# count the number of explosive plays
# listof {str: any}, str, str -> listof 4 num
def count_explosive_plays(plays, winner, loser):
    explosive_run = 10
    explosive_pass = 20
    explosive_plays = [0, 0]
    for play in plays:
        if play['run_pass'] == 'R' and play['gain_loss_net'] >= explosive_run:
            if play['offense'] == winner:
                explosive_plays[0] = explosive_plays[0] + 1
            else:
                explosive_plays[1] = explosive_plays[1] + 1
        elif play['run_pass'] == 'P' and play['gain_loss_net'] >= explosive_pass:
            if play['offense'] == winner:
                explosive_plays[0] = explosive_plays[0] + 1
            else:
                explosive_plays[1] = explosive_plays[1] + 1
    return get_differentials(explosive_plays)

# For a list of plays and the winning team and losing team
# get the percentage of times the defense gets into
# a specified zone and prevents a TD
# listof {str: any}, str, str, num, num -> listof 4 num
def get_zone_efficiency(plays, winner, loser, min_bound, max_bound):
    # We want unique drives so we'll use sets to ignore duplicates
    successful_drives = [set(), set()]
    total_drives = [set(), set()]
    for play in plays:
        if (int(play['field_position']) <= max_bound
            and int(play['field_position']) >= min_bound):
            if play['drive_end_event'] != 'TOUCHDOWN':
                # This is from the perspective of the defense
                # So touchdowns are bad
                if play['defense'] == winner:
                    successful_drives[0].add(play['drive'])
                else:
                    successful_drives[1].add(play['drive'])
            if play['defense'] == winner:
                total_drives[0].add(play['drive'])
            else:
                total_drives[1].add(play['drive'])

    # Adjust for the cases where a team never even gets there
    if len(total_drives[0]) == 0:
        successful_drives[0].add('sad')
        total_drives[0].add('sad')
    if len(total_drives[1]) == 0:
        successful_drives[1].add('sad')
        total_drives[1].add('sad')
        
    effeciencies = [round(len(successful_drives[0])/len(total_drives[0]),2),
                    round(len(successful_drives[1])/len(total_drives[1]),2)]

    return get_differentials(effeciencies)

# For a list of plays and the winning team and losing team
# get the percentage of times the defense stops 
# a third down from being converted
# listof {str: any}, str, str -> listof 4 num
def get_third_down_efficiency(plays, winner, loser):
    successful_third_downs = [0, 0]
    total_third_downs = [0, 0]
    for play in plays:
        if (play['down'] == 3):
            if play['distance'] > play['gain_loss_net']:
                # This is from the perspective of the defense
                # So conversions are bad
                if play['defense'] == winner:
                    successful_third_downs[0] += 1
                else:
                    successful_third_downs[1] += 1
            if play['defense'] == winner:
                total_third_downs[0] += 1
            else:
                total_third_downs[1] += 1

    # Adjust for the (extremely rare) cases where a team never even gets there
    if total_third_downs[0] == 0:
        successful_third_downs[0] = 1
        total_third_downs[0] = 1
    if total_third_downs[1] == 0:
        successful_third_downs[1] = 1
        total_third_downs[1] = 1
        
    effeciencies = [round(successful_third_downs[0]/total_third_downs[0],2),
                    round(successful_third_downs[1]/total_third_downs[1],2)]

    return get_differentials(effeciencies)

# For a list of plays and the winning team and losing team
# get the percentage of plays that end in a
# sack, TFL, FF, INT, or PBU
# listof {str: any}, str, str -> listof 4 num
def get_havoc_rate(plays, winner, loser):
    havoc_plays = [0, 0]
    total_plays = [0, 0]
    for play in plays:
        if play['defense'] == winner:
            team = 0
        else:
            team = 1
        if ((play['sack'] is not None)
            or (play['interception'] is not None)
            or (play['forced_fumble'] is not None)
            or (play['pass_breakup'] is not None)
            or ((play['tackle'] is not None)
                and (play['gain_loss_net'] < 0))):
            havoc_plays[team] += 1
        total_plays [team] += 1
        
    effeciencies = [round(havoc_plays[0]/total_plays[0],2),
                    round(havoc_plays[1]/total_plays[1],2)]

    return get_differentials(effeciencies)
            
# For a list of plays and the winning team and losing team
# sum the yards a runner gains after first contact
# listof {str: any}, str, str -> listof 4 num
def sum_yards_after_contact(plays, winner, loser):
    outputs = [0, 0]
    for play in plays:
        if play['offense'] == winner:
            team = 0
        else:
            team = 1
        if (play['yards_after_contact'] is not None):
            outputs[team] += play['yards_after_contact']

    return get_differentials(outputs)

# For a list of plays and the winning team and losing team
# sum the yards a runner gains after the catch
# listof {str: any}, str, str -> listof 4 num
def sum_yards_after_catch(plays, winner, loser):
    outputs = [0, 0]
    for play in plays:
        if play['offense'] == winner:
            team = 0
        else:
            team = 1
        if (play['yards_after_catch'] is not None):
            outputs[team] += play['yards_after_catch']    
    return get_differentials(outputs)

# For a list of plays and the winning team and losing team
# count the number of missed tackles the defense makes
# listof {str: any}, str, str -> listof 4 num
def count_missed_tackles(plays, winner, loser):
    outputs = [0, 0]
    for play in plays:
        if play['defense'] == winner:
            team = 0
        else:
            team = 1
        if (play['missed_tackle'] is not None):
            # If multiple tackles are missed, they will be seperated by ';'
            outputs[team] += play['missed_tackle'].count(';') + 1  
    return get_differentials(outputs)

# For a list of plays and the winning team and losing team
# sum the yards lost due to defensive penalties
# listof {str: any}, str, str -> listof 4 num
def sum_def_penalties(plays, winner, loser):
    outputs = [0, 0]
    for play in plays:
        if play['defense'] == winner:
            team = 0
        else:
            team = 1
        # For penalties, we are using all plays so must exclude special teams,
        # while other fields use a pre filtered list of plays.
        if ((play['penalty_yards'] is not None)
            and (play['run_pass'] in ['R','P'])):
            # if penalty yards are positive, they are on defense
            if (play['penalty_yards'] > 0):
                outputs[team] += play['penalty_yards']    
    return get_differentials(outputs)

# For a list of plays and the winning and losing team,
# get he percentage of 1st down series where the defense
# is able to prevent another 1st down or TD
def get_def_DSSR(plays, winner, loser):
    first_downs = [0, 0]
    drives = [0, 0]
    tds = [0, 0]

    
    for play in plays:
        if play['defense'] == winner:
            team = 0
        else:
            team = 1

        # Let's get the total number of opportunities
        if play['down'] == 1:
            first_downs[team] += 1

        # But someone of those were not earned, find how many were new drives
        if play['drive'] is not None:
            drives[team] = max(play['drive'], drives[team])

        # Also include touchdowns as successes
        if play['touchdown'] is not None:
            tds[team] += 1

    DSSRs = [0, 0]
    for team in [0, 1]:
        DSSRs[team] = 1 - round((first_downs[team] - drives[team] + tds[team])
                                / (first_downs[team]), 2)
    return get_differentials(DSSRs)

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
