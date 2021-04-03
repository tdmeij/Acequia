""" This module contains a class GwGxg that calculates some
descriptive statistics from a series of groundwater head measurements
used by groundwater practitioners in the Netherlands 

History: Created 16-08-2015, last updated 12-02-1016
         Migrated to acequia on 15-06-2019

@author: Thomas de Meij

"""


from datetime import datetime
import datetime as dt
import warnings
import numpy as np
from pandas import Series, DataFrame
import pandas as pd

import acequia as aq


def stats_gxg(ts,reflev='datum'):
    """Return table with GxG statistics

    Parameters
    ----------
    ts : aq.GwSeries, pd.Series
        Groundwater head time series

    reflev : {'datum','surface'}, optional
        Reference level for groundwater heads

    Returns
    -------
    pd.DataFrame

    """

    gxg = aq.GxgStats(ts)
    return gxg.gxg(reflev=reflev)


class GxgStats:
    """Calculate descriptive statistics for time series of measured heads

    Parameters
    ----------
    gw : aq.GwSeries, pd.Series
        timeseries of groundwater head measurements relative to datum level

    srname : str, optional
        name of groundwater head series

    surflevel : float, optional
        surface level height (if ref='datum' this option is ignored)

    Notes
    -----
    In the Netherlands, traditionally groundwater head series are 
    summarized using decriptive statistics that characterise the mean 
    highest level (GHG), the mean lowest level (GLG) and the mean spring 
    level (GVG). These three measures together are reffered to as the GxG.
    The definitions of GHG, GLG and GVG are based on time series with 
    measured heads on the 14th and 28th of each month. Therefore the time 
    series of measrued heads is internally resampled to values on the 14th
    and 28yh before calculating the GxG statistics.

    For further reference: 
    P. van der SLuijs and J.J. de Gruijter (1985). 'Water table classes: 
    a method to decribe seasonal fluctuation and duration of water table 
    classes on Dutch soil maps.' Agricultural Water Management 10 (1985) 
    109 - 125. Elsevier Science Publishers, Amsterdam.

    """

    N14 = 18
    REFERENCE = ['datum','surface']
    APPROXIMATIONS = ['SLUIJS82','HEESEN74','SLUIJS76a','SLUIJS76b',
        'SLUIJS89pol','SLUIJS89sto','RUNHAAR89','GAAST06',]
    VGDATES = ['apr1','apr15','mar15']
    VGREFDATE = 'apr1'


    def __init__(self, gw, srname=None, surflevel=None):
        """Return GxG object"""


        if isinstance(gw,aq.GwSeries):

            self._ts = gw.heads(ref='datum')
            self.srname = gw.name()
            if surflevel is None:
                self._surflevel = gw.surface()
            else:
                self._surflevel = surflevel
            self._gw = gw

        elif isinstance(gw,pd.Series):

            self._ts = gw
            self.srname = self._ts.name
            self._surflevel = surflevel
            self._gw = None

        else:
            raise(f'{gw} is not of type aq.GwSeries or pd.Series')

        self._ts1428 = aq.ts1428(self._ts,maxlag=3,remove_nans=False)


    def _yearseries(self,ts,dtype='float64'):
        """Return empty time series with years as index with all years
        between min(year) and max(year) in index (no missing years)"""

        if isinstance(ts,pd.Series):
            years = set(ts.index.year)

        elif isinstance(ts,(list,set,np.ndarray)):
            years = set(ts)

        else:
            raise(f'{ts} must be list-like')

        minyear = min(years)
        maxyear= max(years)
        sr = Series(index=range(minyear,maxyear+1),dtype=dtype)
        return sr


    def vg3(self):
        """Return VG3 (Spring Level) for each year

        VG3 is calculated as the mean of groundwater head 
        levels on 14 march, 28 march and 14 april

        Return
        ------
        pd.Series


        Notes
        -----
        Calculation of GVG based on the average of three dates was 
        introduced by Finke et al. (1999)

        References
        ----------
        Finke, P.A., D.J. Brus, T. Hoogland, J. Oude Voshaar, F. de Vries
        & D. Walvoort (1999). Actuele grondwaterinformatie 1:10.000 in de
        waterschappen Wold en Wieden en Meppelerdiep. Gebruik van digitale 
        maaiveldshoogtes bij de kartering van GHG, GVG en GLG. SC-rapport
        633. (in Dutch).
        """

        self._vg3 = self._yearseries(self._ts1428)
        for i,year in enumerate(self._vg3.index):

            v1 = self._ts1428[dt.datetime(year,3,14)]
            v2 = self._ts1428[dt.datetime(year,3,28)]
            v3 = self._ts1428[dt.datetime(year,4,14)]

            with warnings.catch_warnings():
                # numpy raises a silly warning with nanmean on NaNs
                warnings.filterwarnings(action='ignore', 
                    message='Mean of empty slice')
                self._vg3[year] = round(np.nanmean([v1,v2,v3]),2)

        self._vg3.name = 'VG3'
        return self._vg3


    def vg1(self,refdate=VGREFDATE,maxlag=7):
        """Return VG (Spring Level) for each year as the measurement
        closest to refdate

        Parameters
        ----------
        refdate : {'apr1','apr15','mar15'}, default 'apr1'
            reference date for estimating VG

        maxlag : number
            maximum allowed difference between measurement date en refdate


        Return
        ------
        pd.Series 

        Notes
        -----
        The VG (Voorjaars  Grondwaterstand, Spring Level) is estimated as 
        the single measurement closest to the reference date given by 
        refdate.

        The reference date for calculation of the GVG was changed from
        april 15 to april 1st in de early eighties. In 2000 the 
        Cultuurtechnisch Vademecum proposed march 15 as the new reference 
        date for the GVG but this proposal was not generally adopted.
        In practice april 1st is allways used as reference date and this 
        is used as default for calculations.

        References
        ----------
        Van der Gaast, J.W.J., H.Th.L. Massop & H.R.J. Vroon (2009). Actuele
        grondwaterstandsituatie in natuurgebieden. Rapport 94 WOT. Alterra,
        Wageningen. (in Dutch).
        """

        if refdate not in self.VGDATES:
            warnings.warn((f'Reference date {refdate} for GVG is not '
                f'recognised. Reference date \'{self.VGREFDATE}\' is '
                f'assumed.'))
            refdate = self.VGREFDATE

        vg1 = self._yearseries(self._ts1428)
        for i,year in enumerate(vg1.index):

            if refdate=='apr1':
                date = dt.datetime(year,4,1)
            if refdate=='apr15':
                date = dt.datetime(year,4,15)
            if refdate=='mar15':
                date = dt.datetime(year,3,15)

            daydeltas = self._ts.index - date
            mindelta = np.amin(np.abs(daydeltas))
            sr_nearest = self._ts[np.abs(daydeltas) == mindelta]

            maxdelta = pd.to_timedelta(f'{maxlag} days')
            if (mindelta <= maxdelta):
                vg1[year] = round(sr_nearest.iloc[0],2)

        vg1.name = f'VG{refdate}'
        return vg1


    def xg(self):
        """Return table of GxG groundwater statistics for each 
        hydrological year

        Return
        ------
        pd.DataFrame"""

        if hasattr(self,'_xg'):
            return self._xg

        hydroyears = aq.hydroyear(self._ts1428)
        sr = self._yearseries(hydroyears)
        self._xg = pd.DataFrame(index=sr.index)

        for year in self._xg.index:

            ts = self._ts1428[hydroyears==year]
            ts = ts[ts.notnull()]
            n1428 = round(len(ts))

            hg3 = np.nan
            lg3 = np.nan

            if n1428 >= self.N14:

                hg3 = ts.nlargest(n=3).mean()
                lg3 = ts.nsmallest(n=3).mean()

            hg3w = np.nan
            lg3s = np.nan

            if n1428 >= self.N14:

                ts_win = ts[aq.season(ts)=='winter']
                ts_sum = ts[aq.season(ts)=='summer']

                hg3w = ts_win.nlargest(n=3).mean()
                lg3s = ts_sum.nsmallest(n=3).mean()

            self._xg.loc[year,'hg3'] = round(hg3,2)
            self._xg.loc[year,'lg3'] = round(lg3,2)
            self._xg.loc[year,'hg3w'] = round(hg3w,2)
            self._xg.loc[year,'lg3s'] = round(lg3s,2)
            self._xg['vg3'] = self.vg3()

            for date in self.VGDATES:
                self._xg[f'vg_{date}'] = self.vg1(refdate=date)

            self._xg.loc[year,'n1428'] = n1428

        self._xg['measfrq'] = aq.measfrq(self._ts)

        return self._xg


    def gxg(self, minimal=False, reflev='datum'):
        """Return table with GxG for one head series

        Parameters
        ----------
        minimal : bool, default True
            return minimal selection of stats

        reflev : {'datum','surface'}, default 'datum'
            reference level for gxg statistics

        Return
        ------
        pd.DataFrame"""

        """
        if hasattr(self,'_minimal'):
            if self._minimal!=minimal:
                self._reset()
        self._minimal = minimal

        if self._reflev==reflev:
            if hasattr(self,'_gxg'):
                return self._gxg
        else:
            self._reset()
            self._validate_reflev (reflev)
        """

        if not hasattr(self,'_xg'):
            self._xg = self.xg()

        if reflev is None:
            reflev = self.REFERENCE[0]
            warnings.warn((f'Reference level \'None\' is not allowed. '
                f'Reference level {reflev} is assumed.'))

        gxg = pd.Series(name=self.srname)
        for col in self._xg.columns:
            sr = self._xg[col][self._xg[col].notnull()]

            if col=='measfrq':
                gxg[col] = aq.maxfrq(sr)
                continue

            if reflev=='datum':
                gxg[col] = round(sr.mean(),2)

            if reflev=='surface':
                gxg[col] = round(sr.mean()*100)

            if col=='n1428':
                gxg[col] = round(sr.mean())

        # calculate gt
        if reflev=='surface':
            gxg['gt'] = self.gt()

            for apx in self.APPROXIMATIONS:
                rowname = 'gvg_'+apx.lower()
                gxg[rowname] = self.gvg_approximate(apx)

        gxg['reflev'] = reflev

        # calculate std
        for col in self._xg.columns:

            if col in ['n1428','measfrq']:
                continue

            if reflev=='datum':
                gxg[col+'_std'] = np.round(self._xg[col].std(
                    skipna=True),2)

            elif reflev=='surface':
                sr = self._xg[col]*100
                gxg[col+'_std'] = np.round(sr.std(skipna=True))

            else:
                raise ValueError((f'Reference level {reflev} is not valid.',
                    f'Valid reference levels are {self.REFERENCE}'))

        # calculate standard error
        for col in self._xg.columns:

            if col in ['n1428',]:
                continue

            if col=='measfrq':
                maxfreq = aq.maxfrq(self._xg[col])
                gxg[col] = maxfreq
                continue

            if reflev=='datum':
                sr = self._xg[col]
                gxg[col+'_se'] = np.round(sr.std(skipna=True
                    )/np.sqrt(sr.count()),2)

            if reflev=='surface':
                sr = self._xg[col]*100
                gxg[col+'_se'] = np.round(sr.std(skipna=True
                    )/np.sqrt(sr.count()),0)

        # count nyears
        for col in self._xg.columns:

            if col in ['n1428','measfrq']:
                continue

            sr = self._xg[col][self._xg[col].notnull()]
            gxg[f'{col}_nyrs'] = np.round(sr.count())


        replacements = [('hg3','ghg'),('lg3','glg'),('vg','gvg'),
            ('measfrq','maxfrq')]
        for old,new in replacements:
            gxg.index = gxg.index.str.replace(old,new)
        self._gxg = gxg        

        if minimal:
            colnames = ['ghg','glg','gvg3','gvg_apr1','gt','reflev','n1428',]
            gxg = gxg[self._gxg.index.intersection(colnames)]

        return gxg


    def ghg(self):
        """Return mean highest level (GHG)"""

        if not hasattr(self,'_gxg'):
            self._gxg = self.gxg()

        return self._gxg['ghg']


    def glg(self):
        """Return mean highest level (GHG)"""

        if not hasattr(self,'_gxg'):
            self._gxg = self.gxg()

        return self._gxg['glg']


    def gt(self):
        """Return groundwater class table as str"""

        if not hasattr(self,'_xg'):
            self._xg = self.xg()

        # do not call self._gxg to avoid recursion error because gt() 
        # is used in gxg()
        ghg = np.nanmean(self._xg['hg3'])*100
        glg = np.nanmean(self._xg['lg3'])*100

        if 1: #self._reflev=='datum':
            ghg = self._surflevel-ghg
            glg = self._surflevel-glg            

        if (ghg<0.20) & (glg<0.50):
            return 'I'

        if (ghg<0.25) & (0.50<glg<0.80):
            return 'II'

        if (0.25<ghg<0.40) & (0.50<glg<0.80):
            return 'II*'

        if (ghg<0.25) & (0.80<glg<0.120):
            return 'III'

        if (0.25<ghg<0.40) & (0.80<glg<0.120):
            return 'III*'

        if (ghg>0.40) & (0.80<glg<0.120):
            return 'IV'

        if (ghg<0.25) & (glg>0.120):
            return 'V'

        if (0.25<ghg<0.40) & (glg>0.120):
            return 'V*'

        if (0.40<ghg<0.80) & (glg>0.120):
            return 'VI'

        if (0.80<ghg<1.40):
            return 'VII'

        if (ghg>1.40):
            return 'VII*'

        return None
        # acer palmatum


    def gvg_approximate(self,formula=None):
        """Return GVG calculated with approximation based on GHG and GLG

        Parameters
        ----------
        formula : {'VDS82','VDS89pol','VDS89sto','RUNHAAR'}, default 'VDS82'

        Notes
        -----
        Values for GHG and GLG can be estimated from visual soil profile
        characteristics, allowing mapping of groundwater classes on soil
        maps. GVG unfortunately can not be estimeted is this way.
        Therefore, several regression formulas have been given in litera-
        ture for estimating GVG from GHG and GLG estimates. Three of them
        are implemented: Van der Sluijs (1982), Van der Sluijs (1989) and
        Runhaar (1989)"""


        if formula is None:
            formula = self.APPROXIMATIONS[0]

        if formula not in self.APPROXIMATIONS:
            warnings.warn(f'GVG approximation formula name {formula} not'
                f'recognised. {self.APPROXIMATIONS[0]} is assumed.')

        if not hasattr(self,'_xg'):
            self._xg = self.xg()

        if formula in ['SLUIS89pol','SLUIS89sto']:
            GHG = np.nanmean(self._xg['hg3w'])*100 # must be in cm
            GLG = np.nanmean(self._xg['lg3s'])*100 # ...
        else:
            GHG = np.nanmean(self._xg['hg3'])*100 # must be in cm
            GLG = np.nanmean(self._xg['lg3'])*100

        if 1: #self._ref=='datum':
            GHG = self._surflevel*100-GHG
            GLG = self._surflevel*100-GLG

        if formula=='HEESEN74': # april 15th
            GVG = 0.2*(GLG-GHG)+GHG+12

        elif formula=='SLUIJS76a': # april 14th
            GVG = 0.15*(GLG-GHG)+(1.01*GHG)+14.3

        elif formula=='SLUIJS76b': # april 14th
            GVG = 1.03*GHG+27.3

        elif formula=='SLUIJS82': 
            GVG = 5.4 + 1.02*GHG + 0.19*(GLG-GHG)

        elif formula=='RUNHAAR89':
            GVG = 0.5 + 0.85*GHG + 0.20*GLG # (+/-7,5cm)

        elif formula=='SLUIJS89pol':
            GVG = 12.0 + 0.96*GHG + 0.17*(GLG-GHG)

        elif formula=='SLUIJS89sto':
            GVG = 4.0 + 0.97*GHG + 0.15*(GLG-GHG)

        elif formula=='GAAST06':
            GVG = 13.7 + 0.70*GHG + 0.25*GLG

        else:
            raise ValueError((f'\'{formula}\' was not recognised as a gvg '
                f'approximation formula. Valid names are '
                f'{self.APPROXIMATIONS}'))

        return np.round(GVG)

