################### import packages #######################################################
import pandas as pd
import re
import numpy as np
import os
import hrs_functions

## maybe make this more programatic
## each survey has a letter preceeding variable names, increases by 1 each time
var_dict = {
    2008: 'l'
    , 2010: 'm'
    , 2012: 'n'
    , 2014: 'o'
    , 2016: 'p' 
}

#################################### define functions ####################################
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
    # read the files
    for i in range(len(path_short_list)):
        path = path_short_list[i]
        filename = directory_da + '/' + path.split('/')[8] + '.da'
        dct_file = directory_sta + '/' + path.split('/')[8] +  '.dct'
        print(filename)
        try:
            temp_df = read_stata_files(filename, dct_file)
            temp_df = temp_df[[x for x in temp_df.columns if x.lower() in (id_variables + survey_specific_variables)]]
            
            ## maybe rename them here? some sort of naming dictionary
            
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