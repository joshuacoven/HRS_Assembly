################### import packages #######################################################
import pandas as pd
import re
import numpy as np
import os
import hrs_functions
import copy
import fnmatch

## each survey for HRS core files (post 2000) has a letter preceeding variable names
## increases by 1 but skips i
var_dict = {
      2002: 'h'
    , 2004: 'j' # they skip i for some reason
    , 2006: 'k'
    , 2008: 'l'
    , 2010: 'm'
    , 2012: 'n'
    , 2014: 'o'
    , 2016: 'p' 
}

#################################### functions ####################################
# 3 functions for assembling HRS and CAMS core files
# 1st reads fixed with files with a SAS program statement
# 2nd does this for a whole year for given variables
# 3rd does this for all years

# 1 function for Rand files
# reshapes HRS Rand table into a long for given variable patterns

#################################### HRS and CAMS Core files ####################################
#################################### read_sas_fwf ####################################

## need a .sas program file as the dct
## need a .da data file as the filename
## only reads specified variables from fwf, saves a lot of time

# input types:
# dct_file : string
# filename : string
# variables_to_look_for : dictionary
# survey year: int

def read_sas_fwf(dct_file, filename, variables_to_look_for, survey_year):
    # get relevant variables
    id_vars = ['hhid', 'pn']
    if survey_year < 2001:
        survey_specific_variables = [x for x in variables_to_look_for]
    elif (survey_year % 2) == 1:
        survey_specific_variables = [x + '_' + str(survey_year)[2:4] for x in variables_to_look_for]
    else:
        survey_specific_variables = [var_dict[survey_year] + x for x in variables_to_look_for]
    # parse the .sas file for relevant lines
    lines = []
    colons = []
    with open(dct_file) as f:
        lines = f.readlines()
    for i in range(len(lines)):
        if 'INPUT' in lines[i]:
            cols_start = i
        if 'LABEL' in lines[i]:
            names_start = i
        if ';' in lines[i]:
            colons.append(i)
    cols_end = [x for x in colons if x > cols_start and x < names_start][0]
    names_end = [x for x in colons if x > names_start][0]
    dictionary = lines[cols_start + 1: cols_end]
    colspecs = []
    test_dict = {}
    names = []
    
    # parse the relevant lines into outputs necessary for pd.read_fwf
    for i in dictionary:
        # all of these different comprehensions standardize the differences in sas files over the years
        temp = i.lstrip().split(' ')
        temp = [x.replace('\n', '').split('-') for x in temp]
        temp = [item for sublist in temp for item in sublist] # flatten the list
        temp = [i for i in temp if i]                         # removes empty strings
        if any([temp[0].lower() == y for y in id_vars + survey_specific_variables]):
            names.append(temp[0])
            if temp[1] == '$':
                var = str
                colspecs.append([int(temp[2]) - 1, int(temp[3])])
            else:
                var = float
                colspecs.append([int(temp[1]) - 1, int(temp[2])])
            # need the test_dict because fwf needs to know the datatype of each col
            test_dict[temp[0]] = var    
    return pd.read_fwf(filename, colspecs=colspecs, names = names, converters = test_dict)


#################################### HRS Core files ####################################
#################################### sas_read_year ####################################

# this is an extension of the read_sas_fwf function
# for a given directory and desired variables, will automatically find the right files to read

# input types: 
# directory : string
# variables_to_look_for : dictionary
# survey_year : int
# variables_to_look_for_pre_2002 : dictionary

