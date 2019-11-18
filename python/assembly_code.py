#!/usr/bin/env python
# coding: utf-8

# # To do:
# * add in weighting option
# * add function that bypasses the codebook to find variables based off search terms
# * automatic variable cleaning?
# * clean up existing functions

################### import packages ##########################################
import pandas as pd
import re
import numpy as np
import os
from hrs_functions import *
import copy 
import fnmatch
get_ipython().run_line_magic('load_ext', 'line_profiler')
pd.set_option('display.max_columns', None)

##############################################################################
####### Parameters and codebook variables ####################################
##############################################################################

output_file_name = 'all_data.csv'

################# make sure these are all lowercase!!! #######################
# for HRS core files, 2002 - present
variables_to_look_for = { 'a500':'rmonth_survey'
                         , 'a501':'ryear_survey'
                         , 'p014':'rpr_lose_job'
                         , 'lb032_2':'rrisk_financial'
                         , 'n106':'rhosp_cost_oop'}

# for HRS core files, pre 2002
# 2000 has g's, 1998 has f's, 1996 has e's, 1994 has w's, 1992 has v's
variables_to_look_for_pre_2002 = {
      'g775': 'rmonth_survey'
    , 'f704': 'rmonth_survey'
    , 'e391': 'rmonth_survey'
    , 'w120': 'rmonth_survey'
    , 'v128': 'rmonth_survey'
    , 'g774': 'ryear_survey'
    , 'f703': 'ryear_survey'
    , 'e393': 'ryear_survey'
    , 'w122': 'ryear_survey'
    , 'v127': 'ryear_survey'
    , 'g4996': 'rpr_lose_job'
    , 'f4583': 'rpr_lose_job'
    , 'e3788': 'rpr_lose_job'
    , 'w5801': 'rpr_lose_job' 
    , 'v3205': 'rpr_lose_job'    
}

# for CAMS core files
CAMS_variables = { 'b1': 'rauto_pur_f' 
                , 'b2': 'rrefrig_pur_f' 
                , 'b3': 'rwasherdrier_pur_f'
                , 'b4': 'rdishwasher_pur_f'
                , 'b5': 'rtv_pur_f'}

# for HRS Rand file, choose patterns
#* is a wildcard for wave, so gets it for all waves
hrs_patterns = ['r*mstat', 'r*agey_b', 'h*itot']

# for HRS Rand file, choose patterns
cams_patterns = ['h*ctots', 'h*cdurs', 'h*cndur', 'h*ctotc']

########################## file assembly ############################################
########################## HRS core files ############################################
## Assemble fat files
cwd = os.getcwd()
directory = cwd + '/data/HRS/'
years = [1992, 1994, 1996, 1998, 2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014, 2016]
output = read_all_years(years, directory, variables_to_look_for, variables_to_look_for_pre_2002)
output['hhidpn'] = output['HHID'] + output['PN']

########################## HRS Rand file ############################################
## Read and reshape HRS Rand data
# takes a 10-15 minutes to read because cant read this in a smart way
HRS_Rand = pd.read_stata(cwd + '/data/randhrs1992_2016v1_STATA/randhrs1992_2016v1.dta')

# need to make this long instead of wide
long_hrs_rand = reshape_rand(HRS_Rand, hrs_patterns)
long_hrs_rand['hhidpn'] = long_hrs_rand['hhidpn'].apply(lambda x: str(x).zfill(9))
long_hrs_rand['wave'] = long_hrs_rand['wave'].astype(float)

########################## CAMS core files ############################################
## Assemble CAMS files
cwd = os.getcwd()
directory = cwd + '/data/CAMS/'
years = [2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017]
cams_output = read_all_years(years, directory, CAMS_variables, 'CAMS')
cams_output['hhidpn'] = cams_output['HHID'] + cams_output['PN']
cams_output['wave'] = cams_output['wave'] - 0.5 #CAMS wave matching

########################## CAMS Rand file ############################################
# # Read and reshape CAMS Rand data
# fast, small file
CAMS_Rand = pd.read_stata(cwd + '/data/randcams_2001_2017v1/randcams_2001_2017v1.dta')

# need to make this long instead of wide
long_cams_rand = reshape_rand(CAMS_Rand, cams_patterns)
long_cams_rand['hhidpn'] = long_cams_rand['hhidpn'].apply(lambda x: str(x).zfill(9))
long_cams_rand['wave'] = long_cams_rand['wave'].astype(float)


########################### Join data sources ###########################################
### join HRS core with HRS Rand

# hrs core files have 236962 rows
# hrs rand file has 546689 rows
# this is because the rand file has everyone for every year even if they didnt participate that year
# inner join has 236595 so something is up here
    # my guess is that because rand variables are made up of many variables
    # some people who participated didnt include all vars
    # and therefore dont have these rand variables so inner join is smaller
HRS_Core_and_Rand = output.merge(long_hrs_rand, on = ['hhidpn', 'wave'], how = 'outer')

## join HRS core and HRS Rand with CAMS Rand
# outer join because cams has fewer waves
HRS_Core_and_Rand_and_RANDCAMS = HRS_Core_and_Rand.merge(long_cams_rand, on = ['hhidpn', 'wave'], how = 'outer')

## join HRS core and HRS Rand and CAMS Rand with CAMS core
All_data = HRS_Core_and_Rand_and_RANDCAMS.merge(cams_output, on = ['hhidpn', 'wave'], how = 'outer')

# write to csv
All_data.to_csv(output_file_name, index = False)

