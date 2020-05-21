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
              'Def DSSR',
              'Turnovers',
              'Turnover Ratio',
              'Turnover Opportunities',
              'Passing Yards',
              'Yards per Pass Attempt',
              'Yards per Completion',
              'Pressures',
              'Run Plays',
              '1st Down Run Plays',
              '2nd Down Run Plays',
              '3rd Down Run Plays',
              '4th Down Run Plays',
              'Pass Plays',
              '1st Down Pass Plays',
              '2nd Down Pass Plays',
              '3rd Down Pass Plays',
              '4th Down Pass Plays',
              '1st Down Yards per Rush Play',
              '2nd Down Yards per Rush Play',
              '3rd Down Yards per Rush Play',
              '4th Down Yards per Rush Play',
              '1st Down Yards per Pass Play',
              '2nd Down Yards per Pass Play',
              '3rd Down Yards per Pass Play',
              '4th Down Yards per Pass Play',
              'Completion Percentage',
              '3rd Downs Faced',
              '3rd and Long Percentage',
              'Rate of Reaching Red Zone',
              'Average Endpoint on Red Zone Drives',
              '3 and Outs']
    header = ['Game ID', 'Winner', 'Loser']
    for field in fields:
        new_cols = ['Winner ' + field,
                    'Loser ' + field]
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
        row += get_zone_ppp(plays, game[1], game[2], 13, 25)
        row += get_zone_ppp(plays, game[1], game[2], 1, 12)
        row += get_third_down_efficiency(plays, game[1], game[2])
        row += get_havoc_rate(plays, game[1], game[2])
        row += sum_yards_after_contact(plays, game[1], game[2])
        row += sum_yards_after_catch(plays, game[1], game[2])
        row += count_missed_tackles(plays, game[1], game[2])
        # Penalties can still be relevant for no plays
        row += sum_def_penalties(all_plays, game[1], game[2])
        row += get_def_DSSR(plays, game[1], game[2])
        # Turnovers are special, they are now the only one that include differences
        row += get_turnovers(plays, game[1], game[2])
        row += get_turnover_opps(plays, game[1], game[2])
        row += count_pass_yards(plays, game[1], game[2])
        row += get_yards_per_attempt(plays, game[1], game[2])
        row += get_yards_per_completion(plays, game[1], game[2])
        row += count_pressures(plays, game[1], game[2])
        row += get_rush_plays(plays, game[1], game[2])
        row += get_rush_plays_down(plays, game[1], game[2], 1)
        row += get_rush_plays_down(plays, game[1], game[2], 2)
        row += get_rush_plays_down(plays, game[1], game[2], 3)
        row += get_rush_plays_down(plays, game[1], game[2], 4)
        row += get_pass_plays(plays, game[1], game[2])
        row += get_pass_plays_down(plays, game[1], game[2], 1)
        row += get_pass_plays_down(plays, game[1], game[2], 2)
        row += get_pass_plays_down(plays, game[1], game[2], 3)
        row += get_pass_plays_down(plays, game[1], game[2], 4)
        row += get_yards_per_carry_down(plays, game[1], game[2], 1)
        row += get_yards_per_carry_down(plays, game[1], game[2], 2)
        row += get_yards_per_carry_down(plays, game[1], game[2], 3)
        row += get_yards_per_carry_down(plays, game[1], game[2], 4)
        row += get_yards_per_pass_play_down(plays, game[1], game[2], 1)
        row += get_yards_per_pass_play_down(plays, game[1], game[2], 2)
        row += get_yards_per_pass_play_down(plays, game[1], game[2], 3)
        row += get_yards_per_pass_play_down(plays, game[1], game[2], 4)
        row += get_completion_pct(plays, game[1], game[2])
        row += get_third_downs(plays, game[1], game[2])
        row += get_third_and_long_pct(plays, game[1], game[2])
        row += get_drives_reaching_rz_pct(plays, game[1], game[2])
        row += get_avg_end_posn_rz(plays, game[1], game[2])
        row += get_three_and_outs(plays, game[1], game[2])
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
# listof {str: any}, str, str ->  num
def count_sacks(plays, winner, loser):
    sacks = [0, 0]
    for play in plays:
        if play['sack'] != None:
            if play['defense'] == winner:
                sacks[0] = sacks[0] + 1
            else:
                sacks[1] = sacks[1] + 1
    return sacks

