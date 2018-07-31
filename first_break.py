from bokeh.events import DoubleTap
from bokeh.io import curdoc, show
from bokeh.layouts import column, row, widgetbox
from bokeh.models import Div, Select, LinearAxis, ColumnDataSource, Range1d, Slider, RangeSlider
from bokeh.plotting import figure
import pickle
import pandas as pd
import numpy as np


class BreakData(object):
	def __init__(self, csv_path, pickle_path):
		df = pd.read_csv(csv_path, index_col=0)
		with open(pickle_path, 'rb') as f:
			data = pickle.load(f)

		self._image = data['data']
		df = df[:self._image.shape[0]]
		self._shots = df['shot'].as_matrix()
		self._traces = df['cdpTrace'].as_matrix()
		self._breaks = df['FirstBreak'].as_matrix()
		self._ixs = None
		self._offset = df['offset'].as_matrix()

	def set_all_indices(self, field,value):
		if field == 'Shot':
			self._ixs = self._shots == self._shots
		elif field == 'Trace':
			self._ixs = self._traces == self._traces
		else:
			self._ixs = None

	def set_indices_offset(self, field, value_start, value_end):
		if field == 'Shot':
			self._ixs = [shot <= value_end and shot >= value_start for shot in self._shots]
		elif field == 'All':
			self._ixs = self._shots == self._shots
		else:
			self._ixs = None		
	def set_indices(self, field, value):
		if field == 'Shot':
			self._ixs = self._shots == value
		elif field == 'Trace':
			self._ixs = self._traces == value
		else:
			self._ixs = None

	def get_minmax(self, field):
		if field == 'Shot':
			return self._shots.min(), self._shots.max()
		elif field == 'Trace':
			return self._traces.min(), self._traces.max()
		elif field == 'All':
			return self._shots.min(), self._shots.max()
		else:
			return 0, 1

	def get_image(self):
		return self._image[self._ixs].T

	def get_breaks(self):
		return self._breaks[self._ixs]
	def get_offset(self):
		return self._offset[self._ixs]
