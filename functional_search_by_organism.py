#!/usr/bin/env Python

##########################################################################
#
# Copyright (C) 2015-2016 Sam Westreich
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation;
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##########################################################################
#
# functional_search_by_organism.py
# Created 5/10/16, last modified 5/31/16
# Created by Sam Westreich, stwestreich@ucdavis.edu, github.com/transcript/
#
##########################################################################
#
# The purpose of this script is to, for an organism of choice, find all 
# functional annotations linked to that organism.
#
# In addition, this tool can be used to remove all functional annotations 
# originating from organisms below a certain abundance threshold, in con-
# junction with the script "long_tail_threshold.py".  
#
# USAGE OPTIONS:
# 
# Inputs required:
# -N <organism_name>		The name of the organism you want to search for.
# -O <organism_file>		The RefSeq organism output file.
# -F <function_file> 		The RefSeq function output file.
# -R <results_file>			The name given to the results file (outfile).
# -Q						Enables quiet mode.
# -I <removal_targets>		A list of targets, such as those below a threshold, 
#								to be removed.
#								Generated by long_tail_threshold.py .
# -usage					Prints usage options and exits.
# 
##########################################################################

# imports
import sys, os, operator, time

# String searching function:
def string_find(usage_term):
	for idx, elem in enumerate(sys.argv):
		this_elem = elem
		next_elem = sys.argv[(idx + 1) % len(sys.argv)]
		if elem.upper() == usage_term:
			 return next_elem

# pull ARGV
argv = str(sys.argv).upper()

# file length count
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1
    
# Quiet mode & Usage statement		 
if "-Q" in argv:
	quiet = True
else:
	quiet = False
	print ("\nCOMMAND USED:\t" + " ".join(sys.argv) + "\n")
	print "For usage instructions/options, run with '-usage' flag."

if "-usage" in sys.argv:
	print "USAGE STATEMENT"
	print "-Q\tEnables quiet mode"
	print "-N\tName of organism to search for"
	print "-O\tOrganism output file to be searched"
	print "-F\tFunction output file to be searched"
	print "-R\tOutput file (default is organism_name_results.tab)"
	print "-I\tRemoval targets, list generated by long_tail_threshold.py, OPTIONAL"
	sys.exit()

if "-N" not in argv:
	if "-I" not in argv:
		sys.exit("Missing either:\n\t-N flag for organism of interest\n\t-I flag for list of organisms to remove")
if "-O" not in argv:
	sys.exit("Missing -O flag for organism input file")
if "-F" not in argv:
	sys.exit("Missing -F flag for function input file")

#################################

# PART 1: OBTAIN MG-RAST IDs FOR ORGANISM HITS

org_infile_name = string_find("-O")

org_file_length = file_len(org_infile_name)

try:
	org_infile = open (org_infile_name, "r")
except IOError:
	sys.exit("Unable to open organism MG-RAST output file.")

# Part 1, v1: Get all MG-RAST IDs associated with a single organism of choice.
if "-N" in argv:
	org_name = string_find("-N")

	# counters
	hit_counter = 0
	org_ID_dic = {}
	ID_list = []

	t0 = time.clock()

	for line in org_infile:
		if org_name in line:
			hit_counter += 1
			splitline = line.split("\t")
			org_ID_dic[splitline[1]] = splitline[3]
			ID_list.append(splitline[1])

	t1 = time.clock()

	# Results of searching org infile
	print ("Organism output searched.  Time elapsed: " + str(t1-t0) + " seconds.")
	print (str(len(ID_list)) + " IDs in list, " + str(hit_counter) + " total hits to the organism named " + org_name + ".")

	org_infile.close()

