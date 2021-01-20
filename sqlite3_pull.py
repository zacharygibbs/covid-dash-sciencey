import sqlite3
import pandas as pd
import os
import time
import datetime, time, pytz

def update_table_data():
    conn = sqlite3.connect('covid_data.db')
    df = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv')
    df.to_sql('counties', conn, if_exists='replace')
    dfstate = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')
    dfstate.to_sql('states', conn, if_exists='replace')
    conn.close()
    
def pull_table_data():
    conn = sqlite3.connect('covid_data.db')
    df = pd.read_sql('SELECT * FROM counties', conn)
    dfstate = pd.read_sql('SELECT * FROM states', conn)
    conn.close()
    return df, dfstate
    
def how_long_since_last_updated():
    filename = 'covid_data.db'
    statbuf = os.stat(filename)
    return (time.time() - statbuf.st_mtime)
    
def last_updated():
    filename = 'covid_data.db'
    statbuf = os.stat(filename)
    today = datetime.datetime.fromtimestamp(statbuf.st_mtime).astimezone(pytz.timezone('US/Central'))
    todaystring = today.strftime("%m-%d-%Y %H:%M:%S")
    todaystring = todaystring + ' Central'
    return todaystring