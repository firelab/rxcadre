#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
#  $Id$
#  Project:  RX Cadre Data Visualization
#  Purpose:  Import csv data into tables
#  Author:   Kyle Shannon <kyle@pobox.com>
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
"""
Module for importing spatial time-series data into a searchable format for 
subsetting in space and time.  Typical import format would be csv files.  The
values are imported into a sqlite3 database.  'Meta' tables store information
about what to display.
"""

import csv
import os
import sqlite3
import time
import datetime

from collections import namedtuple
import datetime
import logging
import math
import sys
import unittest
import zipfile

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import wx

sys.path.append(os.path.abspath('windrose'))
from windrose import *

class RxCadreError(Exception):pass
class RxCadreIOError(RxCadreError):pass
class RxCadreInvalidDbError(RxCadreError):pass
class RxCadreInvalidDataError(RxCadreError):pass

logging.basicConfig(level=logging.INFO)

def _import_date(string):
    """
    Parse a datetime from a UTC string
    """
    dt = datetime.datetime.strptime(string, '%m/%d/%Y %I:%M:%S %p')
    return dt




def _extract_xy(wkt):
    """
    Extract x and y coordinates from wkt in the db.  Strip 'POINT' from the
    front, and split the remaining data losing the parentheses
    """

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
        """
        Parse date time and return a string for query
        """
        return dt.strftime('%Y-%m-%d %H:%M:%S')


