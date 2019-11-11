# HRS Assembly
Code to assemble years and parts of the health and retirement survey:
https://hrs.isr.umich.edu

# Data sources:
HRS: Health and Retirement Study
CAMS: Consumption and Activities Mail Survey
	Mailed to a subsample of HRS
RAND CAMS: User friendly version of CAMS data
RAND HRS: User friendly version of HRS data
Notes: CAMS data is from 2001 to present where each additional wave is on odd years. HRS Data is from 1992 (wave 1) to present and each additional wave is every two years on even years

# Workflow:
To recreate the dataset there are 3 main .do files

1. make_hrs_data.do runs many of the auxiliary .do files to create the "using.dta" hrs dataset
	a. This calls on CAMS.do, core_data.do, fat&rand&CAMS_data.do, fat&rand_data.do, fat_data.do, and rand_data.do
2. make_PSID_data.do recreates the PSID dataset
3. make_tabfig.do makes all of the tables and figures in Nathaniel Hendren's 2013 slides

Running all 3 datasets in that order should recreate the two datasets and all figures if the directories are constructed properly. To do this, one must open up the .do files, look at the directory lines "db, global db, db...", and make sure they navigate to where the later files are called. In addition to this, the directories must be structured so that output figures can go to the proper place, i.e., a figures folder, a tables folder, a slides folder....

# make_hrs_data.do:

/* Start with raw HRS files and RAND files */
* Begin with the fat files from the HRS, many files
do "Data Construction/fat_data.do"

* Merge to the RAND Spine HRS file, one file
do "Data Construction/rand_data.do"

/* In addition to the main variables,
the working dataset also contains information on consumption
in the HRS that was used in an early version of this draft.
This is added in the following step. One file */
do "Data Construction/CAMS.do"

* Combine the fat file info and the rand data info
do "Data Construction/fat&rand_data.do"

* Merge in the consumption info
do "Data Construction/fat&rand&CAMS_data.do"


# Updating the data: https://ssl.isr.umich.edu/hrs/files2.php
You will need an account and it can take up to 24 hrs to get your password

To find the CAMS FAT data file, go to the bottom left of the page. It will be titled something like "HRS Mailout CAMS"
Download the zip and you then have a .da, .dct, and a .do file
Run the .do file with the proper directories and you will get your .dta file

To find the CAMS RAND data file, go to the middle right of the page. It will be titled something like "RAND HRS CAMS Spending Data"
This gives you a .dta file so no need to run any .do files here

To find the HRS FAT data file, go to the bottom left of the page. It will be titled something like "{year} HRS Core"
Download the stata zip and then run a bunch of those .do files with the .da's and .dct's to get your .dta's
Hopefully we can make a flexible .do file that does this for you, and updates with an input that's the desired year


# HRS FAT file preprocessing
Download the core files of the desired year, the .sta and the .da
Put the .do, .dct, and the .da files in the same folder
Change the .dct files so that there is no path at the top next to "using", just the file  name
Edit the main .do file included for the year and proper file signatures
Run the codebook to figure out which variables represent the likelihood of losing a job and the likelihood of finding a job
We need VERY FEW variables from the FAT files, even though there are > 7000. We can use stata's lookfor command to identify them. Look at the list already existing in the file, the docs, and then if you want to look for other variables it's probably better to use the docs than to use stata's lookfor command.


# Naming Conventions
Naming convention for variables is 10 for 2010 and 10-y where y is number of surveys before 2010, 10+y for number of surveys after 2010, i.e., 2016 -> 13
Naming convention for CAMS, same deal with waves. 

# Weighting
"The household weight is scaled so as to have the sum of the weights equal the number of households in the population as measured by the March CPS" http://hrsonline.isr.umich.edu/sitedocs/wghtdoc.pdf
One option used in docs is to get a random sampling using the weights as probabilities of selection: http://hrsonline.isr.umich.edu/sitedocs/dmgt/IntroUserGuide.pdf

# Do File Order
To create the HRS database, one must run "make_hrs_data.do"
This file runs the other .do files necessary to make the dataset. The files it calls:
* fat_data.do
	* Pulls in preprocessed HRS FAT files from each wave
	* Keeps desired metrics from each year
	* Creates a few new metrics
	* Appends the years together
	* Outputs fat_data.dta
* rand_data.do
	* Pulls in desired HRS RAND variables
	* Reshapes the RAND variables into a long format from the wide format
	* Outputs rand_data.dta
* CAMS.do
	* Pulls in desired CAMS RAND variables
	* Reshapes this dataset
	* Pulls in desired CAMS HRS variables
	* Merges the datasets
	* Outputs CAMS_fat&rand.dta
* fat&rand&CAMS_data.do
	* Merges CAMS_fat&rand.dta, rand_data.dta, and fat_data.dta together
	* outputs fat&rand&CAMS_data.dta

# Other notes
Rand files tend to be in the wide format (new column for each variable in each year)
Better to reshape these into the long format



