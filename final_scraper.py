'''
Han Gu
4.11.17
This code takes a ticker, pulls down all 10-Ks available from the SEC Edgar database, and writes the contents of those 10-Ks to textfiles
'''

from pprint import pprint
import requests
from bs4 import BeautifulSoup
import sys

def loadTickerToCIKCrosswalk():
	infile = open('cik-ticker.csv', 'r')

	crosswalkDict = {}

	for line in infile:
		line = line.strip()
		thisRow = line.split(',')
		ticker = thisRow[0]
		cik = thisRow[1]

		crosswalkDict[ticker] = cik

	return crosswalkDict



tickerToCIKDict = loadTickerToCIKCrosswalk()


#Get page listing links to 10-K pages (not links to 10-K reports)
ticker = 'SAVE'

cikCodeForTicker = tickerToCIKDict[ticker]


baseURL = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=%s&type=10-K&dateb=&owner=exclude&count=100'


pageOfReportLinks = baseURL % cikCodeForTicker

print(pageOfReportLinks)
#Get all 10-K page links (not 10-K report links)




page = requests.get(pageOfReportLinks)
soup = BeautifulSoup(page.text)


table = soup.find('table', attrs={'class':'tableFile2', 'summary':'Results'})

# pprint(table)
rows = table.find_all('tr')

data = []




'''
https://www.sec.gov/Archives/edgar/data/1090872/000104746910010499/0001047469-10-010499-index.htm
http://www.sec.gov/Archives/edgar/data/320193/000119312510238044/0001193125-10-238044-index.htm
'''

for row in rows:
	cols = row.find_all('td')
	# try:
	# 	print(cols[1].find('a').get('href'))
	# except:
		# print('')
	cols = [ele.text.strip()  if not ele.find('a') else ele.find('a').get('href')  for ele in cols]
	data.append([ele for ele in cols if ele]) # Get rid of empty values




dictOf10KSummaryURLs = {}


for row in range(len(data)): 
	if len(data[row]) <= 0 or  data[row][0] != '10-K': 
		continue


	urlExt = data[row][1]
	summaryPageForThis10K = 'http://www.sec.gov' + urlExt

	date = data[row][3]
	year = date[: date.find('-')]



	dictOf10KSummaryURLs[year] = summaryPageForThis10K



allYears = list(dictOf10KSummaryURLs.keys())
allYears.sort()


#Get all values of the access number (a201610-k9242016.htm) for all 10Ks


dictOf10KHtmURLs = {}


for year in allYears:
	thisURL = dictOf10KSummaryURLs[year]

	summaryPage = requests.get(thisURL)
	soup = BeautifulSoup(summaryPage.text)


	table = soup.find('table', attrs={'class':'tableFile'})

	rows = table.find_all('tr')

	data = []

	for row in rows:
		cols = row.find_all('td')
		cols = [ele.text.strip() for ele in cols]
		data.append([ele for ele in cols if ele]) # Get rid of empty values


	#Get cell with 10K access number

	for row in range(len(data)):
		for col in range(len(data[row])):
			thisCell = str(data[row][col])

			if '10-K' in str(thisCell) or 'FOR THE FISCAL YEAR ENDED' in str(thisCell) or 'ANNUAL REPORT' in str(thisCell) :

				correctColumn = col + 1
				accessNumber = str(data[row][correctColumn])

				break


			

	baseURLForThisYear = thisURL[ : thisURL.rfind('/') + 1]

	dictOf10KHtmURLs[year] = baseURLForThisYear + accessNumber

pprint(dictOf10KHtmURLs)
#Get the text for all 10Ks

dictOf10KTexts = {}

for year in allYears:
	print(year)
	outfile = open(ticker + '_10K_' + year + '.txt', 'w')


	thisYear10KURL = dictOf10KHtmURLs[year]
	print(thisYear10KURL)
	textForThisYear10K = BeautifulSoup(requests.get(thisYear10KURL).text).get_text()

	dictOf10KTexts[year] = textForThisYear10K


	outfile.write(textForThisYear10K)

	outfile.close()




import os
import re
import pickle