def sas_read_year(directory, variables_to_look_for, survey_year, variables_to_look_for_pre_2002):
    # list all files to potentially read
    directory_sas = directory + 'h' + str(survey_year)[2:4] + 'sas'
    directory_da = directory + 'h' + str(survey_year)[2:4] + 'da'
    if variables_to_look_for_pre_2002 == 'CAMS':
        # 2001 has a different directory name
        if survey_year == 2001:
            directory_sas = directory + 'cams' + str(survey_year)[2:4]
            directory_da = directory_sas
        # 2009 has a different directory structure
        elif survey_year == 2009:
            directory_sas = directory + 'cams' + str(survey_year) + '/sas'
            directory_da = directory + 'cams' + str(survey_year) + '/data'
        else:
            directory_sas = directory + 'cams' + str(survey_year)
            directory_da = directory_sas
    if (survey_year < 1996) or (variables_to_look_for_pre_2002 == 'CAMS'):
        path_list = list(set([directory_sas + '/' +  x.split('.')[0] for x in os.listdir(directory_sas) 
                              if ('sas' in x or 'SAS' in x)
                             ]))
    else:
        path_list = list(set([directory_sas + '/' +  x.split('.')[0] for x in os.listdir(directory_sas) 
                              if ('sas' in x or 'SAS' in x)
                              and 'R' in x[len(x.split('.')[0])-1]
                             ]))
    # earlier than 2000, need to read all surveys
    # earlier than 2000 cant tell from var name which survey it's in, different naming conventions
    # after 2000, can take advantage of naming conventions
    # after 2000, only reads files with desired variables to save a lot of time
    if (survey_year < 2001) or (variables_to_look_for_pre_2002 == 'CAMS'):
        # for 1992 and 1994, the order it reads them in is important
        # needs to read a R level one first or else will not read any others in the time period
        # sorting it works
        path_short_list = sorted(path_list)
    else:
        # figure out which surveys to read based on variables to look for
        surveys = [x[0] for x in variables_to_look_for]\
            + [x[0:2] for x in variables_to_look_for if 'lb' in x]

        # find the surveys in the path list
        path_short_list = [x for x in path_list if 'r' in x.split('/')[9].lower() # only get respondent
                           and any(
                               y == x.split('/')[9].lower()[3:len(x.split('/')[9]) - 2] 
                               for y in surveys
                           ) 
                          ]
    
    # these are the id's for all R level surveys in all years
    id_variables = ['hhid', 'pn']
    
    # each survey has different leading letter on each of it's variables
    # this is not the case in 2000 and earlier
    # in 2000 and earlier, a variable doesnt even have the same number
    # need to be extra explicit in the variables_to_look_for
    if survey_year < 2001:
        survey_specific_variables = [x for x in variables_to_look_for_pre_2002]
        # for renaming variables
        rename_dict = copy.deepcopy(variables_to_look_for_pre_2002)
        vars_list = [x for x in variables_to_look_for_pre_2002]
    elif variables_to_look_for_pre_2002 == 'CAMS':
        survey_specific_variables = [x + '_' + str(survey_year)[2:4] for x in variables_to_look_for]
        # for renaming variables
        rename_dict = copy.deepcopy(variables_to_look_for)
        vars_list = [x for x in variables_to_look_for]
    else:
        survey_specific_variables = [var_dict[survey_year] + x
                                 for x in variables_to_look_for]
        # for renaming variables
        rename_dict = copy.deepcopy(variables_to_look_for)
        vars_list = [x for x in variables_to_look_for]
    
    print('looking for variables: ' + str(survey_specific_variables))
    
    for x in range(len(survey_specific_variables)):
        rename_dict[survey_specific_variables[x].upper()] = rename_dict.pop(vars_list[x])
    
    # read the files
    for i in range(len(path_short_list)):
        path = path_short_list[i]
        print(path)
        if survey_year < 2001:
            dct_file = directory_sas + '/' + path.split('/')[9] +  '.SAS' #in the year 2000, files are .SAS and not .sas
            filename = directory_da + '/' + path.split('/')[9] + '.da'
            temp_df = read_sas_fwf(dct_file, filename, variables_to_look_for_pre_2002, survey_year)
        else:
            if survey_year == 2009:
                dct_file = directory_sas + '/' + path.split('/')[10] +  '.sas'
                filename = directory_da + '/' + path.split('/')[10] + '.da'
            else:
                dct_file = directory_sas + '/' + path.split('/')[9] +  '.sas'
                filename = directory_da + '/' + path.split('/')[9] + '.da'
            temp_df = read_sas_fwf(dct_file, filename, variables_to_look_for, survey_year)
        temp_df = temp_df[[x for x in temp_df.columns if x.lower() in (id_variables + survey_specific_variables)]]
        temp_df = temp_df.rename(columns = rename_dict)
        if i == 0:
            year_frame = temp_df
        else:
            try:
                year_frame = year_frame.merge(temp_df, on = ["HHID", "PN"], how = "outer")
            except:
                print('this is a pre-1996 household survey, so exclude') # pre-1996 some surveys wont have a PN

    # make the wave variable, 1992 was wave 1
    wave = (survey_year - 1990) / 2
    year_frame['wave'] = wave
    return year_frame


