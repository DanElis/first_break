from bokeh.events import DoubleTap
from bokeh.io import curdoc, show
from bokeh.layouts import column, row, widgetbox
from bokeh.models import Div, Select, LinearAxis, ColumnDataSource, Range1d, Slider, RangeSlider,LinearColorMapper
from bokeh.plotting import figure
import pickle
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from bokeh.transform import transform

class BreakData(object):
	def __init__(self, csv_path, pickle_path):
		df = pd.read_csv(csv_path, index_col=0)
		with open(pickle_path, 'rb') as f:
			data = pickle.load(f)

		self._image = data['data']
		print('\n\n\n')
		print(df.size)
		print('\n\n\n')
		df = df[:data['data'].shape[0]]
		
		self._shots = df['shot'].values
		self._traces = df['cdpTrace'].values
		self._breaks = df['FirstBreak'].values
		self._ixs = None
		self._offset = df['offset'].values
#		print(self._offset)

	def set_all_indices(self, field,value):
		if field == 'Shot':
			self._ixs = self._shots == self._shots
		elif field == 'Trace':
			self._ixs = self._traces == self._traces
		else:
			self._ixs = None

	def set_indices_offset(self, field, value_start, value_end):
		if field == 'Shot':
			#self._ixs = [print(shot <= value_end and shot >= value_start) for shot in self._shots]
			self._ixs = [shot <= value_end and shot >= value_start for shot in self._shots]
			#print('\n\n\n\n')
			#for i in range(self._shots.size) :
			#	if(self._ixs[i] == False):
			#		print('FALSE')
			#print('\n\n\n\n')
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

class OffsetData(object):
	def __init__(self, csv_path, pickle_path):
		df = pd.read_csv(csv_path, index_col=0)
		with open(pickle_path, 'rb') as f:
			data = pickle.load(f)
		df = df[:data['y'].shape[0]]
		
		self._sourceX = df['SourceX'].values
		self._sourceY = df['SourceY'].values
		self._groupX = df['GroupX'].values
		self._groupY = df['GroupY'].values
		self._shots = df['shot'].values
		self._traces = df['cdpTrace'].values
		self._breaks = df['FirstBreak'].values
		self._ixs = None
		self._offset = df['offset'].values


	def set_indices_offset(self, field, value_start, value_end):
		if field == 'Shot':
			self._ixs = [shot <= value_end and shot >= value_start for shot in self._shots]
		elif field == 'All':
			self._ixs = self._shots == self._shots
		else:
			self._ixs = None		


	def get_minmax(self, field):
		if field == 'Shot':
			return self._shots.min(), self._shots.max()
		else:
			return 0, 1

	def get_breaks(self):
		return self._breaks[self._ixs]
	def get_offset(self):
		return self._offset[self._ixs]
	def get_source(self):
		return self._sourceX,self._sourceY
	def get_group(self):
		return self._groupX,self._groupY
class ObservePage(object):
	def __init__(self):

		self._data = OffsetData(r'fb_on_Shots_4TEST_FB_v2.csv',
							   r'Shots_4TEST_FB_part.pickle')

		# self._div_debug = Div(text='Debug: <br>', width=1000)

		self._plot_image = figure(plot_width=800, plot_height=600,title='Observing system')
		self._groupX , self._groupY = self._data.get_group()
		self._sourceX , self._sourceY= self._data.get_source()
		print(self._sourceX)
		self._ds_source = ColumnDataSource(data = self._get_source())
		self._ds_group = ColumnDataSource(data = self._get_group())

		scatter =self._plot_image.scatter(x='x', y='y', source=self._ds_group, line_color='red', size=2)
		self._plot_image.scatter(x='x', y='y', source=self._ds_source, marker = 'triangle',line_color='blue', size=10)

	def _get_source(self):
		self._sourceX , self._sourceY = self._data.get_source()
		xs = self._sourceX
		ys = self._sourceY
	
		return {'x': xs, 'y': ys}

	def _get_group(self):
		self._groupX , self._groupY = self._data.get_group()
		xs = self._groupX
		ys = self._groupY
	
		return {'x': xs, 'y': ys}
	def _update_all(self, attr, old, new):
		self._ds_group.data = self._get_group()

		self._ds_source.data = self._get_source()

	def get_layout(self):
		plots = row(self._plot_image)

		# return [wbox, plots, self._div_debug]
		return [plots]

	
class OffsetPage(object):
	def __init__(self):
		sel_vals = ['All', 'Shot']

		self._data = OffsetData(r'fb_on_Shots_4TEST_FB_v2.csv',
							   r'Shots_4TEST_FB_part.pickle')
		self._offset = None

		# self._div_debug = Div(text='Debug: <br>', width=1000)
		self._sel_type = Select(title="Slice type:", value=sel_vals[0], options=sel_vals)
		self._sld_slice = RangeSlider(start=0, end=10, value=(0,100), step=1, title="Slice Num")
		self._set_slider()
		self._sld_slice.on_change('value', self._update_all)
		self._sel_type.on_change('value', self.change_type)

		self._plot_image = figure(plot_width=800, plot_height=600,title='Offset')
	  
		self._set_index()
		self._breaks = self._data.get_breaks()
		self._ds_offset = ColumnDataSource(data=self._get_offset())
		colormap = plt.cm.seismic
		create_colors = [colormap(i) for i in np.arange(0,self._data._shots.max()+1,1)]
		colors = [None]*self._data._breaks.size
		
		for i in range(self._data._breaks.size):
			colors[i]=matplotlib.colors.to_hex(create_colors[self._data._shots[i]])
		mapper = LinearColorMapper(palette=colors, low=self._data._shots.min(), high=self._data._shots.max())
		self._plot_image.scatter(x='x', y='y', source=self._ds_offset, line_color=None, fill_color=transform('shot', mapper), size=2)

	def _get_offset(self):
		self._offset = self._data.get_offset()
		xs = self._offset
		ys = self._breaks
	
		return {'x': xs, 'y': ys}
	def _set_index(self):
		self._data.set_indices_offset(self._sel_type.value, self._sld_slice.value[0], self._sld_slice.value[1])
	def _set_slider(self):
		min_val, max_val = self._data.get_minmax(self._sel_type.value)
		self._sld_slice.start = min_val
		self._sld_slice.end = max_val
		self._sld_slice.value = (0,min_val + (max_val - min_val) // 2)
	def change_type(self, attr, old, new):
		min_val, max_val = self._data.get_minmax(self._sel_type.value)
		self._sld_slice.value = (0,min_val + (max_val - min_val) // 2)
		self._sld_slice.start = min_val
		self._sld_slice.end = max_val
		_update_all
	def _update_all(self, attr, old, new):
		self._set_index()
		self._ds_offset.data = self._get_offset()

	def get_layout(self):
		wbox = widgetbox(self._sel_type, self._sld_slice)
		plots = row(self._plot_image)

		# return [wbox, plots, self._div_debug]
		return [column(wbox, plots)]



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
		self._sel_type.on_change('value', self.change_type)

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
	def change_type(self, attr, old, new):
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
obs_page = ObservePage()

layout = column(br_page.get_layout()+[row(off_page.get_layout()+ obs_page.get_layout())])
# layout = br_page.get_layout()

# show(column(layout[1]))
curdoc().add_root(layout)
#curdoc().title = "Seismic dashboard"
