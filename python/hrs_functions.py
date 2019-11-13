################### import packages #######################################################
import pandas as pd
import re
import numpy as np
import os
import hrs_functions
import copy

## each survey (post 2000) has a letter preceeding variable names, increases by 1 but skips i
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

#################################### define functions ####################################

#################################### read_sas_fwf ####################################
## this works and matches stata output
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
        temp = [item for sublist in temp for item in sublist]
        temp = [i for i in temp if i]
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
    if survey_year < 1996:
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
    if survey_year < 2001:
        path_short_list = path_list
    else:
        # figure out which surveys to read based on variables to look for
        surveys = [x[0] for x in variables_to_look_for]\
            + [x[0:2] for x in variables_to_look_for if 'lb' in x]

        # find the surveys in the path list
        path_short_list = [x for x in path_list if 'r' in x.split('/')[8].lower() # only get respondent
                           and any(
                               y == x.split('/')[8].lower()[3:len(x.split('/')[8]) - 2] 
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
        filename = directory_da + '/' + path.split('/')[8] + '.da'
        if survey_year < 2001:
            dct_file = directory_sas + '/' + path.split('/')[8] +  '.SAS' #in the year 2000, files are .SAS and not .sas
            temp_df = read_sas_fwf(dct_file, filename, variables_to_look_for_pre_2002, survey_year)
        else:
            dct_file = directory_sas + '/' + path.split('/')[8] +  '.sas'
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














