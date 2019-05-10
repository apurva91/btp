from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from . import goldencorpus
from . import mesh_explosion
from . import clusterer
from . import postprocessing
from . import mesh_explosion
from . import biological_model
from collections import Counter, OrderedDict
from stop_words import get_stop_words  # use as : list(get_stop_words('en'))
from nltk.corpus import stopwords      # use as : list(stopwords.words('english'))
import scispacy,spacy
import nltk
import json
import re
import operator
import pickle
import tqdm
import numpy as np

best_mesh_terms_id = OrderedDict()
best_mesh_terms = OrderedDict()
tags = []
query = None
filepath = None
stop_words = []
mesh_terms = []

def index(request):
	global stop_words
	# get stopwords into an list
	f = open("home/english",'r')
	stop_words = f.read().split()
	return render(request,'home/index.html')
    
def post(request,isfeedback = None,feedobj = None):
	global best_mesh_terms
	global best_mesh_terms_id
	global query
	global filepath
	global tags
	global mesh_terms

	ismorefilter = 0
	representative_id = 0
	representative = None


	if request.method == 'POST':
		
		if isfeedback :
			print("feedback")
			query = feedobj['query']
			filepath = feedobj['filepath']
			ismorefilter = feedobj['ismorefilter']
		else:
			print("simple")
			query = request.POST.get('query',None)
			filepath = request.POST.get('genefile',None)
		if query:
			if filepath:
				corpus = goldencorpus.GoldenCorpus(query,filepath)
				found,mesh_terms = corpus.fetchData()
				if not found:
					return HttpResponse("Error in fetching data")
				else:
					if ismorefilter:
						print("came")
						feedbackarr = feedobj['feedbackarr']
						print("arr: ",feedbackarr)
						rel_docs = corpus.get_rel_docs_pmid(feedbackarr)
					else:
						rel_docs = corpus.get_rel_docs_pmid(None)
					# mesh_terms = corpus.get_mesh_terms()
					if len(mesh_terms) > 0:
						mesh_exp = mesh_explosion.DataForEachMeshTerm(mesh_terms,query)
						path = mesh_exp.get_data_foldername(query)
						clus = clusterer.Clusterer(rel_docs,path,True,5)
						# Keeping globaly to get access from other functions
						representative_id,representative, best_mesh_terms_id, best_mesh_terms = clus.cluster()
					else:
						return HttpResponse("No meshterms received from pubmed")

					if representative:
						# get all information for representative json
						pp = postprocessing.PostProcessing()
						# tags = pp.term_tagging(best_mesh_terms)
						trimmedtitles , trimmedabs, completeabs = pp.getTitleAbs(0,representative_id,query) 
						topdocs = zip(trimmedtitles, trimmedabs)
						
						topmesh = OrderedDict()
						for clus_no,json_arr in best_mesh_terms.items():
							topmesh[clus_no] = zip(json_arr,best_mesh_terms_id[clus_no])

						previndex = -10
						nextindex = 10
						currindex = 0
						context = {
							'query' : query,
							'topdocs' : topdocs,
							'topmesh' : topmesh,
							# 'tags' : tags,
							'currindex' : currindex,
							'previndex' : previndex,
							'nextindex' : nextindex,
							'json_no' : representative_id,
						}
						return render(request,'home/detail.html',context)
					else:
						return HttpResponse("No result found!!")
			else:
				return HttpResponse("No gene file found in post request !!")
		else:
			return HttpResponse("No query found in post request!!")
	else:
		return HttpResponse("Not a post request!")

