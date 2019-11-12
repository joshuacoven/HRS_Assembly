################### import packages #######################################################
import pandas as pd
import re
import numpy as np
import os
import hrs_functions
import copy

## maybe make this more programatic
## each survey has a letter preceeding variable names, increases by 1 each time
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
## this works and matches stata output
## need a .sas program file as the dct
## need a .da data file as the filename
# only reads specified variables, saves a lot of time
def read_sas_fwf(dct_file, filename, variables_to_look_for, survey_year):
    id_vars = ['hhid', 'pn']
    lines = []
    colons = []
    # parse the .sas file for relevant lines
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
    survey_specific_variables = [var_dict[survey_year] + x
                             for x in variables_to_look_for]
    for i in dictionary:
        temp = i.lstrip().replace('-', '').replace('\n', '').split(' ')
        temp = [i for i in temp if i]
        if any([temp[0].lower() == y for y in id_vars + survey_specific_variables]):
            names.append(temp[0])
            if temp[1] == '$':
                var = str
                colspecs.append(
                    [int(temp[2]) - 1
                     , int(temp[3])
                    ]
                                )
            else:
                var = float
                colspecs.append(
                    [int(temp[1]) - 1
                     , int(temp[2])
                    ]
                                )
            test_dict[temp[0]] = var

        # need the test_dict because fwf needs to know the datatype of each col
    df = pd.read_fwf(filename, colspecs=colspecs, names = names
                 , converters = test_dict)
    return df


def sas_read_year(directory, variables_to_look_for, survey_year):
    # list all files to potentially read
    directory_sas = directory + 'h' + str(survey_year)[2:4] + 'sas'
    directory_da = directory + 'h' + str(survey_year)[2:4] + 'da'
    path_list = list(set([directory_sas + '/' +  x.split('.')[0] for x in os.listdir(directory_sas) 
                          if 'sas' in x
                          and 'R' in x[len(x.split('.')[0])-1]
                         ]))

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
    survey_specific_variables = [var_dict[survey_year] + x
                             for x in variables_to_look_for]
    
    # for renaming variables
    rename_dict = copy.deepcopy(variables_to_look_for)
    vars_list = [x for x in variables_to_look_for]
    for x in range(len(survey_specific_variables)):
        rename_dict[survey_specific_variables[x].upper()] = rename_dict.pop(vars_list[x])
        
    # read the files
    for i in range(len(path_short_list)):
        path = path_short_list[i]
        filename = directory_da + '/' + path.split('/')[8] + '.da'
        dct_file = directory_sas + '/' + path.split('/')[8] +  '.sas'
        print(filename)
        print(dct_file)
        temp_df = read_sas_fwf(dct_file, filename, variables_to_look_for, survey_year)
        temp_df = temp_df[[x for x in temp_df.columns if x.lower() in (id_variables + survey_specific_variables)]]
        temp_df = temp_df.rename(columns = rename_dict)
        if i == 0:
            year_frame = temp_df
        else:
            year_frame = year_frame.merge(temp_df, on = ["HHID", "PN"], how = "outer")

    # make the wave variable, 1992 was wave 1
    wave = (survey_year - 1990) / 2
    year_frame['wave'] = wave
    return year_frame



















##### these are no good due to stata differences in reading fwf files. sas files have numbers that correspond to actual widths
## I think the difference is in how stata reads byte types and is able to skip columns, but not sure
def read_stata_files(filename, dct_file):
    # code adapted from Allen B. Downey, Think Stats: Exploratory Data Analysis
    type_map = dict(byte=int, int=int, long=int, float=float, 
                        double=float, numeric=float)
    index_base = 0
    var_info = []
    with open(dct_file) as f:
        for line in f:
            match = re.search( r'_column\(([^)]*)\)', line)
            if not match:
                continue
            start = int(match.group(1))
            t = line.split()
            vtype, name, fstring = t[1:4]
            name = name.lower()
            if vtype.startswith('str'):
                vtype = str
            else:
                vtype = type_map[vtype]
            long_desc = ' '.join(t[4:]).strip('"')
            var_info.append((start, vtype, name, fstring, long_desc))

    columns = ['start', 'type', 'name', 'fstring', 'desc']
    variables = pd.DataFrame(var_info, columns=columns)

    # fill in the end column by shifting the start column
    variables['end'] = variables.start.shift(-1)
    variables.loc[len(variables)-1, 'end'] = 0

    colspecs = variables[['start', 'end']] - index_base
    colspecs = colspecs.astype(np.int).values.tolist()

    names = variables['name']

    df = pd.read_fwf(filename, colspecs=colspecs, names = names)
    return df

def read_year_of_data(directory, variables_to_look_for, survey_year):
    # list all files to potentially read
    directory_sta = directory + 'h' + str(survey_year)[2:4] + 'sta'
    directory_da = directory + 'h' + str(survey_year)[2:4] + 'da'
    path_list = list(set([directory_sta + '/' +  x.split('.')[0] for x in os.listdir(directory_sta) 
                          if 'dct' in x
                          and 'R' in x[len(x.split('.')[0])-1]
                         ]))
    
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
    
    survey_specific_variables = [var_dict[survey_year] + x
                             for x in variables_to_look_for]
    
    rename_dict = copy.deepcopy(variables_to_look_for)
    vars_list = [x for x in variables_to_look_for]
    
    for x in range(len(survey_specific_variables)):
        rename_dict[survey_specific_variables[x]] = rename_dict.pop(vars_list[x])
        
    # read the files
    for i in range(len(path_short_list)):
        path = path_short_list[i]
        filename = directory_da + '/' + path.split('/')[8] + '.da'
        dct_file = directory_sta + '/' + path.split('/')[8] +  '.dct'
        print(filename)
        try:
            temp_df = read_stata_files(filename, dct_file)
            temp_df = temp_df[[x for x in temp_df.columns if x.lower() in (id_variables + survey_specific_variables)]]
            temp_df = temp_df.rename(columns = rename_dict)
            if i == 0:
                year_frame = temp_df
            else:
                year_frame = year_frame.merge(temp_df, on = ["hhid", "pn"], how = "outer")
        except:
            print('missing files: ' + path)
            pass
        
    # make the wave variable, 1992 was wave 1
    wave = (survey_year - 1990) / 2
    year_frame['wave'] = wave
    return year_frame