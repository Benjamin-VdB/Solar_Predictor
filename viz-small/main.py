## Bokeh Visualisation of distributed Solar production in 2018
## Ben Vandenbroucke
## Dec 2019

## small version for binder

# import Libs
import bokeh
from bokeh.plotting import figure, save, output_file, show
from bokeh.tile_providers import get_provider, Vendors
from bokeh.transform import linear_cmap, log_cmap
from bokeh.models import ColumnDataSource, HoverTool, ColorBar, Div, RangeTool
from bokeh.layouts import layout, column
from bokeh.models.widgets import Button, RadioButtonGroup, Select, Slider,DataTable, TableColumn, RangeSlider
from bokeh.io import curdoc

import pandas as pd
import numpy as np

from pyproj import Proj, transform


# load datasets
preds = pd.read_csv('./data/solar_preds_viz.csv')[['Name','Date','lat','lon', 'Obs_pop(MW_m2_pop)', 'Pred_pop(MW_m2_pop)']].rename(columns = {'Obs_pop(MW_m2_pop)':'Obs', 'Pred_pop(MW_m2_pop)':'Pred'})

# cumulative init
cums = preds.groupby(['Date']).sum().cumsum().reset_index().rename(columns = {'Obs':'Cum_obs', 'Pred':'Cum_pred'})

# map_data
map_data = preds.groupby(['Name','lat','lon']).sum()['Obs'].reset_index()

# convert WGS84 to Web Mercator coords
merc_coord = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'),  list(map_data.lon), list(map_data.lat))
map_data['x'] = merc_coord[0]
map_data['y'] = merc_coord[1]


# Map
source_map = ColumnDataSource(data=dict(name= map_data['Name'], x=map_data['x'], y=map_data['y'], obs=map_data['Obs'] ) )

# creates the map and add the openstreet map layer
map = figure(title="NZ Solar Generation Predictor - Transpower demo", x_range=(18350000, 20000000), y_range=(-6000000, -4000000), x_axis_type="mercator", y_axis_type="mercator", plot_width=700, plot_height=900, toolbar_location="below")
tile_provider = get_provider(Vendors.CARTODBPOSITRON)
map.add_tile(tile_provider)
map.title.text = "Distributed Solar Generation Predictor"
map.title.align = "left"
map.title.text_color = "black"
map.title.text_font_size = "20px"
map.axis.visible = None 
map.xgrid.visible = False
map.ygrid.visible = False
# add the Hover tool
my_hover = HoverTool()
my_hover.tooltips = [('City', '@name'), ('Yearly Production GWh', '@obs') ]
map.add_tools(my_hover)
mapper_power = linear_cmap('obs', 'RdBu6' , 0, 500) 
map.circle(source=source_map,x='x', y='y', size=15, line_color=mapper_power, fill_color= mapper_power )


# instant solar graph

dates = np.array(preds['Date'], dtype=np.datetime64)
source_pi = ColumnDataSource(data=dict(date=dates, obs=preds['Obs'], pred=preds['Pred']))

pi = figure(plot_height=250, plot_width=900, tools="xpan", toolbar_location=None,
		   x_axis_type="datetime", x_axis_location="above",
		   background_fill_color="#efefef", x_range=(dates[0], dates[round(len(dates)/500)]) )

pi.line('date', 'obs', source=source_pi, color='steelblue')
pi.line('date', 'pred', source=source_pi, color='crimson')
pi.yaxis.axis_label = 'GW'

pi_select = figure(title='Instant Solar Power Production (GW)',
				plot_height=250, plot_width=900, y_range=pi.y_range,
				x_axis_type="datetime", y_axis_type=None,
				tools="", toolbar_location=None, background_fill_color="#efefef")

pi_range_tool = RangeTool(x_range=pi.x_range)
pi_range_tool.overlay.fill_color = "navy"
pi_range_tool.overlay.fill_alpha = 0.2

pi_select.line('date', 'obs', source=source_pi, color='steelblue', legend="Measured")
pi_select.line('date', 'pred', source=source_pi, color='crimson', legend="Predicted")
pi_select.ygrid.grid_line_color = None
pi_select.add_tools(pi_range_tool)
pi_select.toolbar.active_multi = pi_range_tool
pi_select.legend.location = "top_center"



