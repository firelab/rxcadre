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

import wx
import wx_rxcadre_gui

from rxcadre import *

class MakeFrame(wx_rxcadre_gui.GUI_test2):

    def __init__(self,parent):
        
        wx_rxcadre_gui.GUI_test2.__init__(self,parent)

    def RxCadreIOError(self, message):
        dialog = wx.MessageDialog(None, message, 'Error',wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()

    def change_tables(self):
        name = self.db
        tables = RxCadre().change_tables(name)
        self.combo.Clear()
        for i in range(0,len(tables)):
                tables[i] = str(tables[i])
        for t in tables:
            if "plot_location" not in t and "event" not in t and "obs_table" not in t:
                self.combo.Append(t)
        events = RxCadre().update_events(name)
        self.event_combo.Clear()
        for e in events:
            self.event_combo.Append(e)

    def set_time(self,min,max):
        min = min.split(" ")
        max = max.split(" ")

        min_date = min[0].split("-")
        max_date = max[0].split("-")

        min_date = wx.DateTimeFromDMY(int(min_date[2]), int(min_date[1])+1, int(min_date[0]))
        max_date = wx.DateTimeFromDMY(int(max_date[2]), int(max_date[1])+1, int(max_date[0]))
                    
        self.start_date.SetValue(min_date)
        self.stop_date.SetValue(max_date)
        min_time = min[1].split(":")
        max_time = max[1].split(":")
        self.start_hour.SetSelection(int(min_time[0])%12 - 1)
        self.start_minute.SetSelection(int(min_time[1]))
        self.start_second.SetSelection(int(min_time[2]))
        if (int(min_time[0]) >  12):
            self.start_ampm.SetSelection(1)
        else:
            self.start_ampm.SetSelection(0)
        self.end_hour.SetSelection(int(max_time[0])%12 - 1)
        self.end_minute.SetSelection(int(max_time[1]) )
        self.end_second.SetSelection(int(max_time[2]))
        if (int(max_time[0]) >  12):
            self.end_ampm.SetSelection(1)
        else:
            self.end_ampm.SetSelection(0)

    def open_msg(self,event):
    
        file_path = os.path.abspath("")
        
        dialog = wx.FileDialog(None, message = "Choose a database:",defaultDir = file_path,style=wx.FD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            req_ext = '.db'
            name = dialog.GetPath()
            if os.path.splitext(name)[-1] != req_ext:
                name = name + req_ext
            db = sqlite3.connect(name)
            if RxCadre().check_valid_db(db) == False:
                self.RxCadreIOError('The selected database appears to be in the wrong format. Please make sure you selected a valid database.')
            else:
                self.db_picker.SetLabel(os.path.split(name)[-1])
                print name
                self.db = name
                self.change_tables()
                dialog.Destroy()

    def create_db(self,event):
        dialog = wx.DirDialog(None, message = "Choose a Directory:",style=wx.DD_DEFAULT_STYLE)
        if dialog.ShowModal() == wx.ID_OK:
            dir = dialog.GetPath()
        dialog = wx.TextEntryDialog(None,message="Enter a name for the new Database",caption = 'Name Entry')
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetValue()
            if name[-3:] != '.db':
                name = name + '.db'
        dialog.Destroy()
        RxCadre().init_new_db(os.path.join(dir,name))
        self.db = os.path.join(dir,name)
        self.db_picker.SetLabel(name)
        self.change_tables()


    def change_picker(self, event):
        name = self.db
        table = self.combo.GetLabel()
        plots_new = RxCadre().change_picker(name, table)
        self.m_choice17.Clear()
        for p in plots_new:
            self.m_choice17.Append(p)
        min = RxCadre().get_min_time(name,table)
        max = RxCadre().get_max_time(name,table)
        self.set_time(min,max)

    def import_data2(self,event):
        if self.db_picker.GetLabel() == "":
            self.RxCadreIOError('Please select a database')
        else:
            name = self.db
            file_path = os.path.dirname(name)
            dialog = wx.FileDialog(None, message = "Select data to import to the current database:",defaultDir = file_path,style=wx.FD_DEFAULT_STYLE)
            if dialog.ShowModal() == wx.ID_OK:
                filename = dialog.GetPath()
            dialog.Destroy()
            if RxCadre().check_valid_file(filename) == False:
                self.RxCadreIOError("""
The selected data does not include the necessary fields for analysis. 
Please make sure that the selected data includes a separate
time, date, plotID, wind speed, wind direction and wind gust column
                                         """)
            else:
                tables = RxCadre().change_tables(name)
                filename_hold = os.path.splitext(filename)[-2]
                filename_hold = os.path.basename(filename_hold)
                if filename_hold in tables:
                    self.RxCadreIOError('This data has already been imported.')
                else:
                    RxCadre().import_data(filename, name)
                    self.change_tables()
                    dialog = wx.MessageDialog(None,os.path.basename(filename) + ' has been successfuly imported to the current database', 'Data imported successfully',wx.OK | wx.ICON_INFORMATION)
                    dialog.ShowModal()
                    basename = os.path.basename(filename)
                    min = RxCadre().get_min_time(name,basename[:basename.index(".")])
                    max = RxCadre().get_max_time(name,basename[:basename.index(".")])

                    self.set_time(min,max)

    def create_all(self,event):
        if (self.db_picker.GetLabel() == ""):
            self.RxCadreIOError('Please Select a Database')
        fname = self.db
        name = fname
        req_ext = '.db'
        if os.path.splitext(name)[-1] != req_ext:
            name = name + req_ext
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
                    data = RxCadre().fetch_point_data(self.m_choice17.GetLabel(),title,self.start,self.end,db)
                    pngfile = RxCadre().create_time_series_image(data, self.m_choice17.GetLabel(),self.start,self.end,db,
                                                                 os.path.join(os.path.dirname(fname),self.m_choice17.GetLabel())+ '_time.png')
                    rosefile = RxCadre().create_windrose(data, self.m_choice17.GetLabel(),self.start,self.end,
                                                         os.path.join(os.path.dirname(fname),self.m_choice17.GetLabel()) + '_rose.png',db)

                    if self.m_checkBox5.GetValue() == True:
                        kmz = RxCadre().create_kmz(self.m_choice17.GetLabel(),os.path.join(os.path.dirname(fname),self.file_name.GetLabel()),
                                                   title,self.start,self.end,os.path.join(os.path.dirname(fname),self.m_choice17.GetLabel())+
                                                   '_time.png',os.path.join(os.path.dirname(fname),self.m_choice17.GetLabel())+ '_rose.png',data,db)
                    if self.m_checkBox6.GetValue() == True:
                        RxCadre().create_field_kmz(os.path.join(os.path.dirname(fname),self.file_name.GetLabel()),title,self.start,self.end,
                                                   self.m_choice17.GetLabel(),os.path.dirname(fname),db)
                    if self.m_checkBox7.GetValue() == True:
                        RxCadre().create_csv(self.m_choice17.GetLabel(),os.path.join(os.path.dirname(fname),self.file_name.GetLabel()),title,self.start,self.end,data,db)

                    if self.m_checkBox8.GetValue() == True:
                        RxCadre().create_ogr(os.path.dirname(fname),title,self.file_name.GetLabel(),self.start,self.end,db)

                    self.bmp = wx.Image(os.path.join(os.path.dirname(fname),self.m_choice17.GetLabel())+ '_rose.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
                    self.bmp.bitmap = wx.StaticBitmap(self.plot_rose, -1, self.bmp)
                    


                    self.bmp2 = wx.Image(os.path.join(os.path.dirname(fname),self.m_choice17.GetLabel())+ '_time.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
                    self.bmp2.bitmap = wx.StaticBitmap(self.plot_time, -1, self.bmp2)
                    self.plot_time.SetSize(self.bmp2.bitmap.GetSize())


                    self.plot_time.Refresh()
                    self.plot_rose.Refresh()

                    if self.m_checkBox9.GetValue() == False:
                        os.remove(os.path.join(os.path.dirname(fname), self.m_choice17.GetLabel()+'_time.png'))
                        os.remove(os.path.join(os.path.dirname(fname), self.m_choice17.GetLabel()+'_rose.png'))
                    
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
                           Two options will appear, 'Select Database' and 'Create Database'. 
                           First, select 'Create Database'. This will open a window in which you can navigate
                           to a location for your future database.  Once a suitable location has been selected
                           a prompt will appear asking for a name of the new database.  Enter a name  
                           and it will be created in the directory you chose in the previous step.  The name of the database
                           you chose has now populated the 'Current Database' window in the interface.  You may now 
                           begin importing data.  Returning to the Menu Bar, select Edit now.  You should see only one 
                           option: 'Import Data'.  Click it and a window will appear.  Navigate to data you'd like 
                           to add to the current database and the data will be imported.  Once imported successfully
                           a prompt will appear letting you know the data has been imported.  \n 
                           You may now select parameters for analysis.  You will see a label in the interface labeled 
                           'Select Table'.  After importing data into the database this menu will auto-populate with 
                           all data tables contained in the current database.  Simply click a value to select it. 
                           Next, find a label that reads 'Select PlotID'.  A list will be next to it.  This 
                           has auto-populated with all unique plot IDs from the chosen table. Select a plot ID for 
                           analysis and continue to the next step.  \n 
                           You should now see many menus next to the labels 'Select Start Date', 
                           'Select Start Time', 'Select End Date' and 'Select End Time'.  These menus allow you 
                           to enter an exact time and date at which to begin end analysis.  The first menu  
                           is to select a date in numeric form (January = 1, February = 2 etc...).
                           This form is the same for both End Date and Start Date.  The first menu following the 
                           'Select Start Time' and 'Select End Time' label will select an hour (12 hour format), followed 
                           by minute, second and AM/PM.  If you'd like to see all data from a table you can select a
                           time frame that includes all the acquired data.\n  
                           You're finally ready to analyze the data.  You may create a specific name for the outputs 
                           by editing the textbox next to the label 'Name for output files', but if you elect 
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
