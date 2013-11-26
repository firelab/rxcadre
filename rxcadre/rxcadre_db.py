#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
#  $Id$
#  Project:  RX Cadre Data Visualization
#  Purpose:  Data management
#  Author:   Kyle Shannon <kyle@pobox.com>
#
###############################################################################
#
#  This is free and unencumbered software released into the public domain.
#
#  Anyone is free to copy, modify, publish, use, compile, sell, or
#  distribute this software, either in source code form or as a compiled
#  binary, for any purpose, commercial or non-commercial, and by any
#  means.
#
#  In jurisdictions that recognize copyright laws, the author or authors
#  of this software dedicate any and all copyright interest in the
#  software to the public domain. We make this dedication for the benefit
#  of the public at large and to the detriment of our heirs and
#  successors. We intend this dedication to be an overt act of
#  relinquishment in perpetuity of all present and future rights to thise)
#  software under copyright law.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#  OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.
#
#  For more information, please refer to <http://unlicense.org/>
#
###############################################################################
'''
SQLite related class for storage of time series data
'''

import datetime
import logging
import os
import sqlite3

###############################################################################
# Logging stuff.
###############################################################################
logging.basicConfig(level=logging.INFO)

def _import_date(string):
    '''
    Parse a datetime from a UTC string
    '''
    try:
        parsed = datetime.datetime.strptime(string, '%m/%d/%Y %I:%M:%S %p')
    except ValueError:
        parsed = datetime.datetime.strptime(string, '%m/%d/%y %I:%M:%S %p')
    return parsed

def _extract_xy(wkt):
    '''
    Extract x and y coordinates from wkt in the db.  Strip 'POINT' from the
    front, and split the remaining data losing the parentheses
    '''

    wkt = wkt.strip().upper()
    if wkt.find('POINT') < 0:
        raise ValueError
    wkt = wkt[wkt.find('(')+1:wkt.find(')')].split()
    if len(wkt) != 2:
        raise ValueError("Invalid wkt: %s" % wkt)
    wkt[0] = wkt[0].replace("\"","")

    wkt[1] = wkt[1].replace("\"","")
    #wkt[1] = _to_decdeg(wkt[1])

    return tuple([float(c) for c in wkt])



