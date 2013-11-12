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

from rxcadre import *
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

class RxCadreInvalidDbError(Exception):pass

class MakeFrame(test_gui.GUI_test1):

    def __init__(self,parent):
        
        test_gui.GUI_test1.__init__(self,parent)

    def RxCadreIOError(self, message):
        dialog = wx.MessageDialog(None, message, 'Error',wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()

    def change_dir(self, event):
        dialog = wx.DirDialog(None,message='Select a working directory',style = wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            dir = dialog.GetPath()
        dialog.Destroy()
        self.cur_dir.SetLabel(dir)

    def change_tables(self):
        name = self.db_picker.GetLabel()
        file_path = self.cur_dir.GetLabel()
        name = file_path + "/" + name
        tables = RxCadre().change_tables(name)
        self.combo.Clear()
        for i in range(0,len(tables)):
                tables[i] = str(tables[i])
        for t in tables:
            if "plot_location" not in t and "event" not in t and "obs_table" not in t:
                self.combo.Append(t)
        events, projects = RxCadre().update_events(name)
        self.proj_combo.Clear()
        self.event_combo.Clear()
        for e in events:
            self.event_combo.Append(e)
        projects2 = ['RxCadre']
        for p in projects:
            if p not in projects2:
                projects2.append(p)
        for p in projects2:
            self.proj_combo.Append(p)

    def open_msg(self,event):
        file_path = self.cur_dir.GetLabel()
        if file_path == "":
            self.RxCadreIOError('Please select a directory')
        else:
            dialog = wx.FileDialog(None, message = "Choose a database:",defaultDir = file_path,style=wx.FD_DEFAULT_STYLE)
            if dialog.ShowModal() == wx.ID_OK:
                name = dialog.GetPath()
                if name[-3:] != '.db':
                    name = name + '.db'
                index = max(name.rfind("/"),name.rfind("\\"))
                name = name[index+1:]
                self.db_picker.SetLabel(name)
                self.change_tables()
                dialog.Destroy()

    def create_db(self,event):
        file_path = self.cur_dir.GetLabel()
        if file_path == "":
            self.RxCadreIOError('Please select a directory')
        else:
            dialog = wx.TextEntryDialog(None,message="Enter a name for the new Database")
            if dialog.ShowModal() == wx.ID_OK:
                name = dialog.GetValue()
            dialog.Destroy()
            RxCadre().init_new_db(name,file_path)
            if name[-3:] != '.db':
                name = name + '.db'
            self.db_picker.SetLabel(name)
            self.change_tables()
            

    def change_picker(self, event):
        name = self.db_picker.GetLabel()
        file_path = self.cur_dir.GetLabel()
        name = file_path + "/" + name
        table = self.combo.GetLabel()
        plots_new = RxCadre().change_picker(name, table)
        self.m_choice17.Clear()
        for p in plots_new:
            self.m_choice17.Append(p)

    def import_data2(self,event):
        file_path = self.cur_dir.GetLabel()
        name = self.db_picker.GetLabel()
        if file_path == "":
            self.RxCadreIOError('Please select a directory')
        else:
            if name == "":
                self.RxCadreIOError('Please select a database')
            else:
                dialog = wx.FileDialog(None, message = "Select data to import to the current database:",defaultDir = file_path,style=wx.FD_DEFAULT_STYLE)
                if dialog.ShowModal() == wx.ID_OK:
                    filename = dialog.GetPath()
                dialog.Destroy()
                RxCadre().import_data(filename, file_path+"/"+name)
        self.change_tables()
        dialog = wx.MessageDialog(None,os.path.basename(filename) + ' has been successfuly imported to the current database', 'Data imported successfully',wx.OK | wx.ICON_INFORMATION)
        dialog.ShowModal()

    def create_all(self,event):
        if (self.db_picker.GetLabel() == ""):
            self.RxCadreIOError('Please Select a Database')
        else:
            
            name = self.db_picker.GetLabel()
            file_path = self.cur_dir.GetLabel()
            name = file_path + "/" + name
            if name[-3:] != '.db':
                name = name + '.db'
            db = sqlite3.connect(name)
            
            cursor = db.cursor()
            
            if (self.combo.GetLabel() == ""):
                self.RxCadreIOError('Please select a data table')
            else:

                if (self.combo.GetLabel() != ""):
                    title = self.combo.GetLabel()
                
                
                if (self.event_combo.GetLabel() == ""):
                    begin = self.start_date.GetLabel()+" "+self.start_hour.GetLabel()+":"+self.start_minute.GetLabel()+":"+self.start_second.GetLabel()+" "+self.start_ampm.GetLabel()
                    stop = self.stop_date.GetLabel() + " "+self.end_hour.GetLabel()+":"+self.end_minute.GetLabel()+":"+self.end_second.GetLabel()+" "+self.end_ampm.GetLabel()
                if (self.event_combo.GetLabel() != ""):
                    name = self.event_combo.GetLabel()
                    sql = "SELECT event_start,event_end FROM event WHERE event_name = '"+name+"'"
                    cursor.execute(sql)
                    time = cursor.fetchall()
                    time = time[0]
                    begin = str(time[0])
                    stop = str(time[1])

                if self.file_name.GetLabel() == "":
                    new_label = self.m_choice17.GetLabel()+"_"+begin+"_"+stop
                    new_label = new_label.replace(" ","_")
                    new_label = new_label.replace("/","-")
                    new_label = new_label.replace(":",".")
                    self.file_name.SetLabel(new_label)
                sql = "SELECT event_name FROM event"
                cursor.execute(sql)
                events = [e[0] for e in cursor.fetchall()]
                if self.file_name.GetLabel() in events:
                    self.RxCadreIOError('This table already exists in this database')
                else:

                    event_vals =  "RxCadre",self.file_name.GetLabel(),begin,stop
                    cursor.execute("INSERT INTO event VALUES (?,?,?,?)",event_vals)
                    
                    self.start = datetime.datetime.strptime(begin, '%m/%d/%Y %I:%M:%S %p')
                    self.end = datetime.datetime.strptime(stop, '%m/%d/%Y %I:%M:%S %p')
                    if self.start == self.end:
                        self.RxCadreIOError('Please select two different times')
                    else:
                    
                        kmz = RxCadre().create_kmz(self.m_choice17.GetLabel(),self.cur_dir.GetLabel() + '/' + self.file_name.GetLabel(),title,self.start,self.end,db)
                        RxCadre().create_csv(self.m_choice17.GetLabel(),self.cur_dir.GetLabel() + '/' + self.file_name.GetLabel(),title,self.start,self.end,db)

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

                        self.file_name.SetLabel("")

                        db.commit()
                        db.close()






    def about(self,event):
        about_message = """
                           To begin using the RxCadre GUI first select 'File' in the upper Menu Bar. 
                           Three options will appear, 'Select Database', 'Create Database' and 'Select Directory'. 
                           First, click 'Select Directory'.  A browser will open allowing you to select a 
                           directory in which you'd like your files to appear.  Next select 'Create Database'. 
                           This will open a prompt asking for a name of the new database.  Enter a name you would 
                           like and it will be created in the directory you chose in the previous step.  You may now 
                           begin importing data.  Returning to the Menu Bar, select Edit now.  You should see only one 
                           option: 'Import Data'.  Click it and a window will appear.  Navigate to data you'd like 
                           to add to the current database and the data will be imported.  The name of the database as
                           well as the name of the directory you chose have now populated windows in the interface
                           next to the labels 'Current Directory' and 'Current Database'.  \n 
                           You may now select parameters for analysis.  You will see a label in the interface labeled 
                           'Select Table'.  After importing data into the database this menu will auto-populate with 
                           all data tables contained in the current database.  Simply click a value to select it. 
                           Next, find a label that reads 'Select PlotID'.  A choice-list will be next to it.  This 
                           has auto-populated with all unique plot IDs from the chosen table. Select a plot ID for 
                           analysis and continue to the next step.  \n 
                           You should now see many drop-down menus next to the labels 'Select Start Date', 
                           'Select Start Time', 'Select End Date' and 'Select End Time'.  These menus allow you 
                           to enter an exact time and date at which to begin end analysis.  The first menu  
                           is to select a month in numeric form (January = 1, February = 2 etc...) followed 
                           by day and then year.  This form is the same for both End Date and Start Date.  The first menu following the 
                           'Select Start Time' and 'Select End Time' label will select an hour (12 hour format), followed 
                           by minute, second and AM/PM.  If you'd like to see all data from a table you can select a
                           time frame that includes all the acquired data.\n  
                           You're finally ready to analyze the data.  You may create a specific name for the outputs 
                           by editing the textbox next to the label 'Name for kmz output', but if you elect 
                           to keep this box empty a name will be auto-generated based on the plotID and timeframe. 
                           Now press 'Create Plots'.  Two plots should appear in the interface.  This may take a 
                           few seconds.  Additionally, the selected data will appear in its own .csv file along 
                           with a compiled .kmz file including both plots in the directory you specified in Step 1. 
                           You may now import new data, select a new table or repeat the process with a new timeframe. 
                           Once the database has had one event processed you may now use the same timeframe for 
                           subsequent tests by selecting a value in the menu next to 'Use the timeframe of existing event'
                           """
        dialog = wx.MessageDialog(None, about_message, 'About',wx.OK | wx.ICON_INFORMATION)
        dialog.ShowModal()
        
    
        
            
app = wx.App(False)
 
frame = MakeFrame(None)
frame.Show(True)
app.MainLoop()