def get(request, json_no):
	global best_mesh_terms
	global best_mesh_terms_id
	global tags
	global query

	if request.method == 'GET':

		pp = postprocessing.PostProcessing()
		# tags = pp.term_tagging(mesh)
		trimmedtitles , trimmedabs, completeabs = pp.getTitleAbs(0,json_no,query) 
		topdocs = zip(trimmedtitles, trimmedabs)
		
		topmesh = OrderedDict()
		for clus_no,json_arr in best_mesh_terms.items():
			topmesh[clus_no] = zip(json_arr,best_mesh_terms_id[clus_no])

		previndex = -10
		nextindex = 10
		currindex = 0
		context = {
			'query' : query,
			'topdocs' : topdocs,
			'topmesh' : topmesh,
			# 'tags' : tags,
			'currindex' : currindex,
			'previndex' : previndex,
			'nextindex' : nextindex,
			'json_no' : json_no,
		}
		return render(request,'home/detail.html',context)

def paginate(request, json_no, abs_index):
	global best_mesh_terms
	global best_mesh_terms_id
	global tags
	global query

	pp = postprocessing.PostProcessing()
	trimmedtitles , trimmedabs, completeabs = pp.getTitleAbs(abs_index,json_no,query) 
	topdocs = zip(trimmedtitles, trimmedabs)
	
	topmesh = OrderedDict()
	for clus_no,json_arr in best_mesh_terms.items():
		topmesh[clus_no] = zip(json_arr,best_mesh_terms_id[clus_no])

	previndex = abs_index - 10
	nextindex = abs_index + 10	
	currindex = abs_index
	context = {
		'query' : query,
		'topdocs' : topdocs,
		'topmesh' : topmesh,
		# 'tags' : tags,
		'currindex' : currindex,
		'previndex' : previndex,
		'nextindex' : nextindex,
		'json_no': json_no,
		# 'isrf' : isrf
	}
	return render(request,'home/detail.html',context)

def cluster_by_jsonno(json_no):
	global best_mesh_terms_id
	print(best_mesh_terms_id)
	json_arr = []
	for k,v in best_mesh_terms_id.items():
		for jno in v:
			if json_no == jno:
				json_arr = v
				break
	return json_arr

def genecloud(request, json_no):
	global query
	global filepath

	pp = postprocessing.PostProcessing()
	if query and filepath:
		flag , gene_arr = pp.gene_cloud(json_no,filepath,query)
		if flag:
			return render(request, 'home/genecloud.html',{'gene_arr': gene_arr})
		else:
			return render(request, 'home/genecloud.html',{'gene_arr': None, 'message': "Wrong file path !"})
	else:
		print("No query or no file path")
		return HttpResponse("Something wrong with gene cloud!")

def meshcloud(request, json_no):
	global query
	pp = postprocessing.PostProcessing()
	flag,meshobj = pp.mesh_cloud(json_no,query)
	if flag:
		return render(request, 'home/meshcloud.html', {'meshobj': meshobj})
	else:
		return HttpResponse("Something wrong with mesh cloud!")

def generelation(request, json_no):
	return HttpResponse("From gene relation")

def entities(request,json_no,eoption):
	global query

	print("json_no: ", json_no)
	print("option: ", eoption)
	json_arr = cluster_by_jsonno(json_no)
	print("arr: ",json_arr)
	pp = postprocessing.PostProcessing()
	flag,allentities,data = pp.get_entities(query,json_arr,eoption)
	# print(allentities)
	if flag:
		return render(request,'home/entities.html',{'entities': allentities,'data':data})
	else:
		return HttpResponse("No entities")

def paperdetail(request,json_no,currindex,offset):
	# open json
	global query

	dfet = mesh_explosion.DataForEachMeshTerm(None,None)
	data_folder_name = dfet.get_data_foldername(query)
	f = open(data_folder_name+"/"+str(json_no)+".json", 'r')
	json_object = json.load(f)
	f.close()
	abstracts = json_object["abstracts"]
	titles = json_object["titles"]
	mesh_terms = json_object["meshterms"]
	pmids = json_object["articleIds"]
	# print(mesh_terms)
	# tag gene in abstract
	# for txt file
	_filepointer = open("home/gene.txt",'r')
	_genefile = _filepointer.read().split('\n')

	for gene in _genefile:
		if len(gene) > 0:
			toreplace = "<span class='highlight'>\g<0></span>"
			pattern = re.compile(re.escape(gene), re.I)
			abstracts[currindex+offset] = re.sub(pattern,toreplace,abstracts[currindex+offset])

	# path = ("home/" + self.filepath)
	# wb = xlrd.open_workbook(path)
	# sheet = wb.sheet_by_index(0)
	context = {
		'title' : titles[currindex + offset],
		'abstract' : abstracts[currindex + offset],
		'pmid' : pmids[currindex + offset],
		'meshterm' : mesh_terms[currindex + offset],
		'json_no': json_no,
		'index' : currindex + offset
	}

	return render(request,'home/paperdetail.html',context)

