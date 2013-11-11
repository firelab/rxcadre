import wx
import test_gui
import sys
import tempfile
import unittest
import csv
import os
import sqlite3
import time
import datetime
import ctypes

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

sys.path.append('../src')

from rxcadre import *


class RxCadreIOError(Exception):pass
class RxCadreInvalidDbError(Exception):pass


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
    
    wkt[0] = wkt[0].replace("\"","")
    wkt[0] = _to_decdeg(wkt[0])

    wkt[1] = wkt[1].replace("\"","")
    wkt[1] = _to_decdeg(wkt[1])
    
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


class MakeFrame(test_gui.GUI_test1):

    def __init__(self,parent):
        
        test_gui.GUI_test1.__init__(self,parent)

    def change_picker(self,event):
        """
        I change the values in the plot_id_picker to only those that are
        actually in the selected table, be it from imported data or stored
        in the database.
        """
        if (self.db_text.GetLabel() != ""):
            name = self.db_text.GetLabel()
            db = sqlite3.connect(name)
        if (self.db_text.GetLabel() == ""):
            name = self.db_picker.GetPath()
            name = name[(name.rfind("\\")+1):]
            db = sqlite3.connect(name)
        

        table = self.combo.GetLabel()
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

        self.m_choice17.Clear()
        for p in plots_new:
            self.m_choice17.Append(p)

        db.commit()
        db.close()
        
        


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
                raise RxCadreIOError(e)
                #print e
                #print name
                #print obs_names
                #print table_names
                return False
        return True

    def db_selected(self, event):
        self.db_text.Clear()
        name = self.db_picker.GetPath()
        name = name[(name.rfind("\\")+1):]
        db = sqlite3.connect(name)
        cursor = db.cursor()
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor.execute(sql)
        table_names = cursor.fetchall()
        for i in range(0,len(table_names)):
            table_names[i] = str(table_names[i]).replace("(","")
            table_names[i] = table_names[i].replace(",)","")
            table_names[i] = table_names[i].replace("u'","")
            table_names[i] = table_names[i].replace("'","")
        self.combo.Clear()
        for t in table_names:
            if "plot_location" not in t and "obs_table" not in t and "event" not in t:
                self.combo.Append(t)

        sql = "SELECT event_name FROM event"
        cursor.execute(sql)
        events = cursor.fetchall()
        print events
        self.event_combo.Clear()
        for i in range(0,len(events)):
            events[i] = str(events[i]).replace("(","")
            events[i] = events[i].replace(",)","")
            events[i] = events[i].replace("u'","")
            events[i] = events[i].replace("'","")
        for e in events:
            self.event_combo.Append(e)

        sql = "SELECT plot_id FROM plot_location"
        cursor.execute(sql)
        plots = cursor.fetchall()
        plots_hold = []

        for i in range(0,len(plots)):
            plots[i] = str(plots[i]).replace("(","")
            plots[i] = plots[i].replace(",)","")
            plots[i] = plots[i].replace("u'","")
            plots[i] = plots[i].replace("'","")
            if (plots[i] not in plots_hold):
                plots_hold.append(plots[i])

        plots = plots_hold
        self.m_choice17.Clear()
        for p in plots:
            self.m_choice17.Append(p)
        db.commit()
        db.close()
    
    def init_new_db(self, event):
        """
        Create a new, empty database with appropriate metatables.  If the file
        previously exists, we fail before connecting using sqlite.  It must be
        a new file.
        """
        filename = self.db_text.GetLabel()
        if os.path.exists(filename):
            raise RxCadreIOError("Database file already exists")
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
        
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor.execute(sql)
        table_names = cursor.fetchall()
        for i in range(0,len(table_names)):
            table_names[i] = str(table_names[i]).replace("(","")
            table_names[i] = table_names[i].replace(",)","")
            table_names[i] = table_names[i].replace("u'","")
            table_names[i] = table_names[i].replace("'","")

            
        self.combo.Clear()
        for t in table_names:
            self.combo.Append(t)

        sql = "SELECT event_name FROM event"
        cursor.execute(sql)
        events = [str(c) for c in cursor.fetchall()]
        print events
        self.event_combo.Clear()
        for e in events:
            self.event_combo.Append(e)

        db.commit()
        self.db_picker.SetPath("")
        valid = self.check_valid_db(db)
        if not valid:
            db.close()
            e = "Failed to create a valid database."
            print e
        print "db created"
        return db

    def update_events(self,event):

        if (self.db_text.GetLabel() != ""):
            name = self.db_text.GetLabel()
            db = sqlite3.connect(name)
        if (self.db_text.GetLabel() == ""):
            name = self.db_picker.GetPath()
            name = name[(name.rfind("\\")+1):]
            db = sqlite3.connect(name)
        sql = "SELECT event_name FROM event"
        cursor.execute(sql)
        events = [c[0] for c in cursor.fetchall()]
        print "EVENTS: ", events
        self.event_combo.Clear()
        for e in events:
            self.event_combo.Append(e)
        db.commit()
        db.close()



    def import_data(self, event):
        
        """Create a table from a selected file in the current database.
        Import the appropriate columns and populate with associated data."""
        #Need more robust system here.  Global boolean maybe?
        if (self.db_text.GetLabel() != ""):
            name = self.db_text.GetLabel()
            db = sqlite3.connect(name)
        if (self.db_text.GetLabel() == ""):
            name = self.db_picker.GetPath()
            name = name[(name.rfind("\\")+1):]
            db = sqlite3.connect(name)
        self.combo.Clear()

        input_csv = self.select_file.GetPath()
        cursor = db.cursor()
        
        title = input_csv[(input_csv.rfind("\\")+1):input_csv.index(".")]
        db.text_factory = str
        data_file = open(input_csv,"r")
        header = data_file.readline().split(",")
        for i in range(0,len(header)):
            header[i] = header[i].replace('\n',"")
            header[i] = header[i].replace('+',"")
            header[i] = header[i].replace(":","")
            header[i] = header[i].replace(")","")
            header[i] = header[i].replace("(","")
        #hold_name = header[0]
        hold_name = title

        #cursor.execute("drop table "+hold_name)
       

        #sql = "CREATE TABLE "+hold_name+"("
        #for i, h in enumerate(header):
        #    sql += h + ' text'
        #    if(i < len(header)-1):
        #        sql += ','
        #sql += ')'

        #cursor.execute(sql)

        cursor.execute("CREATE TABLE "+hold_name+"""(plot_id_table TEXT,
                                                     timestamp DATETIME, speed TEXT,
                                                     direction TEXT, gust TEXT)""")

        #qs = "("+ (len(header)-1)* "?," +"?)"
        #insrt = "insert into " + hold_name+ " values "
        #insrt += qs


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

        self.m_choice17.Clear()
        for p in plot_id:
            p = str(p)
            self.m_choice17.Append(p)

        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor.execute(sql)
        table_names = cursor.fetchall()
        self.combo.Clear()
        table_names = [t[0] for t in table_names]
        for i in range(0,len(table_names)):
            table_names[i] = str(table_names[i])
            if "plot_location" not in table_names[i] and "event" not in table_names[i] and "obs_table" not in table_names[i]:
                self.combo.Append(table_names[i])


        obs_vals =  hold_name, "wkt_geometry", "id,time,speed,dir,gust", "PlotID, Timestamp,Wind Speed,Wind Direction(from North),Wind Gust" 
        cursor.execute("INSERT INTO obs_table VALUES (?,?,?,?)",obs_vals)

       
        db.commit()
        db.close()
        print "Data imported successfully"

    def create_all(self,event):
        if (self.db_text.GetLabel() == "" and self.db_picker.GetPath() == ""):
            raise RxCadreIOError('Please Select a Database')
        if (self.db_text.GetLabel() != ""):
            name = self.db_text.GetLabel()
            db = sqlite3.connect(name)
        if (self.db_text.GetLabel() == ""):
            name = self.db_picker.GetPath()
            name = name[(name.rfind("\\")+1):]
            db = sqlite3.connect(name)
        cursor = db.cursor()
        
        if (self.combo.GetLabel() != "" and self.select_file.GetPath() != ""):
            self.select_file.SetPath("")
        if (self.select_file.GetPath() != ""):
            input_csv = self.select_file.GetPath()
            title = input_csv[(input_csv.rfind("\\")+1):input_csv.index(".")]
        if (self.select_file.GetPath() == ""):
            title = self.combo.GetLabel()

        
        if (self.event_combo.GetLabel() == ""):
            begin = self.start_month.GetLabel()+"/"+self.start_day.GetLabel()+"/"+self.start_year.GetLabel()+" "+self.start_hour.GetLabel()+":"+self.start_minute.GetLabel()+":"+self.start_second.GetLabel()+" "+self.start_ampm.GetLabel()
            stop = self.end_month.GetLabel()+"/"+self.end_day.GetLabel()+"/"+self.end_year.GetLabel()+" "+self.end_hour.GetLabel()+":"+self.end_minute.GetLabel()+":"+self.end_second.GetLabel()+" "+self.end_ampm.GetLabel()
        if (self.event_combo.GetLabel() != ""):
            name = self.event_combo.GetLabel()
            sql = "SELECT event_start,event_end FROM event WHERE event_name = '"+name+"'"
            cursor.execute(sql)
            time = cursor.fetchall()
            time = time[0]
            begin = str(time[0])
            stop = str(time[1])

        if self.file_name.GetLabel() == "":
            #raise RxCadreIOError('Please name output file')
            new_label = self.m_choice17.GetLabel()+"_"+begin+"_"+stop
            new_label = new_label.replace(" ","_")
            new_label = new_label.replace("/","-")
            new_label = new_label.replace(":",".")
            self.file_name.SetLabel(new_label)

        event_vals =  "RxCadre",self.file_name.GetLabel(),begin,stop
        cursor.execute("INSERT INTO event VALUES (?,?,?,?)",event_vals)
        
        self.start = datetime.datetime.strptime(begin, '%m/%d/%Y %I:%M:%S %p')
        self.end = datetime.datetime.strptime(stop, '%m/%d/%Y %I:%M:%S %p')
        if self.start == self.end:
            raise RxCadreIOError('Please select two different times')
        
        kmz = RxCadre().create_kmz(self.m_choice17.GetLabel(),self.file_name.GetLabel(),title,self.start,self.end,db)
        RxCadre().create_csv(self.m_choice17.GetLabel(),self.file_name.GetLabel(),title,self.start,self.end,db)

        self.bmp = wx.Image(self.m_choice17.GetLabel()+'_rose.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.bmp.bitmap = wx.StaticBitmap(self.plot_rose, -1, self.bmp)
    


        self.bmp2 = wx.Image(self.m_choice17.GetLabel()+'_time.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.bmp2.bitmap = wx.StaticBitmap(self.plot_time, -1, self.bmp2)
        self.plot_time.SetSize(self.bmp2.bitmap.GetSize())


        self.plot_time.Refresh()
        self.plot_rose.Refresh()

        os.remove(self.m_choice17.GetLabel()+'_time.png')
        os.remove(self.m_choice17.GetLabel()+'_rose.png')

        sql = "SELECT event_name FROM event"
        cursor.execute(sql)
        events = cursor.fetchall()
        events = [e[0] for e in events]
        for i in range(0,len(events)):
            events[i] = str(events[i])
        self.event_combo.Clear()
        for e in events:
            self.event_combo.Append(e)

        db.commit()
        db.close()
        
        #ctypes.windll.user32.MessageBoxA(0, "Your text", "Your title", 1)
    def open_msg(self,event):
        file_path = "C:/Users/krabil/Documents/GitHub/rxcadre/test/"
        # = wx.PySimpleApp()
        dialog = wx.FileDialog(None, message = "Choose a database:",defaultDir = file_path,style=wx.FD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            self.db_picker.SetPath(dialog.GetPath())
        dialog.Destroy()

    def import_data2(self,event):
        dialog = wx.TextEntryDialog(None,message="Enter a name for the new Database")
        if dialog.ShowModal() == wx.ID_OK:
            print dialog.GetValue()
        dialog.Destroy()

app = wx.App(False)
 
#create an object of GUIFrame
frame = MakeFrame(None)
#show the frame
frame.Show(True)
#start the applications
app.MainLoop()