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



def getSensorData(latest_drone_time, latest_cabauw_time, latest_cabauw_pressure):
    data_radio = pyftpbbc.poll('ftp_radio.json', basetime.strftime('%Y%m%d') + '.txt').read()
    data_cab = pyftpbbc.poll_all('ftp_cabauw.json', basetime.strftime('%Y%m%d')).read()

    cabauw_data = process_cabauw_data(data_cab, basetime, metadata_cabauw, latest_cabauw_time)
    cab_pres = cabauw_data['air_pressure'][-1] if len(cabauw_data['air_pressure']) > 0 else latest_cabauw_pressure

    radio_data = process_drone_data(data_radio, basetime, metadata_radio, cab_pres, latest_drone_time)
    return (radio_data, cabauw_data) 

def safe_max(ar): 
    return max(ar or [0])

def safe_min(ar): 
    return min(ar or [0])

class GraphFrame(wx.Frame):
 # the main frame of the application
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Drone Morning Transition")

        self.Centre()
        self.num_plots = 6
        self.axes = [None] * self.num_plots
        self.plots_per_subplot = [None] * self.num_plots
        self.cum_plots = None
        self.data = getSensorData(None, None, None)
        self.paused = False
        self.demarcation_time_idx = 0

        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
        self.redraw_timer.Start(REDRAW_TIMER_MS)

        parser = argparse.ArgumentParser()
        parser.add_argument("--save-on-refresh", help="Save a PNG after every refresh", action="store_true")
        parser.add_argument("--overwrite", help="Save a PNG after every refresh but overwrite file", action="store_true")
        args = parser.parse_args()
        self.save_on_refresh = args.save_on_refresh
        self.overwrite = args.overwrite

    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        m_expt = menu_file.Append(-1, "&Export Data", "Export data to file")
        self.Bind(wx.EVT_MENU, self.on_save_data, m_expt)

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
        self.new_run_button = wx.Button(self.panel, -1, "New drone flight")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_BUTTON, self.on_new_drone_flight_button, self.new_run_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.Add(self.new_run_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)        
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)

        self.panel.SetSizer(self.vbox)

        # self.vbox.Fit(self)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()


    def plot_drone_data(self, xdata, ydata, axis_idx, color, alpha=1, symbol='-'):
        self.plots_per_subplot[axis_idx] = 1 if self.plots_per_subplot[axis_idx] is None else self.plots_per_subplot[axis_idx] + 1
        return self.axes[axis_idx].plot(xdata, ydata, symbol, linewidth=1, color=color, alpha=alpha)[0]

    def plot_cabauw_data(self, xdata, ydata, axis_idx, alpha=1, symbol='-'):
        self.plots_per_subplot[axis_idx] = 6 if self.plots_per_subplot[axis_idx] is None else self.plots_per_subplot[axis_idx] + 6

        plot10 = self.axes[axis_idx].plot(xdata, ydata[10], symbol, linewidth=1, color='black', alpha=alpha)[0]
        plot20 = self.axes[axis_idx].plot(xdata, ydata[20], symbol, linewidth=1, color='orange', alpha=alpha)[0]
        plot40 = self.axes[axis_idx].plot(xdata, ydata[40], symbol, linewidth=1, color='cyan', alpha=alpha)[0]
        plot80 = self.axes[axis_idx].plot(xdata, ydata[80], symbol, linewidth=1, color='blue', alpha=alpha)[0]
        plot140 = self.axes[axis_idx].plot(xdata, ydata[140], symbol, linewidth=1, color='green', alpha=alpha)[0]
        plot200 = self.axes[axis_idx].plot(xdata, ydata[200], symbol, linewidth=1, color='red', alpha=alpha)[0]
        return [plot10, plot20, plot40, plot80, plot140, plot200]

    def plot_cabauw_markers(self, cabauw_potential_temperatures, cabauw_potential_dewpoint_temperatures):
        plots = []
        for (h, c) in zip([10, 20, 40, 80, 140, 200], ['black', 'orange', 'cyan', 'blue', 'green', 'red']):
            plots.append(self.plot_drone_data(cabauw_potential_temperatures[h][-1], [h], 0, c, alpha=0.5, symbol='o'))
        for (h, c) in zip([10, 20, 40, 80, 140, 200], ['black', 'orange', 'cyan', 'blue', 'green', 'red']):
            plots.append(self.plot_drone_data(cabauw_potential_dewpoint_temperatures[h][-1], [h], 0, c, alpha=0.5, symbol='^'))

        return plots


    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((3.0, 3.0), dpi=self.dpi)
        self.fig.suptitle('{0} - Cabauw Air pressure: {1:.1f} hPa - GPS height: {2:.2f}m - Computed Height: {3:.2f}m'.format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 
            self.data[1]['air_pressure'][-1],
            self.data[0]['height'][-1],
            self.data[0]['computed_height'][-1]
        ))
        self.axes[0] = self.fig.add_subplot(231)
        try:
            self.axes[0].set_facecolor('white')
        except AttributeError:
            self.axes[0].set_axis_bgcolor('white')

        self.axes[0].set_title('Drone - Potential temp/Height', size=12)
        self.axes[0].set_xlabel('Potential Temperature (C)')
        self.axes[0].set_ylabel('Height (m)')

        self.axes[1] = self.fig.add_subplot(232)
        try:
            self.axes[1].set_facecolor('white')
        except AttributeError:
            self.axes[1].set_axis_bgcolor('white')

        self.axes[1].set_title('Drone - Temperature drone', size=12)
        self.axes[1].set_xlabel('Time (UTC)')
        self.axes[1].set_ylabel('Temperature (C)')

        self.axes[2] = self.fig.add_subplot(233)
        try:
            self.axes[2].set_facecolor('white')
        except AttributeError:
            self.axes[2].set_axis_bgcolor('white')

        self.axes[2].set_title('Drone - Mixing ratio', size=12)
        self.axes[2].set_xlabel('Time (UTC)')
        self.axes[2].set_ylabel('Mixing ratio (g / kg)')

        self.axes[3] = self.fig.add_subplot(234)
        try:
            self.axes[3].set_facecolor('white')
        except AttributeError:
            self.axes[3].set_axis_bgcolor('white')

        self.axes[3].set_title('Cabauw - Potential temp/Height', size=12)
        self.axes[3].set_xlabel('Time (UTC)')
        self.axes[3].set_ylabel('Potential Temperature (C)')

        self.axes[4] = self.fig.add_subplot(235)
        try:
            self.axes[4].set_facecolor('white')
        except AttributeError:
            self.axes[4].set_axis_bgcolor('white')

        self.axes[4].set_title('Cabauw - Wind speed', size=12)
        self.axes[4].set_xlabel('Time (UTC)')
        self.axes[4].set_ylabel('Wind speed (m/s)')

        self.axes[5] = self.fig.add_subplot(236)
        try:
            self.axes[5].set_facecolor('white')
        except AttributeError:
            self.axes[5].set_axis_bgcolor('white')

        self.axes[5].set_title('Cabauw - Mixing Ratio', size=12)
        self.axes[5].set_xlabel('Time (UTC)')
        self.axes[5].set_ylabel('Mixing ratio (g / kg)')

        for axis_idx in range(self.num_plots):
            pylab.setp(self.axes[axis_idx].get_xticklabels(), fontsize=8)
            pylab.setp(self.axes[axis_idx].get_yticklabels(), fontsize=8)

        # plot the data as a line series, and save the reference 
        # to the plotted line series
        time_drone = self.data[0]['time']
        time_drone_before = time_drone[:self.demarcation_time_idx]
        time_drone_after = time_drone[self.demarcation_time_idx:]

        temp_drone = self.data[0]['temperature']
        temp_drone_before = temp_drone[:self.demarcation_time_idx]
        temp_drone_after = temp_drone[self.demarcation_time_idx:]

        mixing_ratio_drone = self.data[0]['q']
        mixing_ratio_drone_before = mixing_ratio_drone[:self.demarcation_time_idx]
        mixing_ratio_drone_after = mixing_ratio_drone[self.demarcation_time_idx:]

        pot_temp_drone = self.data[0]['potential_temperature']
        pot_temp_drone_before = pot_temp_drone[:self.demarcation_time_idx]
        pot_temp_drone_after = pot_temp_drone[self.demarcation_time_idx:]

        pot_dewpoint_temp_drone = self.data[0]['potential_dewpoint_temp']
        pot_dewpoint_temp_drone_before = pot_dewpoint_temp_drone[:self.demarcation_time_idx]
        pot_dewpoint_temp_drone_after = pot_dewpoint_temp_drone[self.demarcation_time_idx:]

        height_drone = self.data[0]['computed_height']
        # height_drone = self.data[0]['height']
        height_before = height_drone[:self.demarcation_time_idx]
        height_after = height_drone[self.demarcation_time_idx:]

        cabauw_time = self.data[1]['time']
        cabauw_potential_temperatures = self.data[1]['potential_temperatures']
        cabauw_potential_dewpoint_temperatures = self.data[1]['potential_dew_point_temperatures']
        cabauw_wind_speeds = self.data[1]['wind_speeds']
        cabauw_mixing_ratios = self.data[1]['mixing_ratios']
        # print(pot_temp_drone_after, self.data[0]['height'])
        self.plot_data = [
            self.plot_drone_data(pot_temp_drone_before, height_before, 0, 'red', alpha=0.1),
            self.plot_drone_data(pot_dewpoint_temp_drone_before, height_before, 0, 'blue', alpha=0.1),
            self.plot_drone_data(pot_temp_drone_after, height_after, 0, 'red'),
            self.plot_drone_data(pot_dewpoint_temp_drone_after, height_after, 0, 'blue'),
            self.plot_cabauw_markers(cabauw_potential_temperatures, cabauw_potential_dewpoint_temperatures),
            
            self.plot_drone_data(time_drone_before, temp_drone_before, 1, 'blue', alpha=0.1),
            self.plot_drone_data(time_drone_after, temp_drone_after, 1, 'blue'),
            
            self.plot_drone_data(time_drone_before, mixing_ratio_drone_before, 2, 'blue', alpha=0.1),
            self.plot_drone_data(time_drone_after, mixing_ratio_drone_after, 2, 'blue'),
            
            self.plot_cabauw_data(cabauw_time, cabauw_potential_temperatures, 3),
            self.plot_cabauw_data(cabauw_time, cabauw_wind_speeds, 4),
            self.plot_cabauw_data(cabauw_time, cabauw_mixing_ratios, 5),

            self.plot_drone_data(cabauw_time, [8] * len(cabauw_time), 4, 'purple', symbol='--')
        ]

        xfmt = md.DateFormatter('%H:%M')
        for ax in self.axes[1:]:
            ax.xaxis.set_major_formatter(xfmt)

        (lower, upper) = self.axes[4].get_ybound()
        self.axes[4].set_ybound(lower, max(9, upper))

        self.axes[4].legend(['  10m', '  20m', '  40m', '  80m', '140m', '200m'], loc='upper center', bbox_to_anchor=(0.5, -0.1), fancybox=True, ncol=6)

    def update_cabauw_data(self, xdata, ydata, plot_idx, axes_idx, ydelta=0):
        xmin = np.min(xdata)
        xmax = np.max(xdata)
        ymin = 10000
        ymax = -1000
        for (i, h) in enumerate([10, 20, 40, 80, 140, 200]):
            self.plot_data[plot_idx][i].set_xdata(xdata)
            self.plot_data[plot_idx][i].set_ydata(ydata[h])
            ymin = min(ymin, min(ydata[h]))
            ymax = max(ymax, max(ydata[h]))

        self.axes[axes_idx].set_xbound(lower=xmin, upper=xmax)
        self.axes[axes_idx].set_ybound(lower=ymin - ydelta, upper=ymax + ydelta)


    def draw_plot(self):
        # # redraws the plot
        time_drone = self.data[0]['time']
        time_drone_before = time_drone[:self.demarcation_time_idx]
        time_drone_after = time_drone[self.demarcation_time_idx:]

        temp_drone = self.data[0]['temperature']
        temp_drone_before = temp_drone[:self.demarcation_time_idx]
        temp_drone_after = temp_drone[self.demarcation_time_idx:]

        mixing_ratio_drone = self.data[0]['q']
        mixing_ratio_drone_before = mixing_ratio_drone[:self.demarcation_time_idx]
        mixing_ratio_drone_after = mixing_ratio_drone[self.demarcation_time_idx:]

        pot_temp_drone = self.data[0]['potential_temperature']
        pot_temp_drone_before = pot_temp_drone[:self.demarcation_time_idx]
        pot_temp_drone_after = pot_temp_drone[self.demarcation_time_idx:]

        pot_dewpoint_temp_drone = self.data[0]['potential_dewpoint_temp']
        pot_dewpoint_temp_drone_before = pot_dewpoint_temp_drone[:self.demarcation_time_idx]
        pot_dewpoint_temp_drone_after = pot_dewpoint_temp_drone[self.demarcation_time_idx:]

        height_drone = self.data[0]['computed_height']

        # height_drone = self.data[0]['height']
        height_drone_before = height_drone[:self.demarcation_time_idx]
        height_drone_after = height_drone[self.demarcation_time_idx:]

        cabauw_time = self.data[1]['time']
        cabauw_potential_temperatures = self.data[1]['potential_temperatures']
        cabauw_potential_dewpoint_temperatures = self.data[1]['potential_dew_point_temperatures']
        cabauw_wind_speeds = self.data[1]['wind_speeds']
        cabauw_mixing_ratios = self.data[1]['mixing_ratios']

        # first plot
        self.plot_data[0].set_xdata(pot_temp_drone_before)
        self.plot_data[0].set_ydata(height_drone_before)

        self.plot_data[1].set_xdata(pot_dewpoint_temp_drone_before)
        self.plot_data[1].set_ydata(height_drone_before)

        self.plot_data[2].set_xdata(pot_temp_drone_after)
        self.plot_data[2].set_ydata(height_drone_after)

        self.plot_data[3].set_xdata(pot_dewpoint_temp_drone_after)
        self.plot_data[3].set_ydata(height_drone_after)


        xmin_cab = 1000
        xmax_cab = -1000
        i = 0
        for (h, c) in zip([10, 20, 40, 80, 140, 200], ['black', 'orange', 'cyan', 'blue', 'green', 'red']):
            self.plot_data[4][i].set_xdata(cabauw_potential_temperatures[h][-1])
            self.plot_data[4][i + 6].set_xdata(cabauw_potential_dewpoint_temperatures[h][-1])
            xmin_cab = min(cabauw_potential_dewpoint_temperatures[h][-1], xmin_cab)
            xmin_cab = min(cabauw_potential_temperatures[h][-1], xmin_cab)
            xmax_cab = max(cabauw_potential_dewpoint_temperatures[h][-1], xmax_cab)
            xmax_cab = max(cabauw_potential_temperatures[h][-1], xmax_cab)
            i = i + 1

        pot_temp_min = np.min(pot_temp_drone_after) if len(pot_temp_drone_after) > 0 else 0
        pot_dewpoint_temp_min = np.min(pot_dewpoint_temp_drone_after) if len(pot_dewpoint_temp_drone_after) > 0 else 0

        pot_temp_max = np.max(pot_temp_drone_after) if len(pot_temp_drone_after) > 0 else 0
        pot_dewpoint_temp_max = np.max(pot_dewpoint_temp_drone_after) if len(pot_dewpoint_temp_drone_after) > 0 else 0

        xmin = min(pot_temp_min, pot_dewpoint_temp_min)
        xmax = max(pot_temp_max, pot_dewpoint_temp_max)
        ymax = max(210, np.max(height_drone_after) if len(height_drone_after) > 0 else 0)
        ymin = np.min(height_drone_after) if len(height_drone_after) > 0 else 0
        ydelta = 1
        xdelta = 1
        self.axes[0].set_xbound(lower=min(xmin_cab, xmin) - xdelta, upper=max(xmax_cab, xmax) + xdelta)
        self.axes[0].set_ybound(lower=ymin - ydelta, upper=ymax + ydelta)

        # second plot
        self.plot_data[5].set_xdata(time_drone_before)
        self.plot_data[5].set_ydata(temp_drone_before)
        self.plot_data[6].set_xdata(time_drone_after)
        self.plot_data[6].set_ydata(temp_drone_after)

        xmin = np.min(time_drone)
        xmax = np.max(time_drone)
        ymax = np.max(temp_drone)
        ymin = np.min(temp_drone)
        self.axes[1].set_xbound(lower=xmin, upper=xmax)
        self.axes[1].set_ybound(lower=ymin - ydelta, upper=ymax + ydelta)

        # third plot
        self.plot_data[7].set_xdata(time_drone_before)
        self.plot_data[7].set_ydata(mixing_ratio_drone_before)
        self.plot_data[8].set_xdata(time_drone_after)
        self.plot_data[8].set_ydata(mixing_ratio_drone_after)

        xmin = np.min(time_drone)
        xmax = np.max(time_drone)
        ymax = np.max(mixing_ratio_drone)
        ymin = np.min(mixing_ratio_drone)
        ydelta = 0.5
        self.axes[2].set_xbound(lower=xmin, upper=xmax)
        self.axes[2].set_ybound(lower=ymin - ydelta, upper=ymax + ydelta)


        # fourth plot
        self.update_cabauw_data(cabauw_time, cabauw_potential_temperatures, plot_idx=9, axes_idx=3, ydelta=1)
        self.update_cabauw_data(cabauw_time, cabauw_wind_speeds, plot_idx=10, axes_idx=4, ydelta=1)
        self.update_cabauw_data(cabauw_time, cabauw_mixing_ratios, plot_idx=11, axes_idx=5, ydelta=0.5)
        self.plot_data[12].set_xdata(cabauw_time)
        self.plot_data[12].set_ydata([8] * len(cabauw_time))
        (lower, upper) = self.axes[4].get_ybound()
        self.axes[4].set_ybound(lower, max(9, upper))
        self.canvas.draw()

    def on_pause_button(self, event):
        self.paused = not self.paused

    def on_new_drone_flight_button(self, event):
        self.demarcation_time_idx = len(self.data[0]['time'])
        self.draw_plot()

    def on_update_pause_button(self, event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)

    def save_data(self, path):
        np.savez_compressed(path, drone_data=self.data[0], cabauw_data=self.data[1])

    def on_save_data(self, event):
        file_choices = "Numpy Compressed file (*.npz)|*.npz"

        dlg = wx.FileDialog(
            self, 
            message="Save data...",
            defaultDir=os.getcwd(),
            defaultFile="data.npz",
            wildcard=file_choices,
            style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.save_data(path)
            self.flash_status_message("Saved data to %s" % path)

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
            (new_drone_data, new_cabauw_data) = getSensorData(max(self.data[0]['time']), max(self.data[1]['time']), self.data[1]['air_pressure'][-1])
            all_cabauw_data = {}
            all_drone_data = {}
            for (k, v) in new_drone_data.iteritems():
                all_drone_data[k] = np.append(self.data[0][k], v)

            for (k, v) in new_cabauw_data.iteritems():
                if k == 'air_pressure' or k == 'time': 
                    all_cabauw_data[k] = np.append(self.data[1][k], v)
                else:
                    all_cabauw_data[k] = {}
                    for (k1, v1) in new_cabauw_data[k].iteritems():
                        all_cabauw_data[k][k1] = np.append(self.data[1][k][k1], v1)
                
            self.data = (all_drone_data, all_cabauw_data)

        self.draw_plot()
        self.fig.suptitle('{0} - Cabauw Air pressure: {1:.1f} hPa - GPS height: {2:.2f}m - Computed Height: {3:.2f}m'.format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 
            self.data[1]['air_pressure'][-1],
            self.data[0]['height'][-1],
            self.data[0]['computed_height'][-1]
        ))
        if self.save_on_refresh:
            if self.overwrite:
                self.canvas.print_figure('autosave/{0}.png'.format(datetime.utcnow().strftime('%Y%m%d')), dpi=self.dpi)
            else:
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