def seesimilar(request,json_no,currindex,offset):
	return HttpResponse("From seesimilar")

def feedback(request):
	global stop_words
	global mesh_terms
	global filepath
	global query

	error_occured = 0
	try:
		str_data = request.POST.get('feedback',None)
		option = request.POST.get('option',None)
		choice = request.POST.get('choice',None)
		json_no = request.POST.get('json_no',None)
	except KeyError:
		return HttpResponse("No feedback data found in the request object !!")
	data = json.loads(str_data)
	print("option: ",option)
	print("choice: ",choice)
	print("json_no: ",json_no)
	# Work with new data 
	
	relevant_indices = []
	irrelevant_indices = []
	if int(choice) == 1: # Relevance feedback
		for obj in data:
			if data[obj]['relevant'] == 1:
				relevant_indices.append(data[obj]['offset'])
			else:
				irrelevant_indices.append(data[obj]['offset'])
		# For each relevant paper count frequency of each word and 
		# consider top frequent terms for next search
		print("relevant indices: ",relevant_indices)
		# print("irrele: ", irrelevant_indices)
	elif int(choice) == 2: #Psudo-relevance : choose top 5 documents blindly
		for index in range(0,5):
			relevant_indices.append(index)
	if json_no:
		try:
			file_name = "home/data_folder/"+query+"/"+str(json_no)+'.json'
			print("file: ", file_name)
			with open(file_name, 'r') as f:
				json_object = json.load(f)
		except IOError as e:
			# return error feedback to user
			error_occured = 1
	if not error_occured:
		data_abstract = json_object["abstracts"]
		data_mesh = json_object["meshterms"]
		abs = ""
		relevant_meshterms = []
		if len(relevant_indices) > 0:
			for index in relevant_indices:
				abs += data_abstract[index]
				relevant_meshterms.append(data_mesh[index])
		
		# Recognize entities and count frequency
		# Method one : using scispacy
		frequency = {}
		if int(option) == 1:
			nlp = spacy.load("en_ner_bionlp13cg_md")
			doc = nlp(abs)
			entities = ""
			for ent in doc.ents:
				entities += str(ent) + " "
			frequency = Counter(entities.split()).most_common()
		# print(frequency)

		# Method two: Association mining
		# calculate association 'interest measure for each unique concept' and get the top scored concepts
		# for next round of search
		relevant_abs = []
		if int(option) == 2:
			for index in relevant_indices:
				relevant_abs.append(data_abstract[index])
			alllines = findalllines(relevant_abs)
			allconcepts = findallconcepts(relevant_abs)
			print("allconcepts: ",len(allconcepts))
			concept_score = {}
			for concept in allconcepts:
				# find interest measure for a particular concept
				# print("concept: ",concept)
				conceptcount = 0
				partialquerycount = 0
				intersectioncount = 0
				for line in alllines:
					queryexist = getPartialQueryCount(line,query)
					if isbelong(line,concept):
						conceptexist = 1
					else:
						conceptexist = 0
					intersectionexist = queryexist*conceptexist
					# update total count for each concept
					conceptcount += conceptexist
					partialquerycount += queryexist
					intersectioncount += intersectionexist
				# calculate interest measure for selected concept
				mul = conceptcount * partialquerycount
				if mul:
					concept_score[str(concept)] = len(alllines)*intersectioncount / mul
			# sort concept_socore by value
			concept_score = sorted(concept_score.items(), key=operator.itemgetter(1),reverse=True)
			# print(concept_score)
			with open('concept', 'wb') as con:
				pickle.dump(concept_score,con)
			# Find top k terms : using pretrained model 
			# Load XGboost trained model
			# Then predict 
			# biological_model.dataset_prepare()
			return HttpResponse("Will take long time . Better do in colab.research")
			wordfile = 'word_representation'
			word_dict = {}
			with open(wordfile,'rb') as f:
				word_dict = pickle.load(f)
			print("word loaded")
			filename = 'finalized_model.sav'
			loaded_model = pickle.load(open(filename, 'rb'))
			print("model loaded")
			# Predict
			c = 0
			x_test = []
			for k,v in concept_score:
				try:
					x_test.append(word_dict[str(k)])
				except KeyError:
					continue
			print("test data done")
			y_pred = loaded_model.predict(x_test)
			print("prediction success")
			c = 0
			for i in range(0,len(y_pred)):
				if y_pred[i] == 1:
					frequency[str(x_test[i])] = 1
					c += 1
				if c >= 4:
					break
			print(frequency)
		# First method : find intersection with all mesh explosion and return result for nearest mesh
		# mesh_explo = mesh_explosion.DataForEachMeshTerm(None,None)
		# expanded_mesh_terms = mesh_explo.getMeshTermCombinations(mesh_terms)
		# print(expanded_mesh_terms)

		# Second method: add top terms with user query and search
		ii = 0
		feedbackquery = query
		for k,v in frequency:
			feedbackquery = feedbackquery +" "+ str(k)
			ii = ii + 1
			if ii > 2: break
		myobj = {'query' : feedbackquery, 'filepath' : filepath,'ismorefilter' : 0}
		print(myobj)

		# Third method: Use top terms as filter to create golden corpus
		# ii = 0
		# feedbackarr = []
		# for k,v in frequency:
		# 	feedbackarr.append(k)
		# 	ii = ii + 1
		# 	if ii >= 5: break
		# myobj = {'query' : query,'filepath': filepath,'ismorefilter' : 1,'feedbackarr': feedbackarr}

		return post(request,1,myobj)
	else: # error reading json file
		return HttpResponse("Error in reading json file")

