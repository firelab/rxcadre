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

This document describes the desired output products to be extracted from the
raw data.  Note that in most cases, subsetting by event is just using
pre-defined times to subset the data temporally.

### CSV files

Subset types
* Spatial
* Temporal
* Event
* Combinations of above

Outputs
* csv file

### Google Earth kml/kmz

Subset types
* Spatial
* Temporal
* Event
* Combinations of above

Outputs
* kmz file
* Time series plots
* Wind roses

### Various Geospatial formats

See [OGR Supported Formats](http://gdal.org/ogr/ogr_formats.html) for output 
options.  Note that not all outputs are available depending on
platform/availability.  The kml/kmz files are generated outside of OGR, not
within and don't require OGR.

Subset types:
* Spatial
* Temporal (averaged)
* Event
* Combinations of above

Outputs
* Various spatial files
* Point features with temporal averaged data)

Possibility unknown:
* Time series plots
* Wind roses
* Temporal data (essentially a table with a record for each timestamp for a
given plot)

