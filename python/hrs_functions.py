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
## for 1992, already included in input so add a null string
# in 2000 and earlier, a variable doesnt even have the same number
# need to be extra explicit in the variables_to_look_for, which is why there's a separate input for it
var_dict = {
      1992: ''
    , 1994: ''
    , 1996: ''
    , 1998: ''
    , 2000: ''
    , 2002: 'h'
    , 2004: 'j' # they skip i for some reason
    , 2006: 'k'
    , 2008: 'l'
    , 2010: 'm'
    , 2012: 'n'
    , 2014: 'o'
    , 2016: 'p' 
    , 2018: 'q'
}

#################################### functions ####################################
# 3 functions for assembling HRS and CAMS core files
# 1st reads fixed with files with a SAS program statement
# 2nd does this for a whole year for given variables
# 3rd does this for all years

# 1 function for Rand files
# reshapes Rand table into a long for given variable patterns

#################################### HRS and CAMS Core files ####################################
#################################### read_sas_fwf ####################################

## need a .sas program file as the dct
## need a .da data file as the filename
## only reads specified variables from fwf, saves a lot of time

# input types:
# dct_file: string
# filename: string
# variables_to_look_for: dictionary
# survey year: int

def read_sas_fwf(dct_file, filename, survey_specific_variables):
    # global id variables
    id_vars = ['hhid', 'pn']

    # parse the .sas file for relevant lines
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
    
    # parse the relevant lines into outputs necessary for pd.read_fwf
    colspecs = []
    type_dict = {}
    names = []
    
    # can maybe make this faster by using pandas functions. unnecessary though
    for i in dictionary:
        
        # these comprehensions standardize the differences in sas files over the years
        temp = i.lstrip().split(' ')
        temp = [x.replace('\n', '').split('-') for x in temp]
        temp = [item for sublist in temp for item in sublist] # flatten the list
        temp = [i for i in temp if i]                         # removes empty strings
        
        # only read a variable if it matches survey specific variables
        if any([temp[0].lower() == y for y in id_vars + survey_specific_variables]):
            names.append(temp[0])
            if temp[1] == '$':
                var = str
                colspecs.append([int(temp[2]) - 1, int(temp[3])])
            else:
                var = float
                colspecs.append([int(temp[1]) - 1, int(temp[2])])
            type_dict[temp[0]] = var         
    return pd.read_fwf(filename, colspecs=colspecs, names = names, converters = type_dict)


#################################### HRS and CAMS Core files ##########################
#################################### sas_read_year ####################################

# this is an extension of the read_sas_fwf function
# for a given directory and desired variables, will automatically find the right files to read
# this function deals with the naming and directory structure inconcistencies across 20 years of the HRS
# based on year and cams vs hrs, finds .sas and .da paths, reads the files containing relevant variables

# input types: 
# directory : string
# variables_to_look_for : dictionary
# survey_year : int
# variables_to_look_for_pre_2002 : dictionary

