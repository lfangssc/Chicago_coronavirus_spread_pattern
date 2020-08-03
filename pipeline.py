#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:12:50 2020

@author: peterfang
"""

from __future__ import unicode_literals, print_function
import pandas as pd
import re
import time


"""
The objective of the script is to classify coronavirus patients of March/20 is\
caused by interntal travel or loacl communicty spread. If caused by local communicty spread\
where are the cases, and try to determine the geographical positions.

The data is extremly unstructured, need efforts on data cleaning and infomration retrivial\
Here we mainly use pandas, lambda function and regex. 

The most challenging work here is to engineering on the column "'OTHER INFORMATION (from officials or news stories)'"
which is one sentences or multiple sentences, need to split into individual one and anlayze.
Hard part is to to use program to understand the meaning of the sentences.
"""
#### function to split the column "'OTHER INFORMATION (from officials or news stories)'"to get the second sentences
def second_cent(x):
    try:
        x.split(".")[1]
    except Exception as e1:  
       return'no more information'
    else:
       return  x.split(".")[1]

#### function to search regex key words of travel, travel-related, traveling, no, not
#### based on the combination of the keywords, return "commnnity" or "travel"    
def travel_YesorNo(x):
    match1 = re.search(r'\bno\b',x)
    match2 = re.search(r'\btravel\b',x)
    match3 = re.search(r'\bnot\b',x)
    match4 = re.search(r'\btravel-related\b',x)
    match5 = re.search(r'\btraveled\b',x)
    match6 = re.search(r'\btraveling\b',x)
  
    if (match1 and match2):
        return "community"
    elif (match3 and match4):
        return "community"
    elif (match3 and match5):
        return "community"
    elif not (match2 or match4 or match5 or match6):
        return "community"
    else:
        return "travel"

##### function to determine the case whether come from China or Italy.    
def Abroad(x):
    yes='unknown'
    for c in x.split():
        if c=='china' or c=='italy':
           yes='abroad'
    return yes    

def travel_or_local():
    """
    main function to classify the coronavious cases as travel-related or local spread.
    """
    ##### convert date into unix time. calculate the day diffenence to the reported date of the first case
    df=pd.read_csv('./coronavirus/Chicago_coronavrius.csv')
    df['data_annouced']=df['DATE ANNOUNCED'].apply(lambda x: x[:-2]+'2020')
    df['data_annouced_unix']=df['data_annouced'].apply(lambda x: int(time.mktime(time.strptime(x, '%m/%d/%Y'))))
    df['data_annouced_unix_daydiff']=round((df['data_annouced_unix']-df['data_annouced_unix'].min())/(60*60*24))
    
    ######  "Other information" column has the most important information of the details of patient travel history and address
    ######  The data consists of multiple sentences, need seperate into individual sentences for analysis
    df['histroy']=df['OTHER INFORMATION (from officials or news stories)'].str.lower()
    
    df['histroy_1st_sentence']=df['histroy'].apply(lambda x:str(x).split(".")[0]).str.lower()
    
    df['histroy_2nd_sentence']=df['histroy'].apply(second_cent).str.lower()
    
    
    #######regex analysis to determine the trigger by travel or community spread.
    ####### The travel hisotry are recorded in the first or second sentences, need if-else logic to determine. 
    
    df['histroy_1st_YorN']=df['histroy_1st_sentence'].apply(travel_YesorNo)
    df['histroy_2nd_YorN']=df['histroy_2nd_sentence'].apply(travel_YesorNo)
    
    ########## Complicated data don't explicit state travel-related or community spread, instead recording "China" or "Italy"
    
    df['histroy_abroad']=df['histroy'].astype(str).apply(Abroad)
    
    df['histroy_compound']=df['histroy_1st_YorN'].map(str)+'_'+df['histroy_2nd_YorN'].map(str)+'_'+df['histroy_abroad'].map(str)
    
    df['histroy_result']=df['histroy_compound'].apply(lambda x: 'travel' if (x=='travel_community_unknown' or x=='community_travel_unknown' 
                                                                                     or x=='community_community_abroad' or x=='travel_travel_abroad'
                                                                                     or x=='travel_community_abroad' or x=='community_travel_abroad'
                                                                                     or x=='travel_travel_abroad') else 'community')
    
    #########drop data that has no details information.
    df=df[df['histroy']!='no details reported by public health officials or in news stories']
    
    df=df[['DATE ANNOUNCED','COUNTY','CITY','STATE','GENDER','AGE',
                                  'CONDITION','data_annouced','data_annouced_unix',
                                  'data_annouced_unix_daydiff','histroy','histroy_compound','histroy_result']].copy()

    return df


#################################################### join zipcode
def impute_join(df):
    df_zipcode=pd.read_csv('./coronavirus/zipcode.csv')
    df_mostlikely_city=pd.read_csv('./coronavirus/Chicago_coronavrius_mostlikely_city_final.csv')
    
    df_mostlikely_city=df_mostlikely_city[['City','County']].copy()
    df_mostlikely_city.rename(columns={'City': 'impute_city',
                                             'County': 'COUNTY'}, inplace=True)
    
    df_merge=pd.merge(df, df_mostlikely_city, how='left', on='COUNTY')
    
    
    df_zipcode=df_zipcode[['Zip','Latitude','Longitude']].copy()
    df_zipcode.rename(columns={'Zip': 'zipcode'}, inplace=True)
    
    df_merge=pd.merge(df_merge, df_zipcode, how='left', on='zipcode')
    
    ######### fillna use City Chicago longitude and latitude.
    df_merge['Latitude'].fillna(41.5904)
    df_merge['Longitude'].fillna(-88.0950)
    df_merge.to_csv('./coronavirus/Chicago_coronavrius_geo_info.csv', sep=',')
    

if __name__ == "__main__":
    df_case_category=travel_or_local()
    impute_join(df_case_category)

