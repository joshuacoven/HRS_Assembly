# HRS Assembly https://hrs.isr.umich.edu
* Code to assemble:
	* Health and Retirement Study (HRS)
	* Consumption and Activities Mail Survey (CAMS)
		* A survey mailed to a subsample of HRS participants
	* Rand CAMS: User friendly version of CAMS
	* Rand HRS: User friendly version of HRS
* The code searches only relevant data files and only reads relevant variables, saving significant amounts of time
	* It accomplishes this by taking advantage of file and variable naming conventions
	* It reads only the columns of relevant variables in the fixed with files

# Data sources: 
* HRS core files: 1992 - Present, every 2 years
	* fixed width files and dictionaries
	* Can read quickly (< 1 min) because selects only pertinent survey parts and only the variables needed from those parts
* CAMS core files: 2001 - Present, every 2 years
	* fixed width files and dictionaries
	* Can read quickly (< 1 min) because selects only pertinent survey parts and only the variables needed from those parts
* RAND CAMS files: 2001-2017 at the moment
	* One small .dta file  (< 1 mins)
* RAND HRS files: 2001-2016 at the moment
	* Can't read quickly because all in 1 large .dta file (> 10 mins)

# Capabilities:
* Assemble desired variables from all 4 sources and joins datasets on unique household id x person id
* Saves time by only looking at desired files and desired sections of files based off of variables specified

# To do
* Have variable lookup function so that we don't have to use the codebook
* Clean existing functions
* Automatic variable cleaning for entries like 9999
* Add variable weighting

# Instructions:
1. Download the data: You will need an account and it can take up to 24 hrs to get your password
* 1.1 Download the .sas and .da folders of the HRS Core for each survey wave https://ssl.isr.umich.edu/hrs/files2.php	
* 1.2 Download the HRS Rand data (in stata form): "RAND HRS Longitudinal File 2016 (v.1)" or a later version
		This is also on the public downloads page of the HRS, on the right side
		Drag the stata folder into your "data" folder
* 1.3 Download the CAMS Rand data (in stata form)
		This is also on the public downloads page of the HRS, on the right side
		Drag the stata folder into your "data" folder
* 1.4 Download the CAMS folders for each CAMS mailout

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
* Insert these variables without their first letter in the "variables to look for" dictionary in assembly_code.py, lowercase
* Give them whatever names you want in their dictionary entry

4. Do the same for the Rand codebooks and the CAMS codebook

5. Run the code to join this to the HRS core files

6. Some of the pre-2001 files might have a .da instead of a .DA. Changing those with ".da" to all uppercase, including the extension, will fix that
* Also changed cams03_r.da to CAMS03_R.da. It became easier to make these 3 or 4 filename changes than to code them in

7. If you are getting weird errors, check that all files were downloaded properly from HRS' website
	* Example: Error for referencing "year_frame" before that dataframe was created. It was due to an incomplete download from the HRS website in which not all SAS files from 2012 were downloaded, causing the variables of interest to not line up with the dictionaries present.

# Household level files (HHID = Household ID)
* Added the capability to incorporate HH level files in 2021
* Need to pull 3 new HH level identifiers to use this: QPN_FIN, QPN_FAM, QPN_CS
* To merge to respondent level, need to have this data unique at HHID
* However, multiple people from the same HH may answer the same question, and have different answers
	* Ex: 3 people from the same HH all answer an HH level question like whether they own or rent their home. There is disagreement in this variable, so to aggregate up to the HH level there must be a tiebreaker
* Tiebreaker used:
	* Lowest number is for the first person in the dataset with that HHID, so most likely oldest, or head of household(?)
    * We want the lowest QPN_FIN number for each HHID
    * If no QPN_FIN number for a HHID, select lowest QPN_FAM
    * IF no QPN_FIN or QPN_FAM, we want the lowest QPN_CS number

# Weighting
* Haven't incorporated any weighting yet
* "The household weight is scaled so as to have the sum of the weights equal the number of households in the population as measured by the March CPS" http://hrsonline.isr.umich.edu/sitedocs/wghtdoc.pdf
* One option used in docs is to get a random sampling using the weights as probabilities of selection: http://hrsonline.isr.umich.edu/sitedocs/dmgt/IntroUserGuide.pdf


# SAS vs. STA
* I originally tried to use the stata dictionary files to read the .da's
* The column numbers in the .dct's do not match up with the actual column widths in the fixed width .da files
* Stata is able to read these correctly anyways but at the moment I can't read them with pandas read_fwf function
	* I think this has to do with the way stata reads "byte" types
* The SAS program statements have column numbers that correspond to those actually seen in the data so we use those here instead




