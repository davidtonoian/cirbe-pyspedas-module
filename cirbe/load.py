import numpy as np
import pyspedas

#pyspedas.load dependencies
import logging 

from pyspedas.utilities.dailynames import dailynames
# from pyspedas.utilities.download import download
from pyspedas.utilities.download import download_file
from pytplot import time_clip as tclip
from pytplot import netcdf_to_tplot

from .config import CONFIG

#download.py dependencies
import os

#xr for temporary epoch fix
import xarray as xr
#hide dropbox certificate warningss
import urllib3
urllib3.disable_warnings()


def load(trange=['2024-09-21', '2024-09-22'],
         level='l1', 
         suffix='', 
         version = 'v2',
         downloadonly=False, #not yet implemented
         notplot=False, #not yet implemented
         no_update=False,
         time_clip=False,
         force_download=False):
    """
    This function loads data from the CIRBE mission dropbox folder and return
    the list of loaded variables.
    Not supposed to be called by the user.
    """
    #pathformat here provides only part of the name of the file instead of the path
    pathformat =   f'CIRBE_REPTile-2_{level.upper()}_%Y%m%d{version.lower()}'

    # find the full remote path names using the trange
    remote_names_part = dailynames(file_format=pathformat, trange=trange)

    out_files = []

    #Instead of #files = download() 
    # 1) load remote names according to dropbox scaping file
    ## files = download(remote_file=remote_names, remote_path=CONFIG['remote_data_dir'], local_path=CONFIG['local_data_dir'], no_download=no_update, last_version=True, force_download=force_download)
    files =[]
    remote_names= []
    with open(f'./cirbe/htms/CIRBE_REPTile-2_{level.upper()}_{version.lower()}.txt', 'r') as f:
        for line in f:
            for name in remote_names_part:
                if name in line:
                    remote_names +=[line[:-1]] #copy link
                    files +=[line[line.find(name):(line.find(name)+len(name)+5)]]
                    
    # 2) load files from links 
    for url, name in zip(remote_names, files):
        filename = os.path.join(CONFIG['local_data_dir'], name)
        download_file(
                      url=url,
                      filename=filename,
                      # username=username,
                      # password=password,
                      # verify=verify,
                      # headers=headers,
                      # session=session,
                      # basic_auth=basic_auth,
                      # text_only=text_only,
                      force_download=force_download
                     )
    # 3) create copy of the files with fixed Epoch attribute
    for name in files:
        filename = os.path.join(CONFIG['local_data_dir'], name)
        #fixing Epoch variable attribute including "UTC" where it should not
        try:
            data = xr.load_dataset(filename)
            if data.Epoch.attrs['UNITS'][:3] == 'UTC':
                logging.info("Fixing 'Epoch' variable for "+filename)
                data.Epoch.attrs['UNITS'] = data.Epoch.attrs['UNITS'][4:]
                out_files.append(f"{filename[:-3]}_fixepoch.nc")
                data.to_netcdf(out_files[-1])
                logging.info(f"Saved in {out_files[-1]}")
            else:
                logging.info("No 'UTC' in the 'Epoch' attribute or it was already removed.")
        except:
            logging.warning(f"Cannot open file {name} to fix epoch. Either it is already fixed or there is some other problem")

    if not files:
        logging.error(f"CIRBE LOAD: NO netCDF FILE FOUND! check file {remote_names}")
    # else:
    #     for file in files:
    #         out_files.append(file)

    # out_files = sorted(out_files)
    
    if downloadonly:
        return out_files

    tvars = netcdf_to_tplot(out_files, suffix=suffix)

    # if notplot:
    #     return tvars

    if time_clip:
        for new_var in tvars:
            tclip(new_var, trange[0], trange[1], suffix='')

    return tvars


def reptile2(trange=['2024-09-21', '2024-09-22'],
             type = 'flux', 
             suffix='', 
             version = 'v2',
             downloadonly=False, #not yet implemented
             notplot=False, #not yet implemented
             no_update=False, #not yet implemented
             time_clip=False,
             force_download=False #not yet implemented
            ):
    """
    This function loads data from the CIRBE\REPTile-2 instrument and process it into electron spectra.

    Parameters for Load Routine
    ---------------------------
        trange : list of str
            Time range of interest [starttime, endtime]. Format can be
            ['YYYY-MM-DD','YYYY-MM-DD'] or ['YYYY-MM-DD/hh:mm:ss','YYYY-MM-DD/hh:mm:ss']
            Default: ['2022-08-19', '2022-08-19']

        type: str, optional
            Calibrated data type of L1 data. Only option 'flux' for now.

        version: str, optional.
            Version of L1 data. Options are 'v1' and 'v2'.
            Default: 'v2'.

        downloadonly: bool, optional
            Not implemented yet. If True, only downloads the CDF files without loading them into tplot variables. 
            Default: False.

        notplot: bool, optional
            Not implemented yet. If True, returns data in hash tables instead of creating tplot variables. 
            Default: False.

        no_update: bool
            Not implemented yet. If True, loads data only from the local cache.
            Default: False.

        time_clip: bool
            If True, clips the variables to the exact range specified in the trange. 
            Default: True.

        force_download: bool
            Not implemented yet. Download file even if local version is more recent than server version
            Default: False
    
    
    Returns
    -------
        list of str
            List of tplot variables created.
    """

    tvars = load(trange=trange,
             level='l1', #correct since we are creating l1 data in this function
             suffix=suffix, 
             version = version,
             downloadonly=False, #not yet realised
             notplot=False, #not yet realised
             no_update=False, #not yet realised
             time_clip=time_clip,
             force_download=False
            )

    if type == 'flux':
        logging.info("CIRBE REPTile-2 L2: START PROCESSING.")
        
        t, ecounts = pyspedas.get_data('Ebins_RNG')
        _, inte_prd = pyspedas.get_data('IntePrd')
        #Bowtie matrix can be downloaded from CIRBE website
        bowtie_matrix = np.loadtxt("./cirbe/Bowtie_Matrix.csv", delimiter=",", skiprows = 1)
        gde = bowtie_matrix[:,2]
        energy = bowtie_matrix[:,1]
        channel = bowtie_matrix[:,0]

        etmp = ecounts/inte_prd[:,None]*1e3
        #Ebins_RNG: Counts for range electron channels 1:50 (or channels 61:110 for the combined channels)
        eflux = etmp/gde[None, (channel>60)&(channel<111)] #Ebins_RNG: Counts for range electron channels 1:50 (or channels 61:110 for the combined channels)

        pyspedas.store_data('cirbe_efluxe_adapted',data={'x':t, 'y':(eflux),'v':(energy[60:110])})
        pyspedas.options('cirbe_efluxe_adapted',opt_dict ={'spec': True,'yrange':[0.3,5.],'ystyle':1,'ylog':True,
                        'ytitle':'Energy [MeV]','zlog':True,
                        'zticklen':-0.5,
                        'zrange':[10,1e6],
                        'ztitle':'Flux\n[/cm^2/s/str/MeV]'})
        tvars += ['cirbe_efluxe_adapted']

    return tvars
