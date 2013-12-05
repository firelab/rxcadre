#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
#  $Id$
#  Project:  RX Cadre Data Visualization
#  Purpose:  Import csv data into tables
#  Author:   Kyle Shannon <kyle@pobox.com>
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
'''
Output creator for different data types
'''

from collections import OrderedDict as dict
from datetime import datetime
import os
import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

import numpy as np
from scipy.stats import morestats

sys.path.append(os.path.abspath('windrose'))
import windrose


class RxCadreOutput(object):
    '''
    Interface for outputs, with default exporters.
    '''

    def __init__(self, plot, data):
        '''
        Don't do anything.
        '''
        self.plot = plot
        self.data = data
        self.calc_stats()
        self.frmt_time()


    @property
    def plot_name(self):
        '''
        Plot name
        '''
        return self.plot[0]


    @property
    def plot_x(self):
        '''
        Plot x coordinate
        '''
        return float(self.plot[2])


    @property
    def plot_y(self):
        '''
        Plot y coordinate
        '''
        return float(self.plot[3])


    def export_csv_header(self):
        '''
        Default header string.
        '''
        header = '"plot_id",'
        header += ','.join(['"' + col + '"' for col in self.data.keys()])
        header += '\n'
        return header


    def export_csv(self, prog_func=None):
        '''
        Export data as csv.
        '''
        csv = ''
        if prog_func:
            prog_func(0.0)

        for i, times in enumerate(self.data['timestamp']):
            csv += ','.join([self.plot_name, datetime.
                                        strftime(times, '%Y-%m-%d %H:%M:%S')])
            csv += ','
            csv += ','.join([str(self.data[k][i]) for k in self.data.keys() \
                             if k != 'timestamp'])
            csv += '\n'
            if prog_func:
                if i % 1000:
                    prog_func(float(i) / len(self.data['timestamp']))
        return csv


    def export_ogr(self):
        '''
        Write a ogr features for the point
        '''
        pass


    def calc_stats(self):
        '''
        Calculate normal statistics
        '''

        self.stat = dict()
        for key, val in self.data.items():
            self.stat[key] = dict()
            if key == 'timestamp':
                continue
            samples = np.array(val)
            self.stat[key]['min'] = np.min(samples)
            self.stat[key]['max'] = np.max(samples)
            self.stat[key]['mean'] = np.mean(samples)
            self.stat[key]['stddev'] = np.std(samples)


    def export_kml(self, images):
        '''
        Export the kml for a single plot.
        '''
        try:
            rot = self.stat['direction']['mean']
        except:
            rot = 0.0
        kml =               '  <Placemark>\n'
        kml += self.export_kml_icon(rot)
        kml +=              '    <Point>\n' \
                            '      <coordinates>%.9f,%.9f,0</coordinates>\n' \
                            '    </Point>\n' % (self.plot_x, self.plot_y)
        kml = kml +         '    <name>%s</name>\n' \
                            '    <description>\n' \
                            '      <![CDATA[\n' % self.plot_name
        for image in images:
            kml = kml +     '        <img src = "%s" />\n'  % image
        kml = kml +         '        <table border="1">' \
                            '          <tr>\n' \
                            '            <th>Stats</th>\n' \
                            '          </tr>\n'
        for key in self.stat.keys():
            for key2 in self.stat[key]:
                kml = kml + '          <tr>\n' \
                            '            <td>%s</td>\n' \
                            '            <td>%.2f</td>\n' \
                            '          </tr>\n' % (key+key2,
                                                   self.stat[key][key2])
        kml = kml +         '        </table>\n' \
                            '      ]]>\n' \
                            '    </description>\n' \
                            '  </Placemark>\n'
        return kml


    def export_kml_icon(self, rotation):
        '''
        Default icon image.  No-op.
        '''
        return ''


    def export_timeseries(self, filename=''):
        '''
        Create a time series image for the plot over the time span
        '''
        fig = plt.figure()
        time = [mdates.date2num(d) for d in self.data['timestamp']]
        i = 1
        for key, val in self.data.items():
            axis = fig.add_subplot(len(self.data.keys()) - 1, 2, i)
            axis.plot_date(time, self.data[key])
            i += 1
        fig.autofmt_xdate()
        plt.suptitle('Plot %s from %s to %s' %
                     (self.plot_name,
                      self.data['timestamp'][0].
                      strftime('%m/%d/%Y %I:%M:%S %p'),
                      self.data['timestamp'][-1].
                      strftime('%m/%d/%Y %I:%M:%S %p')))
        if not filename:
            plt.show()
            plt.close()
        else:
            plt.savefig(filename)
            plt.close()
        return filename


    def export_summary_stats(self, filename=''):
        '''
        Default summary stats image.
        '''
        pass


    def frmt_time(self):
        '''
        Convert the timestamp to a valid datetime.  This should be called after
        the initial reading of the data (extract_obs_self.data) to handle timestamp
        discrepencies.  The default assumes YYYY-MM-DD HH:MM:SS.
        '''
        self.data['timestamp'] = [datetime.strptime(timestamp,
                                                    '%Y-%m-%d %H:%M:%S')
                                  for timestamp in self.data['timestamp']]


