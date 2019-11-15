# HRS Assembly https://hrs.isr.umich.edu
Code to assemble years and parts of the health and retirement survey
The code searches only relevant data files, and only reads relevant variables, saving significant amounts of time
It takes advantage of variable naming conventions to save lines of code and lots of time when reading across surveys


# Data sources: 
* HRS core files: 1992 - Present, every 2 years
	* fixed width files and dictionaries
	* Can read quickly (< 1 min) because selects only pertinent survey parts and only the variables needed from those parts
* CAMS core files: 2001 - Present, every 2 years
	* fixed width files and dictionaries
	* Can read quickly (< 1 min) because selects only pertinent survey parts and only the variables needed from those parts
* RAND CAMS files: 2001-2017 at the moment
	* One .dta file
	* Cant read quickly because all in 1 dta file (> 10 mins)
* RAND HRS files: 2001-2016 at the moment
	* One .dta file
	* Cant read quickly because all in 1 dta file (> 10 mins)

# Capabilities right now:
* Assemble desired variables from HRS core files from 1992-present
* Saves time by only looking at desired files and desired sections of files based off of variables specified

# To do
* CAMS HRS wave matching
* Add PSID data maybe
* Make HH level database
* Have special variable lookup function so that we don't have to use the codebook
* Clean existing functions
* Maybe variable cleaning option
* Add variable weighting

# Data sources:
HRS: Health and Retirement Study
CAMS: Consumption and Activities Mail Survey
	Mailed to a subsample of HRS
RAND CAMS: User friendly version of CAMS data
RAND HRS: User friendly version of HRS data
Notes: CAMS data is from 2001 to present where each additional wave is on odd years. HRS Data is from 1992 (wave 1) to present and each additional wave is every two years on even years

# Instructions:
1. Download the .sas and .da folders of the HRS Core for each survey wave https://ssl.isr.umich.edu/hrs/files2.php
	You will need an account and it can take up to 24 hrs to get your password
2. Replicate sample directory structure, ex:
* ./assembly_code.py
* ./data/HRS
* ./data/HRS/h16sas
* ./data/HRS/h16sas/H16A_R.sas
* ...
* ./data/HRS/h16da
* ./data/HRS/h16da/H16A_R.da
* ...
* ./data/HRS/h14sas
* ...
* ./data/HRS/h14da
* ...
* ./data/CAMS/...
* ./data/rand_hrs...
* ./data/rand_cams...

3. Look at HRS codebook to select variables of interest https://hrs.isr.umich.edu/documentation/codebooks
	Insert these variables without their first letter in the "variables to look for" dictionary in assembly_code.py
	Give them whatever names you want in their dictionary entry

4. Run the to assemble the HRS Core files

5. Download the HRS Rand data (in stata form): "RAND HRS Longitudinal File 2016 (v.1)" or a later version
	This is also on the public downloads page of the HRS, on the right side
	Drag the stata folder into your "data" folder

6. Run the code to join this to the HRS core files

# Updating the data: 
To find the CAMS FAT data file, go to the bottom left of the page. It will be titled something like "HRS Mailout CAMS"
Download the zip and you then have a .da, .dct, and a .do file
Run the .do file with the proper directories and you will get your .dta file

To find the CAMS RAND data file, go to the middle right of the page. It will be titled something like "RAND HRS CAMS Spending Data"
This gives you a .dta file so no need to run any .do files here

To find the HRS FAT data file, go to the bottom left of the page. It will be titled something like "{year} HRS Core"
Download the stata zip and then run a bunch of those .do files with the .da's and .dct's to get your .dta's
Hopefully we can make a flexible .do file that does this for you, and updates with an input that's the desired year

# Naming Conventions
Naming convention for variables is 10 for 2010 and 10-y where y is number of surveys before 2010, 10+y for number of surveys after 2010, i.e., 2016 -> 13
Naming convention for CAMS, same deal with waves. 

# Weighting
"The household weight is scaled so as to have the sum of the weights equal the number of households in the population as measured by the March CPS" http://hrsonline.isr.umich.edu/sitedocs/wghtdoc.pdf
One option used in docs is to get a random sampling using the weights as probabilities of selection: http://hrsonline.isr.umich.edu/sitedocs/dmgt/IntroUserGuide.pdf

# Other notes
Rand files tend to be in the wide format (new column for each variable in each year)
Better to reshape these into the long format

# SAS vs. STA
I originally tried to use the stata dictionary files to read the .da's
The column numbers in the .dct's do not match up with the actual column widths in the fixed width .da files
Stata is able to read these correctly anyways but at the moment I can't read them with pandas read_fwf function
	I think this has to do with the way stata reads "byte" types
The SAS program statements have column numbers that correspond to those actually seen in the data so we use those here instead




