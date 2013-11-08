#!/usr/bin/env python
###############################################################################
# $Id$
#
#  Project:  showind
#  Purpose:  Display and subset wind data
#  Author:   Kyle Shannon <kyle@pobox.com>
#
###############################################################################
#  Copyright (c) 2013, Kyle Shannon <kyle@pobox.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
###############################################################################

from collections import namedtuple
import datetime
import logging
import math
import os
import sqlite3
import sys
import unittest
import zipfile

import numpy
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.append(os.path.abspath('windrose'))
from windrose import *

logging.basicConfig(level=logging.INFO)

def _import_date(string):
    '''
    Parse a datetime from a UTC string
    '''
    dt = datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%S")
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
    ##We may have a serious problem in the form of the data
    ##They're using arcminutes, but we may have to convert to decimal

    wkt = self._to_decdeg(wkt)
    wkt = wkt.strip().upper()
    if wkt.find('POINT') < 0:
        raise ValueError
    wkt = wkt[wkt.find('(')+1:wkt.find(')')].split()
    if len(wkt) != 2:
        raise ValueError
    
    return tuple([float(c) for c in wkt])

def _to_decdeg(d):
    d = d.split("'")
    s = float(d[-1])
    s = s / 60.0
    d, m = [float(f) for f in d[0].split('DEG')]
    m += s
    m = m / 60.0
    if d < 0:
        m = m * -1
    d += m
    return d

