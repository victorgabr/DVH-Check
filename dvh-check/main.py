from bokeh.io import curdoc
from view import ScoreCardView

test_file_set = {key: 'scorecard/test_files/%s.dcm' % key for key in ['plan', 'dose', 'structure']}

view = ScoreCardView()

curdoc().add_root(view.layout)
curdoc().title = 'University of Chicago Radiation Oncology - DICOM Score Card'