def get_sections(filename):
    business_count = 0
    risk_count = 0
    line_count = 0
    business = re.compile('^\w{4,5}\s1\.$')
    risks = re.compile('^\w{4,5}\s1A\.$')
    end_section = re.compile('^\w{4,5}\s1B\.$')
    file = open(filename, 'rU')
    key = ""
    sections = {}
    match_found = False

    for line in file:
        line = line.replace("*", "")
        line = line.replace("|", "")
        line = line.replace("-", "")
        line = line.replace("?", "")
        line = line.strip()
        line_count+=1
        #if line_count >300 and line_count < 800:
         #   print(line)
        #if "Item" in line:
         #   print(line)
        #if business.match(line[:7]):
        if (line.lower()[:6] == "item 1" and "business" in line.lower()) or business.match(line[:7]):
            print(line, line_count)
            match_found = True
            business_count+=1
            if business_count == 1:
                key = "Business Overview"
                sections[key] = ""
            else:
                key = "Business Overview"
                sections[key] = ""
        #elif risks.match(line[:8]):
        elif (line.lower()[:7] == "item 1a" and "risk factors" in line.lower()) or risks.match(line[:8]): 
            #print(line, line_count)
            match_found = True
            print(line, line_count)
            risk_count+=1
            if risk_count == 1:
                key = "Risk Factors"
                sections[key] = ""
            else:
                key = "Risk Factors"
                sections[key] = ""
        #elif end_section.match(line[:8]):
        elif (line.lower()[:7] == "item 1b" and "unresolved" in line.lower()) or end_section.match(line[:8]):
            print(line, line_count)
            if line_count > 700:
                break
        else:
            if key != "":
                newline = sections[key] + line + "\n"
                sections[key] = newline
    
    if match_found is False:
        print("Unable to parse sections for " + filename)
    return sections


        
def forAll10Ks(directory):
    for filename in os.listdir(directory):
        for text_file in os.listdir(directory + '/' + filename + '/'):
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename + '/'))
                except OSError:
                    print("This didn't work")
                    
            sections = get_sections(directory + '/' + filename + '/' + text_file)
            filing = filename + "/" + text_file[:len(text_file)-4]+".p"
            pickle.dump(sections, open(filing, "wb"))


forAll10Ks("10Ks")


from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pickle as cPickle 
import editdistance
from os import listdir
from os.path import isfile, join


def convertSentenceToHashMap(x1):

	mapOne= {} 
	for word in x1:
		word.lower() #put all words in lowercase
		if(word not in mapOne): #Make a map with individual words as keys that point to an integer of their frequency
			mapOne[word]= 1
		else:
			mapOne[word]+= 1
	return mapOne

def benchmark(mapOne, mapTwo):
	duplicates= []
	sentenceOneUnique= []
	sentenceTwoUnique= []
	
	for key in mapOne: #Return the sum of the number of word matches between two sentences.
		if(key in mapTwo): 
			duplicates.append(key)
		else:
			sentenceOneUnique.append(key)

	for key in mapTwo:
		if key not in mapOne:
			sentenceTwoUnique.append(key)

	return duplicates, sentenceOneUnique, sentenceTwoUnique


from pprint import pprint
def computeNumDifferences(filename1,filename2):



	numChanges=0
	# print(filename1)
	dictOne = cPickle.load(open(filename1, "rb"))


	try:
		listOne = dictOne['Risk Factors'].split('.')
	except:
		return -1


	dictTwo= cPickle.load(open(filename2, "rb"))
	

	try:
		listTwo = dictTwo['Risk Factors'].split('.')
	except:
		return -1


	# pprint(listTwo)

	outputname=filename1+"matcher.txt"
	# text_file=open(outputname,"w")

	listOneCount = 0 

	sentCount = 0 
	
	for sentenceOne in listOne:

		sentCount = sentCount + 1
		# print(sentCount)

		dups= []
		max= 0.0
		listTwoCount= 0
		listTwoBestCount = 0
		for sentenceTwo in listTwo: 
			result = fuzz.ratio(sentenceOne, sentenceTwo)
			if(result>max):
				max= result
				listTwoBestCount= listTwoCount
				dups= benchmark(convertSentenceToHashMap(sentenceOne.split()), convertSentenceToHashMap(sentenceTwo.split()))
			listTwoCount+=1

		# if(max==100):
		# 	text_file.write(listOne[listOneCount]+"is the same as"+listTwo[listTwoBestCount]+ "\n")

		# else:
			# text_file.write('SENT 1: ' + listOne[listOneCount] + "\n")
			# text_file.write('is most similar to'+ "\n")
			# text_file.write('SENT 2: '+ listTwo[listTwoBestCount]+ "\n")
			# text_file.write("the benchmark is"+ str(max)+ "\n")
			# text_file.write("words matched "+ str(dups[0])+ "\n")	
			# text_file.write("unique to sentence one "+ str(dups[1])+ "\n")
			# text_file.write("unique to sentence two "+ str(dups[2])+ "\n")
		numChanges=numChanges+editdistance.eval(listOne[listOneCount], listTwo[listTwoBestCount])


		listOneCount+=1
	# 	text_file.write(""+ "\n")
	# text_file.close()
	return numChanges	

