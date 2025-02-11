import os

CONFIG = {'local_data_dir': 'cirbe_data/',
          'remote_data_dir': ''
          }

# override local data directory with environment variables
if os.environ.get('SPEDAS_DATA_DIR'):
    CONFIG['local_data_dir'] = os.sep.join([os.environ['SPEDAS_DATA_DIR'], 'cirbe/'])

if os.environ.get('ELFIN_DATA_DIR'):
    CONFIG['local_data_dir'] = os.environ['ELFIN_DATA_DIR']
    