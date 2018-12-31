#!/usr/bin/python
#######Nathan Gilbert
######chartparser.py
#####Septemember 5, 2006
####CS 6340 - Natural Language Processing

import sys
from string import strip, lower
from copy import deepcopy

#A rule from the grammar. 
class Rule:
	def __init__(self,l,r):
		self.lhs = l
		self.rhs = r
	
	def __str__(self):
		return "%s -> %s" % (self.lhs,self.rhs) 

#A word in the dictionary, and its part of speech (POS).
class Word:
	def __init__(self):
		self.word = "" 
		self.pos = []
	
	def setWord(self, w):
		self.word = w

	def setPOS(self, pos):
		self.pos.append(pos)

	def getPOS(self):
		return self.pos

	def getWord(self):
		return self.word

	def __str__(self):
		return "%s := %s" % (self.word,self.pos)

#A row in the chart.
class Row:
	def __init__(self):
		self.lIndex = 0							#The left index number in the sentence for this row.
		self.rIndex = 0							#The right " " " "
		self.label = ""							#The actual POS/terminal that this row represents.
		self.found = []							#What has currently been found for this rule.
		self.toFind = []							#What remains to be found for this rule. 
		self.relatives = []						#Links to this rows children. i.e., this rows constituents. 
	
	def __init__(self, l, r, label, f=[], tof=[], relate=[]):
		self.lIndex = l
		self.rIndex = r 
		self.label = label
		self.found = f
		self.toFind = tof
		self.relatives = relate

	def getToFind(self):
		return self.toFind

	def getRelatives(self):
		return self.relatives

	def addRelative(self, r):
		self.relatives.append(r)

	def pp(self):
		"""The condensed pretty pring function."""
		return "\nCurrent Label:%s\nLeft Index:%d\nRight Index:%d\nTo Find:%s\nFound:%s\nRelatives:%s " % (self.label,self.lIndex,self.rIndex,self.toFind,self.found, self.relatives)

	def prettyPrint(self,t=""):
		tab = t
		childBuffer = tab + self.label

		if (len(self.relatives) > 0):
			for kid in self.relatives:
				if not len(kid.relatives) > 0:
					childBuffer += ": %s" % kid.label
				else:
					childBuffer += "\n%s" % kid.prettyPrint(tab + "  ")

		return childBuffer

	def __str__(self):
		return self.prettyPrint()

