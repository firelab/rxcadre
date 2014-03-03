#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
#  $Id$
#  Project:  RX Cadre Data Visualization
#  Purpose:  RX Cadre Data Visualization interface.
#  Author:   Kyle Shannon <kyle at pobox dot com>
#            Kegan Rabil <krabil@yourdatasmarter.com>
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
Module for importing spatial time-series data into a searchable format for 
subsetting in space and time.  Typical import format would be csv files.  The
values are imported into a sqlite3 database.  'Meta' tables store information
about what to display.
'''

import argparse
from collections import OrderedDict as dict
import datetime
import logging
import math
import os
import sqlite3
import sys
import time
import zipfile

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

import numpy as np

import scipy.stats as stats

from osgeo import ogr
from osgeo import osr

sys.path.append(os.path.abspath('windrose'))

from windrose import *

###############################################################################
# Logging stuff.
###############################################################################
log_level = { 'debug'    : logging.DEBUG,
              'info'     : logging.INFO,
              'warning'  : logging.WARNING,
              'error'    : logging.ERROR,
              'critical' : logging.CRITICAL }

###############################################################################
# Generic module specific errors
###############################################################################

class RxCadreError(Exception):pass
class RxCadreIOError(RxCadreError):pass
class RxCadreInvalidDbError(RxCadreError):pass
class RxCadreInvalidDataError(RxCadreError):pass


def _import_date(string):
    '''
    Parse a datetime from a UTC string
    '''
    try:
        dt = datetime.datetime.strptime(string, '%m/%d/%Y %I:%M:%S %p')
    except ValueError:
        dt = datetime.datetime.strptime(string, '%m/%d/%y %I:%M:%S %p')

    return dt


def _check_extension(f, ext):
    if ext[0] != '.':
        ext = '.' + ext
    return os.path.splitext(f) == ext


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
    #wkt[0] = _to_decdeg(wkt[0])

    wkt[1] = wkt[1].replace("\"","")
    #wkt[1] = _to_decdeg(wkt[1])

    return tuple([float(c) for c in wkt])

def _export_date(dt):
    '''
    Parse date time and return a string for query
    '''
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def _to_decdeg(d):
    '''
    Split a coordinate in degrees, decimal minutes to decimal degrees
    '''
    logging.info('Converting %s to decimal degrees' % d)
    d = d.split("'")
    s = float(d[-1])
    s = s / 60.0
    d, m = [float(f) for f in d[0].split('\xb0')]
    m += s
    m = m / 60.0
    if d < 0:
        m = m * -1
    d += m
    logging.info('Converted to %f' % d)
    return d


class RxCadre:
    '''
    Main interface for RX Cadre data.
    '''
    def __init__(self, db_file=None, new=False):
        if db_file:
            self.db_file = db_file
        if not new:
            try:
                self.db = sqlite3.connect(db_file)
                self.check_valid_db(self.db)
                self.cur = self.db.cursor()
            except:
                self.db = None
                self.cur = None
                self.db_file = None
        else:
            try:
                self.db = self.init_new_db(db_file)
                self.cur = self.db.cursor()
            except:
                self.db = None
                self.cur = None
                self.db_file = None


    def __del__(self):
        '''
        Cleanup, mainly close the db
        '''
        if self.db:
            self.db.close()

    def set_db(self, db):
        '''
        Set a new db
        '''
        if self.check_valid_db(db):
            self.db = db
            self.cur = self.db.cursor()
        else:
            raise RxCadreInvalidDbError("Could not set new database")

    def check_db(self):
        '''
        Simple check to make sure our internal db handle is good.
        '''
        if self.db is None or self.cur is None:
            raise RxCadreInvalidDbError("Invalid database")


    @property
    def db_file(self):
        '''
        Get the file name of the database
        '''
        return self.db_file

    def check_valid_file(self,filepath):
        f= open(filepath,'r')
        header = f.readline().split(",")
        time = date = plotid = speed = direc = gust = -1
        for i in range(0,len(header)):
            header[i] = header[i].lower()
            if "time" in header[i]:
                time = i
            if "date" in header[i]:
                date = i
            if "plot" in header[i]:
                plotid = i
            if "speed" in header[i]:
                speed = i
            if "direction" in header[i]:
                direc = i
            if "gust" in header[i]:
                gust = i
        if time == -1 or date == -1 or plotid == -1 or speed == -1 or direc == -1 or gust == -1:
            return False
        return True


    def event_time(self,name):
        if name[-3:] != '.db':
            name = name + '.db'
        db = sqlite3.connect(name)
        cursor = db.cursor()
        sql = "SELECT event_start,event_end FROM event WHERE event_name = '"+name+"'"
        cursor.execute(sql)
        time = cursor.fetchall()
        time = time[0]
        begin = str(time[0])
        stop = str(time[1])
        return begin, stop

    def get_min_time(self, name, table):
        db = sqlite3.connect(name)
        cursor = db.cursor()
        sql = "SELECT MIN(timestamp) FROM "+table
        cursor.execute(sql)
        min_time = [t[0] for t in cursor.fetchall()]
        min_time = str(min_time[0])
        min_time = min_time.replace("'","")
        return min_time

    def get_max_time(self,name,table):
        db = sqlite3.connect(name)
        cursor = db.cursor()
        sql = "SELECT MAX(timestamp) FROM "+table
        cursor.execute(sql)
        max_time = [t[0] for t in cursor.fetchall()]
        max_time = str(max_time[0])
        max_time = max_time.replace("'","")
        return max_time


    def change_tables(self,name):
        '''
        I change the values of the table to only those that are present in the
        selected database.
        '''

        if name[-3:] != '.db':
            name = name + '.db'
        db = sqlite3.connect(name)
        if self.check_valid_db(db) == False:
            e ='The selected database appears to be of an incorrect format.  Please select a different database.'
            db.commit()
            db.close()
            os.remove(name)

        else:
            cursor = db.cursor()
            sql  = "SELECT name FROM sqlite_master WHERE type = 'table'"
            cursor.execute(sql)
            tables = cursor.fetchall()
            tables = [t[0] for t in tables]

            return tables

    def change_picker(self,name, table):
        """
        I change the values in the plot_id_picker to only those that are
        actually in the selected table, be it from imported data or stored
        in the database.
        """

        if name[-3:] != '.db':
            name = name + '.db'
        db = sqlite3.connect(name)
        cursor = db.cursor()
        sql  = "SELECT plot_id FROM plot_location"
        cursor.execute(sql)
        plots = cursor.fetchall()
        plots_new = []
        plots = [p[0] for p in plots]
        for i in range(0,len(plots)):
            plots[i] = str(plots[i])
            if plots[i] not in plots_new:
                plots_new.append(plots[i])
        return plots_new

    def init_new_db(self, filename):
        '''
        Create a new, empty database with appropriate metatables.  If the file
        previously exists, we fail before connecting using sqlite.  It must be
        a new file.
        '''
        if(os.path.exists(filename)):
            raise RxCadreIOError("File exists.")
        db = sqlite3.connect(filename)
        if not db:
            raise RxCadreIOError("Could not create database")
        cursor = db.cursor()
        sql = '''CREATE TABLE plot_location(plot_id TEXT, x REAL, y REAL,
                                            geometry TEXT, plot_type TEXT)'''
        cursor.execute(sql)
        sql = '''CREATE TABLE event(project_name TEXT,
                                    event_name TEXT NOT NULL,
                                    event_start TEXT NOT NULL,
                                    event_end TEXT NOT NULL,
                                    PRIMARY KEY(project_name, event_name))'''
        cursor.execute(sql)
        sql = '''CREATE TABLE obs_table(obs_table_name TEXT NOT NULL,
                                        table_display name TEXT,
                                        timestamp_column TEXT NOT NULL,
                                        geometry_column TEXT NOT NULL,
                                        obs_cols TEXT NOT NULL,
                                        obs_col_names TEXT)
              '''

        cursor.execute(sql)
        db.commit()
        #update tables, update events, set db_picker to filename
        valid = self.check_valid_db(db)
        if not valid:
            db.close()
            e = "Failed to create a valid database."
            self.RxCadreIOError(e)
        else:
            return db


    def check_valid_db(self, db):
        '''
        Check the schema of an existing db.  This involves checking the
        metatables, and checking to make sure tables registered in obs_tables
        exist.
        '''

        cursor = db.cursor()
        required_tables = set(['plot_location', 'event', 'obs_table'])
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t[0] for t in cursor.fetchall()]
        if not set(table_names) >= required_tables:
            e = "Database does not contain the required tables, missing:"
            e += ",".join(required_tables.difference(table_names))
            return False
        cursor.execute("select obs_table_name from obs_table")

        obs_names = [o[0] for o in cursor.fetchall()]
        for name in obs_names:
            if name not in table_names:
                e = "Database is invalid, missing table: "
                return False
        return True

    def update_events(self, name):

        if name[-3:] != '.db':
            name = name+'.db'
        db = sqlite3.connect(name)
        cursor = db.cursor()

        sql = "SELECT event_name FROM event"
        cursor.execute(sql)
        events = [c[0] for c in cursor.fetchall()]

        return events

    def get_obs_table_names(self):
        '''
        Get the names of all stored observation tables as a list of strings.
        '''
        self.check_db()
        sql = "SELECT obs_table_name FROM obs_table"
        self.cur.execute(sql)
        names = [n[0] for n in self.cur.fetchall()]
        return names


    def get_event_data(self, event_name=None):
        '''
        Get the event names and the start, stop times for the events.
        '''
        self.check_db()
        sql = "SELECT event_name, event_start, event_end from event"
        if event_name:
            sql += ' WHERE event_name=?'
            self.cur.execute(sql, (event_name,))
        else:
            self.cur.execute(sql)
        events = dict()
        for row in self.cur.fetchall():
            events[row[0]] = (row[1], row[2])
        return events


    def get_plot_data(self, plot_name=None):
        '''
        Get simple plot information.
        '''
        self.check_db()
        if not plot_name:
            sql = "SELECT plot_id, geometry, plot_type from plot_location"
            self.cur.execute(sql)
        else:
            sql = '''
                  SELECT plot_id, geometry, x, y, plot_type FROM
                  plot_location WHERE plot_id=?
                  '''
            self.cur.execute(sql, (plot_name,))
        plots = []
        for row in self.cur.fetchall():
            plots.append(list(row))
        return plots


    def get_obs_cols(self, table_name):
        '''
        Get the observation column names
        '''
        sql = '''SELECT obs_cols, obs_col_names FROM obs_table WHERE obs_table_name=?'''
        self.cur.execute(sql, (table_name,))
        row = self.cur.fetchone()
        if not row:
            raise RxCadreInvalidDataError('Table %s is not in obs_table' %
                                          table_name)
        return dict(zip([obs for obs in row[0].split(',')],
                        [obs for obs in row[1].split(',')]))


    def point_location(self, plot, db):
        '''
        Fetch the x and y coordinate of the plot
        '''
        cursor = db.cursor()
        sql = '''SELECT geometry FROM plot_location WHERE plot_id=?'''
        cursor.execute(sql, (plot,))
        row = cursor.fetchone()
        return _extract_xy(row[0])


    def fetch_point_data(self, plot, table,start, end,db):
        '''
        Fetch data for a single point
        '''

        cursor = db.cursor()
        sql = '''SELECT * FROM '''+table+'''
                          WHERE plot_id=? AND timestamp BETWEEN datetime(?)
                           AND datetime(?)'''
        #Note to self: removed quality tab from this.  may want to keep it
        cursor.execute(sql, (plot,_export_date(start),_export_date(end)))
        results = cursor.fetchall()
        if (results != []):
            data = [(t[0],t[1],t[2],t[3],t[4]) for t in results]
        if (results == []):
            e = 'The timeframe selected contains no data for this table.'
            raise RxCadreIOError(e)

        logging.info('Query fetched %i result(s)' % len(data))
        return data

    def calc_statistics(self, data):
        '''
        Generic, normal stats.
        '''
        stats = dict()
        for k,v in data.items():
            if k == 'direction' or k == 'timestamp':
                continue
            samples = np.array(v)
            min = np.min(samples)
            max = np.max(samples)
            mean = np.mean(samples)
            std = np.std(samples)
            stats[k] = (min, max, mean, std)
        return stats

    def calc_circ_statistics(self, data):

        try:
            d = data['direction']
        except KeyError:
            return (0, 0, 0, 0)
        samples = np.array(d)
        min = np.min(d)
        max = np.max(d)
        mean = stats.morestats.circmean(samples, 360, 0)
        std = stats.morestats.circstd(samples, 360, 0)
        return (min, max, mean, std)


    def statistics(self, data,plot,db):
        '''
        Calculate the stats for speed and direction data
        '''
        '''Made it so this function can pull data from db or file'''
        if type(data) == str:
            cursor = db.cursor()

            sql = "SELECT plot_id,timestamp,speed,direction,gust FROM "+data+" WHERE plot_id= '"+plot+"'"

            cursor.execute(sql)
            data = cursor.fetchall()

            spd = [float(spd[2]) for spd in data]
            gust = [float(gust[4]) for gust in data]
            dir = [float(dir[3]) for dir in data]
        if type(data) == list:
            spd = [float(spd[2]) for spd in data]
            gust = [float(gust[4]) for gust in data]
            dir = [float(dir[3]) for dir in data]
        samples = np.array(spd)
        spd_mean = np.mean(samples)
        spd_stddev = np.std(samples)
        samples = np.array(gust)
        gust_max = np.max(samples)
        samples = np.array(dir)
        direction_mean = stats.morestats.circmean(samples, 360, 0)
        direction_stddev = stats.morestats.circstd(samples, 360, 0)
        return (spd_mean, spd_stddev), (gust_max), (direction_mean, direction_stddev)


    def _point_kml(self, plot, data, images=[]):
        '''
        Create a kml representation of a plot
        '''

        #lon, lat = self.point_location(plot,db)
        lon, lat = _extract_xy(self.get_plot_data(plot)[0][1])
        stats = self.calc_statistics(data)
        stats['direction'] = self.calc_circ_statistics(data)
        if stats is None:
            logging.warning('Could not calculate stats')
            return ''
        wind = True
        try:
            d = stats['direction'][2]
            if d < 0:
                d = d + 360.0
        except KeyError:
            wind = False
        stat_order = ('min', 'max', 'mean', 'stddev')

        kml =               '  <Placemark>\n'
        if wind:
            kml = kml +     '    <Style>\n' \
                            '      <IconStyle>\n' \
                            '        <Icon>\n' \
                            '          <href>http://maps.google.com/mapfiles/kml/shapes/arrow.png</href>\n' \
                            '        </Icon>\n' \
                            '        <heading>%s</heading>\n' % d
            kml = kml +     '      </IconStyle>\n' \
                            '    </Style>\n'
        kml = kml +         '    <Point>\n' \
                            '      <coordinates>%.9f,%.9f,0</coordinates>\n' \
                            '    </Point>\n' % (lon, lat)
        kml = kml +         '    <name>%s</name>\n' \
                            '    <description>\n' \
                            '      <![CDATA[\n' % plot
        for image in images:
            kml = kml +     '        <img src = "%s" />\n'  % image
        kml = kml +         '        <table border="1">' \
                            '          <tr>\n' \
                            '            <th>Stats</th>\n' \
                            '          </tr>\n'
        for key in stats.keys():
            for i, s in enumerate(stats[key]):
                kml = kml + '          <tr>\n' \
                            '            <td>%s</td>\n' \
                            '            <td>%.2f</td>\n' \
                            '          </tr>\n' % (stat_order[i], stats[key][i])
        kml = kml +         '        </table>\n' \
                            '      ]]>\n' \
                            '    </description>\n' \
                            '  </Placemark>\n'
        return kml


    def extract_obs_data(self, table_name, plot_name, start=None, end=None):
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

        :return: A dictionary with keys of {obs_cols:obs_names} keys and lists
                 of values, ie:

                 {'wind_spd' : 'Wind Speed(mph)'} : [2.3,4.6,4.4]}
        '''

        sql = '''SELECT * FROM obs_table WHERE obs_table_name=?'''
        self.cur.execute(sql, (table_name,))
        row = self.cur.fetchone()
        if not row:
            raise RxCadreInvalidDataError('Table %s is not in obs_table' %
                                          table_name)
        time_col = row[2]
        obs_cols = [c.strip() for c in row[3].split(',')]
        if not start:
            sql = 'SELECT MIN(datetime(%s)) FROM %s WHERE plot_id=?' % (time_col, table_name)
            self.cur.execute(sql, (plot_name,))
            start = datetime.datetime.strptime(self.cur.fetchone()[0],
                                               '%Y-%m-%d %H:%M:%S')
        if not end:
            sql = 'SELECT MAX(datetime(%s)) FROM %s WHERE plot_id=?' % (time_col, table_name)
            self.cur.execute(sql, (plot_name,))
            end = datetime.datetime.strptime(self.cur.fetchone()[0],
                                             '%Y-%m-%d %H:%M:%S')
        sql = '''
              SELECT %s as timestamp, %s FROM %s WHERE plot_id=? AND 
              datetime(%s) BETWEEN datetime(?) AND datetime(?)
              ''' % (time_col, ','.join(obs_cols), table_name, time_col)

        logging.debug('Unbound sql: %s' % sql)
        self.cur.execute(sql, (plot_name, start, end))

        rows = self.cur.fetchall()

        data = dict()
        # FIXME: Hack for different types of tables.
        if 'direction' in set(obs_cols):
            data['timestamp'] = [datetime.datetime.strptime(r[0] + '.0', '%Y-%m-%d %H:%M:%S.%f') for r in rows]
        else:
            data['timestamp'] = [datetime.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S.%f') for r in rows]
        for i, c in enumerate(obs_cols):
            data[c] = [r[i+1] for r in rows]

        return data

    def create_time_series_image(self, data, plt_title, start, end, filename=''):
        '''
        Create a time series image for the plot over the time span
        '''
        '''
        if type(data) == list:
            spd = [float(spd[2]) for spd in data]
            gust = [float(gust[4]) for gust in data]
            dir = [float(dir[3]) for dir in data]
            time = [mdates.date2num(datetime.datetime.strptime(d[1],'%Y-%m-%d %H:%M:%S')) for d in data]
        if type(data) == str:
            cursor = db.cursor()
            sql = """SELECT * FROM """+data+"""
                          WHERE plot_id=? AND timestamp BETWEEN ? 
                           AND ?"""
            #Note to self: removed quality tab from this.  may want to keep it
            cursor.execute(sql, (plt_title,_export_date(start),_export_date(end)))
            data = cursor.fetchall()
            spd = [float(spd[2]) for spd in data]
            gust = [float(gust[4]) for gust in data]
            dir = [float(dir[3]) for dir in data]
            time = [mdates.date2num(datetime.datetime.strptime(d[1],'%Y-%m-%d %H:%M:%S')) for d in data]
        '''

        # FIXME: Hack for different data.
        wind = True
        try:
            data['direction']
        except KeyError:
            wind = False

        fig = plt.figure()
        time = [mdates.date2num(d) for d in data['timestamp']]
        if not wind:
            cols = self.get_obs_cols('fbp_obs')
            i = 1
            for k,v in cols.items():
                ax = fig.add_subplot(len(cols), 2, i)
                ax.plot_date(time, data[k])
                i += 1
        else:
            #fig = plt.figure(figsize=(8,8), dpi=80)
            ax1 = fig.add_subplot(211)
            ax1.plot_date(time, data['speed'], 'b-')
            #ax1.plot_date(time, data['gust'], 'g-')
            ax1.set_xlabel('Time (s)')
            ax1.set_ylabel('Speed(mph)', color = 'b')
            ax2 = fig.add_subplot(212)
            ax2.plot_date(time, data['direction'], 'r.')
            ax2.set_ylabel('Direction', color='r')

        fig.autofmt_xdate()
        plt.suptitle('Plot %s from %s to %s' % (plt_title, 
                     data['timestamp'][0].strftime('%m/%d/%Y %I:%M:%S %p'),
                     data['timestamp'][-1].strftime('%m/%d/%Y %I:%M:%S %p')))
        if not filename:
            plt.show()
            plt.close()
        else:
            plt.savefig(filename)
            plt.close()
        return filename


    def create_windrose(self, data, plt_title, start, end, filename=''):
        '''
        Create a windrose from a dataset.
        '''

        try:
            data['direction']
        except KeyError:
            return
        if len(data['direction']) >= 1:
            #fig = plt.figure(figsize=(8, 8), dpi=80, facecolor='w', edgecolor='w')
            fig = plt.figure(facecolor='w', edgecolor='w')
            rect = [0.1, 0.1, 0.8, 0.8]
            ax = WindroseAxes(fig, rect, axisbg='w')
            fig.add_axes(ax)
            try:
                ax.bar(data['direction'], data['speed'], normed=True, opening=0.8,
                       edgecolor='white')
            except ValueError as e:
                print(e)
                print('Invalid data for %s' % plt_title)
                raise e
            l = ax.legend(axespad=-0.10)
            #l = ax.legend(1.0)
            plt.setp(l.get_texts(), fontsize=8)
            if filename == '':
                plt.show()
                plt.close()
            else:
                plt.savefig(filename)
                plt.close()
            return filename
        else:
            raise ValueError("Invalid data")

    def create_csv(self, data, start, end, filename):
        '''
        Create a csv dump
        '''
        if not data:
            return
        time = [datetime.datetime.strftime(t, '%Y%m%dT%H:%M:%S') for t in data['timestamp']]
        n = len(time)
        if not n:
            return
        speed = [str(s) for s in data['speed']]
        direction = [str(d) for d in data['direction']]
        gust = [str(g) for g in data['gust']]
        fout = open(filename, 'w')
        fout.write('timestamp,speed,direction,gust\n')
        for i in range(n):
            fout.write(','.join([time[i], speed[i], direction[i], gust[i]]))
            fout.write('\n')
        fout.close()

    def create_ogr(self,path,table,filename,start,end,db):
        '''
        Creates a terrifying Ogre with a CR of 50, 2500 hp, 4d20 + 32 crushing
        damage in an AoE of 15 yds and a basic move of 160.  Suggested loot for
        dispatching the beast: 2500 gold pieces, 1d6 Ogre's Toes, Sword of Greater Banish Evil,
        the remains of Sir Galdrich and the gratitude of King Balther, Lord of Castle Grazen.
        '''

        cursor = db.cursor()
        sql = '''SELECT DISTINCT(plot_id) FROM '''+table+'''
                   WHERE timestamp BETWEEN ? AND ?'''
        cursor.execute(sql, (start, end))
        plots = [c[0] for c in cursor.fetchall()]


        user_frmt = 'ESRI Shapefile'
        driver = ogr.GetDriverByName(user_frmt)
        os.chdir(path) 
        # create a new data source and layer
        if os.path.exists(filename + '.shp'):
            driver.DeleteDataSource(filename +'.shp') 
        ds = driver.CreateDataSource(filename +'.shp')
        if ds is None:
            print('Could not create file')
            raise RxCadreIOError('Could not create OGR datasource')
        SR = osr.SpatialReference()
        SR.ImportFromEPSG(4269)
        SR.ExportToPrettyWkt()
        layer = ds.CreateLayer(filename,SR, geom_type=ogr.wkbPoint)
        featureDefn = layer.GetLayerDefn()


        #FIELDS:
        SR = osr.SpatialReference()
        SR.ImportFromEPSG(4269)

        fieldDefn = ogr.FieldDefn('Plot ID', ogr.OFTString)
        fieldDefn.SetWidth(50)
        layer.CreateField(fieldDefn)

        fieldDefn2 = ogr.FieldDefn('Speed Mean', ogr.OFTString)
        fieldDefn2.SetWidth(50)
        layer.CreateField(fieldDefn2)

        fieldDefn3 = ogr.FieldDefn('Spd Stdev', ogr.OFTString)
        fieldDefn3.SetWidth(50)
        layer.CreateField(fieldDefn3)

        fieldDefn4 = ogr.FieldDefn('Gust Max', ogr.OFTString)
        fieldDefn4.SetWidth(50)
        layer.CreateField(fieldDefn4)

        fieldDefn5 = ogr.FieldDefn('Dir Mean', ogr.OFTString)
        fieldDefn5.SetWidth(50)
        layer.CreateField(fieldDefn5)

        fieldDefn6 = ogr.FieldDefn('Dir Stdev', ogr.OFTString)
        fieldDefn6.SetWidth(50)
        layer.CreateField(fieldDefn6)

        for plot in plots:
            plot = str(plot)
            sql  = '''SELECT x,y FROM plot_location WHERE plot_id = ''''+plot+'''''''

            cursor.execute(sql)
            loc = cursor.fetchall()

            loc = loc[0]

            (spd_mean, spd_stddev), gust_max, (direction_mean, direction_stddev) = self.statistics(table,plot,db)

            # create a new point object
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(loc[0],loc[1])


            #NOW OUR FEATURE PRESENTATION:
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(point)
            feature.SetField('Plot ID', plot)
            feature.SetField('Speed Mean', str(spd_mean))
            feature.SetField('Spd Stdev', str(spd_stddev))
            feature.SetField('Gust Max', str(gust_max))
            feature.SetField('Dir Mean', str(direction_mean))
            feature.SetField('Dir Stdev',str(direction_stddev))


            # add the feature to the output layer
            layer.CreateFeature(feature)

            #small destroy
            point.Destroy()
            feature.Destroy()

        #DESTROY!
        ds.Destroy()


    def create_field_kmz(self, filename, table,start,end,plotID,path,db):
        '''
        Write a kmz with a time series and wind rose.  The stats are included
        in the html bubble as well.
        '''
        cursor = db.cursor()
        sql = '''SELECT DISTINCT(plot_id) FROM '''+table+'''
                   WHERE timestamp BETWEEN ? AND ?'''
        cursor.execute(sql, (start, end))

        kmz = zipfile.ZipFile( filename + '_field.kmz', 'w', 0, True)
        kmlfile = 'doc.kml'
        fout = open(kmlfile, 'w')
        fout.write('<Document>\n')

        plots = cursor.fetchall()
        for plot in plots:
            plot = plot[0]
            logging.info('Processing plot %s' % plot)
            if filename == '':
                filename = plot
            if filename[-4:] != '.kmz':
                filename = filename + '.kmz'

            data = self.fetch_point_data(plot,table,start,end,db)
            if not data:
                continue
            try:
                pngfile = os.path.join(path,plotID + '_time.png')
                rosefile = os.path.join(path,plotID + '_rose.png')
                kml = self._point_kml(plot, data, db,[pngfile,rosefile])
            except Exception as e:
                logging.warning('Unknown exception has occurred')
                #if os.path.exists(pngfile):
                #    os.remove(pngfile)
                #if os.path.exists(rosefile):
                #    os.remove(rosefile)
                continue

            fout.write(kml)
            fout.flush()

            kmz.write(pngfile)
            kmz.write(rosefile)
        fout.write('</Document>\n')
        fout.close()
        kmz.write(kmlfile)
        kmz.close()
        os.remove(kmlfile)
        return filename


    def create_kmz(self, plot, filename,table,start,end,pngfile,rosefile,data):
        '''
        Write a kmz with a time series and wind rose.  The stats are included
        in the html bubble as well.
        '''
        if filename == '':
            filename = plot
        if filename[-4:] != '.kmz':
            filename = filename + '.kmz'

        if rosefile == '':
            images = [pngfile,]
        else:
            images = [pngfile, rosefile]
        kml = self._point_kml(plot, data, images)

        kmlfile = 'doc.kml'
        fout = open(kmlfile, 'w')
        fout.write(kml)
        fout.close()

        kmz = zipfile.ZipFile( filename, 'w', 0, True)
        kmz.write(kmlfile)
        for image in images:
            kmz.write(image)
        kmz.close()
        os.remove(kmlfile)
        for image in images:
            os.remove(image)
        return filename


    def create_csv_old(self, plot, filename,table,start,end,data,db):
        if filename == '':
            filename = plot
        if filename[-4:] != '.csv':
            filename = filename + '.csv'

        #data = self.fetch_point_data(plot,table,start,end,db)
        file = open(filename,"w+")
        file.write('PlotID,DateTime, Speed, Direction, Gust' + '\n')
        for d in data:
            d = str(d)
            d = d.replace("u'","")
            d = d.replace("'","")
            d = d.replace("(","")
            d = d.replace(")","")

            file.write(d+ "\n")
        #file.write(data)
        file.close()


    def import_data(self,input_csv,db):

        '''Create a table from a selected file in the current database.
        Import the appropriate columns and populate with associated data.'''
        name = db
        if name[-3:] != '.db':
            name = name + '.db'
        db = sqlite3.connect(name)
        cursor = db.cursor()
        title = os.path.basename(input_csv)
        title = title[:title.index(".")]
        db.text_factory = str
        data_file = open(input_csv,"r")
        header = data_file.readline().split(",")
        for i in range(0,len(header)):
            header[i] = header[i].replace('\n',"")
            header[i] = header[i].replace('+',"")
            header[i] = header[i].replace(":","")
            header[i] = header[i].replace(")","")
            header[i] = header[i].replace("(","")

        hold_name = title

        time = date = plotid = speed = direc = gust = -1
        for i in range(0,len(header)):
            header[i] = header[i].lower()
            if "time" in header[i]:
                time = i
            if "date" in header[i]:
                date = i
            if ("plot" in header[i]) and ("id" in header[i]):
                plotid = i
            if "speed" in header[i]:
                speed = i
            if "direction" in header[i]:
                direc = i
            if "gust" in header[i]:
                gust = i
            if ("tag" in header[i]) and ("id" in header[i]):
                tagid = i
            if "latitude" in header[i]:
                lat = i
            if "longitude" in header[i]:
                lon = i
            if ("instrument" in header[i]) and ("id" in header[i]):
                instrid = i
        if time == -1 or date == -1 or plotid == -1 or speed == -1 or direc == -1 or gust == -1:
            e = '''
The selected data does not include the necessary fields for analysis. 
Please make sure that the selected data includes a separate
time, date, plotID, wind speed, wind direction and wind gust column
                                '''

        else:

            cursor.execute("CREATE TABLE "+hold_name+'''(plot_id TEXT,
                                                        timestamp DATETIME, speed TEXT,
                                                        direction TEXT, gust TEXT)''')

            n = 0
            line = data_file.readline()
            line = line.split(",")
            begin = line[time]
            end = line[time]
            plot_id = [line[plotid]]
            instr_id = line[instrid]
            instr_id2 = 0
            while (line != None):
                n = n+1
                if len(line) < len(header):
                    break
                else:
                    new_data = line[plotid],_import_date(line[date]+" "+line[time]),line[speed],line[direc],line[gust]
                    cursor.execute("INSERT INTO "+hold_name+" VALUES (?,?,?,?,?)", new_data)
                    if line[time] < begin:
                        begin = line[time]
                    if line[time] > end:
                        end = line[time]
                    if line[plotid] not in plot_id:
                        plot_id.append(line[plotid])

                instr_id = line[instrid]
                if (instr_id != instr_id2):
                    plot_vals = line[plotid],str(_to_decdeg(line[lon].replace("\"",""))), str(_to_decdeg(line[lat].replace("\"",""))),"POINT("+str(_to_decdeg(line[lon].replace("\"","")))+" "+str(_to_decdeg(line[lat].replace("\"","")))+")",line[tagid]
                    cursor.execute("INSERT INTO plot_location VALUES (?,?,?,?,?)",plot_vals)

                instr_id2 = line[instrid]
                line = data_file.readline()
                line = line.split(",")

            sql = "SELECT plot_id FROM plot_location"
            cursor.execute(sql)
            plots = cursor.fetchall()
            plots_hold = []

            obs_vals =  hold_name,"PlotID, Timestamp,Wind Speed,Wind Direction(from North),Wind Gust",header[time], "wkd_geometry", "id,time,speed,dir,gust", "plot_id,time,speed,dir,gust" 
            cursor.execute("INSERT INTO obs_table VALUES (?,?,?,?,?,?)",obs_vals)

            db.commit()
            db.close()
            p = "Data imported successfully"

    def bulk_extract(self, plots, start, end, out_path='.',
                                              field_kmz='',
                                              timeseries='',
                                              windrose='',
                                              ogr='',
                                              csv=''):
        all_plots = self.get_plot_data()
        plot_dict = dict(zip([p[0] for p in all_plots], [p[4] for p in all_plots]))
        plots = args.plots
        for plot in plots:
            try:
                plot_dict[plot]
            except keyerror:
                print("invalid plot specified")
                sys.exit(1)

        if not plots:
            plots = [p[0] for p in all_plots]
        #
        # if we are showing plots, limit it to one plot
        #
        show = args.show_only
        if show:
            #plots = plots[:1]
            pass
        for plot in plots:
            if plot_dict[plot] == 'FBP':
                data = self.extract_obs_data('fbp_obs', plot, start, end)
            elif plot_dict[plot] == 'WIND':
                data = self.extract_obs_data('cup_vane_obs', plot, start, end)
            if not data['timestamp']:
                if not quiet:
                    print('Plot %s does not exist' % plot)
                continue
            if args.timeseries or args.kmz:
                if show:
                    self.create_time_series_image(data, plot, start, end)
                else:
                    self.create_time_series_image(data, plot, start, end,
                                                plot + '_ts.png')
            if args.rose or args.kmz:
                try:
                    if show:
                        self.create_windrose(data, plot, start, end)
                    else:
                        self.create_windrose(data, plot, start, end,
                                           plot + '_wr.png')
                except ValueError:
                    if os.path.exists(plot+'_ts.png'):os.remove(plot+'_ts.png')
                    continue
            if args.kmz:
                if plot_dict[plot] == 'WIND':
                    self.create_kmz(plot, plot + '.kmz', None, start, end,
                                  plot + '_ts.png', plot + '_wr.png', data)
                else:
                    self.create_kmz(plot, plot + '.kmz', None, start, end,
                                  plot + '_ts.png', '', data)

def rxcadre_main(args):
    '''
    Run the command line stuff.
    '''

    quiet = args.quiet
    if not quiet:
        try:
            logging.basicConfig(level=log_level[args.level.lower()])
        except KeyError:
            logging.basicConfig(logging.CRITICAL)

    if args.sub_cmd == 'create':
        rx = RxCadre(args.database, new=True)
        rx.init_new_db(args.database)

    else:
        try:
            rx = RxCadre(args.database)
        except RxCadreError as e:
            print(e)
            sys.exit(1)

        if args.sub_cmd == 'info':
            quiet = False
            if args.show_obs_tables:
                names = rx.get_obs_table_names()
                print('Tables: %s' % ','.join(names))
            if args.show_events:
                events = rx.get_event_data()
                print('Events:')
                if events:
                    for k, v in events.items():
                        print('    %s (%s to %s)' % (k, v[0], v[1]))
            if args.show_plots:
                plots = rx.get_plot_data()
                print('Plots:')
                for p in plots:
                    print('    %s, %s' % (p[0], p[1]))

        elif args.sub_cmd == 'export':

            # Check the time(s)
            if args.event and (args.start or args.end):
                if not quiet:
                    print('Conflicting time options, choose event *or* start/end')
                sys.exit(1)
            if args.event:
                try:
                    start, end = tuple(rx.get_event_data(args.event)[args.event])
                    start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                except KeyError:
                    print("Event %s does not exist" % args.event)
                    sys.exit(1)
                logging.debug('Setting time bounds from event: %s(%s, %s)', 
                              args.event, str(start), str(end))

            elif args.start or args.end:
                try:
                    start = datetime.datetime.strptime(args.start,
                                                       '%Y%m%dT%H%M')
                except ValueError:
                    print('Invaild start date, must be in the format of: ' \
                          'YYYYMMDDTHHMM')
                    sys.exit(1)
                try:
                    end = datetime.datetime.strptime(args.end,
                                                     '%Y%m%dT%H%M')
                except ValueError:
                    print('Invaild end date, must be in the format of: ' \
                          'YYYYMMDDTHHMM')
                    sys.exit(1)

            else:
                start = None
                end = None

            if(start > end):
                print('Start time must be less than end time')
                sys.exit()

            all_plots = rx.get_plot_data()
            plot_dict = dict(zip([p[0] for p in all_plots], [p[2] for p in all_plots]))
            plots = args.plots
            for plot in plots:
                try:
                    plot_dict[plot]
                except KeyError:
                    print("Invalid plot specified")
                    sys.exit(1)

            if not plots:
                plots = [p[0] for p in all_plots]
            #
            # If we are showing plots, limit it to one plot
            #
            show = args.show_only
            if show:
                plots = plots[:1]
                pass
            for plot in plots:
                if plot_dict[plot] == 'FBP':
                    data = rx.extract_obs_data('fbp_obs', plot, start, end)
                elif plot_dict[plot] == 'WIND':
                    data = rx.extract_obs_data('cup_vane_obs', plot, start, end)
                if not data['timestamp']:
                    if not quiet:
                        print('Plot %s does not exist' % plot)
                    continue
                if args.timeseries or args.kmz:
                    if show:
                        rx.create_time_series_image(data, plot, start, end)
                    else:
                        rx.create_time_series_image(data, plot, start, end,
                                                    plot + '_ts.png')
                if args.rose or args.kmz:
                    try:
                        if show:
                            rx.create_windrose(data, plot, start, end)
                        else:
                            rx.create_windrose(data, plot, start, end,
                                               plot + '_wr.png')
                    except ValueError:
                        if(os.path.exists(plot+'_ts.png')):os.remove(plot+'_ts.png')
                        continue
                if args.kmz:
                    if plot_dict[plot] == 'WIND':
                        rx.create_kmz(plot, plot + '.kmz', None, start, end,
                                      plot + '_ts.png', plot + '_wr.png', data)
                    else:
                        rx.create_kmz(plot, plot + '.kmz', None, start, end,
                                      plot + '_ts.png', '', data)
                if args.csv:
                    print(plot)
                    rx.create_csv(data, start, end, plot + '.csv')

if __name__ == "__main__":
    '''
    Command line interface for extracting data.  Users should be able to use
    the cli for extracting one or more plots for a given time period or event.
    Users should also be able to extract meta information from a db.  Editing
    is also allowed.  The functions are accessed via the subcommands:
    rxcadre create
    rxcadre import
    rxcadre export
    rxcadre info
    rxcadre edit
    '''

    '''
    Main parser.  All commands take a database to act on, so that is the last
    argument for everything.
    '''
    parser = argparse.ArgumentParser(prog='rxcadre')
    subparsers = parser.add_subparsers(help='sub-command help', dest='sub_cmd')

    '''
    Create a new database parser.  Only needs the database name.
    '''
    parser_create = subparsers.add_parser('create', help='Create an empty db')

    '''
    Import csv parser with options for naming the table and columns.
    parser_import = subparsers.add_parser('import', help='Import csv data')
    parser_import.add_argument('input_file', type=str,
                               help='csv file to import')
    parser_import.add_argument('--columns', dest='columns', type=str,
                               nargs='*', default=[],
                               help='Columns to import, default is all')
    parser_import.add_argument('--column_names', dest='column_names',
                               type=str, nargs='*', default=[],
                               help='Display column names')
    '''
    '''
    Export parser.
    '''
    parser_extract = subparsers.add_parser('export', help='Extract plot data')
    parser_extract.add_argument('--plots', dest='plots', type=str,
                                nargs='*', default=[],
                                help='Plot names to extract')
    parser_extract.add_argument('--plot-type', dest='plot_type', type=str,
                                default='', help='WIND or FBP')
    parser_extract.add_argument('--start', dest='start', type=str,
                                default=None, help='Start time for subset')
    parser_extract.add_argument('--end', dest='end', type=str,
                                default=None, help='End time for subset')
    parser_extract.add_argument('--event', dest='event', type=str,
                                default='', help='Use start/end from an event')
    parser_extract.add_argument('--kmz', dest='kmz', action='store_true',
                                help='Create a kmz file')
    parser_extract.add_argument('--csv', dest='csv', action='store_true',
                                default='', help='Create a csv file')
    parser_extract.add_argument('--rose', dest='rose', action='store_true',
                                help='Create a windrose file')
    parser_extract.add_argument('--timeseries', dest='timeseries',
                                action='store_true',
                                help='Create a timeseries file')
    parser_extract.add_argument('--ogr', dest='ogr_frmt', type=str,
                                default='ESRI Shapefile',
                                help='Create an ogr dataset using this driver')
    parser_extract.add_argument('--show-only', dest='show_only',
                                action='store_true',
                                help='Show the images, don\'t write a file')
    parser_extract.add_argument('--path', type=str, default='.',
                                help='Output file path')
    #parser_extract.add_argument('--zip', dest='zip', action='store_true',
    #                            help='Create a zip file for all output')

    '''
    Information parser.
    '''
    parser_info = subparsers.add_parser('info', help='Show db information')
    parser_info.add_argument('--tables', dest='show_obs_tables',
                             action='store_true',
                             help='Show observation tables in a database')
    parser_info.add_argument('--events', dest='show_events',
                             action='store_true',
                             help='Show events tables in a database')
    parser_info.add_argument('--plots', dest='show_plots',
                             action='store_true',
                             help='Show plot information in a database')

    '''
    Edit parser.
    parser_edit = subparsers.add_parser('edit', help='Update db information')
    '''

    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet',
                        help='Do not output to stdout')
    parser.add_argument('-l', '--logging', type=str, dest='level',
                        default='critical',
                        help='Logging level(DEBUG,INFO,WARNING,ERROR,CRITICAL')
    parser.add_argument('database', type=str, help='Database to act on')

    args = parser.parse_args()
    logging.info(args)
    try:
        rxcadre_main(args)
    except RxCadreError as e:
        print(e)
        sys.exit(1)
    sys.exit(0)


