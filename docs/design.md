<!--

 * Name:     table_design.md
 * Project:  RX Cadre Data Visualization
 * Purpose:  Table descriptions
 * Author:   Kyle Shannon <kyle@pobox.com>

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>

-->

## Purpose

The RX Cadre (Prescribed Fire Combustion and Atmospheric Dynamic Research) program conducted several field experiments in the fall of 2012.  Several datasets were used to quantify fire weather and behavior.  These data include fire behavior observations (air flow, heat flux, air temperature) and weather data (mostly local wind speed and direction).  In order to make research and publishing easier, these data need to be filtered by time and space.  This python module will act as that filter and allow a variety of data extraction means and storage.

## Architecture

### Source Code

The source will be written in Python 2.x.  Python was chosen due to fast implementation time, rich built in modules (csv, argparse), access to third party modules for graphing (matplotlib), geospatial functionality (GDAL/OGR bindings), a built in, distributed graphical user interface (Tk), and tight integration with a serverless relational database management system (SQLite).

### Data Store

A local SQLite3 database will serve as an intermediary data store.  Data officially live on a large database that has stored comma separated value files and excel files.  These have to be parsed in order to load them into the data store.  Quick access to data subsetting by time and space are needed.

### Documentation

User and developer documentation will be stored at this github repository in the [doc/](https://github.com/ksshannon/rxcadre/tree/master/doc) directory.  Other documentation may be stored in the wiki.

## Future location

This repository will be migrated to the firelab organization as adoption approaches.

## License

This work is part done as part of US Government employees and contractors as part of official duties and therefore is in the public domain.  See LICENSE.
