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


class RxCadreIOError(Exception):pass
class RxCadreInvalidDbError(Exception):pass

class RxCadre:
    """
    Main interface for RX Cadre data.
    """

    def init_new_db(self, filename):
        """
        Create a new, empty database with appropriate metatables.  If the file
        previously exists, we fail before connecting using sqlite.  It must be
        a new file.
        """
        if os.path.exists(filename):
            raise RxCadreIOError("Database file already exists")
        db = sqlite3.connect(filename)
        cursor = db.cursor()
        sql = """CREATE TABLE plot_location(plot_id TEXT NOT NULL PRIMARY KEY,
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
        valid = self.check_valid_db(db)
        if not valid:
            db.close()
            e = "Failed to create a valid database."
            raise RxCadreInvalidDbError(e)
        return db


    def check_valid_db(self, db):
        """
        Check the schema of an existing db.  This involves checking the
        metatables, and checking to make sure tables registered in obs_tables
        exist.
        """

        cursor = db.cursor()
        required_tables = set([u'plot_location', u'event', u'obs_table'])
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t[0] for t in cursor.fetchall()]
        if not set(table_names) <= required_tables:
            e = "Database does not contain the required tables, missing:"
            e += ",".join(required_tables.difference(table_names))
            return False
        cursor.execute("select obs_table_name from obs_table")
        obs_names = cursor.fetchall()
        for name in obs_names:
            if n not in table_names:
                e = "Database is invalid, missing table: %s" % n
                return False
        return True


    def import_rxc_wind_data(self, db, input_csv):
        """Create a table from a selected file in the current database.
        Import the appropriate columns and populate with associated data."""

        #file_path = "C:/Users/krabil/Documents/GitHub/rxcadre/test/test_data.txt"
        cursor = db.cursor()
        db.text_factory = str
        data_file = open(input_csv,"r")
        header = data_file.readline().split(",")
        for i in range(0,len(header)):
            header[i] = header[i].replace('\n',"")
            header[i] = header[i].replace('+',"")
            header[i] = header[i].replace(":","")
            header[i] = header[i].replace(")","")
            header[i] = header[i].replace("(","")
        hold_name = header[0]

        #cursor.execute("drop table "+hold_name)

        sql = "CREATE TABLE "+hold_name+"("
        for i, h in enumerate(header):
            sql += h + ' text'
            if(i < len(header)-1):
                sql += ','
        sql += ')'

        cursor.execute(sql)

        qs = "("+ (len(header)-1)* "?," +"?)"
        insrt = "insert into " + hold_name+ " values "
        insrt += qs

        n = 0
        line = data_file.readline()
        while (line != None):
            n = n+1
            if len(line.split(",")) < len(header):
                break
            else:
                cursor.execute(insrt, line.split(","))
            line = data_file.readline()
        cursor.execute("INSERT INTO obs_table VALUES (?,?,?,?)",header[0:4])
        #The following is purely a sanity check
        #cursor.execute("SELECT * FROM obs_table")         
        #names = cursor.fetchall()
        #print names, len(names)

    