import pandas as pd
import pandas_datareader.data as web



# In[2]:

def get_returns(ticker, start_date, end_date):
    start_date = start_date
    df = web.DataReader(ticker, 'yahoo', start_date, end_date)
    df = df[['Adj Close']]
    df.columns = ['Adj_Close']
    df = df.Adj_Close.pct_change().to_frame()
    return df


def get_percent_change(ticker, start_date, end_date):

	start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
	end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

	print(start_date)
	print(end_date)

	# print(ticker)
	df = web.DataReader(ticker, 'yahoo', start_date, end_date)
	df = df[['Adj Close']]
	df.columns = ['Adj_Close']


	priceOnStartDate = float(df.iloc[0])
	priceOnEndDate = float(df.iloc[-1])

	return (priceOnEndDate - priceOnStartDate) / priceOnStartDate

#"A_10k_GOOG_year_releasedate"

import csv
import datetime
import sys 

timeHorizon = 120 #in days (~20 days per month)

if __name__ == "__main__":

	b = open('test.csv', 'w')
	a = csv.writer(b)
	data=[]

	all10KsDirName = "Pickles/"

	listOfFolderNamesForAllPickleFiles = [folder_name for folder_name in listdir(all10KsDirName) if folder_name.find('.') <= -1]


	dictOf10K_to_textChanges_to_priceChanges = {}

	for folder in listOfFolderNamesForAllPickleFiles:
	    #ticker name is file
	    pickleFolderPath = all10KsDirName + folder + "/"

	    listOfPickleFilesForThisTicker = sorted([pickleFolderPath + file_name  for file_name in listdir(pickleFolderPath) ])


	    for fileIndex in range(len(listOfPickleFilesForThisTicker) - 1):
	    	yearlyData=[]
	    	# try:
	    	firstPickleFileName = listOfPickleFilesForThisTicker[fileIndex] #previous year
	    	secondPickleFileName = listOfPickleFilesForThisTicker[fileIndex + 1] #this year

	    	# print(firstPickleFileName)

	    	ticker = secondPickleFileName[ secondPickleFileName.rfind('/') + 1 : secondPickleFileName.find('_')]

	    	yearlyData.append(ticker)
	    	current_date_string = secondPickleFileName[ secondPickleFileName.rfind('_') + 1 : secondPickleFileName.find('.') ]
	    	# print(current_date_string)
	    	# print(current_date_string)

	    	currentDate_datetime = datetime.datetime.strptime(current_date_string, "%Y-%m-%d")

	    	yearlyData.append(current_date_string)

	    	end_date = currentDate_datetime + datetime.timedelta(days = timeHorizon)

	    	end_date_string = end_date.strftime('%Y-%m-%d')

	    	# print(end_date_string)


	    	# try:

    		numDiffsForThisCombo = computeNumDifferences(secondPickleFileName,firstPickleFileName) #compute # diffs btw this year and last year's 10Ks
    		yearlyData.append(numDiffsForThisCombo)

    		if numDiffsForThisCombo < 0:
    			continue
	    	# except:
	    	# 	continue

	    	# print(numDiffsForThisCombo)



	    	try:
	    		princeChange = get_percent_change(ticker, current_date_string, end_date_string)
	    	except:
	    		break



	    	dictOf10K_to_textChanges_to_priceChanges[secondPickleFileName] = [numDiffsForThisCombo, princeChange]
	    	data.append(yearlyData)
	    	# except:
		    # 	continue
	a.writerows(data)
	b.close()
	cPickle.dump(dictOf10K_to_textChanges_to_priceChanges, open("finalfile.p", 'wb')) 
	print(dictOf10K_to_textChanges_to_priceChanges)