####################################################################
#MAIN
####################################################################
def main(args):
	"""The body of the chart parser.  """

	#Command line argument processing. 
	if len(args) < 3 or (("-h" in args) or ("--help" in args)):
		print "Usage: parser <dictionaryfile> <grammarfile> <sentencesfile>"
		print "Debugging: parser <dictionaryfile> <grammarfile> <sentencefile> +DEBUG"
		sys.exit(0)

	#If DEBUG == true then print debugging information. 
	if "+DEBUG" in args:
		DEBUG = True 
	else:
		DEBUG = False

	inDict = args[0]
	inGram = args[1]
	inSent = args[2]

	try:
		dictFile = open(inDict, "r")
	except IOError:
		print "Dictionary file not found."

	try:
		gramFile = open(inGram, "r")
	except IOError:
		print "Grammar file not found."

	try:
		sentenceFile = open(inSent, "r")
	except IOError:
		print "Sentence file not found."

	#Removing all upper case letter, and stripping any newlines or tab characters from the edges. 
	#Storing all sentences to be parsed in one list. 
	sentenceList = map(strip, map(lower, list(sentenceFile)))

	if DEBUG:
		print "------------------------------"
		print "Sentence List:"
		print "------------------------------"
		for line in sentenceList:
			print line

	#One list to hold them (rules) ...
	ruleList = []
	tmp = []

	for line in gramFile:
		tmp = line.split('->')
		ruleList.append(Rule(*map(strip,tmp)))

	
	wordList = list(dictFile)
	dictionary = []												#contains all the words in the dictionary, matced with their part of speech. 
	w = Word()
	tmp = []

	#Gathering all words and placing them in a dictionary with their relevant parts of speech. 
	for word in wordList:
		tmp = word.split()

		#Check to make sure the word is not already in the dictionary. 
		if tmp[0].strip() in map(lambda x: x.getWord(), dictionary):
			continue

		w.setWord(tmp[0].strip())
		w.setPOS(tmp[1].strip())
		
		#Collecting all other parts of speech for this word. 
		for pair in wordList[wordList.index(word)+1:]:
			p = pair.split()
			if w.getWord() == p[0].strip():
				w.setPOS(p[1].strip())

		dictionary.append(w)
		w = Word()											#clearing the word

	if DEBUG:
		print "\n------------------------------"
		print "Rules:"
		print "------------------------------"
		for r in ruleList:
			print r

		print "\n------------------------------"
		print "Dictionary: "
		print "------------------------------"
		for word in dictionary:
			print word

	#closing file streams.
	dictFile.close()
	gramFile.close()
	sentenceFile.close()

	#Where the magic happens. 
	for s in sentenceList:
		print "----------------------------------------------------------------------"
		print "SENTENCE: %s" % s
		print "----------------------------------------------------------------------"
		curr = s.split()												#splits current string into a list of words. 
		size = len(curr)
		agenda = []
		chart = []
		trees = 0
		
		if DEBUG:
			print "\n%s" % curr

			#0 is the left wall, len(curr) is the right wall of sentence. 
			print size

		w = ""
		c = []
		count = 0
		
		while(len(curr) > 0):

			#initialization rule, curr is a queue.
			w = curr.pop(0)
			
			#keeping a record of where we are in the sentence. 
			count = count + 1

			#create row in chart for each pos and add to agenda
			try:
				index = map(lambda x:x.getWord(), dictionary).index(w)
			except ValueError:
				print "Word not in dictionary: %s" % w
				sys.exit(0)
		
			#generating rows for each pos a word has, then pushing them onto the agenda. 
			for pos in dictionary[index].getPOS():
				agenda.append(Row(count - 1, count, pos, [w],[] , [Row(count,count, w,[] ,[] ,[])]))

			while(len(agenda) > 0):

				#it's a stack. 
				#a = agenda.pop()
				#it's a queue.
				a = agenda.pop(0)
				
				if DEBUG:
					print a
					print "Just popped off agenda..."

				#pushing the initial word and its POS onto the chart.
				if len(a.getToFind()) == 0:
					c.append(a)

				#check for new matches from the rule list
				#This looks through the rule list for rules that could apply
				#to this section of the sentence and it's respective POS. 
				for rule in ruleList:
					newFind = rule.rhs.split()
					if newFind[0] == a.label:
						del newFind[0]
						newRow = Row(a.lIndex, a.rIndex, rule.lhs, [a.label], newFind, [a])

						if len(newFind) == 0:
							agenda.append(newRow)
						else:
							c.append(newRow)

				#check chart to see if this new addition completes or continues any partial matches.
				#looks through chart to see if any new rows can be created by appended to an active arc. 
				for element in c:
					if len(element.getToFind()) > 0 and element.toFind[0] == a.label and element.rIndex == a.lIndex:
						newFind = deepcopy(element.getToFind())
						del newFind[0]
						newRelatives = deepcopy(element.getRelatives())
						newRelatives.append(a)
						newFound = deepcopy(element.found)
						newFound.append(a.label)
						newRow = Row(element.lIndex, a.rIndex, element.label, newFound, newFind, newRelatives)	

						if len(newRow.getToFind()) == 0:
							agenda.append(newRow)
						else:
							c.append(newRow)

		#Random debug info.
		if DEBUG:
			print "\n------------------------------"
			print "Final elements on chart. "
			print "------------------------------"
			for element in c:
				print element
			print "------------------------------"

		#Printing out trees, must be an S row, that spans entire sentence and has no more elements in its 
		#'to find' list. 
		for element in c:
			if element.label == "S" and (element.lIndex == 0 and element.rIndex == count and (len(element.toFind) == 0)):
				trees += 1
				print "\nPARSE #%d" % trees
				print "%s\n" % element

		print "\nFinished: found %d parse tree(s)\n" % trees

if __name__ == "__main__":
	main(sys.argv[1:])

