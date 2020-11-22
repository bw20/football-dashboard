import pandas as pd
import numpy as np
import re

class FootballData(object):
    def __init__(self, start_season, end_season):
        self.start_season = start_season
        self.end_season = end_season
    def create_df(self):
        def seasons_dictionary(starting_decade, ending_decade):
            #Create a dictionary with the decades and seasons for each dataset.
            eng = 'https://github.com/bw20/football-dashboard/tree/main/england-master'
            seasons = {}
            for i in range(int(abs((starting_decade - ending_decade)/10)) + 1):
                decade = starting_decade
                decade_string = str(decade) + 's'
                list_of_seasons = []
                for i in range(10):
                    season = str(decade + i) + '-' + str(decade + i + 1)[2:4]
                    list_of_seasons.append(season)
                    seasons[decade_string] = list_of_seasons
                starting_decade += 10
            df_dictionary = {}
            for decade in seasons:
                for season in seasons[decade]:
                    path = eng + '/' + decade + '/' + season + '/eng.1.csv'
                    df_name = 'df_eng_' + season
                    df_dictionary[df_name] = path
            return df_dictionary
        df_dictionary = seasons_dictionary(1880, 2010)
        df_list = []
        seasons_list = []
        #Identify the index of the starting season and ending season specified
        start_index = list(df_dictionary.keys()).index('df_eng_' + self.start_season)
        end_index = (list(df_dictionary.keys()).index('df_eng_' + self.end_season)) + 1
        #Iterate through these indices to populate the seasons_list with the desired keys for seasons_dictionary
        for i in range(start_index, end_index):
            season_key = list(df_dictionary.keys())[i]
            seasons_list.append(season_key)
        #Use the keys in seasons_list to fetch the paths to each season, and reading them in to a list of dfs in df_list
        for i in df_dictionary:
            if i in seasons_list:
                try:
                    season = re.findall(r'\d\d\d\d-\d\d', i)[0]
                    df = pd.read_csv(df_dictionary[i], index_col=None, header=0, sep='delimiter')
                    df['Season'] = season
                    df_list.append(df)
                except FileNotFoundError:#This exception accommodates the fact that data is not available for all years - for example, seasons that were not played due to WW1 and WW2.
                    continue
        #Finally, merge the dfs in df_list into a single df
        df = pd.concat(df_list, axis =0, ignore_index=True)
        FT_score_list = df['FT'].map(lambda FT: re.findall(r'\d+', FT)) #This converts the string '2-1' to a list [2,1]
        HT_score_list = df['HT'].map(lambda HT: re.findall(r'\d+', HT))
        df['Total goals'] = FT_score_list.map(lambda goals: int(goals[0]) + int(goals[1]))
        df['Home goals'] = FT_score_list.map(lambda goals: int(goals[0])) #note the use of the map() - it seems like applying functions is done as methods when working with dataframes
        df['Away goals'] = FT_score_list.map(lambda goals: int(goals[1])) #I have forced them to be int types because they come from a string (e.g., 2-1) - if python doesn't recognise it as a number then descriptive statistics will be different
        df['First half goals'] = HT_score_list.map(lambda goals: int(goals[0]) + int(goals[1]) if goals != [] else np.NaN) #NOTE:the if condition is necessary because for many games the HT result is missing. They are marked as NaN if so.
        df['Second half goals'] = df['Total goals'] - df['First half goals']
        df = df.drop(columns=['Round']) #Note: In order for the change to take place, you need to re-assign it to the dataframe. you can't just use the method
        return df
    def get_team_stats(self, *teams):
        self.df = FootballData(self.start_season, self.end_season).create_df()
        self.teams = teams
        df_list = []
        if teams[0] == 'all':
        #Removes the (1) part from the Team 1 column, then lists each unique team in the dataset. It will also remove anything in between () brackets as some old results with now-defunct clubs are marked with the years in which they were active (e.g., Accrington FC (1878-1896)). I found that I also needed to strip the strings of any trailing spaces as it created duplicates due to inconsistency with the data formatting in the CSV.
            all_teams = self.df['Team 1'].str.replace(re.compile('\d[()]|[()]\d|(?<!:)[()]|(\d)|(-)'),'').str.strip().unique()
            for team in all_teams:
                df = self.df.loc[(self.df['Team 1'].str.contains(team, re.compile('(\d)|(\d\d)')) == True) | (self.df['Team 2'].str.contains(team, re.compile('(\d)|(\d\d)')) == True)].copy()
                #This line is needed for when multiple teams are selected - e.g., if I wanted Manchester United and Everton fixtures, then the result for games where Manchester United and Everton played each other will be 'duplicated' but the team-specific stats will be different. The first row generated will show the team stats from one team, and the 'duplicated' rows will show the team stats from the other team. This will create a column which will tell us from which perspective the team stats are being reported. This will be important later if we want to analyses comparing the two teams using these team stats.
                df['Team'] = team
                df['Team goals'] = np.where(df['Team 1'].str.contains(team, re.compile('(\d)|(\d\d)')) == True, df['Home goals'], df['Away goals'])
                HT_score_list = df['HT'].map(lambda HT: re.findall(r'\d+', HT))
                df['Team goals (1st half)'] = np.where(df['Team 1'].str.contains(team, re.compile('(\d)|(\d\d)')) == True, HT_score_list.map(lambda goals: int(goals[0]) if goals != [] else np.NaN), HT_score_list.map(lambda goals: int(goals[1]) if goals != [] else np.NaN))
                df['Team goals (2nd half)'] = df['Team goals'] - df['Team goals (1st half)']
                df['Goals against'] = df['Total goals'] - df['Team goals']
                df['Goals against (1st half)'] = df['First half goals'] - df['Team goals (1st half)']
                df['Goals against (2nd half)'] = abs(df['Second half goals'] - df['Team goals (2nd half)'])
                df['Goal difference'] = df['Team goals'] - df['Goals against']
                df['Result'] = np.select([df['Team goals'] > df['Goals against'], df['Team goals'] < df['Goals against']],['Win', 'Loss'], default = 'Draw')
                df['Points'] = np.select([df['Team goals'] > df['Goals against'], df['Team goals'] < df['Goals against']],[3, 0], default = 1)
                df_list.append(df)
        else:
            for team in self.teams:
                if type(team) is list:
                    for i in team:
                        df = self.df.loc[(self.df['Team 1'].str.contains(i, re.compile('(\d)|(\d\d)')) == True) | (self.df['Team 2'].str.contains(i, re.compile('(\d)|(\d\d)')) == True)].copy()
                        df['Team'] = i
                        df['Team goals'] = np.where(df['Team 1'].str.contains(i, re.compile('(\d)|(\d\d)')) == True, df['Home goals'], df['Away goals'])
                        HT_score_list = df['HT'].map(lambda HT: re.findall(r'\d+', HT))
                        df['Team goals (1st half)'] = np.where(df['Team 1'].str.contains(i, re.compile('(\d)|(\d\d)')) == True, HT_score_list.map(lambda goals: int(goals[0]) if goals != [] else np.NaN), HT_score_list.map(lambda goals: int(goals[1]) if goals != [] else np.NaN))
                        df['Team goals (2nd half)'] = df['Team goals'] - df['Team goals (1st half)']
                        df['Goals against'] = df['Total goals'] - df['Team goals']
                        df['Goals against (1st half)'] = df['First half goals'] - df['Team goals (1st half)']
                        df['Goals against (2nd half)'] = abs(df['Second half goals'] - df['Team goals (2nd half)'])
                        df['Goal difference'] = df['Team goals'] - df['Goals against']
                        df['Result'] = np.select([df['Team goals'] > df['Goals against'], df['Team goals'] < df['Goals against']],['Win', 'Loss'], default = 'Draw')
                        df['Points'] = np.select([df['Team goals'] > df['Goals against'], df['Team goals'] < df['Goals against']],[3, 0], default = 1)
                        df_list.append(df)
                else:
                    df = self.df.loc[(self.df['Team 1'].str.contains(team, re.compile('(\d)|(\d\d)')) == True) | (self.df['Team 2'].str.contains(team, re.compile('(\d)|(\d\d)')) == True)].copy()
                    df['Team'] = team
                    df['Team goals'] = np.where(df['Team 1'].str.contains(team, re.compile('(\d)|(\d\d)')) == True, df['Home goals'], df['Away goals'])
                    HT_score_list = df['HT'].map(lambda HT: re.findall(r'\d+', HT))
                    df['Team goals (1st half)'] = np.where(df['Team 1'].str.contains(team, re.compile('(\d)|(\d\d)')) == True, HT_score_list.map(lambda goals: int(goals[0]) if goals != [] else np.NaN), HT_score_list.map(lambda goals: int(goals[1]) if goals != [] else np.NaN))
                    df['Team goals (2nd half)'] = df['Team goals'] - df['Team goals (1st half)']
                    df['Goals against'] = df['Total goals'] - df['Team goals']
                    df['Goals against (1st half)'] = df['First half goals'] - df['Team goals (1st half)']
                    df['Goals against (2nd half)'] = abs(df['Second half goals'] - df['Team goals (2nd half)'])
                    df['Goal difference'] = df['Team goals'] - df['Goals against']
                    df['Result'] = np.select([df['Team goals'] > df['Goals against'], df['Team goals'] < df['Goals against']],['Win', 'Loss'], default = 'Draw')
                    df['Points'] = np.select([df['Team goals'] > df['Goals against'], df['Team goals'] < df['Goals against']],[3, 0], default = 1)
                    df_list.append(df)
        df = pd.concat(df_list)
        df = df.sort_index(ascending=True)
        df = df.reset_index(drop=True)
        return df
    #TODO: Fix this so that the additional columns specify which team it is referring to. i.e., 'Team goals' should be 'Manchester United goals' and 'Goals against' should be 'Liverpool goals'
    def get_matchups(self, team, opposition):
        self.df = FootballData(self.start_season, self.end_season).create_df()
        self.team = team
        self.opposition = opposition
        matchups = self.df.loc[(self.df['Team 1'].str.contains((self.team), re.compile('(\d)|(\d\d)')) == True) & (self.df['Team 2'].str.contains((self.opposition), re.compile('(\d)|(\d\d)')) == True) | (self.df['Team 1'].str.contains((self.opposition), re.compile('(\d)|(\d\d)')) == True) & (self.df['Team 2'].str.contains((self.team), re.compile('(\d)|(\d\d)')) == True)]
        df = matchups[(matchups['Team 1'].str.contains(self.team, re.compile('(\d)|(\d\d)')) == True) | (matchups['Team 2'].str.contains(self.team, re.compile('(\d)|(\d\d)')) == True)].copy()
        df[self.team + ' goals'] = np.where(df['Team 1'].str.contains(self.team, re.compile('(\d)|(\d\d)')) == True, df['Home goals'], df['Away goals'])
        HT_score_list = df['HT'].map(lambda HT: re.findall(r'\d+', HT))
        df[self.team + ' goals (1st half)'] = np.where(df['Team 1'].str.contains(self.team, re.compile('(\d)|(\d\d)')) == True, HT_score_list.map(lambda goals: int(goals[0]) if goals != [] else np.NaN), HT_score_list.map(lambda goals: int(goals[1]) if goals != [] else np.NaN))
        df[self.team + ' goals (2nd half)'] = df[self.team + ' goals'] - df[self.team + ' goals (1st half)']
        df[self.opposition + ' goals'] = df['Total goals'] - df[self.team + ' goals']
        df[self.opposition + ' goals (1st half)'] = df['First half goals'] - df[self.team + ' goals (1st half)']
        df[self.opposition + ' (2nd half)'] = abs(df['Second half goals'] - df[self.team + ' goals (2nd half)'])
        df['GD ' + self.team] = df[self.team + ' goals'] - df[self.opposition + ' goals']
        df['GD ' + self.opposition] = df[self.opposition + ' goals'] - df[self.team + ' goals']
        df[self.team + ' result'] = np.select([df[self.team + ' goals'] > df[self.opposition + ' goals'], df[self.team + ' goals'] < df[self.opposition + ' goals']],['Win', 'Loss'], default = 'Draw')
        df[self.opposition + ' result'] = np.select([df[self.opposition + ' goals'] > df[self.team + ' goals'], df[self.opposition + ' goals'] < df[self.team + ' goals']],[3, 0], default = 1)
        return df
