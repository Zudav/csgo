from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys


# Loading ID file
# Relative file path for ID file
file_relative = r"../data/team_IDs.csv"

try:
    # Check if ID file exists
    file = Path(file_relative).resolve(strict=True)
except FileNotFoundError:
    # doesn't exist
    print("Could not find file {}".format(Path(file_relative).resolve(strict=False)))
    sys.exit(1)
else:
    # Load list with team names and corresponding IDs
    df_team_ids = pd.read_csv(file, index_col="Name")
    print("Loaded ID file from {}".format(Path(file_relative).resolve()))


# Function definitions
def get_team_id(team):
    # Use entered team name to get ID
    team_id = df_team_ids.loc[team.lower(), "ID"]
    return team_id


def current_rank(team):
    print("Getting current rank for {}".format(team))
    # Turn name into lowercase characters only
    team = team.lower()
    
    # Use entered team name to get ID
    team_id = get_team_id(team)
    
    # Turn spaces into dashes
    team_name = team.split()
    team_name = "-".join(team_name)
    
    # Get current ranking of team
    team_profile = requests.get("https://www.hltv.org/team/{}/{}".format(team_id, team_name)).text
    team_profile_soup = BeautifulSoup(team_profile, "lxml")
    team_stats = team_profile_soup.find("div", class_="profile-team-stat")
    if len(team_stats.span.text) > 1:
        current_rank = team_stats.span.text[1:] # get rid of "#" by skipping char at index 0
    else: # if len <= 1 it means the team is unranked
        current_rank = float("NaN")
    
    return current_rank


# Ask user for team name (not case sensitive)
while True:    
    try:
        entered_name = input("\nTeam Name: ")
        team_id = get_team_id(entered_name)
        
    except KeyError:
        print("Unable to find '{}' in team ID list".format(entered_name))
    
    else:
        break

# Ask for time frame in number of days into the past
while True:
    try:
        delta = int(input("Timeframe in days: "))
    except ValueError:
        print("Please enter an integer number, eg '100' (w/o quotation marks) for 100 days")
    else:
        start_date = (datetime.now()- timedelta(days=delta)).date()
        break

# Save current date as end date and get current team rank
end_date = datetime.now().date()
team_rnk_now = current_rank(entered_name)

params = [team_id, entered_name, start_date, end_date]
results_url = r"https://www.hltv.org/stats/teams/matches/{}/{}?startDate={}&endDate={}".format(*params)

print("\nRequesting url \n{}\n".format(results_url))
source = requests.get(results_url).text
soup = BeautifulSoup(source, "lxml")


# Create empty list that will be filled with dicts containing match results
results_list = []
# Create a dict that will hold current team ranks
current_ranks_dict = {entered_name: team_rnk_now}

body = soup.find("tbody")
for match in body.findAll("tr"):
    date = match.find("td", class_="time").a.text
    date = pd.to_datetime(date, format="%d/%m/%y")
    
    event = match.find("td", class_="gtSmartphone-only").a.text
    
    opponent_name = match.find("td", class_=None).a.text
    
    map_name = match.find("td", class_="statsMapPlayed").text

    match_result = match.find("td", class_="gtSmartphone-only text-center").text.split()
    team_score = int(match_result[0])
    opponent_score = int(match_result[2])
    
    if team_score > opponent_score:
        outcome = "W"
    elif team_score < opponent_score:
        outcome = "L"
    elif team_score == opponent_score:
        outcome = "D"
    else:
        outcome = None
        
    # Get current ranking of opponent team if not already done
    if opponent_name in current_ranks_dict:
        opponent_rnk_now = current_ranks_dict[opponent_name]
    else:
        opponent_rnk_now = current_rank(opponent_name)
        current_ranks_dict[opponent_name] = opponent_rnk_now
        
    # Get rankings at the time of the match
    #######
    # Note:
    # Rankings are always reassessed on mondays so I have to find the monday prior to the match date
    # I think for now I just have to assign a rank if the team is top30 and otherwise assign e.g. 100
    # In the long run I could scan all the regional ratings, get the points for each team and create a list
    # including all teams that are top30 in any given region. That's apparently what this website does:
    # https://hltvranking.y0fl0w.de/ (see information thing at the top)
    #######
    
    # Create a dict with all the relevant information
    match_results_dict = {
        "Date": date,
        "Event": event,
        "Team_Name": entered_name,
        "Outcome": outcome,
        "Opponent_Name": opponent_name,
        "Team_Score": team_score,
        "Opponent_Score": opponent_score,
        "Map": map_name,
        "Team_rnk_now": team_rnk_now,
        "Opponent_rnk_now": opponent_rnk_now
    }
    # Append dict to list of results
    results_list.append(match_results_dict)


# Create dataframe from list of dicts
df = pd.DataFrame(results_list)

# Save df as csv file
save_name = "-".join(entered_name.lower().split())
filename = "{}_{}_{}.csv".format(save_name, start_date, end_date)
save_file = Path(r"../data/{}".format(filename)).resolve()
df.to_csv(save_file, index=False)
print("\nFile saved at: \n{}".format(save_file))

