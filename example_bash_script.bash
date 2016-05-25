#!/bin/bash

####################################################################
#
# Sample bash pipeline script for using SAMSA
##
# For this sample pipeline, we have two paired-end sequenced metatranscriptomes:
#		control_reads_R1.fastq
#		control_reads_R2.fastq
#		experiment_reads_R1.fastq
#		experiment_reads_R2.fastq
#
# This bash script assumes that all SAMSA pipeline scripts are located in ./SAMSA/
# as a directory.
#
####################################################################

# Step 1: Processing raw sequence files
#		These files need to be cleaned of any adaptor contamination and the 
#		paired-end files must be merged to create an ExtendedFrags file.
#
#		To complete these steps, FLASH (http://ccb.jhu.edu/software/FLASH/) and
#		Trimmomatic (http://www.usadellab.org/cms/?page=trimmomatic) must be installed.
#
#		Replace "@@AuthorizationKey@@" with your Authorization key.

python SAMSA/SAMSA_pre_annotation_pipeline.py -Ends 2 -A @@AuthorizationKey@@ -D sample_files/ -F ~/Desktop/Code/FLASH/flash -T ~/Desktop/Code/Trimmomatic/trimmomatic.jar

# 		For all of the raw sequence files, the pre-annotation pipeline should clean
#		the files, removing adaptors, and should merge the paired-end files.  The output
#		will be labeled as control_file_.extendedFrags.fastq .

####################################################################
#
# Step 2: Uploading files to MG-RAST
#		If using the SAMSA_pre_annotation_pipeline.py script, the files will automatically
#		be uploaded to MG-RAST.
#
#		If performing the steps manually, use the following command, but be sure to
#		replace "@@AuthorizationKey@@" with your Authorization key.

python SAMSA/upload_MG-RAST.py -A @@AuthorizationKey@@ -F control_file_.extendedFrags.fastq
python SAMSA/upload_MG-RAST.py -A @@AuthorizationKey@@ -F experiment_file_.extendedFrags.fastq

####################################################################
#
# Step 3: MG-RAST submission
#		This step cannot be performed from the command line.  Log in to MG-RAST
#		(metagenomics.anl.gov) and submit the uploaded files for annotation.  
#		NOTE: Be sure that "dereplication" is turned OFF (requires unchecking a box)

#		If you plan to publicly release your data, you may submit metadata as well, to speed
#		up the time spent waiting in queue.

####################################################################
#
# Step 4: Downloading annotations from MG-RAST
#		Depending upon whether metadata was submitted, MG-RAST may take several days or longer
#		to process the data.  You will receive an email when files are completed.  The next step
#		is to download the results.
#
#		You will need to log into MG-RAST (metagenomics.anl.gov) and retrieve the annotation ID
#		for each file.  You may also need to update your Authorization key, under Preferences.
#
#		Replace "@@AuthorizationKey@@" with your Authorization key.
# 		Replace "@@AnnotationID@@" with each file's annotation ID.

python SAMSA/MG-RAST_API_downloader.py -S RefSeq -A @@AuthorizationKey@@ -D Organism -I @@AnnotationID@@ -O control_organism_annotations.tab
python SAMSA/MG-RAST_API_downloader.py -S RefSeq -A @@AuthorizationKey@@ -D Function -I @@AnnotationID@@ -O control_function_annotations.tab
python SAMSA/MG-RAST_API_downloader.py -S RefSeq -A @@AuthorizationKey@@ -D Organism -I @@AnnotationID@@ -O experiment_organism_annotations.tab
python SAMSA/MG-RAST_API_downloader.py -S RefSeq -A @@AuthorizationKey@@ -D Function -I @@AnnotationID@@ -O experiment_function_annotations.tab

####################################################################
#
# Step 5: Analyzing annotation files
# 		These annotation files must now be aggregated into summaries, using analysis_counter.py.
#		Note that functional annotations receive the "-m" flag, to preserve M5nr internal IDs.
#		This script assumes that these files are located in the "sample_output_files/" folder.

python SAMSA/analysis_counter.py sample_output_files/control_organism_annotations.tab -o sample_output_files/control_organism_summary.tab 
python SAMSA/analysis_counter.py sample_output_files/control_function_annotations.tab -o sample_output_files/control_function_summary.tab -m
python SAMSA/analysis_counter.py sample_output_files/experiment_organism_annotations.tab -o sample_output_files/experiment_organism_summary.tab
python SAMSA/analysis_counter.py sample_output_files/experiment_function_annotations.tab -o sample_output_files/experiment_function_summary.tab -m

####################################################################
#
# Step 6: Preparing summary files for import into R
#		The analysis_counter.py script generates summary data at the top of the file; this data needs to
# 		be scrubbed before the remaining spreadsheet data can be imported into R.  In addition, the
#		organism and function names are sometimes bulky and need to be reduced.

python SAMSA/RefSeq_output_reducer.py -I sample_output_files/control_organism_summary.tab -O sample_output_files/control_organism_summary_simplified.tab
python SAMSA/RefSeq_output_reducer.py -I sample_output_files/experiment_organism_summary.tab -O sample_output_files/experiment_organism_summary_simplified.tab

python SAMSA/func_data_trimmer.py -I sample_output_files/control_function_summary.tab -O sample_output_files/control_function_summary_simplified.tab
python SAMSA/func_data_trimmer.py -I sample_output_files/experiment_function_summary.tab -O sample_output_files/experiment_function_summary_simplified.tab

####################################################################
#
# Step 7: Import into R and analysis
#		For this step, simply run the R markdown (.Rmd) scripts included in the SAMSA pipeline and follow
#		the instructions in the markdown scripts.
#
####################################################################
#
# Step 8: Converting organism results to Family level for higher taxonomy comparisons
#		By default, the annotations from MG-RAST are returned at the Genus level.  However, if comparisons
#		at a higher taxonomic order are needed, this can be performed using the taxonomy_shifter.py program:

python SAMSA/taxonomy_shifter.py -F sample_output_files/control_organism_summary_simplified.tab -R SAMSA/Bacterial_Genus_flattened.tsv -T Family -O sample_output_files/control_organism_Family_summary.tab 
python SAMSA/taxonomy_shifter.py -F sample_output_files/experiment_organism_summary_simplified.tab -R SAMSA/Bacterial_Genus_flattened.tsv -T Family -O sample_output_files/experiment_organism_Family_summary.tab 

#		At this point, the Family level files may be loaded into R and the rest of the analysis may proceed 
#		as normal.
#
####################################################################
