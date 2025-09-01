from nba_api.stats.library.http import NBAStatsHTTP
from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime

NBAStatsHTTP._NBAStatsHTTP__HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
    'Connection': 'keep-alive'
}

startTimes = {}

def fetch_games():
    today = datetime.now().strftime('%Y-%m-%d')
    sb = scoreboardv2.ScoreboardV2(game_date=today)
    frames = sb.get_data_frames()
    return frames[0]

while True:
    games = fetch_games()
    for _, game in games.iterrows():
        game_id = game['GAME_ID']
        game_status = game['GAME_STATUS_TEXT']
        if game_id not in startTimes and game_status == "In Progress":
            startTimes[game_id] = datetime.now()
        elif game_id in startTimes and game_status == "Delayed":
            delay_duration = (datetime.now() - startTimes[game_id]).total_seconds() / 60
    # Sleep for a minute before polling again
    import time
    time.sleep(60) # Poll every 60s 