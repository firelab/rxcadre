#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
#  $Id$
#  Project:  RX Cadre Data Visualization
#  Purpose:  Import csv data into tables
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

from rxcadre_except import RxCadreInvalidDbError

from rxcadre_db import RxCadreDb
from rxcadre_plot import RxCadrePlot

class RxCadre2(object):

    def __init__(self, db_file=None):
        '''
        Create the database object.
        '''

        self.db = RxCadreDb(db_file)

    def _point_kml(self, plot, stats, images=[]):
        '''
        Create a kml representation of a plot
        '''
        lon, lat = _extract_xy(self.get_plot_data(plot)[0][1])
        stats = self.calc_statistics(data)
        stats['direction'] = self.calc_circ_statistics(data)
        if stats is None:
            logging.warning('Could not calculate stats')
            return ''
        wind = True
        try:
            d = stats['direction'][2]
            if d < 0:
                d = d + 360.0
        except KeyError:
            wind = False
        stat_order = ('min', 'max', 'mean', 'stddev')

        kml =               '  <Placemark>\n'
        if wind:
            kml = kml +     '    <Style>\n' \
                            '      <IconStyle>\n' \
                            '        <Icon>\n' \
                            '          <href>http://maps.google.com/mapfiles/kml/shapes/arrow.png</href>\n' \
                            '        </Icon>\n' \
                            '        <heading>%s</heading>\n' % d
            kml = kml +     '      </IconStyle>\n' \
                            '    </Style>\n'
        kml = kml +         '    <Point>\n' \
                            '      <coordinates>%.9f,%.9f,0</coordinates>\n' \
                            '    </Point>\n' % (lon, lat)
        kml = kml +         '    <name>%s</name>\n' \
                            '    <description>\n' \
                            '      <![CDATA[\n' % plot
        for image in images:
            kml = kml +     '        <img src = "%s" />\n'  % image
        kml = kml +         '        <table border="1">' \
                            '          <tr>\n' \
                            '            <th>Stats</th>\n' \
                            '          </tr>\n'
        for key in stats.keys():
            for i, s in enumerate(stats[key]):
                kml = kml + '          <tr>\n' \
                            '            <td>%s</td>\n' \
                            '            <td>%.2f</td>\n' \
                            '          </tr>\n' % (stat_order[i], stats[key][i])
        kml = kml +         '        </table>\n' \
                            '      ]]>\n' \
                            '    </description>\n' \
                            '  </Placemark>\n'
        return kml


    def export_ogr(self, outfile, sum_only=True, frmt='ESRI Shapefile'):
        pass



