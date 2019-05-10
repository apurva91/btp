import scispacy
import spacy
import sklearn_crfsuite
# import eli5
import pickle
import csv
import re
from nltk import tokenize

def entity_recog_nn(text):
	nlp1 = spacy.load("en_ner_jnlpba_md")
	nlp2 = spacy.load("en_ner_bc5cdr_md")
	doc1 = nlp1(text)
	doc2 = nlp2(text)
	disease=[]
	dna=[]
	rna=[]
	protein=[]

	for entity in doc1.ents:
		if entity.label_=="DNA":
			dna.append(entity.text)
		elif entity.label_=="RNA":
			rna.append(entity.text)
		else:
			protein.append(entity.text)

	for entity in doc2.ents:
		if entity.label_=="DISEASE":
			disease.append(entity.text)
	disease = set(disease)
	protein = set(protein)
	rna = set(rna)
	dna = set(dna)
	return disease,protein,rna,dna

def entity_recog_rb(text):
	test = tokenize.sent_tokenize(text)
	temp = []
	for sent in test:
		temp.append(sent.strip().split(' '))


	X = [sent2features(s) for s in temp]

	loaded_model1 = pickle.load(open('home/gene_model.pkl', 'rb'))
	loaded_model2 = pickle.load(open('home/disease_model.pkl', 'rb'))

	y1 = loaded_model1.predict(X)
	y2 = loaded_model2.predict(X)

	disease=[]
	dna=[]
	rna=[]
	protein=[]

	print(y1)
	print(y2)
	ent=''

	
	k=-1
	l=-1
	m=-1
	n=-1
	for i in range(len(y1)):
		for j in range(len(y1[i])):
			if y1[i][j]=='B-protein':
				protein.append(temp[i][j]+' ')
				k += 1
			elif y1[i][j]=='I-protein':
				protein[k] += temp[i][j]
			elif y1[i][j]=='B-DNA':
				dna.append(temp[i][j]+' ')
				l += 1
			elif y1[i][j]=='I-DNA':
				dna[l] += temp[i][j]
			elif y1[i][j]=='B-RNA':
				rna.append(temp[i][j]+' ')
				m += 1
			elif y1[i][j]=='I-RNA':
				rna[m] += temp[i][j]


	for i in range(len(y2)):
		for j in range(len(y2[i])):
			if y2[i][j]=='B-Disease':
				disease.append(temp[i][j]+' ')
				n += 1
			elif y2[i][j]=='I-Disease':
				disease[n] += temp[i][j]

	disease = set(disease)
	protein = set(protein)
	rna = set(rna)
	dna = set(dna)
	return disease,protein,rna,dna
	

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
