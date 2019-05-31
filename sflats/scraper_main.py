import json
import pandas as pd
import time
import requests
import numpy as np
import re
import os
from collections import deque
from pandas.api.types import CategoricalDtype
from .Maply import plot_map
from .dist_Map import plot_district_map
from .graphs import allplots


class Flats:
    '''
    Main class used for scraping and analysis of flat market in Prague.

    Most useful methods:
    update: scrapes and updates/creates previous/new file
    load_dataset: Loads and partially cleans the dataset
    map: provides detailed map of every currently available flat with filtering
    district_map: provides aggregate statistics for city districts
    plots: provides most relevant plots 

    '''
    _t = time.strftime("%d-%m-%Y")

    def __init__(self, folder='.'):

        self.folder = folder
        if os.path.isfile(folder + '/scrape.csv'): # Check if the file exists, if it does check if it is up to date, warn user if it is not.
            self._uptodate()
        else:
            print('There is no database file, change the folder or call update method to create a new file.')

    def _uptodate(self):
        with open(self.folder + '/scrape.csv','r',encoding='utf8') as f:
            lastline = deque(f,1) # deque container is used as it is memory/cpu efficient in reading headers/tails of large files
            self.lastdate = str(list(lastline)[0])[-11:-1]
            if self.lastdate != self._t:
                print('Your database is outdated, consider calling update method. Latest record is from {}.'.format(self.lastdate))
                return(False)
            return(True)

    def update(self, verbosity=True, force_update=False):
        if (self._uptodate()) and (not force_update) :
            print('No need to update, database is up to date.')
            return 
        exists = os.path.isfile(self.folder + '/scrape.csv')
        #Check if there is previous scrape, if not set header
        if exists:
            flats = []
        else:
            flats = [['Type','Area','District','Street','GPS Lat','GPS Lon','Price','in_construction', 'after_reconstruction', 'terrace', 'metro', 'tram', 'train', 'atm', 'post_office', 'drugstore','sports', 'balcony','loggia','panel','furnished','partly_furnished','not_furnished','garage','collective','Labels','urlLoc','id','Date']]

        i = 0
        t = time.strftime("%d-%m-%Y")

        #These labels are from the json file, but we don't use labels which are not attributed to any flats
        allLabels = ['in_construction','after_reconstruction', 'terrace', 'metro', 'tram', 'train', 'atm', 'post_office', 'drugstore',
                    'sports','balcony','loggia','panel','furnished','partly_furnished','not_furnished','garage','collective']
                    
        Empty = False
        while not Empty:
            i += 1
            ls = requests.get("https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&locality_region_id=10&no_auction=1&page={}&per_page=60".format(i)).text
            ls = json.loads(ls)

            #Website returns skeleton json files after we go through all flats, therefore we check if there are any flats, if not we break the while statement
            if not ls['_embedded']['estates']:
                Empty = True 
            else:
                for obj in ls['_embedded']['estates']:
                    flat = []

                    name = obj['name'].split() # Name is always represented by string "Prodej bytu [type of flat] [Area] m^2"
                    flat.append(name[2]) # Type of a flat
                    flat.append(name[-2]) # Area

                    try:
                        flat.append(re.search('Praha \d?\d',obj['locality']).group(0)) # Regex search for city district 
                    except AttributeError:
                        flat.append('Praha') # if there is no specific district, we just use Praha

                    flat.append(obj['locality'].partition(',')[0].replace('ulice ',''))   #Partition adress string to get street name, then remove 'ulice ' which is redundant 
                    flat.append(obj['gps']['lat']) # save GPS location
                    flat.append(obj['gps']['lon'])
                    
                    flat.append(obj['price']) # Price


                    # We will add binary categories for every possible label
                    labels = obj['labelsReleased']
                    labels = [item for sublist in labels for item in sublist] # flattens the list of lists
                    for lab in allLabels:
                        if lab not in labels:
                            flat.append(0)
                        else:
                            flat.append(1)
                    flat.append(labels)

                    flat.append(obj['seo']['locality']) # Location used for URL construction
                    flat.append(obj['hash_id']) # unique ID
                    flat.append(t) # Date

                    #Add flat to the list
                    flats.append(flat)
            if verbosity:
                print("Iteration: {}".format(i)) # Show info during runtime
            time.sleep(9.5+np.random.normal(1,1)) # Wait ~10.5sec so we don't get banned 

        #Create dataframe out of list
        df = pd.DataFrame(flats)

        #Check if there is already scrape from previous runs, if not we edit df header
        if not exists:
            df.columns = df.iloc[0]
            df = df.drop(0)

        # Export to csv or append to previous scrape
        if exists:
            with open('scrape.csv','a',encoding='utf-8',newline='') as f:
                df.to_csv(f, header=False,index=False)
        else:
            df.to_csv('scrape.csv', encoding='utf-8',index=False)

    def load_dataset(self,remove_noprice=True, latest_only=False, remove_labels=False, verbosity=True):
        '''
        Loads dataset from 'scrape.csv' file

        Parameters:
        remove_noprice (bool): removes all flats with very low price, which often indicate that real price is not disclosed
        latest_only (bool): load only data from latest scrape
        remove_labels (bool): remove labels of flats such as metro availability, garage etc. which are mostly never filled 

        Returns:
        pandas.DataFrame object
        '''

        dataset = pd.read_csv(self.folder + '/scrape.csv', parse_dates=['Date'], infer_datetime_format=True)

        if latest_only:
            lastdate  = dataset.iloc[-1,:]['Date']
            dataset = dataset.loc[dataset['Date'] == lastdate, :]
            dataset = dataset.reset_index()

        #Remove flats with lower than 10m^2 area, just because its probably an error
        dataset = dataset[dataset.Area > 10]

        if remove_noprice:
            old_size = dataset.shape[0]
            dataset = dataset[dataset.Price > 10001]
            new_size = dataset.shape[0]
            if verbosity:
                print('Removed {} flats without price.'.format(old_size - new_size))
            
        if remove_labels:
            dataset = dataset[['Type','Area','District','Street','GPS Lat','GPS Lon','Price', 'urlLoc','id','Date']]

        # Set the type as ordered categorical variable 
        types = CategoricalDtype(categories=['1+kk','1+1','2+kk','2+1','3+kk','3+1','4+kk','4+1','5+kk','5+1','6','atypické'],ordered=True)
        dataset.Type = dataset.Type.astype(types)
        
        #Remove very rare flats with 0 area
        dataset = dataset[dataset['Area']>0]

        #Calculate price per m^2
        dataset['Ppm2'] = np.round(dataset.Price/dataset.Area,2)

        self.dataset = dataset
        return(self.dataset)

    def add_doc(value):
        def _doc(func):
            func.__doc__ = value
            return func
        return _doc

    @add_doc(plot_map.__doc__)
    def map(self):
        plot_map(self.load_dataset(remove_noprice = True, latest_only = False, remove_labels = True,verbosity = False), self.load_dataset(True,True,True,False))

    @add_doc(plot_district_map.__doc__)
    def district_map(self,color_by='None',latest_only=True):
        if latest_only:
            plot_district_map(self.load_dataset(True,True,True,False), color_by=color_by)
        else:
            plot_district_map(self.load_dataset(True,False,True,False), color_by=color_by)

    @add_doc(allplots.__doc__)
    def plots(self,quant=['Area','Price','Ppm2'],pie=True,flat_count=True,Ppm2_detail=True,flat_type=[]):
        allplots(self.load_dataset(True,False,True,False), quant=quant,pie=True, flat_count=flat_count, Ppm2_detail=Ppm2_detail,flat_type=flat_type)