class OffsetPage(object):
	def __init__(self):
		sel_vals = ['All', 'Shot']

		self._data = BreakData(r'fb_on_Shots_4TEST_FB_v2.csv',
							   r'Shots_4TEST_FB_part.pickle')
		self._image = None
		self._offset = None
		self._cur_pos = 10

		# self._div_debug = Div(text='Debug: <br>', width=1000)
		self._sel_type = Select(title="Slice type:", value=sel_vals[0], options=sel_vals)
		self._sld_slice = RangeSlider(start=0, end=10, value=(0,100), step=1, title="Slice Num")
		self._set_slider()
		self._sld_slice.on_change('value', self._update_all)
		self._sel_type.on_change('value', self._update_all)

		self._plot_image = figure(plot_width=800, plot_height=600, x_range=Range1d(0, 100), y_range=Range1d(0, 100),
								  title='Offset', tools="pan,wheel_zoom,reset")
		self._plot_slice = figure(plot_width=300, plot_height=600, x_range=Range1d(-.8, .8), y_range=Range1d(0, 100),
								  title='Slice')
	  
		self._set_index()
		self._ds_image = ColumnDataSource(data=self._get_image())
		self._ds_offset = ColumnDataSource(data=self._get_offset())
		self._ds_slice = ColumnDataSource(data=self._get_slice())
		self._ds_brslice = ColumnDataSource(data=self._get_brslice())
		self._ds_sliceline = ColumnDataSource(data=self._get_sliceline())

		#self._plot_image.image(image='image', source=self._ds_image, x=0, y=0, dw=100, dh=100, palette="RdGy11")
		# self._plot_image.image(image='image', source=self._ds_image, x=0, y=0, dw=100, dh=100, palette="Oranges9")
		self._plot_image.circle(x='x', y='y', source=self._ds_offset, color='red', size=5)
		self._plot_image.circle(x='x', y='y', source=self._ds_sliceline, color='blue')

		self._plot_slice.line(x='x', y='y', source=self._ds_slice, color='blue')
		self._plot_slice.line(x='x', y='y', source=self._ds_brslice, color='red', line_width=2)

	def _get_image(self):
		self._image = self._data.get_image()
		return {'image': [np.clip(self._image, -.5, .5)]}

	def _get_offset(self):
		#p.xaxis.axis_label = 'offset'
        #p.yaxis.axis_label = 'FirstBreak'
		self._offset = self._data.get_offset()
		xs = (np.arange(self._offset.size) + .5) * 100 / self._image.shape[1]
		ys = self._offset * 100 / self._image.shape[0]
		return {'x': xs, 'y': ys}

	def _get_slice(self):
		ys = np.arange(self._image.shape[0]) * 100 / self._image.shape[0]
		return {'x': self._image[:, self._cur_pos], 'y': ys}

	def _get_brslice(self):
		y = (self._offset[self._cur_pos]) * 100 / self._image.shape[0]

		return {'x': [-.5, .5], 'y': [y, y]}

	def _get_sliceline(self):
		x = (self._cur_pos + .5) * 100 / self._image.shape[1]
		# self._div_debug.text += "{} <br>".format(x)
		return {'x': [x, x], 'y': [0, 100]}

	def _set_index(self):
		self._data.set_indices_offset(self._sel_type.value, self._sld_slice.start, self._sld_slice.end)
		#self._data.set_indices(self._sel_type.value, self._sld_slice.start)
	def _set_slider(self):
		min_val, max_val = self._data.get_minmax(self._sel_type.value)
		self._sld_slice.start = min_val
		self._sld_slice.end = max_val
		self._sld_slice.value = (0,min_val + (max_val - min_val) // 2)

	def _update_all(self, attr, old, new):
		self._set_index()
		self._ds_offset.data = self._get_offset()
		self._ds_sliceline.data = self._get_sliceline()
		if self._cur_pos >= self._image.shape[1]:
			self._cur_pos = 0
		self._ds_slice.data = self._get_slice()
		self._ds_brslice.data = self._get_brslice()

	def get_layout(self):
		wbox = widgetbox(self._sel_type, self._sld_slice)
		plots = row(self._plot_image)

		# return [wbox, plots, self._div_debug]
		return [wbox, plots]



class BreakPage(object):
	def __init__(self):
		sel_vals = ['Trace', 'Shot']

		self._data = BreakData(r'fb_on_Shots_4TEST_FB_v2.csv',
							   r'Shots_4TEST_FB_part.pickle')
		self._image = None
		self._breaks = None
		self._cur_pos = 10
		#self._div_debug = Div(text='Debug: <br>', width=1000)
		self._sel_type = Select(title="Slice type:", value=sel_vals[0], options=sel_vals)
		self._sld_slice = Slider(start=0, end=10, value=1, step=1, title="Slice Num")
		self._set_slider()
		self._sld_slice.on_change('value', self._update_all)
		self._sel_type.on_change('value', self.change_minmax)

		self._plot_image = figure(plot_width=800, plot_height=600, x_range=Range1d(0, 100), y_range=Range1d(0, 100),
								  title='Breaks', tools="pan,wheel_zoom,reset")
		self._plot_slice = figure(plot_width=300, plot_height=600, x_range=Range1d(-.8, .8), y_range=Range1d(0, 100),
								  title='Slice')
		self._plot_image.on_event(DoubleTap, self._select_point)

		self._set_index()
		self._ds_image = ColumnDataSource(data=self._get_image())
		self._ds_breaks = ColumnDataSource(data=self._get_breaks())
		self._ds_slice = ColumnDataSource(data=self._get_slice())
		self._ds_brslice = ColumnDataSource(data=self._get_brslice())
		self._ds_sliceline = ColumnDataSource(data=self._get_sliceline())

		self._plot_image.image(image='image', source=self._ds_image, x=0, y=0, dw=100, dh=100, palette="RdGy11")
		# self._plot_image.image(image='image', source=self._ds_image, x=0, y=0, dw=100, dh=100, palette="Oranges9")
		self._plot_image.line(x='x', y='y', source=self._ds_breaks, color='red', line_width=2)
		self._plot_image.line(x='x', y='y', source=self._ds_sliceline, color='blue')

		self._plot_slice.line(x='x', y='y', source=self._ds_slice, color='blue')
		self._plot_slice.line(x='x', y='y', source=self._ds_brslice, color='red', line_width=2)

	def _get_image(self):
		self._image = self._data.get_image()
		return {'image': [np.clip(self._image, -.5, .5)]}

	def _get_breaks(self):
		self._breaks = self._data.get_breaks()
		xs = (np.arange(self._breaks.size) + .5) * 100 / self._image.shape[1]
		ys = self._breaks * 100 / self._image.shape[0]
		return {'x': xs, 'y': ys}

	def _get_slice(self):
		ys = np.arange(self._image.shape[0]) * 100 / self._image.shape[0]
		return {'x': self._image[:, self._cur_pos], 'y': ys}

	def _get_brslice(self):
		y = (self._breaks[self._cur_pos]) * 100 / self._image.shape[0]
		return {'x': [-.5, .5], 'y': [y, y]}

	def _get_sliceline(self):
		x = (self._cur_pos + .5) * 100 / self._image.shape[1]
		#self._div_debug.text +=str(self._data._ixs)#"{} <br>".format(new)
		return {'x': [x, x], 'y': [0, 100]}

	def _set_index(self):
		self._data.set_indices(self._sel_type.value, self._sld_slice.value)

	def _set_slider(self):
		min_val, max_val = self._data.get_minmax(self._sel_type.value)
		self._sld_slice.start = min_val
		self._sld_slice.end = max_val
		self._sld_slice.value = min_val + (max_val - min_val) // 2
	def change_minmax(self, attr, old, new):
		min_val, max_val = self._data.get_minmax(self._sel_type.value)
		self._sld_slice.start = min_val
		self._sld_slice.end = max_val
		_update_all
	def _update_all(self, attr, old, new):
		self._set_index()
		self._ds_image.data = self._get_image()
		self._ds_breaks.data = self._get_breaks()

		if self._cur_pos >= self._image.shape[1]:
			self._cur_pos = 0
		self._ds_sliceline.data = self._get_sliceline()
		self._ds_slice.data = self._get_slice()
		self._ds_brslice.data = self._get_brslice()

	def _select_point(self, event):
		#self._div_debug.text += +str(self._data._ixs)#"{} <br>".format(new)
		self._cur_pos = int(event.x * self._image.shape[1] / 100)
		self._ds_slice.data = self._get_slice()
		self._ds_brslice.data = self._get_brslice()
		self._ds_sliceline.data = self._get_sliceline()

	def get_layout(self):
		wbox = widgetbox(self._sel_type, self._sld_slice)
		plots = row(self._plot_image, self._plot_slice)
		#self._div_debug.text  += "{} <br>".format(new)
		#return [wbox, plots, self._div_debug]
		return [wbox, plots]

off_page = OffsetPage()
br_page = BreakPage()
layout = column(br_page.get_layout()+off_page.get_layout())
# layout = br_page.get_layout()

# show(column(layout[1]))
curdoc().add_root(layout)
#curdoc().title = "Seismic dashboard"
