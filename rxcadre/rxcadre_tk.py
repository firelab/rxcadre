#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
#  $Id$
#  Project:  RX Cadre Data Visualization
#  Purpose:  Simple tk GUI.
#  Author:   Kyle Shannon <kyle at pobox dot com>
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

from Tkinter import *
from tkFileDialog import askopenfilename, asksaveasfilename, askdirectory
import tkMessageBox

from rxcadre import RxCadre
from rxcadre_except import RxCadreError

HAVE_OGR = True
try:
    from osgeo import ogr
except ImportError:
    HAVE_OGR = False

class RxCadreTk(Frame):

    def messagebox(self, message, btype='warning'):
        bt_dict = {'info':tkMessageBox.showinfo,
                   'warning':tkMessageBox.showwarning}
        if not message:
            return
        try:
            bt_dict[btype]('RxCadre', message)
        except:
            pass
        return

    def update_listboxes(self):
        event_data = self.cadre.get_event_data()
        if not event_data:
            self.messagebox('There are no events associated with this db')
            return
        for event in event_data.keys():
            self.event_listbox.insert(END, event)
        plot_data = self.cadre.get_plot_data()
        for plot in plot_data:
            self.plot_listbox.insert(END, plot[0])

    def connect_db(self):

        self.plot_listbox.delete(0, END)
        self.event_listbox.delete(0, END)
        fname = askopenfilename(filetypes=(('SQLite files', '*.db *.sqlite'),
                                           ('All files', '*.*')),
                                initialdir='../data')
        if not fname:
            return
        try:
            self.cadre = RxCadre(fname)
        except RxCadreError as e:
            print(e)
        self.update_listboxes()

    def create_db(self):

        fname = asksaveasfilename(filetypes=(('SQLite files', '*.db *.sqlite'),))
        if not fname:
            return
        self.cadre.init_new_db(fname)
        self.cadre = RxCadre(fname)

    def import_db(self):

        fname = askopenfilename(filetypes=(('CSV files', '*.txt *.csv'),),
                                initialdir='../data')
        if not fname:
            return
        try:
            self.cadre.import_wind_data(fname, volatile=True)
        except RxCadreError as e:
            messagebox(e)
        self.cadre_thread.join()
        self.update_listboxes()

    def read_sql_file(self):

        fname = askopenfilename(filetypes=(('SQL files', '*.sql *.txt'),))
        if not fname:
            return
        self.cadre.read_sql(fname)
        self.update_listboxes()

    def load_event_data(self):
        '''
        Load pertinent information from a specific event

        This is primarily the date and time, although we do filter the plot
        list based on name (currently the start of plots is the event name).
        This should possibly be made optional.
        '''
        if not self.cadre:
            return
        event = self.event_listbox.get(ACTIVE)
        if not event:
            return
        data = self.cadre.get_event_data(event)
        start, end = data.items()[0][1]
        self.event_start_entry.delete(0, END)
        self.event_start_entry.insert(0, start)
        self.event_end_entry.delete(0, END)
        self.event_end_entry.insert(0, end)
        if self.filter_plots:
            plots = self.cadre.get_plot_data()
            self.plot_listbox.delete(0, END)
            for plot in plots:
                if plot[0].startswith(event):
                    self.plot_listbox.insert(END, plot[0])
        else:
            plots = self.cadre.get_plot_data()
            self.plot_listbox.delete(0, END)
            for plot in plots:
                self.plot_listbox.insert(END, plot[0])

    def create_ts_image(self):
        '''
        Read the plot id and start/stop time from the GUI and create an image.
        '''
        if not self.cadre:
            return
        items = map(int, self.plot_listbox.curselection())
        data = self.plot_listbox.get(0, END)
        plots = [data[int(item)] for item in items]
        start = self.event_start_entry.get()
        end = self.event_end_entry.get()
        if not plots:# or not start or not end:
            return
        pname = askdirectory(initialdir='.')
        if not pname:
            return
        gmax = float(self.gmax_spinbox.get())
        self.cadre.create_time_series_image(plots, 'TEST', start, end, pname, gmax)

    def create_wr_image(self):
        '''
        Read the plot id and start/stop time from the GUI and create an image.
        '''
        if not self.cadre:
            return
        items = map(int, self.plot_listbox.curselection())
        data = self.plot_listbox.get(0, END)
        plots = [data[int(item)] for item in items]
        start = self.event_start_entry.get()
        end = self.event_end_entry.get()
        if not plots or not start or not end:
            return
        pname = askdirectory(initialdir='.')
        if not pname:
            return
        self.cadre.create_windrose_image(plots, 'TEST', start, end, pname)

    def export_ogr(self):
        '''
        Export to an OGR datasource.
        '''

        if not self.cadre or not HAVE_OGR:
            return
        items = map(int, self.plot_listbox.curselection())
        data = self.plot_listbox.get(0, END)
        plots = [data[int(item)] for item in items]
        start = self.event_start_entry.get()
        end = self.event_end_entry.get()
        if not plots or not start or not end:
            return
        fname = asksaveasfilename(filetypes=(('OGR Formats', '*.shp *.csv'),),
                                  initialdir='.')
        if not fname:
            return
        if fname.endswith('.csv' ):
            frmt = 'CSV'
        else:
            frmt = 'ESRI Shapefile'
        self.cadre.export_ogr(plots, start, end, fname, frmt, self.summary_only)

    def export_csv(self):

        if not self.cadre:
            return
        items = map(int, self.plot_listbox.curselection())
        data = self.plot_listbox.get(0, END)
        plots = [data[int(item)] for item in items]
        start = self.event_start_entry.get()
        end = self.event_end_entry.get()
        if not plots or not start or not end:
            return
        pname = askdirectory(initialdir='.')
        if not pname:
            return
        self.cadre.export_csv(plots, start, end, pname)

    def export_kmz(self):

        if not self.cadre:
            return
        items = map(int, self.plot_listbox.curselection())
        data = self.plot_listbox.get(0, END)
        plots = [data[int(item)] for item in items]
        start = self.event_start_entry.get()
        end = self.event_end_entry.get()
        if not plots or not start or not end:
            return
        fname = asksaveasfilename(filetypes=(('Google Earth', '*.kmz'),),
                                  initialdir='.')
        if not fname:
            return
        self.cadre.export_kmz(plots, start, end, fname)
        return 1


    def create_menus(self):
        self.menubar = Menu(self)
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Connect", command=self.connect_db)
        self.filemenu.add_command(label="Create", command=self.create_db)
        self.filemenu.add_command(label="Read sql", command=self.read_sql_file)
        #self.filemenu.add_command(label="Add 'ALL' event", command=self.add_all)
        self.filemenu.add_command(label="Import wind data", command=self.import_db)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.master.config(menu=self.menubar)

    def create_plot_listbox(self):
        self.plot_label = Label(self.plot_frame, text="Plot id:")
        self.plot_label.pack(side=TOP)
        self.plot_name = StringVar(self)
        self.plot_scrollbar = Scrollbar(self.plot_frame, orient=VERTICAL)
        self.plot_listbox = Listbox(self.plot_frame,
                                    yscrollcommand=self.plot_scrollbar.set,
                                    selectmode=EXTENDED)
        self.plot_scrollbar.config(command=self.plot_listbox.yview)
        self.plot_scrollbar.pack(side=RIGHT, fill=Y)
        self.plot_listbox.pack(side=LEFT, fill=BOTH, expand=1)

    def create_event_listbox(self):

        self.event_label = Label(self.event_frame, text="Event:")
        self.event_label.pack(side=TOP)
        self.event_name = StringVar(self)
        self.event_scrollbar = Scrollbar(self.event_frame, orient=VERTICAL)
        self.event_listbox = Listbox(self.event_frame,
                                     yscrollcommand=self.event_scrollbar.set,
                                     selectmode=BROWSE)
        self.event_scrollbar.config(command=self.event_listbox.yview)
        self.event_scrollbar.pack(side=RIGHT, fill=Y)
        self.event_listbox.pack(side=LEFT, fill=BOTH, expand=1)

    def create_event_time_entries(self):

        self.event_start_label = Label(self.event_time_frame, text='Start Time:')
        self.event_start_label.pack()
        self.event_start_entry = Entry(self.event_time_frame)
        self.event_start_entry.pack()
        self.event_end_label = Label(self.event_time_frame, text='End Time:')
        self.event_end_label.pack()
        self.event_end_entry = Entry(self.event_time_frame)
        self.event_end_entry.pack()
        self.event_query_button = Button(self.event_time_frame,
                                         text='Load Event',
                                         command=self.load_event_data)
        self.event_query_button.pack()

    def set_filter(self):
        '''
        Hack for 'broken' check box
        '''
        if self.filter_plots == 0:
            self.filter_plots = 1
        else:
            self.filter_plots = 0

    def set_summary(self):
        '''
        Hack for 'broken' check box
        '''
        if self.summary_only == 0:
            self.summary_only = 1
        else:
            self.summary_only = 0

    def set_gmax(self):
        if self.use_gmax == 0:
            self.use_gmax = 1
        else:
            self.use_gmax = 0

    def create_checkboxes(self):
        '''
        Create various checkboxes for output options.
        '''
        self.plot_checkbox = Checkbutton(self.event_time_frame,
                                         text="Filter Plots by Event",
                                         variable=self.filter_plots,
                                         command=self.set_filter)
        self.plot_checkbox.pack(side=BOTTOM)
        self.plot_checkbox.toggle()
        self.filter_plots = 1
        self.summary_checkbox = Checkbutton(self.event_time_frame,
                                            text="Summarize data",
                                            variable=self.summary_only,
                                            command=self.set_summary)
        self.summary_checkbox.pack(side=BOTTOM)
        self.summary_checkbox.toggle()
        self.summary_only = 1

    def create_gmax_spinbox(self):

        self.gmax_label = Label(self.event_time_frame, text='Y maximum:')
        self.gmax_label.pack()
        self.gmax_spinbox = Spinbox(self.event_time_frame, from_=0, to_=100)
        self.gmax_spinbox.pack()

    def create_out_buttons(self):
        '''
        Create a button that creates a time series image.
        '''
        self.ts_button = Button(self.ts_frame, text='Create Time Series',
                                command=self.create_ts_image)
        self.ts_button.pack()
        self.wr_button = Button(self.ts_frame, text='Create Wind Rose',
                                command=self.create_wr_image)
        self.wr_button.pack()

        if HAVE_OGR:
            self.ogr_button = Button(self.ts_frame, text='Export to OGR',
                                     command=self.export_ogr)
            self.ogr_button.pack()

        self.csv_button = Button(self.ts_frame, text='Export to CSV',
                                 command=self.export_csv)
        self.csv_button.pack()
        self.kmz_button = Button(self.ts_frame, text='Export to KMZ',
                                 command=self.export_kmz)
        self.kmz_button.pack()


    def create(self):
        '''
        Build and pack the entire tk GUI.
        '''

        # Variables
        self.filter_plots = 0
        self.summary_only = 1

        # Menu bar
        self.create_menus()

        # Plot data
        self.plot_frame = Frame(self)

        # Event data
        self.event_frame = Frame(self)
        self.create_plot_listbox()
        self.event_frame.pack(side=LEFT)
        self.create_event_listbox()
        self.event_time_frame = Frame(self)
        self.event_time_frame.pack(side=LEFT)
        self.create_event_time_entries()

        # Pack the plot frame
        self.plot_frame.pack(side=LEFT)

        # Checkable options
        self.create_checkboxes()
        # Global max.
        self.create_gmax_spinbox()

        # Timeseries Image
        self.ts_frame = Frame(self)
        self.ts_frame.pack()
        self.create_out_buttons()

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.cadre = RxCadre()
        self.pack()
        self.create()

def _quit():
    root.quit()
    root.destroy()

root = Tk()
root.protocol("WM_DELETE_WINDOW", _quit)
app = RxCadreTk(master=root)
app.mainloop()