# For a list of plays and the winning team and losing team
# count the rushing yards for each
# listof {str: any}, str, str -> listof 2 num
def count_rush_yards(plays, winner, loser):
    rush_yards = [0, 0]
    for play in plays:
        if play['run_pass'] == 'R':
            if play['offense'] == winner:
                rush_yards[0] = rush_yards[0] + play['gain_loss_net']
            else:
                rush_yards[1] = rush_yards[1] + play['gain_loss_net']
    return rush_yards

# For a list of plays and the winning team and losing team
# get the yards per carry for each
# listof {str: any}, str, str -> listof 2 num
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
    return ypc

# For a list of plays and the winning team and losing team
# count the number of explosive plays
# listof {str: any}, str, str -> listof 2 num
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
    return explosive_plays

# For a list of plays and the winning team and losing team
# get the points per possesion that a team is in
# a specified zone
# listof {str: any}, str, str, num, num -> listof 2 num
def get_zone_ppp(plays, winner, loser, min_bound, max_bound):
    name_to_points = {'TOUCHDOWN': 7,
                      'FIELD GOAL': 3,
                      'PUNT': 0,
                      'END OF GAME': 0,
                      'DOWNS': 0,
                      'MISSED FG': 0,
                      'FUMBLE': 0,
                      'INTERCEPTION': 0,
                      None: 0,
                      'FUMBLE-TD': -7,
                      'INTERCEPTION-TD': -7}

    # We want unique drives so we'll use sets to ignore duplicates
    point_counter = [0, 0]
    total_drives = [set(), set()]
    for play in plays:
        # If it is in the right zone
        if (int(play['field_position']) <= max_bound
            and int(play['field_position']) >= min_bound):
            # If it is new
            if (play['drive'] not in total_drives[0]
                and play['drive'] not in total_drives[1]):
                # Split based on who had the ball
                if play['offense'] == winner:
                    point_counter[0] += name_to_points[play['drive_end_event']]
                    total_drives[0].add(play['drive'])
                else:
                    point_counter[1] += name_to_points[play['drive_end_event']]
                    total_drives[1].add(play['drive'])

    # Adjust for the cases where a team never even gets there
    if len(total_drives[0]) == 0:
        total_drives[0].add('sad')
    if len(total_drives[1]) == 0:
        total_drives[1].add('sad')

    effeciencies = [round(point_counter[0]/len(total_drives[0]),2),
                    round(point_counter[1]/len(total_drives[1]),2)]

    return effeciencies

# For a list of plays and the winning team and losing team
# get the percentage of times the defense stops
# a third down from being converted
# listof {str: any}, str, str -> listof 2 num
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

    return effeciencies

# For a list of plays and the winning team and losing team
# get the percentage of plays that end in a
# sack, TFL, FF, INT, or PBU
# listof {str: any}, str, str -> listof 2 num
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

    return effeciencies

# For a list of plays and the winning team and losing team
# sum the yards a runner gains after first contact
# listof {str: any}, str, str -> listof 2 num
def sum_yards_after_contact(plays, winner, loser):
    outputs = [0, 0]
    for play in plays:
        if play['offense'] == winner:
            team = 0
        else:
            team = 1
        if (play['yards_after_contact'] is not None):
            outputs[team] += play['yards_after_contact']

    return outputs

# For a list of plays and the winning team and losing team
# sum the yards a runner gains after the catch
# listof {str: any}, str, str -> listof 2 num
def sum_yards_after_catch(plays, winner, loser):
    outputs = [0, 0]
    for play in plays:
        if play['offense'] == winner:
            team = 0
        else:
            team = 1
        if (play['yards_after_catch'] is not None):
            outputs[team] += play['yards_after_catch']
    return outputs

# For a list of plays and the winning team and losing team
# count the number of missed tackles the defense makes
# listof {str: any}, str, str -> listof 2 num
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
    return outputs

# For a list of plays and the winning team and losing team
# sum the yards lost due to defensive penalties
# listof {str: any}, str, str -> listof 2 num
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
    return outputs

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
    return DSSRs

# For a list of plays and the winning and losing team,
# get the turnovers forced by each team
def get_turnovers(plays, winner, loser):
    turnovers = [0, 0]
    for play in plays:
        if play['defense'] == winner:
            team = 0
        else:
            team = 1

        if play['interception'] is not None or play['fumble_recovery'] is not None:
            turnovers[team] += 1

    turnovers += [turnovers[0] - turnovers[1], turnovers[1] - turnovers[0]]
    return turnovers

# For a list of plays and the winning and losing team,
# get the passing yards for each team
def count_pass_yards(plays, winner, loser):
    pass_yards = [0, 0]
    for play in plays:
        if play['run_pass'] == 'P':
            if play['offense'] == winner:
                pass_yards[0] = pass_yards[0] + play['gain_loss_net']
            else:
                pass_yards[1] = pass_yards[1] + play['gain_loss_net']
    return pass_yards

