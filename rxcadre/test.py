
import os
import zipfile

from rxcadre_db import RxCadreDb
from rxcadre_output import RxCadreOutput, rxcadre_create_output

db = RxCadreDb('../data/test.db')
plot = db.get_plot_data('S8-A66')[0]
data = db.extract_obs_data('cup_vane_obs', plot[0])
op = rxcadre_create_output('WIND', plot, data)


def rxcadre_export_kmz(plots, start, stop, filename):
    '''
    Convenience for exporting data.  Iterate over the plots and export all
    necessary data.
    '''
    fout = open('doc.kml', 'w')
    fout.write('<Document>\n')
    kmz = zipfile.ZipFile( filename, 'w', 0, True)

    for plot_name in plots:
        plot = db.get_plot_data(plot_name)[0]
        data = db.extract_obs_data('cup_vane_obs', plot[0])
        output = rxcadre_create_output(plot[-1], plot, data)
        rosefile = output.export_summary_stats(plot_name + '_rose.png')
        timefile = output.export_timeseries(plot_name + '_time.png')
        images = [img for img in [rosefile, timefile] if img]
        fout.write(output.export_kml(images))
        for image in images:
            kmz.write(image)
            os.unlink(image)

    fout.write('</Document>\n')
    fout.close()
    kmz.write('doc.kml')
    os.unlink('doc.kml')


def rxcadre_export_csv(plots, start, stop, filename):
    '''
    Export csv data for many plots.  Note that if the plots have two different
    types, then two separate files will be written.
    '''
    pass

rxcadre_export_kmz(['S8-A95', 'S8-A104'], None, None, 'test.kmz')
