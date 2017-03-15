from pytba import api as tba
import gspread

tba.set_api_key("Austin Zhang", "1072bot ", "1.0")
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name('M3R-CY-cc50ee93eb23.json', scope)
gc = gspread.authorize(credentials)
sht1 = gc.open_by_key('1V040FdlW0F2X17aI-Bz3-SzSleTa4v_Ql-dRejrzLYA')
worksheet = sht1.get_worksheet(0)
# def get_coords(x):
#     print(str(x) + ": " + str(x % 10) + "," + str(x // 10))
#
#
# def get_ac(x, y):
#     print(y * 10 + x)

start_y = 0
def ret(col,num):
    return col + str(num)
def decompose(matches):
    match_start = ret("C",70)
    match_end = ret("C",427)
    range = match_start + ":" + match_end
    print(range)
    match_cells = worksheet.range(range)
    x=0
    for cell in match_cells:
        row = cell.row
        col = cell.col
        team_num = worksheet.cell(row, col).value
        nick = tba.team_get(team_num)["nickname"]
        worksheet.update_cell(row, col+1, nick)

    worksheet.update_cells(match_cells)





    pass
    # match_list = [match["match_number"], ]



asdf = {'comp_level': 'qm', 'match_number': 1, 'videos': [], 'time_string': None, 'set_number': 1,
        'key': '2017cama_qm1', 'time': 1489251600, 'score_breakdown': {
        'blue': {'teleopPoints': 80, 'robot3Auto': 'Mobility', 'rotor1Auto': True, 'autoPoints': 75,
                 'rotor1Engaged': True, 'foulCount': 0, 'touchpadFar': 'None', 'foulPoints': 5, 'techFoulCount': 1,
                 'totalPoints': 160, 'tba_rpEarned': 0, 'autoRotorPoints': 60, 'adjustPoints': 0,
                 'robot1Auto': 'Mobility', 'rotor2Auto': False, 'rotor4Engaged': False, 'teleopRotorPoints': 80,
                 'autoFuelHigh': 0, 'teleopFuelHigh': 0, 'teleopTakeoffPoints': 0, 'robot2Auto': 'Mobility',
                 'kPaRankingPointAchieved': False, 'autoFuelLow': 0, 'teleopFuelLow': 0, 'rotorBonusPoints': 0,
                 'autoMobilityPoints': 15, 'rotor3Engaged': True, 'autoFuelPoints': 0, 'teleopFuelPoints': 0,
                 'touchpadMiddle': 'None', 'touchpadNear': 'None', 'rotorRankingPointAchieved': False,
                 'kPaBonusPoints': 0, 'rotor2Engaged': True},
        'red': {'teleopPoints': 130, 'robot3Auto': 'Mobility', 'rotor1Auto': False, 'autoPoints': 10,
                'rotor1Engaged': True, 'foulCount': 1, 'touchpadFar': 'ReadyForTakeoff', 'foulPoints': 25,
                'techFoulCount': 0, 'totalPoints': 165, 'tba_rpEarned': 2, 'autoRotorPoints': 0, 'adjustPoints': 0,
                'robot1Auto': 'Mobility', 'rotor2Auto': False, 'rotor4Engaged': False, 'teleopRotorPoints': 80,
                'autoFuelHigh': 0, 'teleopFuelHigh': 1, 'teleopTakeoffPoints': 50, 'robot2Auto': 'None',
                'kPaRankingPointAchieved': False, 'autoFuelLow': 0, 'teleopFuelLow': 0, 'rotorBonusPoints': 0,
                'autoMobilityPoints': 10, 'rotor3Engaged': False, 'autoFuelPoints': 0, 'teleopFuelPoints': 0,
                'touchpadMiddle': 'None', 'touchpadNear': 'None', 'rotorRankingPointAchieved': False,
                'kPaBonusPoints': 0, 'rotor2Engaged': True}},
        'alliances': {'blue': {'surrogates': [], 'score': 160, 'teams': ['frc4255', 'frc294', 'frc5817']},
                      'red': {'surrogates': [], 'score': 165, 'teams': ['frc2643', 'frc5134', 'frc6699']}},
        'event_key': '2017cama'}

event = tba.event_get("2017cama")
matches = event.matches

decompose(matches)

print(matches)
