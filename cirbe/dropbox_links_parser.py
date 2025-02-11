import logging 

from bs4 import BeautifulSoup, SoupStrainer


def parse_links(local_htm_file ='./cirbe/htms/CIRBE_REPTile-2_L1_v1 - Dropbox.htm', 
                output_txt_file = './cirbe/htms/CIRBE_REPTile-2_L1_v1.txt'):
    """
    Function that creates .txt file of links to files in dropbox folder.
    This function is specifically created to help load CIRBE files
    from https://lasp.colorado.edu/cirbe/data-products/
    """
    with open(local_htm_file, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser', parse_only=SoupStrainer('a'))
        link_array = [x['href'] for x in soup if x.has_attr('href') and x['href'][-4:]=='dl=0']
    link_array = [x[:-1]+'1' for x in link_array]
    with open(output_txt_file, 'w') as fw:
        for line in link_array:
            fw.write(line+'\n')
    logging.info(f"{len(link_array)} links are saved in {output_txt_file}")
    