def _to_decdeg(d):
    """
    Split a coordinate in degrees, decimal minutes to decimal degrees
    """
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
    """
    Main interface for RX Cadre data.
    """
    def __init__(self, db_file=None, new=False):
        if not new:
            try:
                self.db = sqlite3.connect(db_file)
                self.check_valid_db(self.db)
                self.cur = self.db.cursor()
            except:
                self.db = None
                self.cur = None
        else:
            try:
                self.db = self.init_new_db(db_file)
                self.cur = self.db.cursor()
            except:
                self.db = None
                self.cur = None

    def __del__(self):
        """
        Cleanup, mainly close the db
        """
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
        """
        Simple check to make sure our internal db handle is good.
        """
        if self.db is None or self.cur is None:
            raise RxCadreInvalidDbError("Invalid database")


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

    def get_min_time(self,name, table):
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
        """"
        I change the values of the table to only those that are present in the
        selected database.
        """

        if name[-3:] != '.db':
            name = name + '.db'
        db = sqlite3.connect(name)
        if self.check_valid_db(db) == False:
            e ='The selected database appears to be of an incorrect format.  Please select a different database.'
            print e
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
        sql  = "SELECT plot_id_table FROM "+table
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
        """
        Create a new, empty database with appropriate metatables.  If the file
        previously exists, we fail before connecting using sqlite.  It must be
        a new file.
        """
        if(os.path.exists(filename)):
            raise RxCadreIOError("File exists.")
        db = sqlite3.connect(filename)
        if not db:
            raise RxCadreIOError("Could not create database")
        cursor = db.cursor()
        sql = """CREATE TABLE plot_location(plot_id TEXT, x REAL, y REAL,
                                            geometry TEXT, plot_type TEXT)"""
        cursor.execute(sql)
        sql = """CREATE TABLE event(project_name TEXT,
                                    event_name TEXT NOT NULL,
                                    event_start TEXT NOT NULL,
                                    event_end TEXT NOT NULL,
                                    PRIMARY KEY(project_name, event_name))"""
        cursor.execute(sql)
        sql = """CREATE TABLE obs_table(obs_table_name TEXT NOT NULL,
                                        table_display name TEXT,
                                        timestamp_column TEXT NOT NULL,
                                        geometry_column TEXT NOT NULL,
                                        obs_cols TEXT NOT NULL,
                                        obs_col_names TEXT)
              """

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
        """
        Check the schema of an existing db.  This involves checking the
        metatables, and checking to make sure tables registered in obs_tables
        exist.
        """

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

        sql = "SELECT project_name FROM event"
        cursor.execute(sql)
        projects = [c[0] for c in cursor.fetchall()]
        return events, projects

    def get_obs_table_names(self):
        """
        Get the names of all stored observation tables as a list of strings.
        """
        self.check_db()
        sql = "SELECT obs_table_name FROM obs_table"
        self.cur.execute(sql)
        names = [n[0] for n in self.cur.fetchall()]
        return names


    def point_location(self, plot, db):
        """
        Fetch the x and y coordinate of the plot
        """
        cursor = db.cursor()
        sql = """SELECT geometry FROM plot_location WHERE plot_id=?"""
        cursor.execute(sql, (plot,))
        row = cursor.fetchone()
        return _extract_xy(row[0])


    def fetch_point_data(self, plot, table,start, end,db):
        """
        Fetch data for a single point
        """

        cursor = db.cursor()
        sql = """SELECT * FROM """+table+"""
                          WHERE plot_id_table=? AND timestamp BETWEEN ? 
                           AND ?"""
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

    def statistics(self, data,db):
        """
        Calculate the stats for speed and direction data
        """
        """Made it so this function can pull data from db or file"""
        if type(data) == str:
            cursor = db.cursor()

            sql = "SELECT plot_id_table,timestamp,speed,direction,gust FROM "+data
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


    def _point_kml(self, plot, data, db, images=[]):
        """
        Create a kml representation of a plot
        """
        #print images

        lon, lat = self.point_location(plot,db)
        stats = self.statistics(data,db)
        if stats is None:
            logging.warning('Could not calculate stats')
            return ''
        d = stats[2][0]
        if d < 0:
            d = d + 360.0

        kml =               '  <Placemark>\n' \
                            '    <Style>\n' \
                            '      <IconStyle>\n' \
                            '        <Icon>\n' \
                            '          <href>http://maps.google.com/mapfiles/kml/shapes/arrow.png</href>\n' \
                            '        </Icon>\n' \
                            '        <heading>%s</heading>\n' \
                            '      </IconStyle>\n' \
                            '    </Style>\n' \
                            '    <Point>\n' \
                            '      <coordinates>%.9f,%.9f,0</coordinates>\n' \
                            '    </Point>\n' % (d, lon, lat)
        kml = kml +         '    <name>%s</name>\n' \
                            '    <description>\n' \
                            '      <![CDATA[\n' % plot
        for image in images:
            kml = kml +     '        <img src = "%s" />\n'  % image
        kml = kml +         '        <table border="1">' \
                            '          <tr>\n' \
                            '            <th>Stats</th>\n' \
                            '          </tr>\n' \
                            '          <tr>\n' \
                            '            <td>Average Speed</td>\n' \
                            '            <td>%.2f</td>\n' \
                            '          </tr>\n' \
                            '          <tr>\n' \
                            '            <td>STDDEV Speed</td>\n' \
                            '            <td>%.2f</td>\n' \
                            '          </tr>\n' \
                            '          <tr>\n' \
                            '            <td>Max Gust</td>\n' \
                            '            <td>%.2f</td>\n' \
                            '          </tr>\n' \
                            '          <tr>\n' \
                            '            <td>Average Direction</td>\n' \
                            '            <td>%.2f</td>\n' \
                            '          </tr>\n' \
                            '          <tr>\n' \
                            '            <td>STDDEV Direction</td>\n' \
                            '            <td>%.2f</td>\n' \
                            '          </tr>\n' \
                            '        </table>\n'% (stats[0][0], stats[0][1],
                                                   stats[1], stats[2][0], 
                                                   stats[2][1])
        kml = kml +         '      ]]>\n' \
                            '    </description>\n' \
                            '  </Placemark>\n'
        return kml


    def extract_obs_data(self, table_name, plot_name, start=None, end=None,
                         cols={}):
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
        self.cur.execute(sql, (table_name,))
        row = self.cur.fetchone()
        if not row:
            raise RxCadreInvalidDataError('Table %s is not in obs_table' %
                                          table_name)
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
        logging.debug('SQL as stmt: %s' % col_def)
        sql = '''
              SELECT %s as timestamp, %s FROM %s WHERE plot_id=?
              ''' % (time_col, col_def, table_name)
        #AND %s BETWEEN ? AND ?
        logging.debug('Unbound sql: %s' % sql)
        self.cur.execute(sql, (plot_name,))

        rows = self.cur.fetchall()

        data = dict()
        data['timestamp'] = [r[0] for r in rows]
        for i, c in enumerate(obs_cols):
            data[c] = [r[i+1] for r in rows]

        return data

    def create_time_series_image(self, data, plt_title, start, end, db, filename = ''):
        """
        Create a time series image for the plot over the time span
        """
        if type(data) == list:
            spd = [float(spd[2]) for spd in data]
            gust = [float(gust[4]) for gust in data]
            dir = [float(dir[3]) for dir in data]
            time = [mdates.date2num(datetime.datetime.strptime(d[1],'%Y-%m-%d %H:%M:%S')) for d in data]
        if type(data) == str:
            cursor = db.cursor()
            sql = """SELECT * FROM """+data+"""
                          WHERE plot_id_table=? AND timestamp BETWEEN ? 
                           AND ?"""
            #Note to self: removed quality tab from this.  may want to keep it
            cursor.execute(sql, (plt_title,_export_date(start),_export_date(end)))
            data = cursor.fetchall()
            spd = [float(spd[2]) for spd in data]
            gust = [float(gust[4]) for gust in data]
            dir = [float(dir[3]) for dir in data]
            time = [mdates.date2num(datetime.datetime.strptime(d[1],'%Y-%m-%d %H:%M:%S')) for d in data]

        #fig = plt.figure(figsize=(8,8), dpi=80)
        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        ax1.plot_date(time, spd, 'b-')
        #ax1.plot_date(time, gust, 'g-')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Speed(mph)', color = 'b')
        ax2 = fig.add_subplot(212)
        ax2.plot_date(time, dir, 'r.')
        ax2.set_ylabel('Direction', color='r')
        fig.autofmt_xdate()
        plt.suptitle('Plot %s from %s to %s' % (plt_title, 
                     start.strftime('%m/%d/%Y %I:%M:%S %p'),
                     end.strftime('%m/%d/%Y %I:%M:%S %p')))
        if not filename:
            plt.show()
            plt.close()
        else:
            plt.savefig(filename)
            plt.close()
        return filename


    def create_windrose(self, data, filename,db):
        """
        Create a windrose from a dataset.
        """
        spd = [float(spd[2]) for spd in data]
        gust = [float(gust[4]) for gust in data]
        dir = [float(dir[3]) for dir in data]

        time = [mdates.date2num(datetime.datetime.strptime(d[1],
                '%Y-%m-%d %H:%M:%S')) for d in data]

        if len(data) >= 1:
            #fig = plt.figure(figsize=(8, 8), dpi=80, facecolor='w', edgecolor='w')
            fig = plt.figure(facecolor='w', edgecolor='w')
            rect = [0.1, 0.1, 0.8, 0.8]
            ax = WindroseAxes(fig, rect, axisbg='w')
            fig.add_axes(ax)
            ax.bar(dir, spd, normed=True, opening=0.8, edgecolor='white')
            #l = ax.legend(axespad=-0.10)
            l = ax.legend(1.0)
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


    def create_field_kmz(self, filename, table,start,end,plotID,path,db):
        """
        Write a kmz with a time series and wind rose.  The stats are included
        in the html bubble as well.
        """
        cursor = db.cursor()
        sql = """SELECT DISTINCT(plot_id_table) FROM """+table+"""
                   WHERE timestamp BETWEEN ? AND ?"""
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
            #need to specify table to fetch point from
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


    def create_kmz(self, plot, filename,table,start,end,db):
        """
        Write a kmz with a time series and wind rose.  The stats are included
        in the html bubble as well.
        """
        if filename == '':
            filename = plot
        if filename[-4:] != '.kmz':
            filename = filename + '.kmz'

        data = self.fetch_point_data(plot,table,start,end,db)
        pngfile = self.create_time_series_image(data, plot, start,end,db, plot + '_time.png')
        rosefile = self.create_windrose(data, plot + '_rose.png',db)
        kml = self._point_kml(plot, data, db,[pngfile,rosefile])

        kmlfile = 'doc.kml'
        fout = open(kmlfile, 'w')
        fout.write(kml)
        fout.close()

        kmz = zipfile.ZipFile( filename, 'w', 0, True)
        kmz.write(kmlfile)
        kmz.write(pngfile)
        kmz.write(rosefile)
        kmz.close()
        os.remove(kmlfile)
        #os.remove(pngfile)
        #os.remove(rosefile)
        return filename


    def create_csv(self, plot, filename,table,start,end,db):
        if filename == '':
            filename = plot
        if filename[-4:] != '.csv':
            filename = filename + '.csv'

        data = self.fetch_point_data(plot,table,start,end,db)
        file = open(filename,"w+")
        file.write('PlotID,Date\\Time, Speed, Direction, Gust' + '\n')
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

        """Create a table from a selected file in the current database.
        Import the appropriate columns and populate with associated data."""
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
            e = """
The selected data does not include the necessary fields for analysis. 
Please make sure that the selected data includes a separate
time, date, plotID, wind speed, wind direction and wind gust column
                                """

        else:

            cursor.execute("CREATE TABLE "+hold_name+"""(plot_id_table TEXT,
                                                        timestamp DATETIME, speed TEXT,
                                                        direction TEXT, gust TEXT)""")

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

