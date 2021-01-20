import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import flask
import plotly.graph_objs as go
import pandas as pd
import datetime, time, pytz
import numpy as np
import os
from dash.exceptions import PreventUpdate
import sqlite3
from sqlite3_pull import *

import logging
import threading
import time

global df, dfstate
global todaystring

county_pop_data = pd.read_csv('county_pops_census2019.csv')

data_pull_freq_mins_source = 1 
data_pull_freq_mins_local = .5

def get_new_data_sql():
    global df, dfstate, todaystring
    if db_exists_and_has_tables():#os.path.exists('covid_data.db'):
        todaystring = last_updated()
        time_since_updated = how_long_since_last_updated()
        today_now = datetime.datetime.now().astimezone(pytz.timezone('US/Central'))
        todaystring_now = today_now.strftime("%m-%d-%Y %H:%M:%S")
        print('Initiating new data pull local:  %s'%(todaystring_now))
        df, dfstate =  pull_table_data()
        if time_since_updated > data_pull_freq_mins_source*60:
            today_now = datetime.datetime.now().astimezone(pytz.timezone('US/Central'))
            todaystring_now = today_now.strftime("%m-%d-%Y %H:%M:%S")
            print('Initiating new data pull source:  %s'%(todaystring_now))
            x = threading.Thread(target=update_table_data, args=())
            x.start()#update_table_data()
        return df, dfstate
    else:
        today_now = datetime.datetime.now().astimezone(pytz.timezone('US/Central'))
        todaystring_now = today_now.strftime("%m-%d-%Y %H:%M:%S")
        print('Initiating new data pull source_new:  %s'%(todaystring_now))
        a=update_table_data()
        a.run()
        todaystring = last_updated()
        today_now = datetime.datetime.now().astimezone(pytz.timezone('US/Central'))
        todaystring_now = today_now.strftime("%m-%d-%Y %H:%M:%S")
        print('Initiating new data pull local:  %s'%(todaystring_now))
        df, dfstate =  pull_table_data()
        pass
        return df, dfstate


def get_new_data():
    global df, dfstate, todaystring
    today = datetime.datetime.now().astimezone(pytz.timezone('US/Central'))
    todaystring = today.strftime("%m-%d-%Y %H:%M:%S")
    todaystring = todaystring + 'Central'
    #loadtime = datetime.now()
    #loadtime = "%s Central Time"%(loadtime.astimezone(pytz.timezone('US/Central')).isoformat())

    basepath = None

    ## handle file download
    files = [i for i in os.listdir(basepath) if (('.csv' in i) and ('counties' in i))]

    todaystring_short = today.strftime("%m-%d-%Y %H")
    
    if np.any(['us-counties' + todaystring_short in file for file in files]):
        print('Loading todays county data from memory')
        todaystring = files[['us-counties' +todaystring_short in file for file in files].index(True)]
        df = pd.read_csv(todaystring)
    else:    
        print("Downloading New Data for us-counties_%s; deleting old csv data thats stored"%(todaystring))
        df = pd.read_csv(
            'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv')
        df.to_csv('us-counties'+todaystring+'.csv')
        for oldcsv in files:
            os.remove(os.path.join(basepath and basepath or '', oldcsv))

    files = [i for i in os.listdir(basepath) if (('.csv' in i) and ('states' in i))]

    if np.any(['us-states' + todaystring_short in file for file in files]):
        print('Loading todays state data from memory')
        todaystring = files[['us-states' + todaystring_short in file for file in files].index(True)]
        dfstate = pd.read_csv(todaystring)
    else:    
        print("Downloading New Data for us-states_%s; deleting old csv data thats stored"%(todaystring))
        dfstate = pd.read_csv(
            'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')
        dfstate.to_csv('us-states'+todaystring+'.csv')
        for oldcsv in files:
            os.remove(os.path.join(basepath and basepath or '', oldcsv))
    return df, dfstate
df, dfstate = get_new_data_sql()
#statedf = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')
def get_chartdata1(state,county,stat='cases', popnorm=False):
    if county:
        x = df.date[(df['state'] == state) & (df['county']==county)]
        if popnorm:
            countypop = county_pop_data[(county_pop_data['state']==state) & (county_pop_data['county']==county)]['Pop'].sum()
            y = df[(df['state'] == state) & (df['county']==county)][stat] / countypop * 1000
        else:
            y = df[(df['state'] == state) & (df['county']==county)][stat]
    else:
        #statepop_states = pd.unique(county_pop_data['state'])
        
        x = dfstate.date[dfstate['state'] == state]
        if popnorm:
            statepop = county_pop_data[county_pop_data['state']==state]['Pop'].sum()
            y = dfstate[dfstate['state'] == state][stat] / statepop * 1000
        else:
            y = dfstate[dfstate['state'] == state][stat]
    return x,y
