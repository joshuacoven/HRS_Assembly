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
pd.set_option('display.max_columns', None)

##############################################################################
####### Parameters and codebook variables ####################################
##############################################################################

output_file_name = 'all_data.csv'

################# make sure these are all lowercase!!! #######################
# for HRS core files, 2002 - present
variables_to_look_for = { 'a500':'rmonth_survey'
                         , 'a501':'ryear_survey'

                        ## race variables
                        , 'b028': 'hispanic'
                        , 'b020m1m': 'type_hispanic'
                        , 'b089m1m': 'race'

                        ## expectation variables
                         #, 'p014':'rpr_lose_job'
                         #, 'lb032_2':'rrisk_financial'
                         #, 'n106':'rhosp_cost_oop'

                         ## home value expectation variables
                         , 'p197': 'home_value_x_percent_fill_2016'
                         , 'p170': 'home_value_x_percent_fill_pre_2016'
                         , 'p168': 'rpr_home_value_x_percent'

                         , 'p196': 'home_value_change_fill'
                         , 'p166':'rpr_home_value_change'

                         , 'p167': 'epistemic_home_value'
                         , 'p169': 'epistemic_assignment'
                         
                         # test for housing survey
                         , 'h004': 'own_or_rent_home'
                         # for anything 
                         , 'pn_fin': 'PN_FIN'
                         , 'pn_fam': 'PN_FAM'
                         , 'pn_cs': 'PN_CS'
                          }

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
    #, 'g4996': 'rpr_lose_job'
    #, 'f4583': 'rpr_lose_job'
    #, 'e3788': 'rpr_lose_job'
    #, 'w5801': 'rpr_lose_job' 
    #, 'v3205': 'rpr_lose_job'  
    #   
}

# for CAMS core files
CAMS_variables = {# 'b1': 'rauto_pur_f' 
                #, 'b2': 'rrefrig_pur_f' 
                #, 'b3': 'rwasherdrier_pur_f'
                #, 'b4': 'rdishwasher_pur_f'
                #, 'b5': 'rtv_pur_f'
                }

# for HRS Rand file, choose patterns
#* is a wildcard for wave, so gets it for all waves
hrs_patterns = ['s*racem'
                , 'r*racem'
                #'r*mstat'
                #, 'r*agey_b'
                #, 'h*itot'
                ]

# for HRS Rand file, choose patterns
cams_patterns = [#'h*ctots'
                #, 'h*cdurs'
                #, 'h*cndur'
                #, 'h*ctotc'
                ]

########################## file assembly ############################################
########################## HRS core files ############################################
## Assemble fat files
cwd = os.getcwd()
directory = cwd + '/data/HRS/'
years = [1992, 1994, 1996, 1998, 2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014, 
         2016, 2018]
output = read_all_years(years, directory, variables_to_look_for, variables_to_look_for_pre_2002)
output['hhidpn'] = output['HHID'] + output['PN']
print(output.groupby('wave').count())

########################## HRS Rand file ############################################
## Read and reshape HRS Rand data
# takes a 10-15 minutes to read because cant read this in a smart way
if len(hrs_patterns) > 0:
    HRS_Rand = pd.read_stata(cwd + '/data/randhrs1992_2016v2_STATA/randhrs1992_2016v2.dta')

    # need to make this long instead of wide
    long_hrs_rand = reshape_rand(HRS_Rand, hrs_patterns)
    long_hrs_rand['hhidpn'] = long_hrs_rand['hhidpn'].apply(lambda x: str(x).zfill(9))
    long_hrs_rand['wave'] = long_hrs_rand['wave'].astype(float)

########################## CAMS core files ############################################
## Assemble CAMS files
if len(CAMS_variables) > 0:
    directory = cwd + '/data/CAMS/'
    years = [2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017]
    cams_output = read_all_years(years, directory, CAMS_variables, 'CAMS')
    cams_output['hhidpn'] = cams_output['HHID'] + cams_output['PN']
    cams_output['wave'] = cams_output['wave'] - 0.5 #CAMS wave matching

########################## CAMS Rand file ############################################
# # Read and reshape CAMS Rand data
# fast, small file
if len(cams_patterns) > 0:
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

# all 4 file sources
if len(cams_patterns)*len(hrs_patterns)*len(CAMS_variables) > 0:
    HRS_Core_and_Rand = output.merge(long_hrs_rand, on = ['hhidpn', 'wave'], how = 'outer')
    #print(HRS_Core_and_Rand)
    ## join HRS core and HRS Rand with CAMS Rand
    # outer join because cams has fewer waves
    HRS_Core_and_Rand_and_RANDCAMS = HRS_Core_and_Rand.merge(long_cams_rand, on = ['hhidpn', 'wave'], how = 'outer')
    #print(HRS_Core_and_Rand_and_RANDCAMS)
    
    ## join HRS core and HRS Rand and CAMS Rand with CAMS core
    All_data = HRS_Core_and_Rand_and_RANDCAMS.merge(cams_output, on = ['hhidpn', 'wave'], how = 'outer')
    #print(All_data)
    
    # write to csv
    All_data.to_csv(output_file_name, index = False)

# only 2 file sources
elif (len(hrs_patterns) > 0) & (len(cams_patterns)*len(CAMS_variables) == 0):
    HRS_Core_and_Rand = output.merge(long_hrs_rand, on = ['hhidpn', 'wave'], how = 'outer')
    #print(HRS_Core_and_Rand.groupby('wave').count())
    HRS_Core_and_Rand.to_csv(output_file_name, index = False)

# only 1 file source
else:
    #print(output)
    output.to_csv(output_file_name, index = False)