# For a list of plays and the winning and losing team,
# get the yards per pass attempt for each team
def get_yards_per_attempt(plays, winner, loser):
    catches = [0, 0]
    yards = [0, 0]
    for play in plays:
        if play['run_pass'] == 'P':
            if play['offense'] == winner:
                catches[0] = catches[0] + 1
                yards[0] = yards[0] + play['gain_loss_net']
            else:
                catches[1] = catches[1] + 1
                yards[1] = yards[1] + play['gain_loss_net']
    ypc = [round(yards[0]/catches[0], 2), round(yards[1]/catches[1], 2)]
    return ypc

# For a list of plays and the winning and losing team,
# get the pressures for each team
def count_pressures(plays, winner, loser):
    pressures = [0, 0]
    for play in plays:
        if play['defense'] == winner:
            team = 0
        else:
            team = 1

        if play['sack'] is not None or play['hit_players'] is not None or play['hurry_players'] is not None:
            pressures[team] += 1

    return pressures

# For a list of plays and the winning and losing team,
# get the turnover opportunities forced by each team
def get_turnover_opps(plays, winner, loser):
    turnovers = [0, 0]
    for play in plays:
        if play['defense'] == winner:
            team = 0
        else:
            team = 1

        if play['interception'] is not None or play['forced_fumble'] is not None:
            turnovers[team] += 1

    return turnovers

# For a list of plays and the winning and losing team,
# get the yards per pass completion for each team
def get_yards_per_completion(plays, winner, loser):
    catches = [0, 0]
    yards = [0, 0]
    for play in plays:
        if play['run_pass'] == 'P' and play['pass_result'] == 'COMPLETE':
            if play['offense'] == winner:
                catches[0] = catches[0] + 1
                yards[0] = yards[0] + play['gain_loss_net']
            else:
                catches[1] = catches[1] + 1
                yards[1] = yards[1] + play['gain_loss_net']
    ypc = [round(yards[0]/catches[0], 2), round(yards[1]/catches[1], 2)]
    return ypc

# For a list of plays and the winning and losing team,
# get the number of rushing plays by each team
def get_rush_plays(plays, winner, loser):
    rush_plays = [0, 0]
    for play in plays:
        if play['run_pass'] == 'R':
            if play['offense'] == winner:
                rush_plays[0] += 1
            else:
                rush_plays[1] += 1
    return rush_plays

# For a list of plays and the winning and losing team,
# get the number of rushing plays by each team on a specific down
def get_rush_plays_down(plays, winner, loser, down):
    rush_plays = [0, 0]
    for play in plays:
        if play['run_pass'] == 'R' and play['down'] == down:
            if play['offense'] == winner:
                rush_plays[0] += 1
            else:
                rush_plays[1] += 1
    return rush_plays

# For a list of plays and the winning and losing team,
# get the number of passing plays by each team
def get_pass_plays(plays, winner, loser):
    pass_plays = [0, 0]
    for play in plays:
        if play['run_pass'] == 'P':
            if play['offense'] == winner:
                pass_plays[0] += 1
            else:
                pass_plays[1] += 1
    return pass_plays

# For a list of plays and the winning and losing team,
# get the number of passing plays by each team on a specific down
def get_pass_plays_down(plays, winner, loser, down):
    pass_plays = [0, 0]
    for play in plays:
        if play['run_pass'] == 'R' and play['down'] == down:
            if play['offense'] == winner:
                pass_plays[0] += 1
            else:
                pass_plays[1] += 1
    return pass_plays

# For a list of plays and the winning and losing team,
# get the yards per rushing play on a specific down
def get_yards_per_carry_down(plays, winner, loser, down):
    carries = [0, 0]
    yards = [0, 0]
    for play in plays:
        if play['run_pass'] == 'R' and play['down'] == down:
            if play['offense'] == winner:
                carries[0] = carries[0] + 1
                yards[0] = yards[0] + play['gain_loss_net']
            else:
                carries[1] = carries[1] + 1
                yards[1] = yards[1] + play['gain_loss_net']
    ypc = [0, 0]
    if carries[0] != 0:
        ypc[0] = round(yards[0]/carries[0], 2)
    if carries[1] != 0:
        ypc[1] = round(yards[1]/carries[1], 2)
    return ypc

