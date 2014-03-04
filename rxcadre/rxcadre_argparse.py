#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
#  $Id$
#  Project:  RX Cadre Data Visualization
#  Purpose:  RX Cadre argument parser
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

import argparse

'''
Command line interface for extracting data.  Users should be able to use
the cli for extracting one or more plots for a given time period or event.
Users should also be able to extract meta information from a db.  Editing
is also allowed.  The functions are accessed via the subcommands:
rxcadre create
rxcadre import
rxcadre export
rxcadre info
rxcadre edit
'''

'''
Main parser.  All commands take a database to act on, so that is the last
argument for everything.
'''
parser = argparse.ArgumentParser(prog='rxcadre')
subparsers = parser.add_subparsers(help='sub-command help', dest='sub_cmd')

'''
Create a new database parser.  Only needs the database name.
'''
parser_create = subparsers.add_parser('create', help='Create an empty db')

'''
Import csv parser with options for naming the table and columns.
parser_import = subparsers.add_parser('import', help='Import csv data')
parser_import.add_argument('input_file', type=str,
                           help='csv file to import')
parser_import.add_argument('--columns', dest='columns', type=str,
                           nargs='*', default=[],
                           help='Columns to import, default is all')
parser_import.add_argument('--column_names', dest='column_names',
                           type=str, nargs='*', default=[],
                           help='Display column names')
'''
'''
Export parser.
'''
parser_extract = subparsers.add_parser('export', help='Extract plot data')
parser_extract.add_argument('--plots', dest='plots', type=str,
                            nargs='*', default=[],
                            help='Plot names to extract')
parser_extract.add_argument('--plot-type', dest='plot_type', type=str,
                            default='', help='WIND or FBP')
parser_extract.add_argument('--start', dest='start', type=str,
                            default=None, help='Start time for subset')
parser_extract.add_argument('--end', dest='end', type=str,
                            default=None, help='End time for subset')
parser_extract.add_argument('--event', dest='event', type=str,
                            default='', help='Use start/end from an event')
parser_extract.add_argument('--kmz', dest='kmz', action='store_true',
                            help='Create a kmz file')
parser_extract.add_argument('--csv', dest='csv', action='store_true',
                            default='', help='Create a csv file')
parser_extract.add_argument('--rose', dest='rose', action='store_true',
                            help='Create a windrose file')
parser_extract.add_argument('--timeseries', dest='timeseries',
                            action='store_true',
                            help='Create a timeseries file')
parser_extract.add_argument('--ogr', dest='ogr_frmt', type=str,
                            default='ESRI Shapefile',
                            help='Create an ogr dataset using this driver')
parser_extract.add_argument('--show-only', dest='show_only',
                            action='store_true',
                            help='Show the images, don\'t write a file')
parser_extract.add_argument('--path', type=str, default='.',
                            help='Output file path')
#parser_extract.add_argument('--zip', dest='zip', action='store_true',
#                            help='Create a zip file for all output')

'''
Information parser.
'''
parser_info = subparsers.add_parser('info', help='Show db information')
parser_info.add_argument('--tables', dest='show_obs_tables',
                         action='store_true',
                         help='Show observation tables in a database')
parser_info.add_argument('--events', dest='show_events',
                         action='store_true',
                         help='Show events tables in a database')
parser_info.add_argument('--plots', dest='show_plots',
                         action='store_true',
                         help='Show plot information in a database')

'''
Edit parser.
parser_edit = subparsers.add_parser('edit', help='Update db information')
'''

parser.add_argument('-q', '--quiet', action='store_true', dest='quiet',
                    help='Do not output to stdout')
parser.add_argument('-l', '--logging', type=str, dest='level',
                    default='critical',
                    help='Logging level(DEBUG,INFO,WARNING,ERROR,CRITICAL')
parser.add_argument('database', type=str, help='Database to act on')

args = parser.parse_args()

