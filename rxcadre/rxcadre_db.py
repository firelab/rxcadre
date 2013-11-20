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
#  relinquishment in perpetuity of all present and future rights to this
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

import logging
import sqlite3

###############################################################################
# Logging stuff.
###############################################################################
logging.basicConfig(level=logging.INFO)


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


    def _init_new_db(self):
        '''
        Create a new, empty database with appropriate metatables.  If the file
        previously exists, we fail before connecting using sqlite.  It must be
        a new file.
        '''
        sql = '''CREATE TABLE plot_location(plot_id TEXT, x REAL, y REAL,
                                            geometry TEXT, plot_type TEXT)'''
        self._cursor.execute(sql)
        sql = '''CREATE TABLE event(project_name TEXT,
                                    event_name TEXT NOT NULL,
                                    event_start TEXT NOT NULL,
                                    event_end TEXT NOT NULL,
                                    PRIMARY KEY(project_name, event_name))'''
        self._cursor.execute(sql)
        sql = '''CREATE TABLE obs_table(obs_table_name TEXT NOT NULL,
                                        table_display name TEXT,
                                        timestamp_column TEXT NOT NULL,
                                        geometry_column TEXT NOT NULL,
                                        obs_cols TEXT NOT NULL,
                                        obs_col_names TEXT)
              '''

        self._cursor.execute(sql)
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
        self._cursor.execute(sql, table_name, table_name, time_col,
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


    def point_location(self, plot, db):
        '''
        Fetch the x and y coordinate of the plot
        '''
        sql = '''SELECT geometry FROM plot_location WHERE plot_id=?'''
        self._cursor.execute(sql, (plot,))
        row = cursor.fetchone()
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
        # TODO: Check columns against supplied columns, not supported yet.
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
        logging.debug('Unbound sql: %s', sql)
        self._cursor.execute(sql, (plot_name,))

        rows = self._cursor.fetchall()

        data = dict()
        data['timestamp'] = [r[0] for r in rows]
        for i, col in enumerate(obs_cols):
            data[col] = [r[i+1] for r in rows]

        return data