def findalllines(abstracts):
	abslist = []
	line = ""
	nline = 0
	for abs in abstracts:
		for x in range(0,len(abs)):
			if abs[x] == '.':
				if x < len(abs) - 1 and abs[x+1].isupper():
					nline += 1
				elif x == len(abs) - 1:
					nline += 1
				abslist.append(line)
				line = ""
			else:
				line += abs[x]
	return abslist

def findallconcepts(abstracts):
	conceptlist = []
	upperconceptlist = []
	python_s_words = list(get_stop_words('en'))         #About 900 stopwords
	nltk_words = list(stopwords.words('english'))       #About 150 stopwords
	python_s_words.extend(nltk_words)
	python_s_words = [word.upper() for word in python_s_words]
	for abs in abstracts:
		for word in abs.split():
			if not word.upper() in python_s_words:
				if not word.upper() in upperconceptlist:
					conceptlist.append(word)
					upperconceptlist.append(word.upper())
	return conceptlist

def getPartialQueryCount(line,query):
	python_s_words = list(get_stop_words('en'))         #About 900 stopwords
	nltk_words = list(stopwords.words('english'))       #About 150 stopwords
	python_s_words.extend(nltk_words)
	line_words = [word for word in line.split() if word not in stop_words]
	query_words = [word for word in query.split() if word not in stop_words]

	count = 0
	for lw in line_words:
		if lw in query_words:
			count += 1
	weighted_interested = count/len(query_words)
	return weighted_interested

def isbelong(line, concept):
	for word in line.split():
		if concept == word:
			return 1
	return 0

