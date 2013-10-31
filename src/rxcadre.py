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
import json

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
        db.close()
        if not valid:
            e = "Failed to create a valid database."
            raise RxCadreInvalidDbError(e)


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

    def import_data(self, db, file_path, import_fx=None):
        """
        Import a new data set into the database.  An obs table should be
        created and registered with obs_tables.  It also should populate the
        plot_location data if possible.  The import_fx is an optional function
        that does the importing.
        """
        con = sqlite3.connect(db)

        data_file = open(file_path,"r")
        header = data_file.readline().split(",")

        cursor = con.cursor()
        hold_name = header[0]
        cursor.execute("CREAT TABLE " + hold_name + "(" + header[0] + ")")
        for i in range(1,len(header)):
            cursor.execute("ALTER TABLE " + hold_name + " ADD COLUMN " + json.dumps(header[i]))

        #The line below is what I'm trying to fix
        cursor.execute("insert into hold_name values (?)", data_file.readline().split(","))
        cursor.execute("insert into obs_table values(header[0],header[1],header[2],header[3])")


