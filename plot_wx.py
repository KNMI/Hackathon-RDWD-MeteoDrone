import os
import pprint
import random
import sys
import wx
import time
# The recommended way to use wx with mpl is with the WXAgg backend
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas, NavigationToolbar2WxAgg as NavigationToolbar
import matplotlib.dates as md
import numpy as np
import pylab
import pyftpbbc
from datetime import datetime
from data import process_drone_data, process_cabauw_data
import json 
import pytz
import argparse
REDRAW_TIMER_MS = 12000
basetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) 
metadata_radio = json.loads(open('metadata_radio.json').read())['metadata']['columns']
metadata_cabauw = json.loads(open('metadata_cab.json').read())['metadata']['columns']

def getSensorData():
    data_radio = pyftpbbc.poll('ftp_radio.json', basetime.strftime('%Y%m%d') + '.txt').read()
    data_cab = pyftpbbc.poll_all('ftp_cabauw.json', basetime.strftime('%Y%m%d')).read()
    cabauw_data = process_cabauw_data(data_cab, basetime, metadata_cabauw)
    radio_data = process_drone_data(data_radio, basetime, metadata_radio, cabauw_data['air_pressure'][-1])
    return (radio_data, cabauw_data) 

class GraphFrame(wx.Frame):
 # the main frame of the application
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Drone Morning Transition")

        self.Centre()

        self.data = getSensorData()
        self.paused = False

        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
        self.redraw_timer.Start(REDRAW_TIMER_MS)

        parser = argparse.ArgumentParser()
        parser.add_argument("--save-on-refresh", help="Save a PNG after every refresh", action="store_true")
        args = parser.parse_args()
        self.save_on_refresh = args.save_on_refresh

    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)

        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        self.panel = wx.Panel(self)

        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)

  # pause button
        self.pause_button = wx.Button(self.panel, -1, "Pause")
        self.cabauw_pressure_label = wx.StaticText(self.panel, label='Cabauw Air pressure: {0:.1f} hPa'.format(self.data[1]['air_pressure'][-1]), style=wx.ALIGN_CENTRE)
        self.gps_height_label = wx.StaticText(self.panel, label='GPS Height: {0:.2f}m'.format(self.data[0]['height'][-1]), style=wx.ALIGN_CENTRE)
        self.computed_height_label = wx.StaticText(self.panel, label='Computed Height: {0:.2f}m'.format(self.data[0]['computed_height'][-1]), style=wx.ALIGN_CENTRE)
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.Add(self.cabauw_pressure_label, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.Add(self.gps_height_label, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.Add(self.computed_height_label, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)        
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)

        self.panel.SetSizer(self.vbox)

        # self.vbox.Fit(self)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((3.0, 3.0), dpi=self.dpi)

        self.axes2 = self.fig.add_subplot(231)
        self.axes2.set_axis_bgcolor('white')
        self.axes2.set_title('Potential temp/Height', size=12)
        self.axes2.set_xlabel('Potential Temperature (C)')
        self.axes2.set_ylabel('Height (m)')

        self.axes = self.fig.add_subplot(232)
        self.axes.set_axis_bgcolor('white')
        self.axes.set_title('Temperature drone', size=12)
        self.axes.set_xlabel('Time (UTC)')
        self.axes.set_ylabel('Temperature (C)')

        self.axes1 = self.fig.add_subplot(233)
        self.axes1.set_axis_bgcolor('white')
        self.axes1.set_title('Mixing ratio', size=12)
        self.axes1.set_xlabel('Time (UTC)')
        self.axes1.set_ylabel('Mixing ratio (g / kg)')

        self.axes3 = self.fig.add_subplot(234)
        self.axes3.set_axis_bgcolor('white')
        self.axes3.set_title('Potential temp/Height', size=12)
        self.axes3.set_xlabel('Time (UTC)')
        self.axes3.set_ylabel('Potential Temperature (C)')

        self.axes4 = self.fig.add_subplot(235)
        self.axes4.set_axis_bgcolor('white')
        self.axes4.set_title('Wind speed', size=12)
        self.axes4.set_xlabel('Time (UTC)')
        self.axes4.set_ylabel('Wind speed (m/s)')

        self.axes5 = self.fig.add_subplot(236)
        self.axes5.set_axis_bgcolor('white')
        self.axes5.set_title('Mixing Ratio Cabauw', size=12)
        self.axes5.set_xlabel('Time (UTC)')
        self.axes5.set_ylabel('Mixing ratio (g / kg)')


        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)
        pylab.setp(self.axes1.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes1.get_yticklabels(), fontsize=8)
        pylab.setp(self.axes2.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes2.get_yticklabels(), fontsize=8)
        pylab.setp(self.axes3.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes3.get_yticklabels(), fontsize=8)
        pylab.setp(self.axes4.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes4.get_yticklabels(), fontsize=8)
        pylab.setp(self.axes5.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes5.get_yticklabels(), fontsize=8)

        # plot the data as a line series, and save the reference 
        # to the plotted line series
        time_drone = self.data[0]['time']
        temp_drone = self.data[0]['temperature']
        mixing_ratio_drone = self.data[0]['temperature']
        pot_temp_drone = self.data[0]['potential_temperature']
        pot_dewpoint_temp_drone = self.data[0]['potential_dewpoint_temp']
        height_drone = self.data[0]['computed_height']


        cabauw_time = self.data[1]['time']
        cabauw_potential_temperatures = self.data[1]['potential_temperatures']
        cabauw_wind_speeds = self.data[1]['wind_speeds']
        cabauw_mixing_ratios = self.data[1]['mixing_ratios']
        Nstart=5000
        Ndata=6000
        self.plot_data = [
            self.axes.plot(
                time_drone, 
                temp_drone, 
            linewidth=1,
            color="blue",
            )[0],

            self.axes1.plot(
            time_drone, 
            mixing_ratio_drone, 
            linewidth=1,
            color="blue",
            )[0],

            self.axes2.plot(
                pot_temp_drone[Nstart:Ndata],
                height_drone[Nstart:Ndata],
                color="red",
                alpha=1,
            )[0],
            self.axes2.plot(
            pot_dewpoint_temp_drone[Nstart:Ndata],
            height_drone[Nstart:Ndata],
            linewidth=1,
            color="blue",
            )[0],

            self.axes3.plot(
            cabauw_time, 
            cabauw_potential_temperatures[10], 
            linewidth=1,
            color="black",
            )[0],

            self.axes3.plot(
            cabauw_time, 
            cabauw_potential_temperatures[20], 
            linewidth=1,
            color="orange",
            )[0],
            self.axes3.plot(
            cabauw_time, 
            cabauw_potential_temperatures[40], 
            linewidth=1,
            color="cyan",
            )[0],
            self.axes3.plot(
            cabauw_time, 
            cabauw_potential_temperatures[80], 
            linewidth=1,
            color="blue",
            )[0],
            self.axes3.plot(
            cabauw_time, 
            cabauw_potential_temperatures[140], 
            linewidth=1,
            color="green",
            )[0],
            self.axes3.plot(
            cabauw_time, 
            cabauw_potential_temperatures[200], 
            linewidth=1,
            color="red",
            )[0],
            self.axes2.plot(
            self.data[0]['potential_temperature'][0:Nstart], 
            self.data[0]['computed_height'][0:Nstart], 
            color="red",
                alpha=0.1,
            )[0],
            self.axes2.plot(
            self.data[0]['potential_dewpoint_temp'][0:Nstart], 
            self.data[0]['computed_height'][0:Nstart], 
            color="blue",
                alpha=0.1,
            )[0],
            self.axes2.plot(
            self.data[1]['potential_temperatures'][200][-1], 
               200,'o',
               color="blue",
                alpha=1,
            )[0],
            self.axes4.plot(
            cabauw_time, 
            cabauw_wind_speeds[10], 
            linewidth=1,
            color="black",
            )[0],

            self.axes4.plot(
            cabauw_time, 
            cabauw_wind_speeds[20], 
            linewidth=1,
            color="orange",
            )[0],
            self.axes4.plot(
            cabauw_time, 
            cabauw_wind_speeds[40], 
            linewidth=1,
            color="cyan",
            )[0],
            self.axes4.plot(
            cabauw_time, 
            cabauw_wind_speeds[80], 
            linewidth=1,
            color="blue",
            )[0],
            self.axes4.plot(
            cabauw_time, 
            cabauw_wind_speeds[140], 
            linewidth=1,
            color="green",
            )[0],
            self.axes4.plot(
            cabauw_time, 
            cabauw_wind_speeds[200], 
            linewidth=1,
            color="red",
            )[0],
            self.axes5.plot(
            cabauw_time, 
            cabauw_mixing_ratios[10], 
            linewidth=1,
            color="black",
            )[0],

            self.axes5.plot(
            cabauw_time, 
            cabauw_mixing_ratios[20], 
            linewidth=1,
            color="orange",
            )[0],
            self.axes5.plot(
            cabauw_time, 
            cabauw_mixing_ratios[40], 
            linewidth=1,
            color="cyan",
            )[0],
            self.axes5.plot(
            cabauw_time, 
            cabauw_mixing_ratios[80], 
            linewidth=1,
            color="blue",
            )[0],
            self.axes5.plot(
            cabauw_time, 
            cabauw_mixing_ratios[140], 
            linewidth=1,
            color="green",
            )[0],
            self.axes5.plot(
            cabauw_time, 
            cabauw_mixing_ratios[200], 
            linewidth=1,
            color="red",
            )[0],
        ]
        xfmt = md.DateFormatter('%H:%M')
        self.axes.xaxis.set_major_formatter(xfmt)
        self.axes1.xaxis.set_major_formatter(xfmt)
        self.axes3.xaxis.set_major_formatter(xfmt)
        self.axes4.xaxis.set_major_formatter(xfmt)
        self.axes5.xaxis.set_major_formatter(xfmt)
        self.axes4.legend(['  10', '  20', '  40', '  80', '140', '200'], loc='upper center', bbox_to_anchor=(0.5, -0.1), fancybox=True, ncol=6)

    def draw_plot(self):
        # redraws the plot

        pylab.setp(self.axes.get_xticklabels(), visible=True)
        pylab.setp(self.axes1.get_xticklabels(), visible=True)
        pylab.setp(self.axes2.get_xticklabels(), visible=True)
        pylab.setp(self.axes3.get_xticklabels(), visible=True)
        xmin = self.data[0]['time'][0]
        xmax = self.data[0]['time'][-1]
        self.axes.set_xbound(lower=xmin, upper=xmax)
        self.axes.set_ybound(lower=min(self.data[0]['temperature']) - 2, upper=max(self.data[0]['temperature']) + 2)
        self.axes1.set_xbound(lower=xmin, upper=xmax)
        self.axes1.set_ybound(lower=min(self.data[0]['q']) - 0.0002, upper=max(self.data[0]['q']) + 0.0002)
        xmin = min(min(self.data[0]['potential_dewpoint_temp']), min(self.data[0]['potential_temperature'])) - 5
        xmax = max(max(self.data[0]['potential_dewpoint_temp']), max(self.data[0]['potential_temperature'])) + 5
        self.axes2.set_xbound(lower=xmin, upper=xmax)
        self.axes2.set_ybound(lower=min(self.data[0]['computed_height']) - 2, upper=max(self.data[0]['computed_height']) + 2)

        Ndata=len(self.data[0]['potential_temperature'])
        #Ndata=6500
        xmin = min(min(self.data[0]['potential_dewpoint_temp'][0:Ndata]), min(self.data[0]['potential_temperature'][0:Ndata])) - 5
        xmax = max(max(self.data[0]['potential_dewpoint_temp'][0:Ndata]), max(self.data[0]['potential_temperature'][0:Ndata])) + 5
        self.axes2.set_xbound(lower=xmin, upper=xmax)
        self.axes2.set_ybound(lower=min(self.data[0]['computed_height'][0:Ndata]) - 2, upper=max(self.data[0]['computed_height'][0:Ndata]) + 2)
        print "Nsieb",Ndata
        Nstart=Ndata-1000
        if Nstart<1:Nstart=1


        xmin = self.data[1]['time'][0]
        xmax = self.data[1]['time'][-1]

        heights = [10, 20, 40, 80, 140, 200]
        min_temp = 1000
        max_temp = -1
        for h in heights:
            min_temp = min(min(self.data[1]['potential_temperatures'][h]), min_temp)
            max_temp = max(max(self.data[1]['potential_temperatures'][h]), max_temp)

        self.axes3.set_xbound(lower=xmin, upper=xmax)
        self.axes3.set_ybound(lower=min_temp - 0.5, upper=max_temp + 0.5)
        self.plot_data[0].set_xdata(self.data[0]['time'])
        self.plot_data[1].set_xdata(self.data[0]['time'])
        self.plot_data[2].set_xdata(self.data[0]['potential_temperature'][Nstart:Ndata])
        self.plot_data[3].set_xdata(self.data[0]['potential_dewpoint_temp'][Nstart:Ndata])
        self.plot_data[4].set_xdata(self.data[1]['time'])
        self.plot_data[5].set_xdata(self.data[1]['time'])
        self.plot_data[6].set_xdata(self.data[1]['time'])
        self.plot_data[7].set_xdata(self.data[1]['time'])
        self.plot_data[8].set_xdata(self.data[1]['time'])
        self.plot_data[9].set_xdata(self.data[1]['time'])
        self.plot_data[10].set_xdata(self.data[0]['potential_temperature'][0:Nstart])
        self.plot_data[11].set_xdata(self.data[0]['potential_dewpoint_temp'][0:Nstart])

        self.plot_data[0].set_ydata(self.data[0]['temperature'])
        self.plot_data[1].set_ydata(self.data[0]['q'])
        self.plot_data[2].set_ydata(self.data[0]['computed_height'][Nstart:Ndata])
        self.plot_data[3].set_ydata(self.data[0]['computed_height'][Nstart:Ndata])
        self.plot_data[4].set_ydata(self.data[1]['potential_temperatures'][10])
        self.plot_data[5].set_ydata(self.data[1]['potential_temperatures'][20])
        self.plot_data[6].set_ydata(self.data[1]['potential_temperatures'][40])
        self.plot_data[7].set_ydata(self.data[1]['potential_temperatures'][80])
        self.plot_data[8].set_ydata(self.data[1]['potential_temperatures'][140])
        self.plot_data[9].set_ydata(self.data[1]['potential_temperatures'][200])
        self.plot_data[10].set_ydata(self.data[0]['computed_height'][0:Nstart])
        self.plot_data[11].set_ydata(self.data[0]['computed_height'][0:Nstart])
        self.plot_data[12].set_xdata(self.data[1]['potential_temperatures'][200][-1])

        self.canvas.draw()

    def on_pause_button(self, event):
        self.paused = not self.paused

    def on_update_pause_button(self, event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)

    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"

        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)

    def on_redraw_timer(self, event):
        if not self.paused:
            self.data = getSensorData()
            self.cabauw_pressure_label.SetLabel('Cabauw Air pressure: {0:.1f} hPa'.format(self.data[1]['air_pressure'][-1]))
            self.gps_height_label.SetLabel('GPS Height: {0:.2f}m'.format(self.data[0]['height'][-1]))
            self.computed_height_label.SetLabel('Computed Height: {0:.2f}m'.format(self.data[0]['computed_height'][-1]))
        self.draw_plot()
        if self.save_on_refresh:
            self.canvas.print_figure('autosave/{0}.png'.format(datetime.utcnow().strftime('%Y%m%d-%H%M%S')), dpi=self.dpi)

    def on_exit(self, event):
        self.Destroy()

    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER, 
            self.on_flash_status_off, 
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)

    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')


if __name__ == '__main__':
    app = wx.App(False)
    app.frame = GraphFrame()
    app.frame.Show()
    app.frame.Maximize(True)
    app.MainLoop()
