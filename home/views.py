from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from . import goldencorpus
from . import mesh_explosion
from . import clusterer
from . import postprocessing
from . import mesh_explosion
from . import biological_model
from . import entity_recognition as enrecog
from . import relation_data_prepare as relation
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
gene_filepath = None
pmid_filepath = None
gene_set = []
stop_words = []
mesh_terms = []

def index(request):
	return render(request,'home/index.html')
    
def post(request,isfeedback = None,feedobj = None):
	global best_mesh_terms
	global best_mesh_terms_id
	global query
	global gene_filepath
	global pmid_filepath
	global gene_set
	global cluster_algo
	global tags
	global mesh_terms

	representative_id = 0
	representative = None

	if request.method == 'POST':
		# if it is a call from feedback method
		if isfeedback :
			print("feedback")
			query = feedobj['query']
			gene_filepath = feedobj['gene_filepath']
			pmid_filepath = feedobj['pmid_filepath']
			gene_set = feedobj['gene_set']
			cluster_algo = feedobj['cluster_algo']
		else:
			print("non feedback")
			query = request.POST.get('query',None)
			gene_filepath = request.POST.get('genefile',None)
			pmid_filepath = request.POST.get('pmidfile',None)
			gene_set = request.POST.get('geneset',None)
			cluster_algo = request.POST.get('cluster',None)
		if query:
			# create golden corpus
			if gene_filepath or gene_set:
				corpus = goldencorpus.GoldenCorpus()
				found,mesh_terms = corpus.fetchData(query,10000)
				if not found:
					return HttpResponse("Error in fetching data")
				else:
					rel_docs = corpus.get_rel_docs_pmid(query,gene_filepath,gene_set)
					# return HttpResponse("testing")
			# Golden corpus given
			else:
				path = "home/"+pmid_filepath
				with open(path,"r") as fp:
					rel_docs = fp.read().split('\n')
				# print(rel_docs)
				if len(rel_docs) < 20:
					return render(request,'home/error.html',{"message":"Please give atleast 20 PMIDs"})
			if len(mesh_terms) > 0:
				mesh_exp = mesh_explosion.DataForEachMeshTerm(mesh_terms,query)
				path = mesh_exp.get_data_foldername(query)
				if cluster_algo == None or int(cluster_algo) == "1":
					print("kmean")
					clus = clusterer.Clusterer(rel_docs,path,True,5)
				else:
					print("dbscan")
					clus = clusterer.Clusterer(rel_docs,path,False,5)
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
	global gene_filepath

	json_arr = cluster_by_jsonno(json_no)
	pp = postprocessing.PostProcessing()
	flag,data = pp.gene_cloud(query,json_arr)
	if flag:
		return render(request, 'home/genecloud.html',{'data': data})
	else:
		return HttpResponse('Something wrong : check postprocessing.py')

def meshcloud(request, json_no):
	global query
	pp = postprocessing.PostProcessing()
	flag,meshobj = pp.mesh_cloud(json_no,query)
	if flag:
		return render(request, 'home/meshcloud.html', {'meshobj': meshobj})
	else:
		return HttpResponse("Something wrong with mesh cloud!")

