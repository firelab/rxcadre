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

class RxCadreIOError(Exception):pass
class RxCadreInvalidDbError(Exception):pass


def file_acc(filepath, mode):
    ''' Check if a file exists and is accessible. '''
    try:
        f = open(filepath, mode)
    except IOError as e:
        return False
 
    return True

def _import_date(string):
    '''
    Parse a datetime from a UTC string
    '''
    dt = datetime.datetime.strptime(string, '%m/%d/%Y %I:%M:%S %p')
    return dt

def _export_date(dt):
    '''
    Parse date time and return a string for query
    '''
    return dt.strftime('%Y-%m-%d %H:%M:%S')

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
        print len(wkt), wkt
        raise ValueError
    print wkt
    wkt[0] = wkt[0].replace("\"","")
    #wkt[0] = _to_decdeg(wkt[0])

    wkt[1] = wkt[1].replace("\"","")
    #wkt[1] = _to_decdeg(wkt[1])
    
    return tuple([float(c) for c in wkt])

def _to_decdeg(d):
    d = d.split("'")
    s = float(d[-1])
    s = s / 60.0
    
    d, m = [float(f) for f in d[0].split('\xb0')]
    m += s
    m = m / 60.0
    if d < 0:
        m = m * -1
    d += m
    return d


class RxCadre:
    """
    Main interface for RX Cadre data.
    """
    def get_time(self,event):
        begin = self.start_month.GetLabel()+"/"+self.start_day.GetLabel()+"/"+self.start_year.GetLabel()+" "+self.start_hour.GetLabel()+":"+self.start_minute.GetLabel()+":"+self.start_second.GetLabel()+" "+self.start_ampm.GetLabel()
        stop = self.end_month.GetLabel()+"/"+self.end_day.GetLabel()+"/"+self.end_year.GetLabel()+" "+self.end_hour.GetLabel()+":"+self.end_minute.GetLabel()+":"+self.end_second.GetLabel()+" "+self.end_ampm.GetLabel()
        begin = str(begin)
        stop = str(stop)
        return begin, stop
    
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

    def create_title(self, begin, stop):
        new_label = self.m_choice17.GetLabel()+"_"+begin+"_"+stop
        new_label = new_label.replace(" ","_")
        new_label = new_label.replace("/","-")
        new_label = new_label.replace(":",".")
        self.file_name.SetLabel(new_label)
        return new_label

    def get_project(self,event):
        if self.proj_combo.GetLabel() == "":
            project = "RxCadre"
        else:
            project = self.proj_combo.GetLabel()
        return project

    def display_rose(self, plot, png):
        self.bmp = wx.Image(plot+'_rose.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.bmp.bitmap = wx.StaticBitmap(self.plot_rose, -1, self.bmp)
        self.plot_time.SetSize(self.bmp2.bitmap.GetSize())
        self.plot_time.Refresh()
        os.remove(plot +'_time.png')

    def display_time(self, plot, png):
        self.bmp2 = wx.Image(plot+'_time.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.bmp2.bitmap = wx.StaticBitmap(self.plot_time, -1, self.bmp2)
        self.plot_time.SetSize(self.bmp2.bitmap.GetSize())
        self.plot_rose.Refresh()
        os.remove(plot +'_rose.png')
        

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

        

        

    def init_new_db(self, filename,filepath):
        """
        Create a new, empty database with appropriate metatables.  If the file
        previously exists, we fail before connecting using sqlite.  It must be
        a new file.
        """
        if filename[-3:] != '.db':
            filename = filename + '.db'
        if filepath[-1] != '\\':
            filepath = filepath + '\\'
        if file_acc(filepath+filename,"r") == True:
            e = "Database file already exists"
        else:
            filename = filepath  + filename
            db = sqlite3.connect(filename)
            cursor = db.cursor()
            sql = """CREATE TABLE plot_location(plot_id TEXT, 
                                                geometry TEXT, plot_type TEXT)"""
            cursor.execute(sql)
            sql = """CREATE TABLE event(project_name TEXT,
                                        event_name TEXT NOT NULL,
                                        event_start TEXT NOT NULL,
                                        event_end TEXT NOT NULL,
                                        PRIMARY KEY(project_name, event_name))"""
            cursor.execute(sql)
            sql = """CREATE TABLE obs_table(obs_table_name TEXT NOT NULL,
                                            geometry_column TEXT NOT NULL,
                                            obs_cols TEXT NOT NULL,
                                            obs_col_names TEXT)"""
            cursor.execute(sql)
            db.commit()
            #update tables, update events, set db_picker to filename
            valid = self.check_valid_db(db)
            if not valid:
                db.close()
                e = "Failed to create a valid database."
                self.RxCadreIOError(e)
            else:
                print "db created"
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


    def update_tables(self):

        name = self.db_picker.GetLabel()
        if name[-3:] != '.db':
            name = name+'.db'
        db = sqlite3.connect(name)
        cursor = db.cursor()
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor.execute(sql)
        table_names = cursor.fetchall()
        self.combo.Clear()
        table_names = [t[0] for t in table_names]
        for i in range(0,len(table_names)):
            table_names[i] = str(table_names[i])
            if "plot_location" not in table_names[i] and "event" not in table_names[i] and "obs_table" not in table_names[i]:
                self.combo.Append(table_names[i])






    def point_location(self, plot, db):
        '''
        Fetch the x and y coordinate of the plot
        '''
        cursor = db.cursor()
        sql = """SELECT geometry FROM plot_location WHERE plot_id=?"""
        cursor.execute(sql, (plot,))
        row = cursor.fetchone()
        #print "ROW: "  , row
        return _extract_xy(row[0])


    def fetch_point_data(self, plot, table,start, end,db):
        '''
        Fetch data for a single point
        '''
        
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
            e = 'Catastrophe'
            raise RxCadreIOError(e)
        
        logging.info('Query fetched %i result(s)' % len(data))
        return data

    def statistics(self, data,db):
        '''
        Calculate the stats for speed and direction data
        '''
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
        '''
        Create a kml representation of a plot
        '''
        print images

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



    def create_time_series_image(self, data, plt_title, start, end, db, filename = ''):
        '''
        Create a time series image for the plot over the time span
        '''
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
            print data
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
        '''
        Create a windrose from a dataset.
        '''
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
            if __debug__:
                print 'Unknown failure in bigbutte.create_image()'
            return None

    def create_field_kmz(self, filename, table,start,end,db):
        '''
        Write a kmz with a time series and wind rose.  The stats are included
        in the html bubble as well.
        '''
        cursor = db.cursor()
        sql = '''SELECT DISTINCT(plot_id) FROM mean_flow_obs
                   WHERE date_time BETWEEN ? AND ?'''
        cursor.execute(sql, (start, end))

        kmz = zipfile.ZipFile( filename, 'w', 0, True)
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
                pngfile = self.create_time_series_image(data, plot, db, plot + '_time.png')
                rosefile = self.create_windrose(data, plot + '_rose.png',db)
                kml = self._point_kml(plot, data, db,[pngfile,rosefile])
            except Exception as e:
                logging.warning('Unknown exception has occurred')
                if os.path.exists(pngfile):
                    os.remove(pngfile)
                if os.path.exists(rosefile):
                    os.remove(rosefile)
                continue

            fout.write(kml)
            fout.flush()

            kmz.write(pngfile)
            kmz.write(rosefile)
            os.remove(pngfile)
            os.remove(rosefile)
        fout.write('</Document>\n')
        fout.close()
        kmz.write(kmlfile)
        kmz.close()
        os.remove(kmlfile)
        return filename



    

    def create_kmz(self, plot, filename,table,start,end,db):
        '''
        Write a kmz with a time series and wind rose.  The stats are included
        in the html bubble as well.
        '''
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
    #New Stuff End

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
            self.RxCadreIOError("""
The selected data does not include the necessary fields for analysis. 
Please make sure that the selected data includes a separate
time, date, plotID, wind speed, wind direction and wind gust column
                                """)

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
                    plot_vals = line[plotid],"POINT("+str(_to_decdeg(line[lon].replace("\"","")))+" "+str(_to_decdeg(line[lat].replace("\"","")))+")",line[tagid]
                    cursor.execute("INSERT INTO plot_location VALUES (?,?,?)",plot_vals)
                    
                instr_id2 = line[instrid]
                line = data_file.readline()
                line = line.split(",")

            sql = "SELECT plot_id FROM plot_location"
            cursor.execute(sql)
            plots = cursor.fetchall()
            plots_hold = []

            #update plotIDs

            #update tables


            obs_vals =  hold_name, "wkt_geometry", "id,time,speed,dir,gust", "PlotID, Timestamp,Wind Speed,Wind Direction(from North),Wind Gust" 
            cursor.execute("INSERT INTO obs_table VALUES (?,?,?,?)",obs_vals)

            #msg_import
               
            db.commit()
            db.close()
            p = "Data imported successfully"



        

    

    

    
       

    


