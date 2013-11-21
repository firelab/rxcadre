/*****************************************************************************
 * $Id$
 *
 * Name:     new_tables.sql
 * Project:  RX Cadre Data Visualization
 * Purpose:  Table schema declarations
 * Author:   Kyle Shannon <kyle@pobox.com>
 *
 * This is free and unencumbered software released into the public domain.
 *
 * Anyone is free to copy, modify, publish, use, compile, sell, or
 * distribute this software, either in source code form or as a compiled
 * binary, for any purpose, commercial or non-commercial, and by any
 * means.
 *
 * In jurisdictions that recognize copyright laws, the author or authors
 * of this software dedicate any and all copyright interest in the
 * software to the public domain. We make this dedication for the benefit
 * of the public at large and to the detriment of our heirs and
 * successors. We intend this dedication to be an overt act of
 * relinquishment in perpetuity of all present and future rights to this
 * software under copyright law.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
 * OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 * ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *
 * For more information, please refer to <http://unlicense.org/>
 *
 ****************************************************************************/

BEGIN;
INSERT INTO event VALUES('S6',datetime('2012-10-3119:11'),datetime('2012-10-31T20:00'));
INSERT INTO event VALUES('S5',datetime('2012-11-01T18:10'),datetime('2012-11-01T19:30'));
INSERT INTO event VALUES('S4',datetime('2012-11-01T19:35'),datetime('2012-11-01T21:15'));
INSERT INTO event VALUES('S3',datetime('2012-11-01T21:20'),datetime('2012-11-01T22:30'));
INSERT INTO event VALUES('L1G',datetime('2012-11-04T18:31'),datetime('2012-11-04T23:59'));
INSERT INTO event VALUES('S7',datetime('2012-11-07T17:25'),datetime('2012-11-07T18:50'));
INSERT INTO event VALUES('S8',datetime('2012-11-07T20:16'),datetime('2012-11-07T21:30'));
INSERT INTO event VALUES('S9',datetime('2012-11-07T18:54'),datetime('2012-11-07T20:10'));
INSERT INTO event VALUES('L2G',datetime('2012-11-10T18:23'),datetime('2012-11-10T23:59'));
INSERT INTO event VALUES('L2F',datetime('2012-11-11T18:02'),datetime('2012-11-11T23:59'));
COMMIT;

