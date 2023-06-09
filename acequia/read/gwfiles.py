"""
Module with GwFiles object that holds a list of groundwater series
source filepaths.
"""

import os
import os.path
import warnings
from pandas import Series, DataFrame
import pandas as pd

from ..gwseries import GwSeries

class GwFiles:
    """Collection of groundwater head source files.
    
    Files with groundwater head data are read from a sourcefolder
    and can be iterated over returning GwSeries objects.
    Data can also be written to output directories as json or csv files 
    with "to_json" or "to_csv" methods.
    
    Examples
    --------
    >>> srcdir = <directory with dinoloket sourcefiles>
    >>> gwf = GwFiles.from_dinocsv(srcdir)
    >>> for gw in gwf.iteritems():
    ...     print(gw)
    >>> gwf.to_json(<outputdir>)
    ...
    """

    FILETBL_COLS = ['series', 'loc', 'fil', 'fname', 'fpath',]

    def __init__(self,filetbl):
        """Create a GwFiles object with class methods from_dinocsv, 
        from_json or from_csv.
        
        Examples
        --------
        >>> srcdir = <valid path to directory with dinoloket sourcefiles>
        >>> gwf = GwFiles.from_dinocsv(srcdir)
        ...
        """

        # test validity of filetbl
        if not isinstance(filetbl,DataFrame):
            raise ValueError((f'Argument filetbl must be {type(DataFrame())} '
                f'not {type(filetbl)}'))

        missing_cols = [col for col in self.FILETBL_COLS if col not in filetbl.columns]
        if missing_cols:
            raise ValueError(('Filetbl is missing required columns: '
                f'{missing_cols}.'))

        self.filetbl = filetbl

    def __len__(self):    
        return len(self.filetbl)

    def __repr__(self):
        return (f'{self.__class__.__name__} (n={len(self.filetbl)})')

    @classmethod
    def from_dinocsv(cls,srcdir,loclist=None):
        """Create GwFiles object from folder with DinoLoket sourcefiles.
        
        Parameters
        ----------
        srcdir : str
            Path to directory with Dinoloket csv sourcefiles.
        loclist : list, optional
            List of strings with valid location names to restrict
            number of files read from srcdir.
        """

        if not os.path.isdir(srcdir):
            raise ValueError(f'Directory {srcdir} does not exist')

        # table of filenames
        filenames = [fname for fname in os.listdir(srcdir) if fname.endswith('1.csv')]
        filetbl = pd.DataFrame({"fname":filenames})

        # add columns to filetbl
        filetbl["fpath"]= filetbl["fname"].apply(lambda x:srcdir+x)
        filetbl.insert(0,"loc",filetbl["fname"].apply(lambda x:x[0:8]))
        filetbl.insert(1,"fil",filetbl["fname"].apply(lambda x:x[8:11].lstrip("0")))
        filetbl.insert(0,"series",filetbl["loc"]+"_"+filetbl['fil'])

        if loclist is not None:
            mask = filetbl['loc'].isin(loclist)
            filetbl = filetbl[mask].reset_index(drop=True)

        return cls(filetbl)

    def iteritems(self):
        """Iterate over all series and return gwseries object."""
        for idx,row in self.filetbl.iterrows():
            gw = GwSeries.from_dinogws(row['fpath'])
            yield gw

    def to_json(self,dirpath):
        """Write all gwseries to json files.

        Parameters
        ----------
        dirpath : str
            Valid output directory for json files.

        Returns
        -------
        List of json objects.
        """
        jsonlist = []
        for gw in self.iteritems():
            jsonlist.append(gw.to_json(dirpath))
        return jsonlist

    def to_csv(self,dirpath):
        """Write all gwseries to json files.

        Parameters
        ----------
        dirpath : str
            Valid output directory for json files.

        Returns
        -------
        List of pandas series.
        """
        csvlist = []
        for gw in self.iteritems():
            csvlist.append(gw.to_csv(dirpath))
        return csvlist

    # Classmethods below are defined here to make sure input files have 
    # allready been created by code above.

    @classmethod
    def from_json(cls,srcdir,loclist=None):
        """Create GwFiles object from folder with json sourcefiles.
        
        Parameters
        ----------
        srcdir : str
            Path to directory with json GwSeries sourcefiles.
        loclist : list, optional
            List of strings with valid location names to restrict
            number of files read from srcdir.
        """

        if not os.path.isdir(srcdir):
            raise ValueError(f'Directory {srcdir} does not exist')

        # table of filenames
        filenames = [fname for fname in os.listdir(srcdir) if fname.endswith('.json')]
        filetbl = pd.DataFrame({"fname":filenames})

        # add columns to filetbl
        filetbl["fpath"]= filetbl["fname"].apply(lambda x:srcdir+x)
        filetbl.insert(0,"loc",filetbl["fname"].apply(lambda x:x.split('_')[0]))
        filetbl.insert(1,"fil",filetbl["fname"].apply(lambda x:x.split("_")[-1].lstrip("0")))
        filetbl.insert(0,"series",filetbl["loc"]+"_"+filetbl['fil'])

        if loclist is not None:
            mask = filetbl['loc'].isin(loclist)
            filetbl = filetbl[mask].reset_index(drop=True)

        return cls(filetbl)

    @classmethod
    def from_csv(cls,srcdir,loclist=None):
        """Create GwFiles object from folder with json sourcefiles.
        
        Parameters
        ----------
        srcdir : str
            Path to directory with GwSeries csv sourcefiles.
        loclist : list, optional
            List of strings with valid location names to restrict
            number of files read from srcdir.
        """

        if not os.path.isdir(srcdir):
            raise ValueError(f'Directory {srcdir} does not exist')

        # table of filenames
        filenames = [fname for fname in os.listdir(srcdir) if fname.endswith('.csv')]
        filetbl = pd.DataFrame({"fname":filenames})

        # add columns to filetbl
        filetbl["fpath"]= filetbl["fname"].apply(lambda x:srcdir+x)
        filetbl.insert(0,"loc",filetbl["fname"].apply(lambda x:x.split('_')[0]))
        filetbl.insert(1,"fil",filetbl["fname"].apply(lambda x:x.split("_")[-1].lstrip("0")))
        filetbl.insert(0,"series",filetbl["loc"]+"_"+filetbl['fil'])

        if loclist is not None:
            mask = filetbl['loc'].isin(loclist)
            filetbl = filetbl[mask].reset_index(drop=True)

        return cls(filetbl)





