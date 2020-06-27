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


global df, dfstate
global todaystring


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

    if np.any([todaystring in file for file in files]):
        print('Loading todays county data from memory')
        df = pd.read_csv('us-counties'+todaystring+'.csv')
    else:    
        print("Downloading New Data for us-counties_%s; deleting old csv data thats stored"%(todaystring))
        df = pd.read_csv(
            'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv')
        df.to_csv('us-counties'+todaystring+'.csv')
        for oldcsv in files:
            os.remove(os.path.join(basepath and basepath or '', oldcsv))

    files = [i for i in os.listdir(basepath) if (('.csv' in i) and ('states' in i))]

    if np.any([todaystring in file for file in files]):
        print('Loading todays state data from memory')
        dfstate = pd.read_csv('us-states'+todaystring+'.csv')
    else:    
        print("Downloading New Data for us-states_%s; deleting old csv data thats stored"%(todaystring))
        dfstate = pd.read_csv(
            'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')
        dfstate.to_csv('us-states'+todaystring+'.csv')
        for oldcsv in files:
            os.remove(os.path.join(basepath and basepath or '', oldcsv))
    return df, dfstate
df, dfstate = get_new_data()
#statedf = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')
def get_chartdata1(state,county,stat='cases'):
    if county:
        x = df.date[(df['state'] == state) & (df['county']==county)]
        y = df[(df['state'] == state) & (df['county']==county)][stat]
    else:
        x = dfstate.date[dfstate['state'] == state]
        y = dfstate[dfstate['state'] == state][stat]
    return x,y
def get_chartdata(states,counties,stat='cases'):
    output = []
    #can do either states only or counties within a single state, but not comparing county from one state to county to another; you'd need more rigorous restrictions on input
    for state in states:
        if counties:
            for county in counties:
                output.append(get_chartdata1(state,county,stat))
        else:
            output.append(get_chartdata1(state,None,stat))
    if len(states)>0:
        return list(zip(*output))
    else:
        return [[],[]]

##Set initial state of dashboard
state0 = ['Oklahoma','Texas','Colorado','Arizona']

dfstate_filtered = dfstate[(dfstate['date']==np.max(dfstate.date))]
dfstate_sorted = dfstate_filtered.sort_values('cases',ascending=False)
state0_labels = dfstate_sorted.state
cases0_labels = dfstate_sorted.cases

county0 = []
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
                                                                html.Div(children='Per State, County etc.', style={
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
                                                    html.Div(children=['Zach Gibbs: ', dcc.Link('Cool Sciencey', href='http://www.coolsciencey.com')]),
                                                    html.Div(children=['Data Source: ',dcc.Link('NY Times covid-19-data on GitHub',href='http://github.com/nytimes/covid-19-data/')]),
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
	dcc.Interval(id='interval-component',interval=1000*60*60, n_intervals=0),
])

@app.callback([Output('date-label','children')],
		[Input('interval-component', 'n_intervals')])
def interval_update(numint):
    get_new_data()
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
    Input('county_dropdown','value')]
    )
def update_charts(stat,scale,statevals,countyvals):
    xs,ys = get_chartdata(statevals, countyvals,stat)
    dys = [np.diff(i) for i in ys]  
    if countyvals:
        if statevals:
            chart_text = ['%s-%s'%(statevals[0],county) for county in countyvals]
        else:
            return {'data':[]}, {'data':[]}
    else:
        chart_text = statevals
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
                    ],
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
                x=xs[index][:-1],
                y=dys[index],
                text=chart_text[index],
                opacity=0.8,
                name=i
            ) for index,i in enumerate(chart_text)                
            ],
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
    #app.run_server(debug=True,port=8080,host='0.0.0.0')
    app.run_server(debug=False)
