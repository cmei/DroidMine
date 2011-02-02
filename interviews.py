import re
import urllib2
from urllib import urlencode
from getpass import getpass
from time import sleep
from os import system

######### constants ##########
PAGE_LOGIN = "https://jobmine.ccol.uwaterloo.ca/servlets/iclientservlet/SS/?cmd=login&languageCd=ENG&sessionId="
PAGE_INTERVIEWS = "https://jobmine.ccol.uwaterloo.ca/servlets/iclientservlet/SS/?ICType=Panel&Menu=UW_CO_STUDENTS&Market=GBL&PanelGroupName=UW_CO_STU_INTVS&RL=&target=main0"

FILE_JOBS = "/home/vardhan/jobs.dat" # must be an absolute path


######### config ############
INTERVAL = 1000 # check every INTERVAL seconds for new jobs
userid = "vmudunur"
pwd = ""



# don't touch the rest ---

opener = urllib2.build_opener( urllib2.HTTPCookieProcessor(), urllib2.HTTPRedirectHandler(), urllib2.HTTPSHandler() )
urllib2.install_opener(opener)

#
# ask for userid and passwd
#
def prompt():
	global userid, pwd

	if userid == "":
		print "Username:",
		userid = raw_input()
	
	if pwd == "":
		pwd = getpass()

#
# login to jobmine
#
def login():
	global userid, pwd, opener

	post_data = urlencode( {"userid": userid, "pwd": pwd, 'timezoneOffset': 300, 'submit': "Submit", 'httpPort': '' } )
	stream = opener.open(PAGE_LOGIN, post_data)
	while "Your User ID and/or Password are invalid." in stream.read():
		userid = pwd = ""
		print "Your User ID and/or Password are invalid."
		prompt()

		stream.close()
		return login()
	
	stream.close()

	print "Logged in!"

#
# load jobs from job file, return in a dictionary
#
def load_jobs():
	joblist = {}

	try:
		f = open(FILE_JOBS, 'r')
		for job in f:
			if job == "":
				continue
			fields = job.strip().split("\t")
			joblist[fields[0]] = [fields[1], fields[2]]
		f.close()
	except IOError:
		print "load_jobs failed"

	return joblist

#
# store jobs into job file
#
def store_jobs(jobs):
	f = 0
	try:
		f = open(FILE_JOBS, 'w')
	
		for jobid in jobs:
			f.write(jobid + "\t" + jobs[jobid][0] + "\t" + jobs[jobid][1] + "\n")
		f.close()
	except IOError:
		print "store_jobs failed"

#
# check interviews page, return dictionary of new jobs
#
def interviews():
	global opener

	joblist = load_jobs()

	stream = opener.open( PAGE_INTERVIEWS )
	data = stream.read()
	stream.close()

	# contains new elements that are going to be added to the job list
	joblist_new = {}

	# regex is overkill, but quick to write
	table = re.search("<TABLE dir=ltr BORDER=0 CELLPADDING=2 CELLSPACING=0 COLS=13 STYLE=\"BORDER-STYLE:NONE;\" CLASS='PSLEVEL1GRID'>(.+?)<\/TABLE>", data, re.M | re.S).group(1)

	# list of all the jobs
	jobs = re.findall("(<TR VALIGN=CENTER>(?:.+?)<\/TR>)+", table, re.M | re.S)

	jobi = 1 # job index
	while jobi < len(jobs):
		job = jobs[jobi]
		lines = job.split("\n")

		jobid = lines[3]
		company = lines[6]
		title = lines[10]
		title = re.search("\>(.+?)<\/A>", title).group(1);
		
		if jobid not in joblist:
			joblist[jobid] = [company, title]
			joblist_new[jobid] = [company, title]

		jobi = jobi + 1

	store_jobs(joblist)

	return (joblist_new,{})[len(joblist) == len(joblist_new)]

prompt()

while 1:
	login()
	new_list = interviews()

	for jobid in new_list:
		job = new_list[jobid]
		system("notify-send 'New Interview' '"+ new_list[jobid][0] +"\n"+ new_list[jobid][1] + "'")

	sleep(INTERVAL)