def entityrelation(request, json_no, option):
	global query

	json_arr = cluster_by_jsonno(json_no)
	pp = postprocessing.PostProcessing()
	flag,data = pp.entityrelation(query,json_arr)
	if flag:
		return render(request,'home/multirelation.html',{"data": data})
	else:
		return render(request,'home/error.html',{"message":"Something wrong with entity relation"})

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


	abstracts = []
	titles = []
	mesh_terms = []
	pmids = []
	# get data folder path
	dfet = mesh_explosion.DataForEachMeshTerm(None,None)
	data_folder_name = dfet.get_data_foldername(query)
	with open(data_folder_name+"/"+str(json_no)+".json", 'r') as f:
		json_object = json.load(f)
		abstracts = json_object["abstracts"]
		titles = json_object["titles"]
		mesh_terms = json_object["meshterms"]
		pmids = json_object["articleIds"]
	disease = []
	gene = []
	protein = []
	# calling rule based entity recognition model
	# disease,gene,protein = enrecog.entity_recog_nn(abs)
	disease,gene,protein = enrecog.entity_recog_rb(abstracts[currindex+offset])
	if disease:
		disease = list(disease)
	if gene:
		gene = list(gene)
	if protein:
		protein = list(protein)
	if len(disease):
		for rog in disease:
			toreplace = "<span class='disease-highlight' data-toggle=\"tooltip\" title=\"Disease\">\g<0></span>"
			if len(rog) > 2:
				pattern = re.escape(rog)
				abstracts[currindex+offset] = re.sub(pattern,toreplace,abstracts[currindex+offset])
				titles[currindex+offset] = re.sub(pattern,toreplace,titles[currindex+offset])
				# mesh_terms[currindex+offset] = re.sub(pattern,toreplace,mesh_terms[currindex+offset])
	if len(protein):
		for pro in protein:
			toreplace = "<span class='protein-highlight' data-toggle=\"tooltip\" title=\"Protein\">\g<0></span>"
			if len(pro) > 2:
				pattern = re.escape(pro)
				abstracts[currindex+offset] = re.sub(pattern,toreplace,abstracts[currindex+offset])
				titles[currindex+offset] = re.sub(pattern,toreplace,titles[currindex+offset])
				# mesh_terms[currindex+offset] = re.sub(pattern,toreplace,mesh_terms[currindex+offset])
	if len(gene):
		for _g in gene:
			toreplace = "<span class='gene-highlight' data-toggle=\"tooltip\" title=\"Gene\">\g<0></span>"
			if len(_g) > 2:
				pattern = re.escape(_g)
				abstracts[currindex+offset] = re.sub(pattern,toreplace,abstracts[currindex+offset])
				titles[currindex+offset] = re.sub(pattern,toreplace,titles[currindex+offset])
				# mesh_terms[currindex+offset] = re.sub(pattern,toreplace,mesh_terms[currindex+offset])

	context = {
		'title' : titles[currindex + offset],
		'abstract' : abstracts[currindex + offset],
		'pmid' : pmids[currindex + offset],
		'meshterm' : mesh_terms[currindex + offset],
		'json_no': json_no,
		'index' : currindex + offset
	}

	return render(request,'home/paperdetail.html',context)
	# relation.data_prepare()
	# return HttpResponse("called relation")

def seesimilar(request,json_no,currindex,offset):
	return HttpResponse("From seesimilar")

def feedback(request):
	global stop_words
	global mesh_terms
	global gene_filepath
	global pmid_filepath
	global gene_set
	global cluster_algo
	global query

	error_occured = 0
	try:
		str_data = request.POST.get('feedback',None)
		option = request.POST.get('option',None)
		choice = request.POST.get('choice',None)
		json_no = request.POST.get('json_no',None)
	except KeyError:
		return render(request,'home/error.html',{"message":"No feedback data found in the request object"})
	data = json.loads(str_data)
	
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
		
		if int(option) == 1:
			nlp = spacy.load("en_ner_bionlp13cg_md")
			doc = nlp(abs) #only returns bio-medical terms
			entities = "" 
			for ent in doc.ents:
				entities += str(ent) + " "
			frequency = Counter(entities.split()).most_common()

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
			print(concept_score)
			# with open('concept', 'wb') as con:
			# 	pickle.dump(concept_score,con)
			# Find top k terms : using pretrained model 
			# Load XGboost trained model
			# Then predict 
			# biological_model.dataset_prepare()
			# return HttpResponse("Will take long time . Better do in colab.research")
			# wordfile = 'word_representation'
			# word_dict = {}
			# with open(wordfile,'rb') as f:
			# 	word_dict = pickle.load(f)
			# print("word loaded")
			# filename = 'finalized_model.sav'
			# loaded_model = pickle.load(open(filename, 'rb'))
			# print("model loaded")
			
			# Predict
			# c = 0
			# x_test = []
			# for k,v in concept_score:
			# 	try:
			# 		x_test.append(word_dict[str(k)])
			# 	except KeyError:
			# 		continue
			# print("test data done")
			# y_pred = loaded_model.predict(x_test)
			# print("prediction success")
			# c = 0
			# for i in range(0,len(y_pred)):
			# 	if y_pred[i] == 1:
			# 		frequency[str(x_test[i])] = 1
			# 		c += 1
			# 	if c >= 4:
			# 		break
			# print(frequency)

			# simple top k terms of association mining
			frequency = []
			c = 0
			for item in concept_score:
				frequency.append(item)
				c += 1
				if c == 2:
					break
			print(frequency)
		# add top terms with user query and search
		ii = 0
		feedbackquery = query
		# print(frequency)
		# print("Top terms: ")
		for k,v in frequency:
			# print(str(k))
			feedbackquery = feedbackquery +" "+ str(k)
			ii = ii + 1
			if ii > 2: break
		myobj = {'query' : feedbackquery, 'gene_filepath' : gene_filepath, 'pmid_filepath' : pmid_filepath, 'gene_set' : gene_set, 'cluster_algo': cluster_algo}

		return post(request,1,myobj)
	else: 
		return render(request,'home/error.html',{"message":"No json file found"})