#################################### HRS Core files ####################################
#################################### read_hrs_all_years ####################################

# this is an extension of the sas_read_year function to work across multiple years
# for all years specified, gets all variables specified from the HRS core files

# input types:
# years :  list
# directory : string
# variables_to_look_for : dictionary
# variables_to_look_for_pre_2002 : dictionary

def read_hrs_all_years(years, directory, variables_to_look_for, variables_to_look_for_pre_2002):
    for i in range(len(years)):
        yr = years[i]
        print('reading files for survey year: ' + str(yr))
        if i == 0:
            final_frame = sas_read_year(directory, variables_to_look_for, yr, variables_to_look_for_pre_2002)
        else:
            temp_df = sas_read_year(directory, variables_to_look_for, yr, variables_to_look_for_pre_2002)
            final_frame = final_frame.append(temp_df, sort = False)
        if yr == 1992:
            final_frame = final_frame.drop_duplicates().reset_index(drop = True) #1992 may have a duplicate problem
        print('\n')
    return final_frame.reset_index(drop = True)


#################################### RAND Files ##############################################
#################################### reshape_rand ####################################

# this reshapes the HRS Rand & CAMS Rand data files from wide to long, for desired variables called "patterns"

def reshape_rand(HRS_Rand, patterns):
    col_list = list(HRS_Rand.columns)
    id_columns = ['hhidpn']
    short_list = []
    for pat in patterns:
        short_list = short_list + fnmatch.filter(col_list, pat)

    # get only columns that will go into final output
    HRS_Rand_small = HRS_Rand[id_columns + short_list]

    # index the data based off of ID columns
    indexed_df = HRS_Rand_small.set_index('hhidpn')

    # Stack the columns to achieve the baseline long format for the data
    stacked_df = indexed_df.stack(dropna=False)

    # Now do a reset index to numeric, we only needed it to pivot our data during the reshape
    long_df = stacked_df.reset_index()

    # extract numbers from feature name column to make wave column
    long_df['wave'] = long_df.loc[:,'level_1'].str.extract(r'(\d\d|\d)',expand=False)

    # extract remove numbers from remaining feature name column
    long_df['level_1'] = long_df['level_1'].str.replace('\d+', '')

    # get list of final features to have as columns in the output df
    features = list(long_df.level_1.unique())
    long_df = long_df.rename(columns = {0: 'value'})

    # prepare output dataframe
    long_df_id = long_df[['hhidpn', 'wave']].drop_duplicates().reset_index(drop = True)
    for i in range(len(features)):
        # select only rows with features fitting the output column feature
        temp_df = long_df.loc[long_df['level_1'] == features[i]].reset_index(drop = True)
        # we do joins in this part just incase there is a variable that is not included for all years
        # it will join the features on the unique combo of hhidpn x wave
        if i == 0:
            final_df = long_df_id.merge(temp_df, on = ['hhidpn', 'wave'], how = 'outer')
            final_df = final_df.rename(columns = {'value': features[i]})
        else:
            final_df = final_df.merge(temp_df, on = ['hhidpn', 'wave'], how = 'outer')
            final_df = final_df.rename(columns = {'value': features[i]})
    return final_df[['hhidpn', 'wave'] + features]










