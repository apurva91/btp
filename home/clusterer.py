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
		raw_data = []
		self.data_folder_name = dataFolder+"/"
		for filename in os.listdir(self.data_folder_name):
		    f = open(self.data_folder_name+filename, 'r')
		    json_object = json.load(f)
		    f.close()
		    raw_data.append(json_object)
		    
		print ('Number of Cluster Points -------> ')
		print (len(raw_data))

		self.cluster_data = raw_data
		self.kmeans = kmeans
		self.related_docs = relDocsSet
		self.hyper = hyper

	# def get_final_set(self):
	# 	return self.final_set

	def cluster(self):
		data_abstract = [clusterpoint["abstracts"] for clusterpoint in self.cluster_data]
		data_title = [clusterpoint["titles"] for clusterpoint in self.cluster_data]
		data_query_label = [clusterpoint["query"] for clusterpoint in self.cluster_data]
		data_query_id = [clusterpoint["queryId"] for clusterpoint in self.cluster_data]

		# print(data_abstract)
		final_abstracts = []
		for i in range(0,len(data_abstract)):
			abstracts = ""
			for j in range(0,len(data_abstract[i])):
				abstracts = abstracts+data_title[i][j]+data_abstract[i][j]
			final_abstracts.append(abstracts)
		
		# Perform an IDF normalization on the output of HashingVectorizer
		hasher = HashingVectorizer(n_features=1000, stop_words='english', norm=None, binary=False)
		vectorizer = make_pipeline(hasher, TfidfTransformer())
		X = vectorizer.fit_transform(final_abstracts)
		print ("n_samples: %d, n_features: %d" % X.shape)
		# print(data_query_label)
		# print(X)

		# K-Means or DBSCAN
		if self.kmeans:
			num_clusters = int(self.hyper)
			km = KMeans(n_clusters=num_clusters, init='k-means++', max_iter=100, n_init=1, verbose=True)
			t0 = time()
			km.fit(X)
			print("done in %0.3fs" % (time() - t0))
			# print(len(set(km.labels_)))
		else:
			km = DBSCAN(eps=float(self.hyper), min_samples=10).fit(X)
			num_clusters = len(set(km.labels_))

		cluster_labels = km.labels_
		cluster_centers = km.cluster_centers_
		# print("cluster centers: ",cluster_centers)
		query_clusters = []
		query_clusters_pmids = []

		for i in range(0,num_clusters):
		    temp = []
		    tempset = set()
		    query_clusters_pmids.append(tempset)
		    query_clusters.append(temp)
		# Each row(cluster 0 to 8) will contain its corresponding MeshTerm nos
		for i in range(0,len(cluster_labels)):
			query_clusters[cluster_labels[i]].append(i+1)

			pmids = self.cluster_data[i]["articleIds"]
			# print("pmids: ", pmids)
			for pmid in pmids:
				if pmid:
					query_clusters_pmids[cluster_labels[i]].add(int(pmid))

		print ("cluster_id\tnum_queries\tnum_pmids")
		print ("-------------------------------------------------------------")
		for i in range(0,num_clusters):
		    print (str(i) + "\t\t" + str(len(query_clusters[i])) + "\t\t" + str(len(query_clusters_pmids[i])))

		relevant_docs = self.related_docs

		random.shuffle(relevant_docs)

		# learning vs testing split of Golden corpus 

		training_cnt = int(1.0*len(relevant_docs))
		relevant_known = set(relevant_docs[:training_cnt])
		relevant_blind = set(relevant_docs[training_cnt:])
		
		cluster_score = [float(len(relevant_known.intersection(cluster_pmids))/(len(cluster_pmids) + 1)) for cluster_pmids in query_clusters_pmids]
		
		print(cluster_score)
		cluster_score_relative = [float(score/max(cluster_score)) for score in cluster_score]
		
		# blind_intersection = [len(relevant_blind.intersection(cluster_pmids)) for cluster_pmids in query_clusters_pmids]
		# print ("Cluster ID\tRelevance Score\tBlind Intersection")
		# for i in range(0,num_clusters):
		#     print (str(i) + "\t\t" + str(cluster_score_relative[i]) + "\t\t" + str(blind_intersection[i]))

		clus_dict = OrderedDict()
		final_corpus = set()
		for i in range(0,num_clusters):
			if cluster_score_relative[i] > 0.5:
				clus_dict[cluster_score_relative[i]] = i

		sortedscore = sorted(clus_dict.items(), reverse=True)
		# print(sortedscore)
		optimized_query = []
		optimized_query_ids = []
		done = 0
		j = 0
		minp = sys.float_info.max
		
		for _score , _clus_no in sortedscore:
			optimized_query.append([])
			optimized_query_ids.append([])
			if not done:
				print('Number of Abstracts in Best Cluster: {}',len(query_clusters_pmids[_clus_no]))
			for _k in query_clusters[_clus_no]:
				if not done:
					dist = distance.euclidean(cluster_centers[_clus_no], X[_k - 1].toarray())
					if dist < minp:
						minp = dist
						representative = data_query_label[_k-1]
						representative_id = _k
						print("----------------------------------------",_k)
				optimized_query_ids[j].append(_k)
				optimized_query[j].append(data_query_label[_k-1])
			j += 1
			done = 1

		# open given gene list
		# path = ("home/gene_list.xlsx")
		# wb = xlrd.open_workbook(path)
		# sheet = wb.sheet_by_index(0)
		# mydata = ""
		# meshObj = {}
		# geneObj={}
		# for name in optimized_query_ids[0]:
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
		return representative_id,representative,optimized_query_ids, optimized_query