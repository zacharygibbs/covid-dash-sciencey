import sqlite3
import pandas as pd
import os
import time
import datetime, time, pytz
import sys
import threading


def update_table_data():
    conn = sqlite3.connect('covid_data.db',check_same_thread=True,timeout=3000)
    df = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv')
    df.to_sql('counties', conn, if_exists='replace')
    dfstate = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')
    dfstate.to_sql('states', conn, if_exists='replace')
    conn.close()
    return None
    
def pull_table_data():
    conn = sqlite3.connect('covid_data.db', check_same_thread=True, timeout=3000)
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
    pass
    return todaystring

def db_exists_and_has_tables():
    a=os.path.exists('covid_data.db')
    if a:
        conn = sqlite3.connect('covid_data.db',check_same_thread=True,timeout=3000)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = list(zip(*cur.fetchall()))[0]
        b = 'states' in tables
        c = 'counties' in tables
        conn.close()
        return b and c
    else:
        return False

def county_df(state,county):
    conn = sqlite3.connect('covid_data.db',check_same_thread=True,timeout=3000)
    res=pd.read_sql("""
                        SELECT * FROM counties WHERE state="%s" and county="%s"
                        
                        """%(state, county),conn)
    conn.close()
    return res
           
def state_df(state):
    conn = sqlite3.connect('covid_data.db',check_same_thread=True,timeout=3000)
    res=pd.read_sql("""
                        SELECT * FROM states WHERE state="%s"
                            """%(state),conn)
    conn.close()
    return res
                       
def state_counties(state):
    conn = sqlite3.connect('covid_data.db',check_same_thread=True,timeout=3000)
    res=pd.read_sql('SELECT * FROM counties WHERE state="%s"'%(state),conn)
    conn.close()
    return res

def state_dropdown():
    conn = sqlite3.connect('covid_data.db',check_same_thread=True,timeout=3000)
    res=pd.read_sql("""
                        SELECT * FROM states
                        WHERE date=(SELECT max(date) from states)
                        ORDER BY cases DESC;
                        """,conn)
    conn.close()
    return list(zip(res['state'], res['cases']))

def county_dropdown(state):
    conn = sqlite3.connect('covid_data.db',check_same_thread=True,timeout=3000)
    res=pd.read_sql("""
                        SELECT * FROM counties
                        WHERE date=(SELECT max(date) from counties) AND state="%s"
                        ORDER BY cases DESC;
                        """%(state),conn)
    conn.close()
    return list(zip(res['county'], res['cases']))