def processmesh(meshstring):
	mesh = ""
	found = 0
	for c in meshstring:
		if c == '/':
			found = 1
	if found:
		mesharr = meshstring.split('/')
		for i in range(0,len(mesharr)-1):
			mesh += mesharr[i] + ' '
		return mesh
	else:
		return meshstring		

def rerank(request):
	global best_mesh_terms
	global best_mesh_terms_id
	global tags
	global query

	if request.method == 'POST':
		try:
			str_data = request.POST.get('feedback',None)
			json_no = request.POST.get('json_no',None)
			option = request.POST.get('option',None)
		except KeyError:
			return render(request,'home/error.html',{"message":"No feedback data found in the request object"})
		data = json.loads(str_data)
		relevant_indices = []
		irrelevant_indices = []
		for obj in data:
			if data[obj]['relevant'] == 1:
				relevant_indices.append(data[obj]['offset'])
			else:
				irrelevant_indices.append(data[obj]['offset'])
		print("relevant indices: ",relevant_indices)
			
		pp = postprocessing.PostProcessing()
		trimmedtitles , trimmedabs, actualabstracts = pp.getalltrimmed(json_no,query) 
		
		# Rerank by frequent terms
		if int(option) == 1: 
			print("Requested rerank by frequent terms")
			# get reranked docs from actualabstracts
			abs = ""
			if len(relevant_indices) > 0:
				for index in relevant_indices:
					abs += actualabstracts[index]
			# get k-profile for feedback docs
			nlp = spacy.load("en_ner_bionlp13cg_md")
			doc = nlp(abs)
			entities = ""
			for ent in doc.ents:
				entities += str(ent) + " "
			frequency = Counter(entities.split()).most_common()
			k_profile = []
			k = 0
			for term,score in frequency:
				k_profile.append(term.lower())
				if k == 20: 
					break
				k += 1
			# individual docs k-profile
			doc_k_profile = []
			for abs in actualabstracts:
				doc = nlp(abs)
				entities = ""
				for ent in doc.ents:
					entities += str(ent) + " "
				frequency = Counter(entities.split()).most_common()
				doc_profile = []
				k = 0
				for term,score in frequency:
					doc_profile.append(term.lower())
					if k == 20: 
						break
					k += 1
				doc_k_profile.append(doc_profile)
			# similarity measure between feedback docs and each individual doc
			# each entry will contain array of abstract index as multiple abs can might have same score
			profile_obj = OrderedDict() 
			for index in range(0, len(doc_k_profile)):
				common = set(k_profile).intersection(set(doc_k_profile[index]))
				score = len(common)
				try:
					profile_obj[str(score)].append(index)
				except KeyError:
					profile_obj[str(score)] = []
					profile_obj[str(score)].append(index)
			sorted_profile = sorted(profile_obj.items(),reverse=True) # more score first
			finalabs = []
			finaltitles = []
			for key,indexarr in sorted_profile:
				for index in indexarr:
					finalabs.append(trimmedabs[index])
					finaltitles.append(trimmedtitles[index])
					if len(finaltitles) >= 10:
						break
			topdocs = zip(finaltitles, finalabs)
			topmesh = OrderedDict()
			for clus_no,json_arr in best_mesh_terms.items():
				topmesh[clus_no] = zip(json_arr,best_mesh_terms_id[clus_no])
				
		elif int(option) == 2:
			print("Request for rerank by mesh terms")
			# Rerank by frequent Mesh terms
			if json_no:
				try:
					file_name = "home/data_folder/"+query+"/"+str(json_no)+'.json'
					print("file: ", file_name)
					with open(file_name, 'r') as f:
						json_object = json.load(f)
						data_mesh = json_object["meshterms"]
				except IOError as e:
					return render(request,'home/error.html',{"message":"Could not open file"})
			# k-profile of mesh terms from selected docs
			relevant_mesh = []
			if len(relevant_indices) > 0:
				for index in relevant_indices:
					relevant_mesh.extend(data_mesh[index])
			relevant_mesh_obj = {}
			for meshterm in relevant_mesh:
				mesh = processmesh(meshterm)
				try:
					relevant_mesh_obj[mesh] += 1
				except KeyError:
					relevant_mesh_obj[mesh] = 1
			# if not enough mesh terms 
			if len(relevant_mesh_obj) < 1:
				return render(request,'home/error.html',{"message":"Not enough Mesh terms found in the selected documents"})
			sorted_mesh_obj = sorted(relevant_mesh_obj.items(),key=lambda x:x[1],reverse=True)
			k_profile_rel_mesh = []
			k = 0
			for key,v in sorted_mesh_obj:
				k_profile_rel_mesh.append(key)
				if k == 20:
					break
				k += 1
			print("k-profile for relevant doc done")
			# find k-profile for each doc of the selected json
			k_profile_arr = []
			for index in range(0,len(data_mesh)):
				k_profile = []
				mesh_obj = {}
				for meshstring in data_mesh[index]:
					mesh = processmesh(meshstring)
					try:
						mesh_obj[mesh] += 1
					except KeyError:
						mesh_obj[mesh] = 1
				sorted_mesh_obj = sorted(mesh_obj.items(), key=lambda x:x[1], reverse=True)
				k = 0
				for key,v in sorted_mesh_obj:
					k_profile.append(key)
					if k == 20:
						break
					k += 1
				k_profile_arr.append(k_profile)
			print("k-profile for all doc done")
			print("total abs :", len(actualabstracts))
			print("profile len: ", len(k_profile_arr))
			# similarity measure
			profile_obj = OrderedDict()
			for index in range(0,len(k_profile_arr)):
				common = set(k_profile_rel_mesh).intersection(set(k_profile_arr[index]))
				score = len(common)
				try:
					profile_obj[str(score)].append(index)
				except KeyError:
					profile_obj[str(score)] = []
					profile_obj[str(score)].append(index)
			sorted_profile = sorted(profile_obj.items(),reverse=True)
			print("similarity measure done")
			# compute topdocs
			finalabs = []
			finaltitles = []
			for key,indexarr in sorted_profile:
				for index in indexarr:
					finalabs.append(trimmedabs[index])
					finaltitles.append(trimmedtitles[index])
					if(len(finaltitles) >= 10): 
						break
			topdocs = zip(finaltitles, finalabs)
			topmesh = OrderedDict()
			for clus_no,json_arr in best_mesh_terms.items():
				topmesh[clus_no] = zip(json_arr,best_mesh_terms_id[clus_no])
		# start from 0th index
		previndex = -10
		nextindex = 10
		currindex = 0
		context = {
			'query' : query,
			'topdocs' : topdocs,
			'topmesh' : topmesh,
			'currindex' : currindex,
			'previndex' : previndex,
			'nextindex' : nextindex,
			'json_no' : json_no,
		}
		return render(request,'home/detail.html',context)
	else:
		return render(request,'home/error.html',{"message":"Not a post request"})		

def entity_feedback(request):
	try:
		str_data = request.POST.get('feedbackdata',None)
	except KeyError:
		return JsonResponse({"message":"No feedback data found in the request object !!"})
	data = json.loads(str_data)
	print(data)
	return JsonResponse({"message": "Thank you for your valuable feedback"})	

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