class RxCadreDb():
    '''Data management for rxcadre module'''

    def __init__(self, db_file):
        if not db_file or type(db_file) is not str:
            if db_file != "":
                raise ValueError('Invalid file name')
        self._db_file = db_file
        self._dbase = sqlite3.connect(db_file)
        self._cursor = self._dbase.cursor()


    @property
    def db_file(self):
        '''
        Get the file name of the database
        '''
        return self._db_file


    def __del__(self):
        '''
        Cleanup, mainly close the db
        '''
        if self._dbase:
            self._dbase.close()


    def init_new_db(self):
        '''
        Create a new, empty database with appropriate metatables.  If the file
        previously exists, we fail before connecting using sqlite.  It must be
        a new file.
        '''
        stmts = open('../data/new_tables.sql').read().split(';')
        for stmt in stmts:
            self._cursor.execute(stmt)
        """
        See data/*.sql for creation routines.

        sql = '''CREATE TABLE plot_location(plot_id TEXT, x REAL, y REAL,
                                            geometry TEXT, plot_type TEXT)'''
        self._cursor.execute(sql)
        sql = '''CREATE TABLE event(event_name TEXT NOT NULL,
                                    event_start TEXT NOT NULL,
                                    event_end TEXT NOT NULL,
                                    PRIMARY KEY(project_name, event_name))'''
        self._cursor.execute(sql)
        sql = '''CREATE TABLE obs_table(obs_table_name TEXT NOT NULL,
                                        table_display name TEXT,
                                        timestamp_column TEXT NOT NULL,
                                        obs_cols TEXT NOT NULL,
                                        obs_col_names TEXT,
                                        PRIMARY KEY(obs_table_name))
              '''
        self._cursor.execute(sql)
        sql = '''CREATE_TABLE cup_vane_obs(plot_id TEXT NOT NULL,
                                           timestamp TEXT NOT NULL,
                                           direction REAL,
                                           speed REAL,
                                           gust REAL,
                                           PRIMARY KEY(plot_id, timestamp)
              '''

        self._cursor.execute(sql)
        sql = '''CREATE_TABLE fbp_obs(plot_id TEXT NOT NULL,
                                           timestamp TEXT NOT NULL,
                                           temperature REAL,
                                           ks_v REAL,
                                           ks_h REAL,
                                           mt_t REAL,
                                           mt_r REAL,
                                           nar REAL,
                                           PRIMARY KEY(plot_id, timestamp)
              '''

        self._cursor.execute(sql)
        sql = 'INSERT INTO obs_table VALUES(?, ?, ?, ?, ?)'
        self._cursor.execute(sql, ('cup_vane_obs', 'Wind Data', 'timestamp',
                                   'direction,speed,gust',
                                   'Direction,Speed,Gust')
        self._cursor.execute(sql, ('fbp_obs', 'Fire Behavior Data',
                                   'timestamp',
                                   'temperature,ks_v,ks_h,mt_t,mt_r,nar'
                                   'Temperature(C),Pressure Vertical,Pressure \
                                   Horizontal,Medtherm Total, Medtherm \
                                   Radiation,Narrow Angle \
                                   Radiometer,speed,gust')
                                   'Direction,Speed,Gust')
        """

        self._dbase.commit()


    def check_valid_db(self):
        '''
        Check the schema of an existing db.  This involves checking the
        metatables, and checking to make sure tables registered in obs_tables
        exist.
        '''

        required_tables = set(['plot_location', 'event', 'obs_table'])
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        self._cursor.execute(sql)
        table_names = [t[0] for t in self._cursor.fetchall()]
        if not set(table_names) >= required_tables:
            return False
        self._cursor.execute("SELECT obs_table_name FROM obs_table")

        obs_names = [o[0] for o in self._cursor.fetchall()]
        for name in obs_names:
            if name not in table_names:
                return False
        return True

    def register_obs_table(self, table_name, time_col, time_frmt,
                           col_names=None):
        '''
        Register an observation table with the obs_tables table.

        param table_name: Name of the table to register.

        param time_col: Name of the column that contains the time stamp data.

        param time_frmt: Format of the desired datetime format for use with
                         strftime and strptime, ie %Y-%m-%dT%H:%M:%s

        param col_names: a dictionary of actual column names and human readable
                         column names.  If absent, use all cols (other than
                         timestamp and plot_id

        return: None.
        '''

        sql = '''PRAGMA table_info(?)'''
        self._cursor.execute(sql, table_name)
        rows = self._cursor.fetchall()
        if not rows:
            raise ValueError('Table does not exist in the database')
        if col_names:
            if type(col_names) is not dict:
                raise ValueError('Invalid column definition')
            valid_cols = set([row[1] for row in rows])
            if set(col_names.keys()) < valid_cols:
                raise ValueError('Column definition is invalid')
        sql = '''INSERT INTO obs_table VALUES(?, ?, ?, ?, ?, ?, ?)'''
        self._cursor.execute(sql, table_name, table_name,
                                   time_col,
                             ','.join([name for name in col_names.keys()]),
                             ','.join([name for name in col_names.values()]))
        self._dbase.commit()


    def get_obs_table_names(self):
        '''
        Get the names of all stored observation tables as a list of strings.
        '''
        sql = "SELECT obs_table_name FROM obs_table"
        self._cursor.execute(sql)
        names = [n[0] for n in self._cursor.fetchall()]
        return names


    def get_event_data(self):
        '''
        Get the event names and the start, stop times for the events.
        '''
        sql = "SELECT event_name, event_start, event_end from event"
        self._cursor.execute(sql)
        events = dict()
        for row in self._cursor.fetchall():
            events[row[0]] = (row[1], row[2])
        return events


    def get_plot_data(self):
        '''
        Get simple plot information.
        '''
        sql = "SELECT plot_id, geometry from plot_location"
        self._cursor.execute(sql)
        plots = []
        for row in self._cursor.fetchall():
            plots.append(list(row))
        return plots


    def point_location(self, plot):
        '''
        Fetch the x and y coordinate of the plot
        '''
        sql = '''SELECT geometry FROM plot_location WHERE plot_id=?'''
        self._cursor.execute(sql, (plot,))
        row = self._cursor.fetchone()
        return _extract_xy(row[0])


    def extract_obs_data(self, table_name, plot_name, start=None, end=None,
                         cols=None):
        '''
        Extract data from a table in obs_table for generating output.

        :param table_name: Name of the table to query.  Must be in the
                           obs_table.

        :param plot_name: Name of the plot to extract data for.  Must be in the
                          plot_location table.

        :param start: datetime representation of when to start data extraction,
                      if absent, use earliest available timestamp.

        :param end: datetime representation of when to end data extraction,
                    if absent, use latest available timestamp.

        :param cols: dictionary with keys representing names of columns to
                     extract.  If absent, the metadata from obs_table (obs_cols
                     and obs_col_names) will be used.  The values associated
                     with the keys are human readable names for display.  If
                     they are absent, obs_col_names is checked, and then the
                     text in obs_cols is used.  If present, it the keys *must*
                     be a subset of columns in the obs_tables/obs_cols values

        :return: A dictionary with keys of {obs_cols:obs_names} keys and lists
                 of values, ie:

                 {'wind_spd' : 'Wind Speed(mph)'} : [2.3,4.6,4.4]}
        '''

        sql = '''SELECT * FROM obs_table WHERE obs_table_name=?'''
        self._cursor.execute(sql, (table_name,))
        row = self._cursor.fetchone()
        if not row:
            raise IOError('Table %s is not in obs_table' % table_name)
        time_col = row[1]
        geom_col = row[2]
        obs_cols = [c.strip() for c in row[3].split(',')]
        obs_names = [c.strip() for c in row[4].split(',')]
        if cols:
            if set(cols.keys()) > set(obs_cols):
                raise ValueError('Invalid column requested')
        col_def = ''
        for i, col in enumerate(obs_cols):
            col_def += '%s as %s' % (col, obs_names[i])
            if i < len(obs_cols) -1:
                col_def += ','
        logging.debug('SQL as stmt: %s', col_def)
        sql = '''
              SELECT %s as timestamp, %s FROM %s WHERE plot_id=?
              ''' % (time_col, col_def, table_name)
        #AND %s BETWEEN ? AND ?
        print('Unbound sql: %s', sql)
        self._cursor.execute(sql, (plot_name,))

        rows = self._cursor.fetchall()

        data = dict()
        data['timestamp'] = [r[0] for r in rows]
        for i, col in enumerate(obs_cols):
            data[col] = [r[i+1] for r in rows]

        return data


    def import_wind_data(self, csv_file, volatile=False, prog_func=None):
        '''
        Read in the data for the hobo loggers.  We currently have this as a
        large single csv.

        param volatile: turn of journaling in sqlite, much faster, but may lose
                        data

        param prog_func: optional progress call back in the form:
                         prog_func(float) that takes a decimal fraction p
                         where:
                         0 =< p =< 1.0
        '''

        if volatile:
            self._cursor.execute('PRAGMA journal_mode=OFF')

        fin = open(csv_file)
        sql = "INSERT INTO cup_vane_obs VALUES(?, ?, ?, ?, ?)"
        i = 0
        fin.readline()
        lines = fin.readlines()
        if prog_func:
            count = len(lines)
            inc = int(float(count) / 100)
            prog_func(0.0)

        self._cursor.execute('BEGIN')
        for line in lines:
            if not line:
                continue
            line = line.split(',')
            plot = '-'.join(line[6:8])
            data = []
            #
            # FIXME: Currently, this plot has a bad timestamp in the giant
            #        file, skip it for now, and load the data from L1G-A13.csv
            #
            if plot == 'L1G-A13':
                continue
            data.append(plot)
            data.append(_import_date(' '.join(line[1:3])))
            data.append(float(line[3]))
            data.append(float(line[4]))
            data.append(float(line[5]))
            self._cursor.execute(sql, tuple(data))
            i += 1
            if not volatile and i % inc == 0:
                self._dbase.commit()
            if prog_func:
                prog_func(float(i) / count)

        self._cursor.execute('END')
        self._dbase.commit()
        if volatile:
            self._cursor.execute('PRAGMA journal_mode=ON')

        if prog_func:
            prog_func(1.0)


    def import_fbp_data(self, path, volatile=False, prog_func=None):
        '''
        Import the fire behavior package data from a path.  This recursively
        runs through and opens any/all csv file and does a very simple header
        check.  Import data is assumed to be constant schema.

        If the path is only on csv file, import that.

        Time is in 2 columns, 1 and 2 as Date and then time

        We import temperature, medtherm, kiel-static probe, narrow-angle
        radiometer, medtherm housing temperature, and battery voltage.

        These are columns 4, (5,6), (27,28), 7, 29, 31

        :param path: path to start recursive import
        :return:
        '''

        csv_files = []
        if path.endswith('.csv'):
            csv_files.append(path)
        else:
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(".csv"):
                         csv_files.append(os.path.join(root, file))

        if not csv_files:
            raise ValueError('Invalid path, no csv files found')
        i = 0
        if prog_func:
            prog_func(0.0)
        csv_count = len(csv_files)

        if volatile:
            self._cursor.execute('PRAGMA journal_mode=OFF')

        sql = 'INSERT INTO fbp_obs VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        plot = 'S8-11'
        h = True
        for csv in csv_files:
            print(csv)
            self._cursor.execute('BEGIN')
            fin = open(csv)
            for line in fin:
                if h:
                    h = False
                    continue
                line = line.split(',')
                date = line[1].strip().replace('/', '-')
                time = line[2].strip()
                dt = date + ' ' + time
                if not dt.find('.') >= 0:
                    dt += '.0'
                else:
                    dt = dt[:-2]
                print dt
                t = float(line[4])
                mtt = float(line[5])
                mtr = float(line[6])
                ksv = float(line[27])
                ksh = float(line[28])
                nar = float(line[7])
                mth = float(line[29])
                bat = float(line[31])
                self._cursor.execute(sql, (plot, dt, t, mtt, mtr, ksv, ksh,
                                           nar, mth, bat))
            self._cursor.execute('END')

        if volatile:
            self._cursor.execute('PRAGMA journal_mode=ON')

        if prog_func:
            prog_func(1.0)


