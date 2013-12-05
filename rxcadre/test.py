
import os
import sys
import zipfile

from rxcadre_db import RxCadreDb
from rxcadre_output import RxCadreOutput, rxcadre_create_output

def progress(done, msg=''):
    if done == 1.0:
        sys.stdout.write('\r100% Done.\n')
    else:
        if msg and msg[-1] != ' ':
            msg += ' '
        sys.stdout.write('\r%s%2d%% Done' % (msg, 100 * done))
    sys.stdout.flush()

db = RxCadreDb('../data/test.db')
plot = db.get_plot_data('S8-A66')[0]
data = db.extract_obs_data('cup_vane_obs', plot[0])
op = rxcadre_create_output('WIND', plot, data)

table_dict = {'WIND':'cup_vane_obs',
              'FBP':'fbp_obs'}

def rxcadre_export_kmz(plots, start, stop, filename, prog_func=None):
    '''
    Convenience for exporting data.  Iterate over the plots and export all
    necessary data.
    '''
    fout = open('doc.kml', 'w')
    fout.write('<Document>\n')
    kmz = zipfile.ZipFile( filename, 'w', 0, True)

    if prog_func:
        prog_func(0.0)

    for i, plot_name in enumerate(plots):
        plot = db.get_plot_data(plot_name)[0]
        data = db.extract_obs_data(table_dict[plot[-1]], plot_name, start, stop)
        output = rxcadre_create_output(plot[-1], plot, data)
        rosefile = output.export_summary_stats(plot_name + '_rose.png')
        timefile = output.export_timeseries(plot_name + '_time.png')
        images = [img for img in [rosefile, timefile] if img]
        fout.write(output.export_kml(images))
        for image in images:
            kmz.write(image)
            os.unlink(image)

        if prog_func:
            prog_func(float(i) / len(plots), 'Building KMZ...')

    fout.write('</Document>\n')
    fout.close()
    kmz.write('doc.kml')
    os.unlink('doc.kml')

    if prog_func:
        prog_func(1.0)


def rxcadre_export_csv(plots, start, stop, outpath, aggregate=True,
                       prog_func=None):
    '''
    Export csv data for many plots.  All plots will have a seperate file.  This
    uses the 'short circuit' in export_plot_data by sending it a output
    filename as a csv.
    '''

    if prog_func:
        prog_func(0.0)

    filename = 'output.csv'
    for i, plot_name in enumerate(plots):
        filename = os.path.join(outpath, plot_name + '.csv')
        plot = db.get_plot_data(plot_name)[0]
        data = db.extract_obs_data(table_dict[plot[-1]], plot_name, start, stop,
                                   filename)
        if prog_func:
            prog_func(float(i) / len(plots), 'Extracting CSV...')
    if prog_func:
        prog_func(1.0)


#rxcadre_export_kmz(['S8-A95', 'S8-A104']*5, None, None, 'test.kmz', progress)
rxcadre_export_csv(['S8-A95', 'S8-A104']*5, None, None, '.', True, progress)
