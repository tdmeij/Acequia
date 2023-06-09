
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats
import statsmodels.api as sm
import statsmodels.graphics.tsaplots
from statsmodels.tsa.stattools import ccf, acf, pacf


def plot_tsmodel_statistics(obs=None,sim=None,res=None,noise=None,
    figtitle=None,figtype='full'):
    """Plot statistical diagnostics of a time series model

    Parameters
    ----------
    obs : pd.Series
        time series with observations
    sim : pd.Series
        time series with simulated values
    res : pd.Series
        time series with residuals
    noise : pd.Series
        time series with noise
    figtitle : str
        title above output graph

    Notes
    -----
    Definition of input time series is as followed:
    obs : observed values
    sim : values simulated with a transfer-function
    res : calculated differences between obs and sim
    noise : values of res after a noise model is applied

    """
    pms = TsModelStatsPlot(obs=obs,sim=sim,res=res,noise=noise,figtitle=figtitle)
    return pms.plot(figtype=figtype)


class TsModelStatsPlot():
    """Plot statistical diagnostics of a time series model"""

    _clrdict = {
        'obs' : '#f18805',
        'sim' : '#1f2bfb',
        'res' : '#1f2bfb',
        'noise' : '#8a2be2',
        'stats' : '#5e6175', #'#0000ff', #'#9bccf9' #'#ffcf40'
        'bandwidth' : '#fff98e',
        }

    _axtitlefontsize = 18.
    _axtitle_dict = {'fontsize':10.}
    _noiselim = [None,None]
    _markersize = 5.
    _titlefontsize = 7.
    _suptitlefontsize = 12.


    def __init__(self,obs=None,sim=None,res=None,noise=None,figtitle=None):
        """Parameters
        ----------
        obs : pd.Series
            time series with observations
        sim : pd.Series
            time series with simulated values
        res : pd.Series
            time series with residuals
        noise : pd.Series
            time series with noise
        figtitle : str
            title above output graph

        Notes
        -----
        Definition of input time series is as followed:
        obs : observed values
        sim : values simulated with a transfer-function
        res : calculated differences between obs and sim
        noise : values of res after a noise model is applied

        """

        self._obs = obs
        self._sim = sim
        self._res = res
        self._noise = noise
        self._figtitle = figtitle

        self._fig_width = 6.4
        self._fig_height = 5.4


    def plot(self,figtype='full'):
        """Plot figure

        Parameters
        ---------
        figtype : {'full','basic'}, default 'full'
            model statistics figure type

        Return
        ------
        plt.fig

        """

        if figtype=='full':
            self._fullfigure()

        if figtype=='basic':
            self._basicfigure()

        return self._fig


    def __repr__(self):
        return (f'{self.__class__.__name__}')


    def _fullfigure(self):
        """Define figure and gridspec object """

        # define empty figure and gridspec
        self._nrows = 7
        self._ncols = 2

        self._fig = plt.figure(constrained_layout=True, 
            figsize=(self._fig_width,self._fig_height))
        gs = self._fig.add_gridspec(self._nrows,self._ncols)

        # create empty subaxes using gridspec
        self._axs = {}
        self._axs['mlfit'] = self._fig.add_subplot(gs[0:2,:])
        self._axs['residuals'] = self._fig.add_subplot(gs[2,:])
        self._axs['noise'] = self._fig.add_subplot(gs[3,:])
        self._axs['residuals_acf'] = self._fig.add_subplot(gs[4,0])
        self._axs['residuals_pacf'] = self._fig.add_subplot(gs[4,1])
        self._axs['noise_acf'] = self._fig.add_subplot(gs[5,0])
        self._axs['noise_pacf'] = self._fig.add_subplot(gs[5,1])
        self._axs['noise_histogram'] =  self._fig.add_subplot(gs[6,0])
        self._axs['noise_qq'] = self._fig.add_subplot(gs[6,1])

        # plot subplots
        self._plot_modelfit()
        self._plot_residuals()
        self._plot_noise()
        self._plot_residuals_acf()
        self._plot_residuals_pacf()
        self._plot_noise_acf()
        self._plot_noise_pacf()
        self._plot_noise_histogram()
        self._plot_noise_qq()

        self._format_axes(axnames=['residuals_acf','residuals_pacf',
            'noise_acf','noise_pacf'])

        self._fig.suptitle(self._figtitle, fontsize=self._suptitlefontsize,
            fontweight='bold')

        return self._fig


    def _basicfigure(self):
        """Define figure and gridspec object """

        # define empty figure and gridspec
        self._nrows = 5 #7
        self._ncols = 2
        #self._fig_width = 18
        #self._fig_height = 15

        self._fig = plt.figure(constrained_layout=True, 
            figsize=(self._fig_width,self._fig_height))
        gs = self._fig.add_gridspec(self._nrows,self._ncols)

        # create empty subaxes using gridspec
        self._axs = {}
        self._axs['mlfit'] = self._fig.add_subplot(gs[0:2,:])
        ##self._axs['residuals'] = self._fig.add_subplot(gs[2,:])
        self._axs['noise'] = self._fig.add_subplot(gs[2,:])
        ##self._axs['residuals_acf'] = self._fig.add_subplot(gs[4,0])
        ##self._axs['residuals_pacf'] = self._fig.add_subplot(gs[4,1])
        self._axs['noise_acf'] = self._fig.add_subplot(gs[3:5,0])
        ##self._axs['noise_pacf'] = self._fig.add_subplot(gs[5,1])
        self._axs['noise_histogram'] =  self._fig.add_subplot(gs[3:5,1])
        ##self._axs['noise_qq'] = self._fig.add_subplot(gs[6,1])

        # plot subplots
        self._plot_modelfit()
        ##self._plot_residuals()
        self._plot_noise()
        ##self._plot_residuals_acf()
        ##self._plot_residuals_pacf()
        self._plot_noise_acf()
        ##self._plot_noise_pacf()
        ##self._format_axes()
        self._plot_noise_histogram()
        ##self._plot_noise_qq()

        self._format_axes(axnames=['noise_acf'])

        self._fig.suptitle(self._figtitle, fontsize=self._suptitlefontsize,
            fontweight='bold')

        return self._fig


    def _plot_modelfit(self):
        """plot simulations and measurements in one graph"""

        x = self._sim.index.values
        y = self._sim.values
        clrs = self._clrdict['sim']
        self._axs['mlfit'].plot(x,y,c=clrs,label='transfer model')

        x = self._obs.index.values
        y = self._obs.values
        clrs = self._clrdict['obs']
        self._axs['mlfit'].plot(x,y,linestyle='None',marker='o',
            markersize=self._markersize,
            markerfacecolor=clrs,markeredgecolor='None',
            label='observations')

        self._axs['mlfit'].legend(loc='lower right')
        #self._axs['mlfit'].axes.get_xaxis().set_visible(False)


    def _plot_residuals(self):
        """Plot residuals in seperate graph"""

        x = self._res.index.values
        y = self._res.values
        clrs = self._clrdict['sim']
        self._axs['residuals'].plot(x,y,linestyle='None',marker='o',
            markersize=self._markersize,
            markerfacecolor=clrs,markeredgecolor='None',)
            #label='residuals (correlated)')

        self._axs['residuals'].set_title('residuals (correlated)',
            fontdict=self._axtitle_dict)

        ylim = self._axs['residuals'].get_ylim()
        resmax = round(max(abs(ylim[0]),abs(ylim[1])),1)
        self._reslim = [-resmax,resmax]

        self._axs['residuals'].set_ylim(self._reslim)
        self._axs['residuals'].set_title(
            'Residuals of the transfer-model (correlated)',
            self._axtitle_dict)

        self._axs['residuals'].axes.get_xaxis().set_visible(False)


    def _plot_noise(self):
        """Plot model innovations in seperate graph"""

        x = self._noise.index.values
        y = self._noise.values
        clrs = self._clrdict['noise']
        self._axs['noise'].plot(x,y,linestyle='None',marker='o',
            markersize=self._markersize,
            markerfacecolor=clrs,markeredgecolor='None',)
            #label='noise (uncorrelated)')

        self._axs['noise'].set_title('noise (uncorrelated)',
            self._axtitle_dict)


        ylim = self._axs['noise'].get_ylim()
        noisemax = round(max(abs(ylim[0]),abs(ylim[1])),1)
        self._noiselim = [-noisemax,noisemax]
        self._axs['noise'].set_ylim(self._noiselim)
        self._axs['noise'].set_title('Noise (uncorrelated)',
            self._axtitle_dict)

        self._axs['noise'].axes.get_xaxis().set_visible(False)


    def _plot_residuals_acf(self):
        """Plot autocorrelation of the noise""" 
        residuals = self._res
        statsmodels.graphics.tsaplots.plot_acf(residuals, 
            ax=self._axs['residuals_acf'], lags=30, alpha=0.05,
            zero=False) ##, title='Autocorrelation residuals')

        self._axs['residuals_acf'].set_title(
            'Autocorrelation of the residuals',self._axtitle_dict)


    def _plot_residuals_pacf(self):
        """Plot partial autocorrelation of the noise"""
        residuals = self._res
        statsmodels.graphics.tsaplots.plot_pacf(residuals, ax=self._axs['residuals_pacf'], lags=30, alpha=0.05, 
             zero=False, title='Partial autocorrelation residuals')

        self._axs['residuals_pacf'].set_title(
            'Partial autocorrelation of the residuals',self._axtitle_dict)


    def _plot_noise_acf(self):
        """Plot autocorrelation of the innovations"""
        noise = self._noise
        statsmodels.graphics.tsaplots.plot_acf(noise, 
            ax=self._axs['noise_acf'], lags=30, alpha=0.05, 
            zero=False)
        self._axs['noise_acf'].set_title(
            'Autocorrelation of the noise',self._axtitle_dict)


    def _plot_noise_pacf(self):
        """Plot partial autocorrelation of the innovations"""
        noise = self._noise
        statsmodels.graphics.tsaplots.plot_pacf(noise, 
            ax=self._axs['noise_pacf'], lags=30, alpha=0.05, 
            zero=False)
        self._axs['noise_pacf'].set_title(
            'Partial autocorrelation of the noise',self._axtitle_dict)


    def _format_axes(self,axnames=[]):

        for axname in axnames:

            if axname.startswith('residuals'):
                clrs = self._clrdict['res']
            elif axname.startswith('noise'):
                clrs = self._clrdict['noise']
            else:
                clrs = '#ee22cc'

            ax = self._axs[axname]
            ax.get_lines()[1].set_markerfacecolor(clrs) #'#8a2be2')
            ax.get_lines()[1].set_markeredgecolor(clrs)

            # set color of correlation plot bandwith
            art = ax.properties()['default_bbox_extra_artists'][1]
            art.set_facecolor(self._clrdict['bandwidth'])


    def _plot_noise_histogram(self):
        """Plot histogram of innovations"""

        noise = self._noise
        clrs = self._clrdict['noise']

        # empirical distribution
        n, bins, patches = self._axs['noise_histogram'].hist(noise,
            50, density=True, facecolor=clrs, alpha=0.75)

        # theoretical distribution
        x = np.arange(-0.5,0.5,0.01)
        y = scipy.stats.norm.pdf(x,0,np.std(noise))
        clrs = self._clrdict['stats']
        self._axs['noise_histogram'].plot(x,y,color=clrs,linewidth=2)

        self._axs['noise_histogram'].set_xlim(self._noiselim)
        self._axs['noise_histogram'].set_title(
            'Histogram of the noise',self._axtitle_dict)


    def _plot_noise_qq(self):
        """Plot qqplot of innovations"""

        noise = self._noise
        sm.qqplot(noise, scipy.stats.t, fit=True, line="45", ax=self._axs['noise_qq'])
        line1,line2 = self._axs['noise_qq'].get_lines() #line1: innovations line2: normal distribution
        line1.set_markerfacecolor('#8a2be2')
        line1.set_markeredgecolor('None')
        line1.set_markersize(4)
        line2.set_color(self._clrdict['stats']) #'#666666')
        #axs[2,1].set_xlabel('Theoretische kwantielen standaard normale verdeling',fontsize=12)
        #axs[2,1].set_ylabel('Kwantielen noise',fontsize=12)
        self._axs['noise_qq'].set_title(
            'QQ-plot of the noise',self._axtitle_dict)

