import os
import json
import sys
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn import metrics
from sklearn.cluster import KMeans, MiniBatchKMeans
from scipy.spatial import distance
from time import time
from sklearn.cluster import DBSCAN
from collections import OrderedDict
import collections
import random
import xlrd

class Clusterer:
	def __init__(self, relDocsSet, dataFolder, kmeans, hyper):
		self.cluster_data = None
		self.dataFolder = dataFolder
		self.kmeans = kmeans
		self.related_docs = relDocsSet
		self.hyper = hyper

	def cluster(self):
		raw_data = []
		self.data_folder_name = self.dataFolder+"/"
		for filename in os.listdir(self.data_folder_name):
			try:
				with open(self.data_folder_name+filename, 'r') as f:
					json_object = json.load(f)
					raw_data.append(json_object)
			except FileNotFoundError:
				continue
		self.cluster_data = raw_data
		
		# data preparation for clustering
		data_abstract = [json_data["abstracts"] for json_data in self.cluster_data] # contains array of array of abstracts
		data_title = [json_data["titles"] for json_data in self.cluster_data]
		data_query = [json_data["query"] for json_data in self.cluster_data]

		# Convert array of array of abstracts to array of abstracts 
		# by merging all abstracts of a json file into single string
		# Now no.of abstracts will be same as no.of json file we have.
		# You can think we are clustering json files by clustering their abstructs
		final_abstracts = []
		for i in range(0,len(data_abstract)):
			abstracts = ""
			for j in range(0,len(data_abstract[i])):
				abstracts = abstracts+data_title[i][j]+data_abstract[i][j]
			final_abstracts.append(abstracts)
		
		# Each string abstract is a point for our cluster algo
		# We convert this point into feature vector for the algo. We will have 'n' vector for 'n' json file.
		# Each vector consists of word from corresponding abstract string.
		# Then all words are replaced with the TfIdf frequency. 
		# So finaly vector will contain frequency value rather than word itself.
		# Then normalize the values

		# Perform an IDF normalization on the output of HashingVectorizer
		hasher = HashingVectorizer(n_features=1000, stop_words='english', norm=None, binary=False)
		vectorizer = make_pipeline(hasher, TfidfTransformer())
		X = vectorizer.fit_transform(final_abstracts) # X is an array of feature vectors which will be input to kmeans algo
		print ("n_samples: %d, n_features: %d" % X.shape)

		# km = DBSCAN(eps=0.1, min_samples=2).fit(X)
		# num_clusters = len(set(km.labels_))
		num_clusters = 4
		print("no of cluster: ",num_clusters)
		# K-Means or DBSCAN
		if self.kmeans:
			# num_clusters = int(self.hyper)
			km = KMeans(n_clusters=num_clusters, init='k-means++', max_iter=100, n_init=1, verbose=True)
			t0 = time()
			km.fit(X)
			print("done in %0.3fs" % (time() - t0))
		# km.labels_ contains cluster number for each feature vector/json (position wise) 
		# i.e. km_labels_[0] contains cluster number for 0-th feature vector/json and so on 
		cluster_labels = km.labels_
		cluster_centers = km.cluster_centers_
		print("cluster labels: ",cluster_labels)

		# query_clusters is a 2d array which contains cluster wise json numbers
		# query_clusters_pmids is a 2d set which contains cluster wise pmids
		query_clusters = []
		query_clusters_pmids = [] # used for computing socre for cluster by taking intersection with golden corpus
		for i in range(0,num_clusters):
		    temp = []
		    tempset = set()
		    query_clusters_pmids.append(tempset)
		    query_clusters.append(temp)
		# Each row(cluster 0 to k-1) will contain its corresponding json nos
		for i in range(0,len(cluster_labels)):
			query_clusters[cluster_labels[i]].append(i+1) # i+1 is json number i-th label
			pmids = self.cluster_data[i]["articleIds"]
			for pmid in pmids:
				if pmid:
					query_clusters_pmids[cluster_labels[i]].add(int(pmid))

		print ("cluster_id\tnum_queries\tnum_pmids")
		print ("-------------------------------------------------------------")
		for i in range(0,num_clusters):
		    print (str(i) + "\t\t" + str(len(query_clusters[i])) + "\t\t" + str(len(query_clusters_pmids[i])))

		relevant_docs = self.related_docs

		# random.shuffle(relevant_docs)

		# learning vs testing split of Golden corpus 
		training_cnt = int(.7*len(relevant_docs))
		relevant_known = set(relevant_docs[:training_cnt])
		relevant_blind = set(relevant_docs[training_cnt:])
		
		# Computing cluster score for each cluster by taking 
		# intersection between training set of pmids and cluster pmids
		intersection = [0 + len(relevant_known.intersection(cluster_pmids)) for cluster_pmids in query_clusters_pmids]
		cluster_score = [1.0 + float(len(relevant_known.intersection(cluster_pmids))/(len(cluster_pmids) + 1)) for cluster_pmids in query_clusters_pmids]
		cluster_score_relative = [float(score/(1.0 + max(cluster_score))) for score in cluster_score]

		# evaluation with testing set of pmids
		blind_intersection = [0 + len(relevant_blind.intersection(cluster_pmids)) for cluster_pmids in query_clusters_pmids]
		blind_score = [1.0 + float(len(relevant_blind.intersection(cluster_pmids))/(len(cluster_pmids) + 1)) for cluster_pmids in query_clusters_pmids]
		blind_score_relative = [float(score/(1.0 + max(blind_score))) for score in blind_score]

		print ("Cluster ID\t\tRelevance Score\t\tBlind Score\t\tIntersection\t\tBlind Intersection")
		for i in range(0,num_clusters):
		    print ("  "+ str(i) + "\t\t" + str(cluster_score_relative[i]) +"\t\t"+ str(blind_score_relative[i]) + "\t\t" + str(intersection[i]) +"\t\t" + str(blind_intersection[i]))

		# Sort cluster by cluster score
		# But multiple cluster might have same score
		# So we keep a dictionary with score as key and array of cluster number as value
		
		thresh = 0
		clus_dict = OrderedDict()
		for i in range(0,num_clusters):
			if cluster_score_relative[i] > thresh: 
				try:
					clus_dict[cluster_score_relative[i]].append(i)
				except KeyError:
					clus_dict[cluster_score_relative[i]] = []
					clus_dict[cluster_score_relative[i]].append(i)
		sorted_dict_by_score = sorted(clus_dict.items(), reverse=True)
		print(sorted_dict_by_score)
		
		# top_cluster_query_ids is a unordered dict with key as cluster no. and value as array of json_no. 
		# top_cluster_query is a unordered dict with key as cluster no. and value as array of query corresponding to json_no
		top_cluster_query_ids = OrderedDict()
		top_cluster_query = OrderedDict()
		done = 0
		minp = sys.float_info.max
		# representative_id contains best json number
		representative_id = 0
		# representative contains query of best json number
		representative = None
		
		# Following code finds representative json from best(1st) cluster 
		# and populate top_cluster_query , top_cluster_query_ids 2d arrays 
		for _score , _clus_no_arr in sorted_dict_by_score:
			# Making current dict element has value (i.e. array of cluster no.)
			if len(_clus_no_arr) > 0:
				for _clus_no in _clus_no_arr:
					# Making sure cluster has atleast one json number in it
					if len(query_clusters[_clus_no]) > 0:
						top_cluster_query[_clus_no] = []
						top_cluster_query_ids[_clus_no] = []
						if not done:
							print("Best Cluster id: ",_clus_no)
							print('Number of Abstracts in Best Cluster: ',len(query_clusters_pmids[_clus_no]))
						# Finding representative for best(1st) cluster by calculating euclidian distance between each feature  
						# vector with cluster center of the cluster.
						for json_no in query_clusters[_clus_no]:
							# Only for first cluster i.e best cluster
							if not done:
								# json_no starts with 1 but X starts with 0 so we take [json_no - 1]
								# X[json_no - 1] is frequency vector for json file json_no
								dist = distance.euclidean(cluster_centers[_clus_no], X[json_no - 1].toarray())
								if dist < minp:
									minp = dist
									representative = data_query[json_no-1]
									representative_id = json_no
							top_cluster_query_ids[_clus_no].append(json_no)
							top_cluster_query[_clus_no].append(data_query[json_no-1])
						done = 1

		print("representative: ", representative)
		print("id: ", representative_id)


		# open given gene list
		# path = ("home/gene_list.xlsx")
		# wb = xlrd.open_workbook(path)
		# sheet = wb.sheet_by_index(0)
		# mydata = ""
		# meshObj = {}
		# geneObj={}
		# for name in top_cluster_query_ids[0]:
		# 	# open a file name.json
		# 	f = open(self.data_folder_name + str(name)+".json", 'r')
		# 	json_object = json.load(f)
		# 	f.close()
		# 	absstring = " "
		# 	titlestring = " "
		# 	for abs in json_object["abstracts"]:
		# 		absstring += abs
		# 	for title in json_object["titles"]:
		# 		titlestring += title
		# 	for mesharr in json_object["meshterms"]:
		# 		for mesh in mesharr:
		# 			try:
		# 				meshObj[mesh] += 1
		# 			except KeyError:
		# 				meshObj[mesh] = 1
		# 	mydata += absstring + titlestring
			
		# 	for row in range(0,sheet.nrows):
		# 		for col in range(0,sheet.ncols):
		# 			if row != 0 and col!=0 and col != 1 and col!=8 and col!=9 and col!=10 and col!=11 and col!=12 and sheet.cell_value(row,col):
		# 				if str(sheet.cell_value(row,col))+" " in mydata:
		# 					try:
		# 						geneObj[sheet.cell_value(row,col)] += 1			
		# 					except KeyError:
		# 						geneObj[sheet.cell_value(row,col)] = 1
		# 	print('File Completed: ',name)

		# # print(geneObj)
		# print('------------------------------------------------------')
		# for w in sorted(geneObj, key=geneObj.get, reverse=True):
		# 	print (w, geneObj[w])
		# print('-------------------------------------------------------')
		# for w in sorted(meshObj, key=meshObj.get, reverse=True):
			# print (w, meshObj[w])

		# print(representative)
		return representative_id,representative,top_cluster_query_ids, top_cluster_query