# Part 1, v2: Get all MG-RAST IDs associated with all organisms from a file.
if "-I" in argv:
	removal_targets_filename = string_find("-I")
	try:
		removal_targets_file = open (removal_targets_filename, "r")
	except IOError:
		sys.exit ("Unable to open file of target organisms to be removed.")
	
	org_targets = []
	
	for line in removal_targets_file:
		splitline = line.split("\t")
		if splitline[2] not in org_targets:
			org_targets.append(splitline[2])
	if quiet == False:
		print ("Targets file indexed.  " + str(len(org_targets)) + " target organisms will be screened against in the functions database.")
	
	# counters
	hit_counter = 0
	org_ID_dic = {}
	ID_list = []
	org_line_counter = 0

	t0 = time.clock()

	for line in org_infile:
		org_line_counter += 1
		for org_name in org_targets:
			if org_name in line:
				hit_counter += 1
				splitline = line.split("\t")
				org_ID_dic[splitline[1]] = splitline[3]
				ID_list.append(splitline[1])
		if org_line_counter % 100000 == 0:
			if quiet == False:
				print (str(float(org_line_counter)/float(org_file_length)*100) + "% completed\t-\t" +  str(org_line_counter) + " lines processed so far for MG-RAST org file.")

	t1 = time.clock()

	# Results of searching org infile
	print ("MG-RAST organism output searched.  Time elapsed: " + str(t1-t0) + " seconds.")
	print (str(len(ID_list)) + " IDs in list, " + str(hit_counter) + " total hits to all organisms from the removal file.")

	org_infile.close()

##########################################	

# Part 2: Searching each of these IDs from the org infile against the MG-RAST function results.
func_infile_name = string_find("-F")
try:
	func_infile = open (func_infile_name, "r")
except IOError:
	sys.exit("Unable to open function MG-RAST output file.")
	
# This part is for removing all thresholded-against organisms
if "-I" in argv:
	final_db = {}
	tally_db = {}
	line_counter = 0
	removed_counter = 0
	error_counter = 0
	
	t2 = time.clock()
	
	for line in func_infile:
		splitline = line.split("\t")
		line_counter += 1
		try:
			if splitline[1] in ID_list:
				removed_counter += 1
				continue
			else:
				final_db[splitline[1]] = splitline[3]
				try:
					tally_db[splitline[1]] += 1
				except KeyError:
					tally_db[splitline[1]] = 1
					continue
		except IndexError:
			error_counter += 1
			continue
		if line_counter % 100000 == 0:
			if quiet == False:
				print (str(line_counter) + " lines processed so far in function file.")
			
	t3 = time.clock()
				
# This part is for searching only for a single organism.
else:
	# build a database of all func results
	func_db = {}
	
	for line in func_infile:
		splitline = line.split("\t")
		try:
			func_db[splitline[1]] = splitline[3]
		except IndexError:
	#		print line
			continue
		
	print "Functional database of all entries successfully assembled."
	
	# matching to results from org file
	final_db = {}
	tally_db = {}
	error_counter = 0
	process_counter = 0
	
	t2 = time.clock()
	
	for org_ID in ID_list:
		process_counter += 1
		try:
			final_db[org_ID] = func_db[org_ID]
			try:
				tally_db[org_ID] += 1
			except KeyError:
				tally_db[org_ID] = 1
				continue
		except KeyError:
			error_counter += 1
			continue
	#			print ("Not matched in functional database:\t" + org_ID)
		if process_counter % 10000 == 0:
			if quiet == False:
				print (str(process_counter) + " lines processed so far in function file.")
	
	t3 = time.clock()

# outfile
if "-R" in argv:
	outfile_name = string_find("-R")
else:
	if "-N" in argv:
		outfile_name = org_name + "_results.tab"
	else:
		outfile_name = func_infile_name[:-4] + ".thresholded.tab"

outfile = open (outfile_name, "w")

for k, v in sorted(tally_db.items(), key=lambda (k,v): -v):
	outfile.write ( str(v) + "\t" + str(final_db[k]).strip() + "\t" + k + "\n") 

print ("All matches searched.  Time elapsed: " + str(t3-t2) + " seconds.")
if "-I" in argv:
	print ("Number of functional annotations removed: " + str(removed_counter))
else:
	print ("Number of different functional annotations found for organism " + org_name + ": " + str(len(set(final_db.values()))))

print ("Error rate: " + str(error_counter) + " errors out of " + str(len(ID_list)) + " total annotations.")

