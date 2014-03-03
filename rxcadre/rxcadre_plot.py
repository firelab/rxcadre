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

from rxcadre_except import RxCadreInvalidDataError

class RxCadrePlot(object):
    '''
    Represents a single point and associated data.
    '''
    def __init__(self, name='', plot_type='UNKNOWN', x=0, y=0):
        self.name = name
        self.plot_type = plot_type
        self.x = x
        self.y = y
        self.data = None
        self.stats = None

    @property
    def name(self):
        return self.name

    @property
    def wkt(self):
        if x and y:
            return 'POINT(%f %f)' % (x, y)
        return 'POINT EMPTY'

    @property
    def x(self):
        return x

    @property
    def y(self):
        return y

    def calc_stats(self):
        '''
        Calculate statistics on data associated with the plot
        '''

        if not self.data:
            raise RxCadreInvalidDataError('No data associate with plot: %s' \
                                          % self.name)

