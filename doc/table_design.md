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

## Summary

This document describes the simple schema for the RX Cadre table schema.  The
project is designed to visualize anemometer (cup and vane) data as well as fire
behavior package (FBP) data.  There are several tables and associated
meta-tables that have to be updated and populated to use the visualization.

## Tables

### Plot Location (plot\_location)

Plot location describes the names of the plot _location_ for each point.  All
plots are described as points.  Geometry is stored as OGC well-known text
geometry (POINT( x y )).  Plot type may be used to extract other data from
tables.

| project\_name | plot\_id | x         | y         | wkt\_geometry              | plot\_type |
| ------------- | -------- | --------- | ----------| -------------------------- | ---------- |
| 'RX Cadre'    | KYLE\_1  | -113.99   | 47.01     | POINT(-113.99 47.01)       | CUP\_VANE  |
| 'RX Cadre'    | KYLE\_2  | -114.0043 | 45.044856 | POINT(-114.0043 45.044856) | FBP        |

PRIMARY\_KEY(plot\_id)

### Observation tables (obs\_tables)

This table describes which values from which observation tables can be
displayed.  All observation tables should be registered in this table.  The
_obs\_table\_name_ must be a name in the database.  _obs\_cols_ are the column
names that hold observation data, comma separated.  _obs\_col\_names_ are
human-readable strings for each column, comma separated.

| obs\_table\_name | obs\_disp\_name | time\_column | geometry\_column | obs\_cols                 | obs\_col\_names                  |
| ---------------- | --------------- | ------------ | ---------------- | ------------------------- | -------------------------------- |
| cup\_vane\_obs   | 'Wind Data'     | 'timestamp'  | 'wkt_geometry'   | 'dir,speed,gust'          | 'Direction,Speed(mph),Gust(mph)' |
| fbp\_obs         | 'Fire Behavior' | 'timestamp'  | 'wkt_geometry'   | 'tmp,ksh,ksv,mtr,mtt,nar' | 'Temperature(C),Horizontal Wind Speed(m/s),Vertical Wind Speed(m/s),Medtherm Radiant Flux(kw/m^2),Medtherm Total Heat Flux(kw/m^2),Narrow Angle Radiometer(kw/m^2)' |

PRIMARY\_KEY(obs\_table\_name)

### Event table

The event table holds pre-determined events for a given project.  The table
specifies the start and end time for some event for subsetting temporally.

| project\_name | event\_name | event\_start    | event\_end      |
| ------------- | ----------- | --------------- | --------------- |
| 'RX Cadre'    | 'S1'        | '20120912T1243' | '20120912T1534' |
| 'RX Cadre'    | 'S4'        | '20120914T1822' | '20120914T1930' |


PRIMARY\_KEY(project\_name, event\_name)

#### _Notes_\:

This table is not necessary, it only allows for pre-determined events.  Queries
can be made by using start/end times.

### Various observation tables

These tables hold actual observations.  The schema is not standard, but in
order to be used, it must be registered with the obs\_tables table.  The
following are examples.

#### Table cup\_vane\_obs

| plot\_id | timestamp                  | dir | speed | gust |
| -------- | -------------------------- | --- | ----- | ---- |
| A10      | 'Sep 12, 2012 08:34:32 PM' | 182 | 19    | 33   |
| A10      | 'Sep 12, 2012 08:34:35 PM' | 166 | 12    | 15   |

PRIMARY\_KEY(plot\_id, timestamp)