# cumulative graph

dates = np.array(cums['Date'], dtype=np.datetime64)
source_pc = ColumnDataSource(data=dict(date=dates, cum_obs=cums['Cum_obs'], cum_pred=cums['Cum_pred']))

pc = figure(title='Cumulative Solar Power Production (GWh)',
			plot_height=250, plot_width=900, toolbar_location=None,
		   x_axis_type="datetime", x_axis_location="below",
		   background_fill_color="#efefef" )

pc.line('date', 'cum_obs', source=source_pc, color='steelblue', line_width=3)
pc.line('date', 'cum_pred', source=source_pc, color='crimson', line_width=3)
pc.yaxis.axis_label = 'GWh'



# widgets
station_select = Select(title="Solar Node:", value='All', options= ['All'] + list(preds.Name.unique()) )

eff_coef = Slider(title="Efficiency Coefficient:", start=0, end=1, value=0.5, step=0.05)

panel_surf = Slider(title="Surface per inhabitant (m2):", start=0, end=5, value=1, step=0.5)



# Data filters
def select_data_solar():
	station_val = station_select.value
	coef = eff_coef.value
	surf = panel_surf.value
		
	selected = preds
	
	# filter station
	if (station_val != 'All'):
		selected = selected[selected.Name.str.contains(station_val)==True]
		
		# apply efficiency and panel surface, convert in GW
		selected['Obs'] = selected['Obs']*coef*surf/1000
		selected['Pred'] = selected['Pred']*coef*surf/1000
		selected_cums = selected.groupby(['Date']).sum().cumsum().reset_index().rename(columns = {'Obs':'Cum_obs', 'Pred':'Cum_pred'})
		# 6 points per hour
		selected_cums['Cum_obs'] = selected_cums['Cum_obs']/6
		selected_cums['Cum_pred'] = selected_cums['Cum_pred']/6
		
	else:
		selected = selected.groupby('Date').sum().reset_index()
		selected['Obs'] = selected['Obs']*coef*surf/1000
		selected['Pred'] = selected['Pred']*coef*surf/1000
		selected_cums = selected.groupby(['Date']).sum().cumsum().reset_index().rename(columns = {'Obs':'Cum_obs', 'Pred':'Cum_pred'})
		selected_cums['Cum_obs'] = selected_cums['Cum_obs']/6
		selected_cums['Cum_pred'] = selected_cums['Cum_pred']/6
		
	return selected, selected_cums
	
	


# update graphs data
def update_solar():
	df, df_cum = select_data_solar()
	source_pi.data = dict(date=np.array(df['Date'],dtype=np.datetime64), obs=df['Obs'], pred=df['Pred'] )
	source_pc.data = dict(date=np.array(df_cum['Date'],dtype=np.datetime64), cum_obs=df_cum['Cum_obs'], cum_pred=df_cum['Cum_pred'] )
	update_map()
	
def update_map():
	coef = eff_coef.value
	surf = panel_surf.value
	# map_data
	map_df = preds.groupby(['Name','lat','lon']).sum()['Obs'].reset_index()
	map_df['Obs'] = map_data['Obs']*coef*surf/6000
	
	# convert WGS84 to Web Mercator coords
	merc_coord = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'),  list(map_df.lon), list(map_df.lat))
	map_df['x'] = merc_coord[0]
	map_df['y'] = merc_coord[1]
	source_map.data = dict(name= map_df['Name'], x=map_df['x'], y=map_df['y'], obs=map_df['Obs'] )
	

    
# changes on control
controls_solar = [station_select, eff_coef, panel_surf]
for control in controls_solar:
    control.on_change('value', lambda attr, old, new: update_solar())
	

l = layout([[[map],[[station_select, eff_coef, panel_surf],pi,pi_select, pc] ]] , sizing_mode="stretch_width")


# initial load of the data
update_solar()


#show(l)
curdoc().add_root(l)
curdoc().title = "Transpower Demo"




