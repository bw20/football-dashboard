def seasons_dictionary(starting_decade, ending_decade):
    #Create a dictionary with the decades and seasons for each dataset.
    eng = '\england-master'
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
            path = eng + '\\' + decade + '\\' + season + '\eng.1.csv'
            df_name = 'df_eng_' + season
            df_dictionary[df_name] = path
    return df_dictionary
df_dictionary = seasons_dictionary(1880, 2010)
df_list = []
seasons_list = []
#Identify the index of the starting season and ending season specified
start_index = list(df_dictionary.keys()).index('df_eng_' + starting_decade)
end_index = (list(df_dictionary.keys()).index('df_eng_' + ending_decade)) + 1
#Iterate through these indices to populate the seasons_list with the desired keys for seasons_dictionary
for i in range(start_index, end_index):
    season_key = list(df_dictionary.keys())[i]
    seasons_list.append(season_key)
#Use the keys in seasons_list to fetch the paths to each season, and reading them in to a list of dfs in df_list
for i in df_dictionary:
    if i in seasons_list:
        try:
            season = re.findall(r'\d\d\d\d-\d\d', i)[0]
            df = pd.read_csv(df_dictionary[i], index_col=None, header=0)
            df['Season'] = season
            df_list.append(df)
        except FileNotFoundError: #This exception accommodates the fact that data is not available for all years - for example, seasons that were not played due to WW1 and WW2.
            continue