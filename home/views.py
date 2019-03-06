from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from . import goldencorpus
from . import mesh_explosion
from . import clusterer
from . import postprocessing
import json
import re

mesh = []
mesh_id = []
tags = []
query = None
filepath = None

def index(request):
    return render(request,'home/index.html')
    
def post(request):
	global mesh
	global mesh_id
	global query
	global filepath
	global tags

	if request.method == 'POST':
		query = request.POST.get('query',None)
		filepath = request.POST.get('filepath',None)

		if filepath and query:
			if filepath:
				corpus = goldencorpus.GoldenCorpus(query,filepath)
				if not corpus.fetchData():
					return HttpResponse("Error in fetching data")
				rel_docs = corpus.get_rel_docs_pmid()
				mesh_terms = corpus.get_mesh_terms()
				if len(mesh_terms) > 0:
					mesh_exp = mesh_explosion.DataForEachMeshTerm(mesh_terms,query)
					path = mesh_exp.get_data_foldername(query)
					clus = clusterer.Clusterer(rel_docs,path,True,5)
					representative_id,representative, best_mesh_terms_id, best_mesh_terms = clus.cluster()
					mesh = best_mesh_terms
					mesh_id = best_mesh_terms_id
				else:
					return HttpResponse("No meshterms received from pubmed")

				if representative:
					# get all information for representative json
					pp = postprocessing.PostProcessing()
					tags = pp.term_tagging(best_mesh_terms)
					trimmedtitles , trimmedabs, completeabs = pp.getTitleAbs(0,representative_id,query) 
					topdocs = zip(trimmedtitles, trimmedabs)
					
					mesharr = []
					for clusno in range(0, len(best_mesh_terms)):
						topmesh = zip(best_mesh_terms[clusno],best_mesh_terms_id[clusno])
						mesharr.append(topmesh)
					previndex = -10
					nextindex = 10
					currindex = 0
					context = {
						'query' : query,
						'topdocs' : topdocs,
						'mesharr' : mesharr,
						'tags' : tags,
						'currindex' : currindex,
						'previndex' : previndex,
						'nextindex' : nextindex,
						'json_no' : representative_id,
					}
					return render(request,'home/detail.html',context)
				else:
					return HttpResponse("No result found!!")
			else:
				return HttpResponse("Error! getting gene file !!")
		else:
			return HttpResponse("No query found in post request!!")
	else:
		return HttpResponse("Not a post request!")
def get(request, json_no):
	global mesh
	global mesh_id
	global tags
	global query

	if request.method == 'GET':

		pp = postprocessing.PostProcessing()
		tags = pp.term_tagging(mesh)
		trimmedtitles , trimmedabs, completeabs = pp.getTitleAbs(0,json_no,query) 
		topdocs = zip(trimmedtitles, trimmedabs)
		mesharr = []
		for clusno in range(0, len(mesh)):
			topmesh = zip(mesh[clusno],mesh_id[clusno])
			mesharr.append(topmesh)
		previndex = -10
		nextindex = 10
		currindex = 0
		context = {
			'query' : query,
			'topdocs' : topdocs,
			'mesharr' : mesharr,
			'tags' : tags,
			'currindex' : currindex,
			'previndex' : previndex,
			'nextindex' : nextindex,
			'json_no' : json_no,
		}
		return render(request,'home/detail.html',context)

def paginate(request, json_no, abs_index):
	global mesh
	global mesh_id
	global tags
	global query

	pp = postprocessing.PostProcessing()
	trimmedtitles , trimmedabs, completeabs = pp.getTitleAbs(abs_index,json_no,query) 
	topdocs = zip(trimmedtitles, trimmedabs)
	mesharr = []
	for clusno in range(0, len(mesh)):
		topmesh = zip(mesh[clusno],mesh_id[clusno])
		mesharr.append(topmesh)
	previndex = abs_index - 10
	nextindex = abs_index + 10	
	currindex = abs_index
	context = {
		'query' : query,
		'topdocs' : topdocs,
		'mesharr' : mesharr,
		'tags' : tags,
		'currindex' : currindex,
		'previndex' : previndex,
		'nextindex' : nextindex,
		'json_no': json_no,
		'isrf' : isrf
	}
	return render(request,'home/detail.html',context)

def genecloud(request, json_no):
	global query
	global filepath

	pp = postprocessing.PostProcessing()
	if query and filepath:
		gene_arr = pp.gene_cloud(json_no,filepath,query)
		return render(request, 'home/genecloud.html',{'gene_arr': gene_arr})
	else:
		print("No query or no file path")
		return HttpResponse("Something wrong with gene cloud!")
def meshcloud(request, json_no):
	global query
	pp = postprocessing.PostProcessing()
	meshobj = pp.mesh_cloud(json_no,query)
	if meshobj:
		return render(request, 'home/meshcloud.html', {'meshobj': meshobj})
	else:
		return HttpResponse("Something wrong with mesh cloud!")
def generelation(request, json_no):
	return HttpResponse("From gene relation")
	
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

def feedback(request):
	data = request.POST.get('feedback',None)
	# print(data)
	# Work with new data 
	relevant_indices = []
	irrelevant_indices = []
	for obj in data:
		if obj["relevant"] == 1:
			relevant_indices.append(obj["offset"])
		else:
			irrelevant_indices.append(obj["offset"])
	# For each relevant paper count frequency of each word and 
	# consider top frequent terms for next search
	


	obj = {'message' : "Got the data"}
	return JsonResponse(obj)