def sas_read_year(directory, variables_to_look_for, survey_year, variables_to_look_for_pre_2002):
    # HRS and CAMS assignment
    id_variables = ['hhid', 'pn']
    
    # HRS assignments
    if survey_year < 2001:
        variables_to_look_for = variables_to_look_for_pre_2002  
    # get directories given year and survey type
    directory_sas = directory + 'h' + str(survey_year)[2:4] + 'sas'
    directory_da = directory + 'h' + str(survey_year)[2:4] + 'da'
    # get survey specific variables
    if variables_to_look_for_pre_2002 != 'CAMS':
        survey_specific_variables = [var_dict[survey_year] + x for x in variables_to_look_for]

    # CAMS assignments
    if variables_to_look_for_pre_2002 == 'CAMS':
        # survey specific variables
        survey_specific_variables = [x + '_' + str(survey_year)[2:4] for x in variables_to_look_for]
        # CAMS directories
        # 2001 has a different directory name
        if survey_year == 2001:
            ext = 'cams' + str(survey_year)[2:4]
            ext_da = ext
        # 2009 has a different directory structure
        elif survey_year == 2009:
            ext = 'cams' + str(survey_year) + '/sas'
            ext_da = 'cams' + str(survey_year) + '/data'
        else:
            ext = 'cams' + str(survey_year)
            ext_da = ext
        directory_sas = directory + ext
        directory_da = directory + ext_da

    # get list of paths: pre 1996 and some cams dont have R in them
    if survey_year < 1996:
        path_list = sorted(list(set([directory_sas + '/' +  x.split('.')[0] 
                                for x in os.listdir(directory_sas) 
                                    if 'sas' in x.lower()])))
    else:
        path_list = sorted(list(set([directory_sas + '/' +  x.split('.')[0] 
                                for x in os.listdir(directory_sas) 
                                    if ('sas' in x.lower())
                                    and (
                                          ('r' in x[len(x.split('.')[0])-1].lower()) #respondent
                                        | ('h' in x[len(x.split('.')[0])-1].lower()) #household
                                        )
                                     
                            ]
                           )
                       )
                  )
        #path_list = sorted(list(set([directory_sas + '/' +  x.split('.')[0] 
        #                        for x in os.listdir(directory_sas) 
        #                            if ('sas' in x.lower())
        #                            and ('r' in x[len(x.split('.')[0])-1].lower())])))
    
    # from paths, get paths leading to files which have our desired variables
    # earlier than 2000, need to read all surveys because naming conventions and variables are unrelated
    # after 2000, only reads files with desired variables in them to save a lot of time
    path_short_list = path_list
    #print(path_short_list)
    if (survey_year > 2000) and (variables_to_look_for_pre_2002 != 'CAMS'):
        surveys = [x[0] for x in variables_to_look_for] + [x[0:2] for x in variables_to_look_for if 'lb' in x]
        path_short_list = [x for x in path_list if (('r' in x.split('/')[len(x.split('/'))-1].lower()  # get respondent
                                                        and any(y == x.split('/')[len(x.split('/'))-1].lower()[3:len(x.split('/')[len(x.split('/'))-1]) - 2] 
                                                                    for y in surveys) # get specific file
                                                    )  
                                                   ) 
                            or (('h' in x.split('/')[len(x.split('/'))-1].lower())  # get household
                                # take all surveys we are looking for, only keep if HH survey (this is the last list comprehension below)
                                and any(y == x.split('/')[len(x.split('/'))-1].lower()[3:len(x.split('/')[len(x.split('/'))-1]) - 2] 
                                                                    for y in [w for w in surveys if w in ['h', 'q', 'r', 'u']])
                                )
                           ]
    #
    (path_short_list)
    # rename variables to names chosen in input dictionary
    rename_dict = copy.deepcopy(variables_to_look_for)
    vars_list = [x for x in variables_to_look_for]
    for x in range(len(survey_specific_variables)):
        rename_dict[survey_specific_variables[x].upper()] = rename_dict.pop(vars_list[x])  
    print('looking for variables: ' + str(survey_specific_variables))
    
    # get proper file extensions
    # this maybe can get coded away if handle all the info in path and path short list better
    for i in range(len(path_short_list)):
        path = path_short_list[i]
        path_ind = len(path.split('/')) - 1
        if survey_year < 2001:
            ext_surv_dct = '/' + path.split('/')[path_ind] +  '.SAS' #in the year 2000, files are .SAS and not .sas
            ext_surv_da = '/' + path.split('/')[path_ind] + '.DA'
        else:
            ext_surv_dct = '/' + path.split('/')[path_ind] +  '.sas'
            ext_surv_da = '/' + path.split('/')[path_ind] + '.da'
        dct_file = directory_sas + ext_surv_dct
        filename = directory_da + ext_surv_da
        print(filename)
        # read the files
        temp_df = read_sas_fwf(dct_file, filename, survey_specific_variables)
        temp_df = temp_df.rename(columns = rename_dict)
        if i == 0:
            if 'PN' in temp_df.columns:
                # then it's a respondent survey
                year_frame = temp_df
            else:# 'QPN_FIN' in temp_df.columns:
                #then it's a household survey: household methodology in greater detail below
                temp_df = temp_df.sort_values(['HHID'] + survey_specific_variables[-3:]).reset_index(drop = True)
                    
                # Keep top row for each HHID
                temp_df = temp_df.drop_duplicates(subset=['HHID'], keep = 'first')
                year_frame = temp_df
        else:
            try:
                year_frame = year_frame.merge(temp_df, on = ["HHID", "PN"], how = "outer")
            except:
                try:
                    ##### MERGE HOUSEHOLD DATA ON TO RESPONDENT LEVEL, GET DATASET UNIQUE AT THE HHID LEVEL ###############
                    # Lowest number is for the first person in the dataset with that HHID, so most likely oldest, or head of household(?)
                    ### We want the lowest QPN_FIN number for each HHID
                    ### If no QPN_FIN number for a HHID, select lowest QPN_FAM
                    ### IF no QPN_FIN or QPN_FAM, we want the lowest QPN_CS number
                    temp_df = temp_df.sort_values(['HHID', 'PN_CS', 'PN_FIN', 'PN_FAM']).reset_index(drop = True)

                    # Keep top row for each HHID
                    temp_df = temp_df.drop_duplicates(subset=['HHID'], keep = 'first')
                    
                    # THEN MERGE ONCE ROWS ARE UNIQUE TO HHID ###########
                    year_frame = year_frame.merge(temp_df, on = ["HHID"], how = "outer") # for households
                    print('household survey')
                except:
                    print('this is a pre-1996 household survey, so exclude') # pre-1996 some surveys wont have a PN

    # make the wave variable, 1992 was wave 1
    year_frame['wave'] = (survey_year - 1990) / 2
    return year_frame


#################################### HRS and CAMS Core files ###############################
#################################### read_all_years ####################################

# this is an extension of the sas_read_year function to work across multiple years
# for all years specified, gets all variables specified from the HRS core files

# input types:
# years :  list
# directory : string
# variables_to_look_for : dictionary
# variables_to_look_for_pre_2002 : dictionary

def read_all_years(years, directory, variables_to_look_for, variables_to_look_for_pre_2002):
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
    final_frame = final_frame.drop_duplicates()
    return final_frame.reset_index(drop = True)


#################################### RAND Files ##############################################
#################################### reshape_rand ####################################

# this reshapes the HRS Rand & CAMS Rand data files from wide to long, for desired variables called "patterns"

def reshape_rand(Rand, patterns):
    col_list = list(Rand.columns)
    id_columns = ['hhidpn']
    short_list = []
    for pat in patterns:
        short_list = short_list + fnmatch.filter(col_list, pat)

    # get only columns that will go into final output
    Rand_small = Rand[id_columns + short_list]

    # index the data based off of ID columns
    indexed_df = Rand_small.set_index('hhidpn')

    # Stack the columns to get long format
    stacked_df = indexed_df.stack(dropna=False)

    # reset index to numeric, just needed to set it to otherwise to stack the columns
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