class RxCadreWindOutput(RxCadreOutput):
    '''
    Output stuff for wind based data.
    '''

    def __init__(self, plot, data):
        super(RxCadreWindOutput, self).__init__(plot=plot, data=data)
        self.plot_type = 'FBP'


    def export_kml_icon(self, rotation):
        '''
        Wind mean direction rotated arrow for an icon.
        '''
        kml =  '    <Style>\n' \
               '      <IconStyle>\n' \
               '        <Icon>\n' \
               '          <href>http://maps.google.com/mapfiles/kml' \
               '/shapes/arrow.png</href>\n' \
               '        </Icon>\n' \
               '        <heading>%s</heading>\n' % rotation
        kml += '      </IconStyle>\n' \
               '    </Style>\n'
        return kml

    def export_timeseries(self, filename=''):
        '''
        We handle the wind stuff slightly differently.
        '''
        fig = plt.figure()
        time = [mdates.date2num(d) for d in self.data['timestamp']]

        #fig = plt.figure(figsize=(8,8), dpi=80)
        ax1 = fig.add_subplot(211)
        ax1.plot_date(time, self.data['speed'], 'b-')
        #ax1.plot_date(time, self.data['gust'], 'g-')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Speed(mph)', color = 'b')
        ax2 = fig.add_subplot(212)
        ax2.plot_date(time, self.data['direction'], 'r.')
        ax2.set_ylabel('Direction', color='r')

        fig.autofmt_xdate()
        plt.suptitle('Plot %s from %s to %s' % (self.plot_name,
                     self.data['timestamp'][0].
                     strftime('%m/%d/%Y %I:%M:%S %p'),
                     self.data['timestamp'][-1].
                     strftime('%m/%d/%Y %I:%M:%S %p')))
        if not filename:
            plt.show()
            plt.close()
        else:
            plt.savefig(filename)
            plt.close()
        return filename


    def export_summary_stats(self, filename=''):
        '''
        Create a windrose from a self.dataset.
        '''
        #fig = plt.figure(figsize=(8, 8), dpi=80, facecolor='w', edgecolor='w')
        fig = plt.figure(facecolor='w', edgecolor='w')
        rect = [0.1, 0.1, 0.8, 0.8]
        axis = windrose.WindroseAxes(fig, rect, axisbg='w')
        fig.add_axes(axis)
        axis.bar(self.data['direction'], self.data['speed'], normed=True, 
                 opening=0.8, edgecolor='white')
        #l = axis.legend(axespad=-0.10)
        leg = axis.legend(1.0)
        plt.setp(leg.get_texts(), fontsize=8)
        if filename == '':
            plt.show()
            plt.close()
        else:
            plt.savefig(filename)
            plt.close()
        return filename


    def calc_stats(self):
        '''
        Calculate wind stats
        '''
        super(RxCadreWindOutput, self).calc_stats()
        samples = np.array(self.data['direction'])
        self.stat['direction']['min'] = np.min(samples)
        self.stat['direction']['max'] = np.max(samples)
        self.stat['direction']['mean'] = morestats.circmean(samples, 360, 0)
        self.stat['direction']['stddev'] = morestats.circstd(samples, 360, 0)


class RxCadreFBPOutput(RxCadreOutput):
    '''
    Format and create outputs for Fire Behavior Packages.
    '''

    def __init__(self, plot, data):

        super(RxCadreFBPOutput, self).__init__(plot=plot, data=data)
        self.plot_type = 'FBP'

    def export_timeseries(self, filename=''):
        '''
        Create a time series image for the plot over the time span
        '''
        fig = plt.figure()
        time = [mdates.date2num(d) for d in self.data['timestamp']]
        i = 1
        for key, val in self.data.items():
            axis = fig.add_subplot(len(self.data.keys()), 2, i)
            axis.plot_date(time, self.data[key])
            i += 1

        fig.autofmt_xdate()
        plt.suptitle('Plot %s from %s to %s' % (self.plot_name,
                     self.data['timestamp'][0].
                     strftime('%m/%d/%Y %I:%M:%S %p'),
                     self.data['timestamp'][-1].
                     strftime('%m/%d/%Y %I:%M:%S %p')))
        if not filename:
            plt.show()
            plt.close()
        else:
            plt.savefig(filename)
            plt.close()
        return filename

    def frmt_time(self):
        '''
        Handle the decimal seconds in the fbp self.data.
        '''
        self.data['timestamp'] = [datetime.strptime(timestamp,
                                                    '%Y-%m-%d %H:%M:%S.%f')
                             for timestamp in self.data['timestamp']]

def rxcadre_create_output(key, plot, data):
    '''
    Factory for plot type.
    '''
    if not key or (key.upper() != 'FPB' and key.upper() != 'WIND'):
        raise ValueError('Invalid key for output creator')
    if key == 'FBP':
        return RxCadreFBPOutput(plot, data)
    else:
        return RxCadreWindOutput(plot, data)

