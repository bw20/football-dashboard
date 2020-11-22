import pandas as pd
import plotly.express as px
import streamlit as st
from FootballData import FootballData

# Organising the datasets
# Function that loads the full dataset (this is cached)
@st.cache
def load_dataset():
    df = FootballData('1886-87','2019-20').get_team_stats('all')
    df = df.groupby(['Season', 'Team'], as_index=False).agg({'Total goals': 'mean', 'Points':'sum', 'Team goals':'mean', 'Goals against':'mean', 'Goal difference':'sum'})
    return df
# Function that takes the full dataset and filters it based on the sidebar criteria - also cached
@st.cache
def filter_dataset(start_date, end_date, selection):
    df = load_dataset()
    start = int(start_date[0:4])
    end = int(end_date[0:4])
    years = abs(start-end)
    seasons_list = []
    for i in range(years + 1):
        season_start = str(start + i)
        season_end = str((start+ i) + 1)
        seasons_list.append(season_start + '-' + season_end[-2:])
    if selection == 'all':
        filter = df.loc[(df['Season'].isin(seasons_list))]
    else:
        filter = df.loc[(df['Season'].isin(seasons_list)) & (df['Team'].isin(selection))]
    return filter

# Load the full dataset (after which it is cached) and use it to present the teams and season options for the sidebar filters
list_of_teams = sorted(load_dataset().Team.unique())
list_of_seasons = sorted(load_dataset().Season.unique())

# Sidebar filters
selected_teams = st.sidebar.multiselect('Select teams:', options=list_of_teams)
team = ', '.join(selected_teams)
all_teams = st.sidebar.checkbox('Select all teams', value=True)
if all_teams == True: #When the checkbox is ticked
    selected_teams = 'all'
    team = 'All teams who played'
start_date = st.sidebar.selectbox('Start season:', options = list_of_seasons, index=list_of_seasons.index('1888-89'))
end_date = st.sidebar.selectbox('End season:', options = list_of_seasons[list_of_seasons.index(start_date):], index=list_of_seasons[list_of_seasons.index(start_date):].index('2019-20'))
#Load the filtered dataset based on the sidebar filters
data = filter_dataset(start_date, end_date, selected_teams)

#st.write('dataset', data)

#The viewable area
st.title('Football Dashboard')
#find out how to chuck an "and" here. Need to have something different when all teams are selected.
st.subheader(f'You have selected: {team} between the seasons {start_date} and {end_date}')

axis_variable_labels = {
    'Total goals':'Goals p/game',
    'Team goals':'Goals for',
    'Goals against':'Goals against',
    'Goal difference':'Goal difference',
    #'Result':'Win/loss/Draw',
    'Points':'Points',
}
corr_x = st.selectbox('X axis variable', options=['Points', 'Total goals', 'Team goals', 'Goals against', 'Goal difference'], format_func=axis_variable_labels.get)
corr_y = st.selectbox('Y axis variable', options=['Points', 'Total goals', 'Team goals', 'Goals against', 'Goal difference'], format_func=axis_variable_labels.get, index=1)
corr_col = st.radio('Colour variable', options=['Season', 'Team'])

#The chart
if st.button('Generate plot') == True:
    try:
        #st.write('data', data)
        fig = px.scatter(data, x=corr_x, y=corr_y, template='plotly_white', color=corr_col, hover_data=['Team', 'Season'], color_continuous_scale=px.colors.sequential.OrRd)
        st.write(fig)
    except KeyError:
        st.write(f'Sorry, {team_filter} did not play in the English top flight during the {start_date} to {end_date} seasons.')