class ShoWind:
    '''
    Extract a given amount of data with time and space constraints.
    '''
    def __init__(self, dbfile, start=None, end=None, geomfilter=None):
        self.dbfile = dbfile
        if start:
            self.start = _import_date(start)
        else:
            self.start = None
        if end:
            self.end = _import_date(end)
        else:
            self.end = None
        self.geomfilter = geomfilter
        self.db = sqlite3.connect(dbfile)
        self.cursor = self.db.cursor()

    def point_location(self, plot):
        '''
        Fetch the x and y coordinate of the plot
        '''
        if plot.startswith('L1-'):
            plot = plot.split('-')
            plot = 'L1G-' + plot[1]
        sql = """SELECT geometry FROM plot_location WHERE plot_id=?"""
        self.cursor.execute(sql, (plot,))
        row = self.cursor.fetchone()
        return _extract_xy(row[0])

    def fetch_point_data(self, plot):
        '''
        Fetch data for a single point
        '''
        sql = """SELECT * FROM mean_flow_obs
                          WHERE plot_id=? AND date_time BETWEEN ? AND ? AND
                          quality='OK'"""
        self.cursor.execute(sql, (plot, self.start, self.end))
        data = self.cursor.fetchall()
        logging.info('Query fetched %i result(s)' % len(data))
        return data

    def _point_kml(self, plot, data, images=[]):
        '''
        Create a kml representation of a plot
        '''

        lon, lat = self.point_location(plot)
        stats = self.statistics(data)
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

    def statistics(self, data):
        '''
        Calculate the stats for speed and direction data
        '''
        spd = [spd[2] for spd in data]
        gust = [gust[3] for gust in data]
        dir = [dir[4] for dir in data]
        samples = numpy.array(spd)
        spd_mean = numpy.mean(samples)
        spd_stddev = numpy.std(samples)
        samples = numpy.array(gust)
        gust_max = numpy.max(samples)
        samples = numpy.array(dir)
        direction_mean = stats.morestats.circmean(samples, 360, 0)
        direction_stddev = stats.morestats.circstd(samples, 360, 0)
        return (spd_mean, spd_stddev), (gust_max), (direction_mean, direction_stddev)

    def create_time_series_image(self, data, plt_title, filename = ''):
        '''
        Create a time series image for the plot over the time span
        '''
        spd = [d[2] for d in data]
        gust = [d[3] for d in data]
        dir = [d[4] for d in data]
        time = [mdates.date2num(datetime.datetime.strptime(d[1],
                '%Y-%m-%d %H:%M:%S')) for d in data]
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
                     self.start.strftime('%Y-%m-%d %H:%M:%S'),
                     self.end.strftime('%Y-%m-%d %H:%M:%S')))
        if not filename:
            plt.show()
            plt.close()
        else:
            plt.savefig(filename)
            plt.close()
        return filename

    def create_windrose(self, data, filename=''):
        '''
        Create a windrose from a dataset.
        '''
        spd = [d[2] for d in data]
        gust = [d[3] for d in data]
        dir = [d[4] for d in data]
        time = [mdates.date2num(datetime.datetime.strptime(d[1],
                '%Y-%m-%d %H:%M:%S')) for d in data]

        if len(data) >= 1:
            #fig = plt.figure(figsize=(8, 8), dpi=80, facecolor='w', edgecolor='w')
            fig = plt.figure(facecolor='w', edgecolor='w')
            rect = [0.1, 0.1, 0.8, 0.8]
            ax = WindroseAxes(fig, rect, axisbg='w')
            fig.add_axes(ax)
            ax.bar(dir, spd, normed=True, opening=0.8, edgecolor='white')
            l = ax.legend(axespad=-0.10)
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

    def create_field_kmz(self, filename):
        '''
        Write a kmz with a time series and wind rose.  The stats are included
        in the html bubble as well.
        '''
        sql = '''SELECT DISTINCT(plot_id) FROM mean_flow_obs
                   WHERE date_time BETWEEN ? AND ?'''
        self.cursor.execute(sql, (self.start, self.end))

        kmz = zipfile.ZipFile( filename, 'w', 0, True)
        kmlfile = 'doc.kml'
        fout = open(kmlfile, 'w')
        fout.write('<Document>\n')

        plots = self.cursor.fetchall()
        for plot in plots:
            plot = plot[0]
            logging.info('Processing plot %s' % plot)
            if filename == '':
                filename = plot
            if filename[-4:] != '.kmz':
                filename = filename + '.kmz'

            data = self.fetch_point_data(plot)
            if not data:
                continue
            try:
                pngfile = self.create_time_series_image(data, plot, plot + '_time.png')
                rosefile = self.create_windrose(data, plot + '_rose.png')
                kml = self._point_kml(plot, data, [pngfile,rosefile])
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

    def create_kmz(self, plot, filename = ''):
        '''
        Write a kmz with a time series and wind rose.  The stats are included
        in the html bubble as well.
        '''
        if filename == '':
            filename = plot
        if filename[-4:] != '.kmz':
            filename = filename + '.kmz'

        data = self.fetch_point_data(plot)
        pngfile = self.create_time_series_image(data, plot, plot + '_time.png')
        rosefile = self.create_windrose(data, plot + '_rose.png')
        kml = self._point_kml(plot, data, [pngfile,rosefile])

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
        os.remove(pngfile)
        os.remove(rosefile)
        return filename

    def create_tables(self, dbfile):
        '''
        Create a new database and tables for mean flow.  Two tables are created,
        one for plot locations, another for the measured data.  These are made
        under the assumption of similar set up for big butte.
        '''
        db = sqlite3.connect(dbfile)
        curs = db.cursor()
        sql = """CREATE TABLE plot_location(plot_id TEXT, 
                                            geometry TEXT, plot_type TEXT)"""
        curs.execute(sql)
        sql = """CREATE TABLE event(project_name TEXT,
                                    event_name TEXT NOT NULL,
                                    event_start TEXT NOT NULL,
                                    event_end TEXT NOT NULL,
                                    PRIMARY KEY(project_name, event_name))"""
        curs.execute(sql)
        sql = """CREATE TABLE obs_table(obs_table_name TEXT NOT NULL,
                                        obs_disp_name TEXT NOT NULL,
                                        geometry_column TEXT NOT NULL,
                                        obs_cols TEXT NOT NULL,
                                        obs_col_names TEXT)"""
        cursor.execute(sql)
        db.commit()
        db.close()

    def import_hobo(self, path):
        '''
        Import csv files from hobo wind sensors.  Import all records in all csv
        files in the path provided.  Tailored to hobo loggers.
        '''
        csv_files = [csv for csv in os.listdir(path) if os.path.splitext(csv)[1] == '.csv']
        csv_files = [os.path.join(path, csv) for csv in csv_files]
        if not csv_files:
            logging.error('No csv files in directory')
            return None
        for csv in csv_files:
            fin = open(csv)
            plot = os.path.splitext(os.path.basename(csv))[0].upper()
            #self.cursor.execute('INSERT INTO plot_location(plot_id) VALUES(?)',
            #                    (plot,))
            header = 0
            for line in fin:
                if header < 2:
                    header += 1
                    continue
                line = line.split(',')
                if len(line) != 5:
                    logging.error('Could not parse csv file properly, not'
                                  'enough records.  Check file: %s' % csv)
                    continue
                date = datetime.datetime.strptime(line[1], '%m/%d/%y %I:%M:%S %p')
                spd = float(line[2])
                gust = float(line[3])
                dir = float(line[4])
                quality = 'OK'
                if spd < 0.0:
                    logging.error('Invalid speed (%f) for plot:%s' % (spd, plot))
                    quality = 'SUSPECT'
                if gust < 0.0:
                    logging.error('Invalid gust (%f) for plot:%s' % (gust, plot))
                    quality = 'SUSPECT'
                if dir < 0.0 or dir > 360.0:
                    logging.error('Invalid dir (%f) for plot:%s' % (dir, plot))
                    quality = 'SUSPECT'
                self.cursor.execute('''INSERT INTO mean_flow_obs(plot_id,
                                       date_time, wind_speed, wind_gust,
                                       wind_dir, quality)
                                       VALUES(?, ?, ?, ?, ?, ?)''',
                                    (plot, date, spd, gust, dir, quality))
            self.db.commit()