def get_yards_per_pass_play_down(plays, winner, loser, down):
    catches = [0, 0]
    yards = [0, 0]
    for play in plays:
        if play['run_pass'] == 'P' and play['down'] == down:
            if play['offense'] == winner:
                catches[0] = catches[0] + 1
                yards[0] = yards[0] + play['gain_loss_net']
            else:
                catches[1] = catches[1] + 1
                yards[1] = yards[1] + play['gain_loss_net']
    ypc = [0, 0]
    if catches[0] != 0:
        ypc[0] = round(yards[0]/catches[0], 2)
    if catches[1] != 0:
        ypc[1] = round(yards[1]/catches[1], 2)
    return ypc

def get_completion_pct(plays, winner, loser):
    passes = [0, 0]
    completions = [0, 0]
    for play in plays:
        if play['run_pass'] == 'P':
            if play['offense'] == winner:
                passes[0] += 1
            else:
                passes[1] += 1
            if play['pass_result'] == 'COMPLETE':
                if play['offense'] == winner:
                    completions[0] += 1
                else:
                    completions[1] += 1
    completion_pct = [round(completions[0]/passes[0], 2), round(completions[1]/passes[1], 2)]
    return completion_pct

def get_third_downs(plays, winner, loser):
    third_downs = [0, 0]
    for play in plays:
        if play['defense'] == winner:
            if play['down'] == 3:
                third_downs[0] += 1
        else:
            if play['down'] == 3:
                third_downs[1] += 1
    return third_downs

def get_third_and_long_pct(plays, winner, loser):
    third_downs = get_third_downs(plays, winner, loser)
    third_and_long = [0, 0]
    for play in plays:
        if play['down'] == 3 and play['distance'] >= 5:
            if play['defense'] == winner:
                third_and_long[0] += 1
            else:
                third_and_long[1] += 1
    third_and_long_pct = [round(third_and_long[0]/third_downs[0], 2), round(third_and_long[1]/third_downs[1], 2)]
    return third_and_long_pct

def get_drives_reaching_rz_pct(plays, winner, loser):
    total_drives = [set(), set()]
    drives_reaching_rz = [set(), set()]
    for play in plays:
        if play['drive'] not in total_drives[0] and play['drive'] not in total_drives[1]:
            if play['defense'] == winner:
                total_drives[0].add(play['drive'])
            else:
                total_drives[1].add(play['drive'])
            field_posn = play['drive_end_field_position']
            if field_posn == None:
                pass
            elif field_posn[0] == "+":
                field_posn = int(field_posn[1:])
                if field_posn >= 0 and field_posn <= 20:
                    if play['defense'] == winner:
                        drives_reaching_rz[0].add(play['drive'])
                    else:
                        drives_reaching_rz[1].add(play['drive'])
    for i in [0, 1]:
        if len(total_drives[i]) == 0:
            total_drives[i].add('sad')
    rates = [round(len(drives_reaching_rz[0])/len(total_drives[0]),2), round(len(drives_reaching_rz[1])/len(total_drives[1]), 2)]
    return rates

def get_avg_end_posn_rz(plays, winner, loser):
    total_end_posn = [0, 0]
    total_drives = [set(), set()]
    for play in plays:
        if play['drive'] not in total_drives[0] and play['drive'] not in total_drives[1]:
            field_posn = play['drive_end_field_position']
            if field_posn == None:
                pass
            elif field_posn[0] == "+":
                field_posn = int(field_posn[1:])
                if field_posn >= 0 and field_posn <= 20:
                    if play['defense'] == winner:
                        total_drives[0].add(play['drive'])
                        total_end_posn[0] += field_posn
                    else:
                        total_drives[1].add(play['drive'])
                        total_end_posn[1] += field_posn
    for i in [0, 1]:
        if len(total_drives[i]) == 0:
            total_drives[i].add('sad')
    rates = [round(total_end_posn[0]/len(total_drives[0]), 2), round(total_end_posn[1]/len(total_drives[1]), 2)]
    return rates

def get_three_and_outs(plays, winner, loser):
    three_and_out_drives = [set(), set()]
    total_drives = [set(), set()]
    for play in plays:
        if play['drive'] not in total_drives[0] and play['drive'] not in total_drives[1]:
            if play['defense'] == winner:
                total_drives[0].add(play['drive'])
            else:
                total_drives[1].add(play['drive'])
            if play['drive_end_play_number'] == 4 and play['drive_end_event'] == "PUNT":
                if play['defense'] == winner:
                    three_and_out_drives[0].add(play['drive'])
                else:
                    three_and_out_drives[1].add(play['drive'])

    return [len(three_and_out_drives[0]), len(three_and_out_drives[1])]

mainloop()
