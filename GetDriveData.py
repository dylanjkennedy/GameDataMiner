import requests
import csv
import sys
import os

def mainloop():
    # no arguments - fetch key from os

    key = os.environ['PFF_API_KEY']

    team = sys.argv[1]

    side = sys.argv[2]

    params = get_params(key)

    games = get_games(team, params)

    drives = []

    for game in games:
    	plays = get_plays(game, params)
    	drives += plays_to_drives(plays, team, side)

    output = drive_level_data(drives)

    output = [output[0]] + sorted(output[1:], key = lambda x: x[1])

    with open('drive_level_data/{}_{}_drive_level_data.csv'.format(team, side), 'w', newline='') as f:
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
        if game['season'] >= 2018:
            if game['away_team'] == team or game['home_team'] == team:
                games.append(str(game['id']))
    return games

def get_plays(game, params):
	plays = []
	r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params) # all the plays from the game
	for play in r.json()['plays']:
		plays.append(play)
	return plays

def plays_to_drives(plays, team, side):
	team_drives = [""]
	opp_drives = [""]
	for i in range(25):
		team_drives.append([])
		opp_drives.append([])
	for play in plays:
		if play["drive"]:
			drive = play["drive"]
			offense = play["offense"]
			if offense == team:
				team_drives[drive].append(play)
			else:
				opp_drives[drive].append(play)

	if side == "offense":
		return team_drives[1:]
	else:
		return opp_drives[1:]

def drive_level_data(drives):
	fields = ['Season',
			  'Game Date',
			  'Offense',
			  'Defense',
			  'Drive #',
			  'Starting Field Position',
			  'Ending Field Position',
			  'Play Count',
			  'Total Yards',
			  'TD Indicator',
			  'Score Indicator',
			  'Attempted FG Indicator',
			  'Turnover on Downs Indicator',
			  'Turnover Indicator',
			  'Garbage Time Indicator',
			  'Red Zone Indicator',
			  'Tite Zone Indicator',
			  'Goal Line Indicator',
			  'Explosive Plays',
			  'Offensive Penalties',
			  'Defensive Penalties',
			  'First Downs',
			  'Sacks']
			  # 'Negative Plays']
	results = [fields]

	for drive in drives:
		row = []
		if drive == []:
			continue
		row.append(drive[0]['season'])
		row.append(drive[0]['game_date'])
		row.append(drive[0]['offense'])
		row.append(drive[0]['defense'])
		row.append(drive[0]['drive'])
		row.append(drive[0]['drive_start_field_position'])
		row.append(drive[0]['drive_end_field_position'])
		row.append(get_playcount(drive))
		row.append(get_totalyards(drive))
		driveEndEvent = drive[0]['drive_end_event']
		row.append(convert(driveEndEvent == "TOUCHDOWN"))
		row.append(convert(driveEndEvent in ["TOUCHDOWN", "FIELD GOAL"]))
		row.append(convert(driveEndEvent in ["FIELD GOAL", "MISSED FG"]))
		row.append(convert(driveEndEvent == "DOWNS"))
		row.append(convert(driveEndEvent in ["FUMBLE", "INTERCEPTION"]))
		row.append(convert(get_garbagetime(drive)))
		row.append(convert(get_zone(drive, 25, 11)))
		row.append(convert(get_zone(drive, 10, 4)))
		row.append(convert(get_zone(drive, 3, 1)))
		row.append(get_explosive_plays(drive))
		row.append(get_penalties(drive, "offense"))
		row.append(get_penalties(drive, "defense"))
		row.append(get_first_downs(drive))
		row.append(get_sacks(drive))
		#row.append(get_negative_plays(drive))

		results.append(row)
	return results

def convert(bool): # turns true/false into 1/0
	if bool:
		return 1
	else:
		return 0

def get_playcount(drive): # counts all plays (except no plays) in a drive
	count = 0
	no_plays = 0
	for play in drive:
		count += 1
		no_plays += play['no_play']

	return count - no_plays

def get_totalyards(drive): # gets total yards advanced in a drive
	start = int(drive[0]['drive_start_field_position'])
	end = int(drive[0]['drive_end_field_position'])
	if start < 0:
		start += 100
	if end < 0:
		end += 100
	return start - end

def get_garbagetime(drive): # returns true if any plays in drive are during garbage time
	garbagetime = False
	for play in drive:
		if play['garbage_time']:
			garbagetime = True
	return garbagetime

def get_zone(drive, start, end): # returns true if any plays in drive snap from between start and end
	zone = False
	for play in drive:
		if int(play['field_position']) <= start and int(play['field_position']) >= end:
			zone = True
	return zone

def get_explosive_plays(drive): # counts explosive plays (12+ yards for a run, 16+ yards for a pass)
	explosive_plays = 0
	for play in drive:
		if play['run_pass'] == "R" and play['gain_loss'] and play['gain_loss'] >= 12:
			explosive_plays += 1
		elif play['run_pass'] == "P" and play['pass_result'] == "RUN" and play['gain_loss'] and play['gain_loss'] >= 12:
			explosive_plays += 1
		elif play['run_pass'] == "P" and play['gain_loss'] and play['gain_loss'] >= 16:
			explosive_plays += 1
	return explosive_plays

def get_negative_plays(drive): # counts plays with negative yardage
	neg_plays = 0
	for play in drive:
		if play['gain_loss'] and play['gain_loss'] < 0:
			neg_plays += 1
	return neg_plays

def get_penalties(drive, side): # counts penalties
	penalties = 0
	for play in drive:
		if play['penalty']:
			penalty = play['penalty'].split(" ")
			if penalty[0] == play[side]:
				penalties += 1
			elif penalty[0] != "" and penalty[0][0] != "(":
				if side == "offense" and play['penalty_yards'] < 0:
					penalties += 1
				elif side == "defense" and play['penalty_yards'] > 0:
					penalties += 1
	return penalties

def get_first_downs(drive):
	first_downs = -1
	for play in drive:
		if play['down'] == 1:
			first_downs += 1
	return first_downs

def get_sacks(drive):
	sacks = 0
	for play in drive:
		if play['sack']:
			sacks += 1
	return sacks

mainloop()