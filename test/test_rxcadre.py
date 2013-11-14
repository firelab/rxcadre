#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
#  $Id$
#  Project:  RX Cadre Data Visualization
#  Purpose:  Test rxcadre module
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

import sys
import unittest

sys.path.append('../src')

from rxcadre import *

class RxCadreTestDb(unittest.TestCase):
    """
    Test database creation and integrity.
    """
    def setUp(self):
        self.rx = RxCadre()

    def create_table_db(self):
        """
        Create a valid db.
        """
        sql = open("../data/new_tables.sql").read().split(";")
        db = sqlite3.connect("")
        c = db.cursor()
        for s in sql:
            c.execute(s)
        db.commit()
        return db


    def create_invalid_db(self):
        """Create a completely invalid db."""
        sql = "CREATE TABLE t(a int)"
        db = sqlite3.connect("")
        c = db.cursor()
        c.execute(sql)
        db.commit()
        return db


    def create_table_data(self):
        '''Create a valid table, then insert a few rows of valid obs data'''
        db = self.rx.init_new_db("")
        c = db.cursor()
        sql = '''
              CREATE TABLE test_obs(plot_id text,
                                    ts text,
                                    m integer)
              '''
        c.execute(sql)
        sql = '''
              INSERT INTO obs_table values(?, ?, ?, ?, ?, ?)
              '''
        c.execute(sql, ('test_obs', 'ts', 'wkt', 'm',
                        'M', 'Test M'))
        sql = '''
              INSERT INTO test_obs values(?, ?, ?)
              '''
        c.execute(sql, ('A', datetime.datetime(2013, 11, 14, 15, 43, 30), 1))
        c.execute(sql, ('A', datetime.datetime(2013, 11, 14, 15, 43, 35), 2))
        c.execute(sql, ('A', datetime.datetime(2013, 11, 14, 15, 43, 40), 3))
        c.execute(sql, ('B', datetime.datetime(2013, 11, 14, 15, 43, 30), 4))
        c.execute(sql, ('B', datetime.datetime(2013, 11, 14, 15, 43, 35), 5))
        c.execute(sql, ('B', datetime.datetime(2013, 11, 14, 15, 43, 40), 6))
        db.commit()
        return db


    def test_db_creation_1(self):
        '''Test valid creation'''
        db = self.create_table_db()
        self.assertTrue(self.rx.check_valid_db(db))

    def test_db_creation_2(self):
        '''Test invalid creation'''
        db = self.create_invalid_db()
        self.assertFalse(self.rx.check_valid_db(db))

    def test_db_internal_create_1(self):
        '''Test the internal creation of various tests'''
        db = self.create_table_data()
        self.assertTrue(self.rx.check_valid_db(db))

    def test_db_init_1(self):
        '''Check internal creation function'''
        db = self.rx.init_new_db("")

    def test_db_init_2(self):
        '''Check valid initialization of db.'''
        db = self.rx.init_new_db("")
        self.assertTrue(self.rx.check_valid_db(db))

    def test_db_init_3(self):
        '''Make sure we don't overwrite files.'''
        self.assertRaises(RxCadreIOError, self.rx.init_new_db,
                          'test_rxcadre.py')

    def test_extract_1(self):
        '''Default extraction'''
        db = self.create_table_data()
        self.rx.set_db(db)
        d = self.rx.extract_obs_data('test_obs', 'A')
        self.assertEqual(len(d), 2)
        self.assertEqual(len(d['timestamp']), 3)
        self.assertEqual(d['m'], [1, 2, 3])


    @unittest.skip('TODO')
    def test_extract_2(self):
        '''Time subset extraction'''
        db = self.create_table_data()
        self.rx.set_db(db)
        s = datetime.datetime(2013, 11, 14, 15, 43, 29)
        e = datetime.datetime(2013, 11, 14, 16, 00, 36)


    @unittest.skip('Failing...')
    def test_db_import_1(self):
        '''Test creating db and importing hobo data.'''
        db = self.rx.init_new_db("")
        self.assertNotEqual(db, None)
        self.rx.import_rxc_wind_data("kegan_test.csv",db)
        self.assertTrue(self.rx.check_valid_db(db))
        kml = self.rx._point_kml("K1",'kegan_test',db)
        kmz = self.rx.create_kmz("K1",'kegan_file','kegan_test',db)


if __name__ == '__main__':

    unittest.main()