def get_chartdata(states,counties,stat='cases',popnorm=False):
    output = []
    #can do either states only or counties within a single state, but not comparing county from one state to county to another; you'd need more rigorous restrictions on input
    
    for state in states:
        if counties:
            for county in counties:
                output.append(get_chartdata1(state,county,stat, popnorm))
        else:
            output.append(get_chartdata1(state,None,stat, popnorm))
    if len(states)>0:
        return list(zip(*output))
    else:
        return [[],[]]

##Set initial state of dashboard
state0 = ['Oklahoma']

dfstate_filtered = dfstate[(dfstate['date']==np.max(dfstate.date))]
dfstate_sorted = dfstate_filtered.sort_values('cases',ascending=False)
state0_labels = dfstate_sorted.state
cases0_labels = dfstate_sorted.cases

county0 = ['Washington']
stat0='cases'
x0, y0 = get_chartdata(state0,county0,stat0)
#x0, y0 = list(zip(*result))

dy0 = [np.diff(i) for i in y0]


external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']
server = flask.Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,server=server)
colors = {
    'background': '#FFFFFFF',
    'text': '#000000'
}


app.layout = html.Div(style={'backgroundColor': colors['background']}, 
                children=[ html.Div(className='row', children =[
                                                                html.H1(
                                                                    children='Covid 19 Stats',
                                                                    style={
                                                                        'textAlign': 'center',
                                                                        'color': colors['text']
                                                                    }
                                                                ),
                                                                html.Div(children='Per State, County, and optionally on a Pop Normalized (Per 1000 people) basis etc.', style={
                                                                    'textAlign': 'center',
                                                                    'color': colors['text']
                                                                        })]),
                            html.Div(className='row', children = [


                                    html.Div(
                                                className='three columns',
                                                children = [
                                                html.Label('State'),
                                                dcc.Dropdown( id='state_dropdown',
                                                    options=[
                                                        {'label':'%s-%i'%(i,j), 'value':i} for (i,j) in zip(state0_labels, cases0_labels)
                                                        #{'label':i, 'value':i} for i in np.sort(df.state.unique())
                                                    ],
                                                    value=state0,
                                                    multi=True
                                                ),
                                                html.Label('County'),
                                                dcc.Dropdown( id='county_dropdown',
                                                    options=[
                                                        {'label':i, 'value':i} for i in np.sort(df.county.unique())
                                                    ],
                                                    value=county0,
                                                    multi=True,
                                                    placeholder = 'Select a County'
                                                ),

                                                html.Label('Cases/Deaths?'),
                                                dcc.RadioItems(
                                                    id='radio-items-stat',
                                                    options=[
                                                        {'label': 'Cases', 'value': 'cases'},
                                                        {'label': 'Deaths', 'value': 'deaths'},
                                                    ],
                                                    value=stat0
                                                ),
                                                dcc.Checklist(
                                                        id='checkbox_7davg',
                                                        options=[
                                                            {'label': '7 day average', 'value': '7d'},
                                                             {'label':'Normalize Per 1000 Population', 'value':'popnorm'}],
                                                        value=['7d']
                                                    )  
                                                ,

                                                html.Label('Log/Linear?'),
                                                dcc.RadioItems(
                                                    id='radio-items-scale',
                                                    options=[
                                                        {'label': 'Linear', 'value': 'linear'},
                                                        {'label': 'Log', 'value': 'log'},
                                                    ],
                                                    value='linear'
                                                ),
                                            
                                                
                                            html.Div(id='date-labelouter',children=[
                                                    html.Div(children=['Zach Gibbs: ', html.A(children='Cool Sciencey', href="http://www.coolsciencey.com",target="_blank")]),
                                                    html.Div(children=['Data Source: ',html.A(children='NY Times covid-19-data on GitHub',href='http://github.com/nytimes/covid-19-data/',target='_blank')]),
                                                    html.Div(id='date-label',children=['Data Last Updated: %s'%(todaystring)])
                                                    ])
                                                ]),
                                        html.Div(className='nine columns', 
                                            children = [
                                                html.Div([
                                                    dcc.Graph(
                                                    id='stat-scatter',
                                                    figure={
                                                        'data': [
                                                                go.Scatter(
                                                                x=x0[index],
                                                                y=y0[index],
                                                                text=state0[index],
                                                                mode='markers',
                                                                opacity=0.8,
                                                                marker={
                                                                    'size': 15,
                                                                    'line': {'width': 0.5, 'color': 'white'}
                                                                },
                                                                name=i
                                                            ) for index,i in enumerate(state0)
                                                        ],
                                                        'layout': go.Layout(
                                                            xaxis={},
                                                            yaxis={'type':'linear'},
                                                            height=400,
                                                            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                                                            legend={'x': 0, 'y': 1},
                                                            hovermode='y unified'
                                                                )
                                                    }
                                                        ),


                                                    dcc.Graph(
                                                        id='Daily Cases',
                                                        figure={
                                                            'data': [

                                                            go.Bar(
                                                                x=x0[index][:-1],
                                                                y=dy0[index],
                                                                text=state0[index],
                                                                opacity=0.8,
                                                                name=i
                                                            ) for index,i in enumerate(state0)                
                                                            ],
                                                            'layout': { 'height':400,
                                                                'plot_bgcolor': colors['background'],
                                                                'paper_bgcolor': colors['background'],
                                                                'font': {
                                                                    'color': colors['text']
                                                                        }
                                                                    }
                                                                }
                                                            )
                                                    ])
                                                ]) 
        ]),
    dcc.Interval(id='interval-component',interval=1000*data_pull_freq_mins_local*60, n_intervals=0),
])