class TestMisc(unittest.TestCase):
    '''
    Test the smaller functions
    '''
    def test_wkt_1(self):
        ''' Test various whitespace in wkt '''
        point = _extract_xy('POINT(10.0 10.0)')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_2(self):
        ''' Test various whitespace in wkt '''
        point = _extract_xy(' POINT(10.0 10.0)')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_3(self):
        ''' Test various whitespace in wkt '''
        point = _extract_xy('POINT(10.0 10.0) ')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_4(self):
        ''' Test various whitespace in wkt '''
        point = _extract_xy('POINT( 10.0 10.0)')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_5(self):
        ''' Test various whitespace in wkt '''
        point = _extract_xy('POINT(10.0 10.0 )')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_6(self):
        ''' Test various whitespace in wkt '''
        point = _extract_xy('POINT( 10.0 10.0 )')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_7(self):
        ''' Test various whitespace in wkt '''
        point = _extract_xy('POINT ( 10.0 10.0)')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_8(self):
        ''' Test various whitespace in wkt '''
        point = _extract_xy('POINT ( 10.0 10.0 )')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_9(self):
        ''' Test various whitespace in wkt '''
        self.assertRaises(ValueError, _extract_xy, 'POLYGON ( 10.0 10.0 )')
    def test_wkt_10(self):
        ''' Test various whitespace in wkt '''
        self.assertRaises(ValueError, _extract_xy, 'POLYGON ( 10.0 10.0 10.0 )')
    def test_wkt_11(self):
        ''' Test various decimal in wkt '''
        point = _extract_xy('POINT (10 10)')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_12(self):
        ''' Test various decimal in wkt '''
        point = _extract_xy('POINT (10 10.0)')
        self.assertEqual(point, (10.0, 10.0))
    def test_wkt_13(self):
        ''' Test various decimal in wkt '''
        point = _extract_xy('POINT (10.0 10)')
        self.assertEqual(point, (10.0, 10.0))

class TestShoWind(unittest.TestCase):
    '''
    Test the access
    '''

def usage():
    print('showind.py [--write] [--windrose] [--timeseries]')
    print('           [--start starttime] [--end endtime]')
    print('           [--event name] plot output_file')
    sys.exit(1)

if __name__ == '__main__':

    if False:
        unittest.main(verbosity=2)

    plot = None
    outfile = None
    start = None
    end = None
    event = None
    write = False
    windrose = False
    timeseries = False

    args = sys.argv
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == '--write':
            write = True
        elif arg == '--windrose':
            windrose = True
        elif arg == '--timeseries':
            timeseries = True
        elif arg == '--start':
            i += 1
            start = args[i]
        elif arg == '--end':
            i += 1
            end = args[i]
        elif arg == '--event':
            i += 1
            event = args[i]
        elif plot is None:
            plot = arg
        elif outfile is None:
            outfile = arg
        i += 1
    if not plot:
        usage()
    if not windrose and not timeseries and plot != 'all':
        usage()
    if not(start and end) and not event:
        usage()

    s = ShoWind('dan.sqlite', start, end)
    if event:
        s.cursor.execute('SELECT start, end FROM events WHERE name=?', (event,))
        row = s.cursor.fetchone()
        start = row[0]
        end = row[1]
        s.start = _import_date(start.replace(' ', 'T'))
        s.end = _import_date(end.replace(' ', 'T'))

    if plot != 'all':
        d = s.fetch_point_data(plot)
        if not d:
            print('Could not fetch data for plot')
            usage()
        if write:
            if outfile:
                f = outfile
            else:
                f = plot + '.png'
        else:
            f = ''
        if timeseries:
            s.create_time_series_image(d, plot, f.replace('.', '_time.'))
        if windrose:
            s.create_windrose(d, f.replace('.', '_rose.'))
    else:
        if not outfile and event:
            outfile = event + '.kmz'
        elif not outfile:
            outfile = 'out.kmz'
        s.create_field_kmz(outfile)

