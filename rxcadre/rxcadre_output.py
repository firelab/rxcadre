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
Output creator for different plot types
'''

from collections import OrderedDict as dict
import os
import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

import numpy as np
import scipy.stats as stats


sys.path.append(os.path.abspath('windrose'))
import windrose


class RxCadreOutput:
    '''
    Interface for outputs, with default exporters.
    '''

    def __init__(self):
        '''
        Don't do anything.
        '''
        #FIXME: add data/stats cache?
        self.plot_type = ''

    def export_csv_header(self, data):
        '''
        Default header string.
        '''
        header = ','.join(['"' + col + '"' for col in data.keys()])
        header += '\n'
        return header


    def export_csv(self, plot, data):
        '''
        Export data as csv.
        '''
        csv = ''
        for i, times in enumerate(data['timestamp']):
            csv += plot + ',' + times + ','
            csv += ','.join([str(data[k][i]) for k in data.keys() \
                             if k != 'timestamp'])
            csv += '\n'
        return csv


    def export_ogr(self, plot, data):
        '''
        Write a ogr features for the point
        '''
        pass


    def calc_stats(self, data):
        '''
        Calculate normal statistics
        '''
        stat = dict()
        for key, val in data.items():
            stat[key] = dict()
            if key == 'timestamp':
                continue
            samples = np.array(val)
            stat[key]['min'] = np.min(samples)
            stat[key]['max'] = np.max(samples)
            stat[key]['mean'] = np.mean(samples)
            stat[key]['stddev'] = np.std(samples)
        return stat


    def export_kml(self, plot, data, images):
        '''
        Export the kml for a single plot.
        '''
        stat = self.calc_stats(data)
        try:
            rot = stat['direction']['mean']
        except:
            rot = 0.0
        kml =               '  <Placemark>\n'
        kml += self.export_kml_icon(rot)
        kml +=              '    <Point>\n' \
                            '      <coordinates>%.9f,%.9f,0</coordinates>\n' \
                            '    </Point>\n'# % (lon, lat)
        kml = kml +         '    <name>%s</name>\n' \
                            '    <description>\n' \
                            '      <![CDATA[\n' % plot
        for image in images:
            kml = kml +     '        <img src = "%s" />\n'  % image
        kml = kml +         '        <table border="1">' \
                            '          <tr>\n' \
                            '            <th>Stats</th>\n' \
                            '          </tr>\n'
        for key in stat.keys():
            for i, sta in enumerate(stat[key]):
                kml = kml + '          <tr>\n' \
                            '            <td>%s</td>\n' \
                            '            <td>%.2f</td>\n' \
                            '          </tr>\n' % (key, stat[key][i])
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


    def export_timeseries(self, plot, data, filename=''):
        '''
        Create a time series image for the plot over the time span
        '''
        fig = plt.figure()
        time = [mdates.date2num(d) for d in data['timestamp']]
        i = 1
        for key, val in data.items():
            axis = fig.add_subplot(len(data.keys()) - 1, 2, i)
            axis.plot_date(time, data[key])
            i += 1
        fig.autofmt_xdate()
        plt.suptitle('Plot %s from %s to %s' % (plot,
                     data['timestamp'][0].strftime('%m/%d/%Y %I:%M:%S %p'),
                     data['timestamp'][-1].strftime('%m/%d/%Y %I:%M:%S %p')))
        if not filename:
            plt.show()
            plt.close()
        else:
            plt.savefig(filename)
            plt.close()
        return filename


    def export_summary_stats(self, plot, data, filename=''):
        '''
        Default summary stats image.
        '''
        pass


class RxCadreWindOutput(RxCadreOutput):
    '''
    Output stuff for wind based data.
    '''

    def __init__(self):

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


    def export_summary_stats(self, plot, data, filename=''):
        '''
        Create a windrose from a dataset.
        '''
        #fig = plt.figure(figsize=(8, 8), dpi=80, facecolor='w', edgecolor='w')
        fig = plt.figure(facecolor='w', edgecolor='w')
        rect = [0.1, 0.1, 0.8, 0.8]
        axis = windrose.WindroseAxes(fig, rect, axisbg='w')
        fig.add_axes(axis)
        axis.bar(data['direction'], data['speed'], normed=True, opening=0.8,
               edgecolor='white')
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


    def calc_stats(self, data):
        '''
        Calculate wind stats
        '''
        stat = dict()
        stat = super.calc_stats(data)
        samples = np.array(data['direction'])
        stat['direction']['min'] = np.min(samples)
        stat['direction']['max'] = np.max(samples)
        stat['direction']['mean'] = stats.morestats.circmean(samples, 360, 0)
        stat['direction']['stddev'] = stats.morestats.circstd(samples, 360, 0)
        return stat


class RxCadreFBPOutput(RxCadreOutput):
    '''
    Format and create outputs for Fire Behavior Packages.
    '''

    def __init__(self):

        self.plot_type = 'FBP'

    def export_timeseries(self, plot, data, filename=''):
        '''
        Create a time series image for the plot over the time span
        '''
        fig = plt.figure()
        time = [mdates.date2num(d) for d in data['timestamp']]
        i = 1
        for key, val in data.items():
            axis = fig.add_subplot(len(data.keys()), 2, i)
            axis.plot_date(time, data[key])
            i += 1

        fig.autofmt_xdate()
        plt.suptitle('Plot %s from %s to %s' % (plot,
                     data['timestamp'][0].strftime('%m/%d/%Y %I:%M:%S %p'),
                     data['timestamp'][-1].strftime('%m/%d/%Y %I:%M:%S %p')))
        if not filename:
            plt.show()
            plt.close()
        else:
            plt.savefig(filename)
            plt.close()
        return filename


def rx_cadre_create_output(key):
    '''
    Factory for plot type.
    '''
    if not key or key.uppercase() != 'FPB' or key.uppercase() != 'WIND':
        raise ValueError('Invalid key for output creator')
    if key == 'FBP':
        return RxCadreFBPOutput()
    else:
        return RxCadreWindOutput()

