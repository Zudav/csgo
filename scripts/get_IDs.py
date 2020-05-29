from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# All teams that played at least minMapCount maps between start_date and end_date
minMapCount = 10
end_date = datetime.now().date()
start_date = (datetime.now() - timedelta(days=365)).date()
params = [start_date, end_date, minMapCount]

teams_url = "https://www.hltv.org/stats/teams?startDate={}&endDate={}&minMapCount={}".format(*params)
print("Requesting url \n{}\n".format(teams_url))
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
    team_id = team_id[-2] # second to last element is ID
    team_dict = {
        "Name": team_name.lower(),
        "ID": team_id # second item from the back contains ID
    }
    print("{}:\t {}".format(team_id, team_name)) 
    team_list.append(team_dict)

# Turn list of dicts into DataFrame
df = pd.DataFrame(team_list)

print("\nFilter:\nAt least {} maps played between {} and {}".format(minMapCount, start_date, end_date))
print("\nNumber of teams found: {}".format(len(df["ID"])))


# Create "../data/" folder in case it doesn't exist
folder_path = Path(r"../data/").resolve()
if not folder_path.is_dir():
    print("\nCreated the following directory: \n{}".format(folder_path))
    folder_path.mkdir()

# Save csv file
file = Path(folder_path, "team_IDs.csv").resolve()
df.to_csv(file, index=False)
print("\nFile saved at: \n{}".format(file))