def rxcadre_main(args):
    """
    Run the command line stuff.
    """
    if args.sub_cmd == 'create':
        RxCadre(args.database)
        rx.init_new_db(args.database)

    elif args.sub_cmd == 'import':
        rx.import_

    elif args.sub_cmd == 'info':
        if args.show_obs_tables:
            names = rx.get_obs_table_names()
            print('Tables: %s' % ','.join(names))

    elif args.sub_cmd == 'graph':
        pass


if __name__ == "__main__":
    """
    Command line interface for extracting data.  Users should be able to use
    the cli for extracting one or more plots for a given time period or event.
    Users should also be able to extract meta information from a db.  Editing
    is also allowed.  The functions are accessed via the subcommands:
    rxcadre create
    rxcadre import
    rxcadre export
    rxcadre info
    rxcadre edit
    """

    import argparse

    """
    Main parser.  All commands take a database to act on, so that is the last
    argument for everything.
    """
    parser = argparse.ArgumentParser(prog='rxcadre')
    subparsers = parser.add_subparsers(help='sub-command help', dest='sub_cmd')

    """
    Create a new database parser.  Only needs the database name.
    """
    parser_create = subparsers.add_parser('create', help='Create an empty db')

    """
    Import csv parser with options for naming the table and columns.
    """
    parser_import = subparsers.add_parser('import', help='Import csv data')
    parser_import.add_argument('input_file', type=str,
                               help='csv file to import')
    parser_import.add_argument('--columns', dest='columns', type=str,
                               nargs='*', default=[],
                               help='Columns to import, default is all')
    parser_import.add_argument('--column_names', dest='column_names',
                               type=str, nargs='*', default=[],
                               help='Display column names')
    """
    Export parser.
    """
    parser_extract = subparsers.add_parser('export', help='Extract plot data')
    parser_extract.add_argument('--plots', dest='plot', type=str,
                                nargs='*', default=[],
                                help='Plot names to extract')
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
    parser_extract.add_argument('--show-only', dest='show-only',
                                action='store_true',
                                help='Show the images, don\'t write a file')
    parser_extract.add_argument('--base-name', type=str, default='',
                                help='Base filename for output')
    #parser_extract.add_argument('--zip', dest='zip', action='store_true',
    #                            help='Create a zip file for all output')

    """
    Information parser.
    """
    parser_info = subparsers.add_parser('info', help='Show db information')
    parser_info.add_argument('--tables', dest='show_obs_tables',
                             action='store_true',
                             help='Show observation tables in a database')
    parser_info.add_argument('--events', dest='show_events',
                             action='store_true',
                             help='Show events tables in a database')

    """
    Edit parser.
    """
    parser_edit = subparsers.add_parser('edit', help='Update db information')

    parser.add_argument('database', type=str, help='Database to act on')

    args = parser.parse_args()
    logging.info(args)
    try:
        rxcadre_main(args)
    except RxCadreError as e:
        print(e)
        sys.exit(1)
    sys.exit(0)