@app.callback([Output('date-label','children')],
        [Input('interval-component', 'n_intervals')])
def interval_update(numint):
    get_new_data_sql()
    return ['Data Last Updated: %s'%(todaystring)]

@app.callback(
    [Output('county_dropdown','options'), Output('county_dropdown','value')],
    [Input('state_dropdown','value')])
def update_countydropdown(statevals):
    if len(statevals)>1 or len(statevals)==0:
        return [],[]
    else:
        df_filtered = df[(df['state']==statevals[0]) & (df['date']==np.max(df.date))]
        df_sorted = df_filtered.sort_values('cases',ascending=False)
        county = df_sorted.county
        cases = df_sorted.cases
        #.county.unique()
        #import pdb;pdb.set_trace()
        return [{'label':'%s-%i'%(i,j), 'value':i} for (i,j) in zip(county, cases)], None




@app.callback(
    Output('county_dropdown','placeholder'),
    [Input('state_dropdown','value')])
def update_countydropdownplaceholder(statevals):
    if len(statevals)>1:
        return 'Cannot Select County if Multiple States selcted..'
    else:
        return 'Select a County'

@app.callback(
    [Output('stat-scatter','figure'), Output('Daily Cases','figure')],
    [Input('radio-items-stat','value'), 
    Input('radio-items-scale','value'), 
    Input('state_dropdown','value'), 
    Input('county_dropdown','value'),
    Input('checkbox_7davg','value')]
    )
def update_charts(stat,scale,statevals,countyvals, sevenday):
    if 'popnorm' in sevenday:
            popnorm = True
    else:
            popnorm = False
    xs,ys = get_chartdata(statevals, countyvals,stat,popnorm)
    
    dys = [np.diff(i) for i in ys]  
    if countyvals:
        if statevals:
            chart_text = ['%s-%s'%(statevals[0],county) for county in countyvals]

        else:
            return {'data':[]}, {'data':[]}
    else:
        chart_text = statevals
                                 
    rolling_avg = [pd.Series(ys[index]).rolling(7).mean() for index,i in enumerate(chart_text)]
    rolling_avg2 = [list(rolling_avg[index][3:]) + list(rolling_avg[index][3:6]) for index,i in enumerate(chart_text)]
    rolling_avg_daily = [pd.Series(dys[index]).rolling(7).mean() for index,i in enumerate(chart_text)]
    rolling_avg_daily2 = [list(rolling_avg_daily[index][3:]) + list(rolling_avg_daily[index][3:6]) for index,i in enumerate(chart_text)]
    #import pdb;pdb.set_trace()
    if '7d' in sevenday:
        add_7dlines1 = [go.Scatter(x=xs[index], y=rolling_avg2[index],text=chart_text[index]+'7dma', mode='lines',name=i) for index,i in enumerate(chart_text)]
        add_7dlines2 = [go.Scatter(
                x=xs[index][1:],
                y=rolling_avg_daily2[index],
                text=chart_text[index]+'7dma',
                mode='lines',
                name=i
            ) for index,i in enumerate(chart_text) ]
    else:
        add_7dlines1=[]
        add_7dlines2 = []
    figure1={'data': [
                        go.Scatter(
                            x=xs[index],
                            y=ys[index],
                            text=chart_text[index],
                            mode='markers',
                            opacity=0.8,
                            marker={
                                'size': 15,
                                'line': {'width': 0.5, 'color': 'white'}
                            },
                            name=i
                        ) for index,i in enumerate(chart_text)
                    ] + add_7dlines1,
                    'layout': go.Layout(
                        xaxis={},
                        yaxis={'type':scale},
                        height=400,
                        margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                        legend={'x': 0, 'y': 1},
                        hovermode='y unified'
                            )
                }

    figure2={
            'data': [
            go.Bar(
                x=xs[index][1:],
                y=dys[index],
                text=chart_text[index],
                opacity=0.8,
                name=i
            ) for index,i in enumerate(chart_text)                
            ]+
            add_7dlines2,
            'layout': { 'height':400,
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {'color': colors['text']},
                 'yaxis':{'type':scale}
                    }
                }
    return figure1, figure2



app.css.config.serve_locally = False
app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})




if __name__ == '__main__':
    app.run_server(debug=True,port=8080,host='0.0.0.0')
    #app.run_server(debug=False)

