import scispacy
import spacy
import sklearn_crfsuite
import pickle
import csv
import re
from nltk import tokenize

def entity_recog_nn(text):
	nlp1 = spacy.load("en_ner_jnlpba_md")
	nlp2 = spacy.load("en_ner_bionlp13cg_md")
	nlp3 = spacy.load("en_ner_bc5cdr_md")
	doc1 = nlp1(text)
	doc2 = nlp2(text)
	doc3 = nlp3(text)
	
	protein = set()
	gene = set()
	disease = set()

	for entity in doc1.ents:
		if entity.label_=="PROTEIN":
			protein.add(entity.text)

	for entity in doc2.ents:
		if entity.label_=="GENE_OR_GENE_PRODUCT" and entity.text not in protein:
			gene.add(entity.text)

	for entity in doc3.ents:
		if entity.label_=="DISEASE":
			disease.add(entity.text)

	return disease,gene,protein

def entity_recog_rb(text):
	test = tokenize.sent_tokenize(text)
	
	temp = []
	for sent in test:
		r = sent.strip().split(' ')
		t = []
		for i in range(len(r)):
			r[i]=r[i].replace(' ','')
			r[i]=r[i].replace('.','')
			r[i]=r[i].replace(',','')
			if len(r[i]) > 0:
				t.append(r[i])
		temp.append(t)

	X = [sent2features(s) for s in temp]

	loaded_model1 = pickle.load(open('protein_model.pkl', 'rb'))
	loaded_model2 = pickle.load(open('gene_model.pkl','rb'))
	loaded_model3 = pickle.load(open('disease_model.pkl', 'rb'))

	y1 = loaded_model1.predict(X)
	y2 = loaded_model2.predict(X)
	y3 = loaded_model3.predict(X)

	protein=[]
	gene=[]
	disease=[]

	prot=set()
	ge=set()
	dis=set()

	n = -1
	for i in range(len(y1)):
		for j in range(len(y1[i])):
			if y1[i][j]=='B-Protein':
				protein.append(temp[i][j]+' ')
				n += 1
			elif y1[i][j]=='I-Protein':
				if n != -1:
					protein[n] += temp[i][j] + ' '

	for p in protein:
		prot.add(p)

	n=-1
	flag=0
	for i in range(len(y2)):
		for j in range(len(y2[i])):
			if y2[i][j]=='B-Gene_or_gene_product':
				gene.append(temp[i][j]+' ')
				n += 1
				flag=1
			elif y2[i][j]=='I-Gene_or_gene_product':
				if n != -1:
					gene[n] += temp[i][j] + ' '
			elif flag and gene[n] in protein:
				if n != -1:
					gene.remove(gene[n])
					n -= 1
					flag=0

	for g in gene:
		ge.add(g)

	n=-1
	for i in range(len(y3)):
		for j in range(len(y3[i])):
			if y3[i][j]=='B-Disease':
				disease.append(temp[i][j]+' ')
				n += 1
			elif y3[i][j]=='I-Disease':
				if n != -1:
					disease[n] += temp[i][j] + ' '

	for d in disease:
		dis.add(d)

	return dis,ge,prot
	

def word2features(sentence, index):

	features = {
		'word': sentence[index],
		'is_first': index == 0,
		'is_last': index == len(sentence) - 1,
		'is_capitalized': sentence[index].upper() == sentence[index],
		'is_all_lower': sentence[index].lower() == sentence[index],
		'prefix-1': sentence[index][0],
		'prefix-2': sentence[index][:2],
		'prefix-3': sentence[index][:3],
		'suffix-1': sentence[index][-1],
		'suffix-2': sentence[index][-2:],
		'suffix-3': sentence[index][-3:],
		'prev_word': '' if index == 0 else sentence[index - 1],
		'next_word': '' if index == len(sentence) - 1 else sentence[index + 1],
		'has_hyphen': '-' in sentence[index],
		'is_numeric': sentence[index].isdigit(),
		'capitals_inside': sentence[index][1:].lower() != sentence[index][1:],
		'contains_digit': bool(re.search(r'\d', sentence[index])),
	}

	return features

def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]
