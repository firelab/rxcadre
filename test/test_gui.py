# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Sep  8 2010)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx

###########################################################################
## Class GUI_test1
###########################################################################

class GUI_test1 ( wx.Frame ):
	
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"RxCadre_testGUI", pos = wx.DefaultPosition, size = wx.Size( 1378,856 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		self.SetBackgroundColour('WHITE')
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer6 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer8 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText14 = wx.StaticText( self, wx.ID_ANY, u"Current Directory:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText14.Wrap( -1 )
		bSizer8.Add( self.m_staticText14, 0, wx.ALL, 5 )
		
		self.cur_dir = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (300,-1), wx.TE_READONLY )
		bSizer8.Add( self.cur_dir, 0, wx.ALL, 5 )
		
		self.m_staticText11 = wx.StaticText( self, wx.ID_ANY, u"Current Database:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )
		bSizer8.Add( self.m_staticText11, 0, wx.ALL, 5 )
		
		self.db_picker = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (300,-1), wx.TE_READONLY )
		bSizer8.Add( self.db_picker, 0, wx.ALL, 5 )
		
		self.m_staticText9 = wx.StaticText( self, wx.ID_ANY, u"Select Table:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText9.Wrap( -1 )
		bSizer8.Add( self.m_staticText9, 0, wx.ALL, 5 )
		
		comboChoices = []
		self.combo = wx.ComboBox( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, comboChoices, 0 )
		bSizer8.Add( self.combo, 0, wx.ALL, 5 )
		
		self.m_staticText10 = wx.StaticText( self, wx.ID_ANY, u"Select PlotID", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10.Wrap( -1 )
		bSizer8.Add( self.m_staticText10, 0, wx.ALL, 5 )
		
		m_choice17Choices = [ u"L1G", u"S8", u"K1" ]
		self.m_choice17 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice17Choices, 0 )
		self.m_choice17.SetSelection( 0 )
		bSizer8.Add( self.m_choice17, 0, wx.ALL, 5 )
		
		bSizer6.Add( bSizer8, 0, wx.EXPAND, 5 )
		
		bSizer9 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Select Start Date:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )
		bSizer9.Add( self.m_staticText3, 0, wx.ALL, 5 )
		
		start_monthChoices = [ u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10", u"11", u"12" ]
		self.start_month = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, start_monthChoices, 0 )
		self.start_month.SetSelection( 0 )
		bSizer9.Add( self.start_month, 0, wx.ALL, 5 )
		
		start_dayChoices = [ u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10", u"11", u"12", u"13", u"14", u"15", u"16", u"17", u"18", u"19", u"20", u"21", u"22", u"23", u"24", u"25", u"26", u"27", u"28", u"29", u"30", u"31" ]
		self.start_day = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, start_dayChoices, 0 )
		self.start_day.SetSelection( 0 )
		bSizer9.Add( self.start_day, 0, wx.ALL, 5 )
		
		start_yearChoices = [ u"1990", u"1991", u"1992", u"1993", u"1994", u"1995", u"1996", u"1997", u"1998", u"1999", u"2000", u"2001", u"2002", u"2003", u"2004", u"2005", u"2006", u"2007", u"2008", u"2009", u"2010", u"2011", u"2012", u"2013", u"2014", u"2015", u"2016", u"2017", u"2018", u"2019", u"2020" ]
		self.start_year = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, start_yearChoices, 0 )
		self.start_year.SetSelection( 0 )
		bSizer9.Add( self.start_year, 0, wx.ALL, 5 )
		
		self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"Select Start Time:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )
		bSizer9.Add( self.m_staticText7, 0, wx.ALL, 5 )
		
		start_hourChoices = [ u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10", u"11", u"12" ]
		self.start_hour = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, start_hourChoices, 0 )
		self.start_hour.SetSelection( 0 )
		bSizer9.Add( self.start_hour, 0, wx.ALL, 5 )
		
		start_minuteChoices = [ u"00", u"01", u"02", u"03", u"04", u"05", u"06", u"07", u"08", u"09", u"10", u"11", u"12", u"13", u"14", u"15", u"16", u"17", u"18", u"19", u"20", u"21", u"22", u"23", u"24", u"25", u"26", u"27", u"28", u"29", u"30", u"31", u"32", u"33", u"34", u"35", u"36", u"37", u"38", u"39", u"40", u"41", u"42", u"43", u"44", u"45", u"46", u"47", u"48", u"49", u"50", u"51", u"52", u"53", u"54", u"55", u"56", u"57", u"58", u"59" ]
		self.start_minute = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, start_minuteChoices, 0 )
		self.start_minute.SetSelection( 0 )
		bSizer9.Add( self.start_minute, 0, wx.ALL, 5 )
		
		start_secondChoices = [ u"00", u"01", u"02", u"03", u"04", u"05", u"06", u"07", u"08", u"09", u"10", u"11", u"12", u"13", u"14", u"15", u"16", u"17", u"18", u"19", u"20", u"21", u"22", u"23", u"24", u"25", u"26", u"27", u"28", u"29", u"30", u"31", u"32", u"33", u"34", u"35", u"36", u"37", u"38", u"39", u"40", u"41", u"42", u"43", u"44", u"45", u"46", u"47", u"48", u"49", u"50", u"51", u"52", u"53", u"54", u"55", u"56", u"57", u"58", u"59" ]
		self.start_second = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, start_secondChoices, 0 )
		self.start_second.SetSelection( 0 )
		bSizer9.Add( self.start_second, 0, wx.ALL, 5 )
		
		start_ampmChoices = [ u"AM", u"PM" ]
		self.start_ampm = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, start_ampmChoices, 0 )
		self.start_ampm.SetSelection( 0 )
		bSizer9.Add( self.start_ampm, 0, wx.ALL, 5 )
		
		self.m_staticText13 = wx.StaticText( self, wx.ID_ANY, u"             Use the timeframe of existing event:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )
		bSizer9.Add( self.m_staticText13, 0, wx.ALL, 5 )
		
		event_comboChoices = []
		self.event_combo = wx.ComboBox( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, event_comboChoices, 0 )
		bSizer9.Add( self.event_combo, 0, wx.ALL, 5 )
		
		bSizer6.Add( bSizer9, 0, wx.EXPAND, 5 )
		
		bSizer10 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"  Select End Date:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		bSizer10.Add( self.m_staticText4, 0, wx.ALL, 5 )
		
		end_monthChoices = [ u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10", u"11", u"12" ]
		self.end_month = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, end_monthChoices, 0 )
		self.end_month.SetSelection( 0 )
		bSizer10.Add( self.end_month, 0, wx.ALL, 5 )
		
		end_dayChoices = [ u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10", u"11", u"12", u"13", u"14", u"15", u"16", u"17", u"18", u"19", u"20", u"21", u"22", u"23", u"24", u"25", u"26", u"27", u"28", u"29", u"30", u"31" ]
		self.end_day = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, end_dayChoices, 0 )
		self.end_day.SetSelection( 0 )
		bSizer10.Add( self.end_day, 0, wx.ALL, 5 )
		
		end_yearChoices = [ u"1990", u"1991", u"1992", u"1993", u"1994", u"1995", u"1996", u"1997", u"1998", u"1999", u"2000", u"2001", u"2002", u"2003", u"2004", u"2005", u"2006", u"2007", u"2008", u"2009", u"2010", u"2011", u"2012", u"2013", u"2014", u"2015", u"2016", u"2017", u"2018", u"2019", u"2020" ]
		self.end_year = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, end_yearChoices, 0 )
		self.end_year.SetSelection( 0 )
		bSizer10.Add( self.end_year, 0, wx.ALL, 5 )
		
		self.m_staticText8 = wx.StaticText( self, wx.ID_ANY, u"  Select End Time:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText8.Wrap( -1 )
		bSizer10.Add( self.m_staticText8, 0, wx.ALL, 5 )
		
		end_hourChoices = [ u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10", u"11", u"12" ]
		self.end_hour = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, end_hourChoices, 0 )
		self.end_hour.SetSelection( 0 )
		bSizer10.Add( self.end_hour, 0, wx.ALL, 5 )
		
		end_minuteChoices = [ u"00", u"01", u"02", u"03", u"04", u"05", u"06", u"07", u"08", u"09", u"10", u"11", u"12", u"13", u"14", u"15", u"16", u"17", u"18", u"19", u"20", u"21", u"22", u"23", u"24", u"25", u"26", u"27", u"28", u"29", u"30", u"31", u"32", u"33", u"34", u"35", u"36", u"37", u"38", u"39", u"40", u"41", u"42", u"43", u"44", u"45", u"46", u"47", u"48", u"49", u"50", u"51", u"52", u"53", u"54", u"55", u"56", u"57", u"58", u"59" ]
		self.end_minute = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, end_minuteChoices, 0 )
		self.end_minute.SetSelection( 0 )
		bSizer10.Add( self.end_minute, 0, wx.ALL, 5 )
		
		end_secondChoices = [ u"00", u"01", u"02", u"03", u"04", u"05", u"06", u"07", u"08", u"09", u"10", u"11", u"12", u"13", u"14", u"15", u"16", u"17", u"18", u"19", u"20", u"21", u"22", u"23", u"24", u"25", u"26", u"27", u"28", u"29", u"30", u"31", u"32", u"33", u"34", u"35", u"36", u"37", u"38", u"39", u"40", u"41", u"42", u"43", u"44", u"45", u"46", u"47", u"48", u"49", u"50", u"51", u"52", u"53", u"54", u"55", u"56", u"57", u"58", u"59" ]
		self.end_second = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, end_secondChoices, 0 )
		self.end_second.SetSelection( 0 )
		bSizer10.Add( self.end_second, 0, wx.ALL, 5 )
		
		end_ampmChoices = [ u"AM", u"PM" ]
		self.end_ampm = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, end_ampmChoices, 0 )
		self.end_ampm.SetSelection( 0 )
		bSizer10.Add( self.end_ampm, 0, wx.ALL, 5 )
		
		
		bSizer10.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		bSizer6.Add( bSizer10, 0, wx.EXPAND, 5 )
		
		bSizer12 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_button7 = wx.Button( self, wx.ID_ANY, u"Create Plots", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer12.Add( self.m_button7, 0, wx.ALL, 5 )
		
		
		bSizer12.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_staticText101 = wx.StaticText( self, wx.ID_ANY, u"Name for kmz output:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText101.Wrap( -1 )
		bSizer12.Add( self.m_staticText101, 0, wx.ALL, 5 )
		
		self.file_name = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer12.Add( self.file_name, 0, wx.ALL, 5 )
		
		bSizer6.Add( bSizer12, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )
		
		bSizer11 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.plot_time = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer11.Add( self.plot_time, 1, wx.ALL|wx.EXPAND, 5 )
		
		self.plot_rose = wx.StaticBitmap( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer11.Add( self.plot_rose, 1, wx.ALL|wx.EXPAND, 5 )
		
		bSizer6.Add( bSizer11, 1, wx.EXPAND, 5 )
		
		self.SetSizer( bSizer6 )
		self.Layout()
		self.m_menubar1 = wx.MenuBar( 0 )
		self.m_menu1 = wx.Menu()
		self.m_menuItem1 = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Select Database", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.AppendItem( self.m_menuItem1 )
		
		self.m_menuItem2 = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Create Database", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.AppendItem( self.m_menuItem2 )
		
		self.m_menuItem3 = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Change Directory", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.AppendItem( self.m_menuItem3 )
		
		self.m_menubar1.Append( self.m_menu1, u"File" ) 
		
		self.m_menu2 = wx.Menu()
		self.m_menuItem4 = wx.MenuItem( self.m_menu2, wx.ID_ANY, u"Import Data", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu2.AppendItem( self.m_menuItem4 )
		
		self.m_menubar1.Append( self.m_menu2, u"Edit" ) 
		
		self.m_menu3 = wx.Menu()
		self.m_menuItem6 = wx.MenuItem( self.m_menu3, wx.ID_ANY, u"About", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu3.AppendItem( self.m_menuItem6 )
		
		self.m_menubar1.Append( self.m_menu3, u"Help" ) 
		
		self.SetMenuBar( self.m_menubar1 )
		
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.db_picker.Bind( wx.EVT_TEXT, self.change_tables )
		self.combo.Bind( wx.EVT_COMBOBOX, self.change_picker )
		self.combo.Bind( wx.EVT_TEXT_ENTER, self.change_picker )
		self.m_button7.Bind( wx.EVT_BUTTON, self.create_all )
		self.Bind( wx.EVT_MENU, self.open_msg, id = self.m_menuItem1.GetId() )
		self.Bind( wx.EVT_MENU, self.create_db, id = self.m_menuItem2.GetId() )
		self.Bind( wx.EVT_MENU, self.change_dir, id = self.m_menuItem3.GetId() )
		self.Bind( wx.EVT_MENU, self.import_data2, id = self.m_menuItem4.GetId() )
		self.Bind( wx.EVT_MENU, self.about, id = self.m_menuItem6.GetId() )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def change_tables( self, event ):
		event.Skip()
	
	def change_picker( self, event ):
		event.Skip()
	
	
	def create_all( self, event ):
		event.Skip()
	
	def open_msg( self, event ):
		event.Skip()
	
	def create_db( self, event ):
		event.Skip()
	
	def change_dir( self, event ):
		event.Skip()
	
	def import_data2( self, event ):
		event.Skip()
	
	def about( self, event ):
		event.Skip()
	

