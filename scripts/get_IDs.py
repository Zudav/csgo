from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta

# All teams that played at least minMapCount maps between start_date and end_date
minMapCount = 10
end_date = datetime.now().date()
start_date = (datetime.now() - timedelta(days=365)).date()
params = [start_date, end_date, minMapCount]

teams_url = "https://www.hltv.org/stats/teams?startDate={}&endDate={}&minMapCount={}".format(*params)
source = requests.get(teams_url).text
soup = BeautifulSoup(source, "lxml")

# Get table that contains all teams
table = soup.find("table", class_="player-ratings-table")
# Create empty list that will be filled with dicts
team_list = []
for team in table.findAll("a", href=True): # loop over all teams
    team_name = team.text
    # Get href object and split into parts
    team_id = team["href"].split("/")
    team_dict = {
        "Name": team_name.lower(),
        "ID": team_id[-2] # second item from the back contains ID
    }
    team_list.append(team_dict)

# Turn list of dicts into DataFrame
df = pd.DataFrame(team_list)

# Save as csv file
df.to_csv(r"../data/team_IDs.csv", index=False)