# HRS Assembly https://hrs.isr.umich.edu
Code to assemble years and parts of the health and retirement survey
The code searches only relevant data files, and only reads relevant variables, saving significant amounts of time
It takes advantage of variable naming conventions to save lines of code and lots of time when reading across surveys


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
2. Put these folders in a directory called "data", where the data directory is in the same directory as assembly code

ex:
* ./assembly_code.py
* ./data/h16sas
* ./data/h16sas/H16A_R.sas
* ...
* ./data/h16da
* ./data/h16da/H16A_R.da
* ...
* ./data/h14sas
* ...
* ./data/h14da
* ...

3. Look at HRS codebook to select variables of interest https://hrs.isr.umich.edu/documentation/codebooks
	Insert these variables without their first letter in the "variables to look for" dictionary in assembly_code.py
	Give them whatever names you want in their dictionary entry

4. Run the code


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

# Sas vs. sta
I originally tried to use the stata dictionary files to read the .da's
The column numbers in the .dct's do not match up with the actual column widths in the fixed width .da files
Stata is able to read these correctly anyways but at the moment I can't read them with pandas read_fwf function
	I think this has to do with the way stata reads bytes types
The SAS program statements have column numbers that correspond to those actually seen in the data so we use those here instead

# To do
* Add CAMS and Rand data
* Maybe add PSID data
* Have special variable lookup function so that we don't have to use the codebook


