from bokeh.io import curdoc
from view import ScoreCardView


view = ScoreCardView()

curdoc().add_root(view.layout)
curdoc().title = 'University of Chicago Radiation Oncology - DICOM Score Card'
