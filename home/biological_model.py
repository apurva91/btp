import numpy as np
import xgboost as xgb
from tqdm import tqdm
from stop_words import get_stop_words  # use as : list(get_stop_words('en'))
from nltk.corpus import stopwords 
import json
import os,glob
import xlsxwriter 
import xlrd
from sklearn import model_selection
from sklearn.metrics import accuracy_score
import pickle
import random



def isbio(word,sheet):
	for row in range(0,sheet.nrows):
		if sheet.cell_value(row,0) == word.lower():
			return 1
	return 0

def dataset_prepare():

	# data_mesh = []
	# data_abs = []

	# folder_path = '/home/tanmoy/extracellular matrix remodelling/'
	# for filename in glob.glob(os.path.join(folder_path, '*.json')):
	# 	with open(filename, 'r') as f:
	# 		json_object = json.load(f)
	# 		for mesh_arr in json_object["meshterms"]:
	# 			data_mesh.extend(mesh for mesh in mesh_arr)
	# 		data_abs.extend(json_object["abstracts"])

	# print("mesh len: ",len(data_mesh))
	# print("abs len: ",len(data_abs))
		
	# conceptlist = []
	# upperconceptlist = []
	# python_s_words = list(get_stop_words('en'))         #About 900 stopwords
	# nltk_words = list(stopwords.words('english'))       #About 150 stopwords
	# python_s_words.extend(nltk_words)
	# python_s_words = [word.lower() for word in python_s_words]

	# a = 0
	# b = 0
	# c = 0
	# workbook = xlsxwriter.Workbook('bio_data.xlsx') 
	# worksheet = workbook.add_worksheet("My sheet")
	# row = 0
	# col = 0
	# for string in data_mesh:
	# 	newstr = string.replace('/',' ')
	# 	newstr = newstr.replace(',',' ')
	# 	newstr = newstr.replace('(',' ')
	# 	newstr = newstr.replace(')',' ')
	# 	newstr = newstr.replace('[',' ')
	# 	newstr = newstr.replace(']',' ')
	# 	newstr = newstr.replace('\'',' ')
	# 	newstr = newstr.replace('%',' ')
	# 	newstr = newstr.replace('<',' ')
	# 	newstr = newstr.replace('>',' ')
	# 	newstr = newstr.replace(';',' ')
	# 	newstr = newstr.replace(':',' ')
	# 	newstr = newstr.replace('!',' ')
	# 	newstr = newstr.replace('@',' ')
	# 	newstr = newstr.replace('#',' ')
	# 	newstr = newstr.replace('$',' ')
	# 	newstr = newstr.replace('^',' ')
	# 	newstr = newstr.replace('&',' ')
	# 	newstr = newstr.replace('*',' ')
	# 	newstr = newstr.replace('~',' ')
	# 	newstr = newstr.replace('`',' ')
	# 	for word in newstr.split():
	# 		if not word.isnumeric() and len(word) > 2: # avoid numeric string and length lesser than 3
	# 			a = a + 1
	# 			if not word.lower() in python_s_words:
	# 				b = b + 1
	# 				worksheet.write(row, col, word.lower()) 
	# 				worksheet.write(row, col + 1, 1) 
	# 				row += 1
	# 			else:
	# 				c = c + 1
	# # workbook.close()


	# # book = xlrd.open_workbook('bio_data.xlsx')
	# # sheet = book.sheet_by_index(0)
	# a = 0
	# b = 0
	# c = 0
	# row += 1
	# for string in data_abs:
	# 	newstr = string.replace('/',' ')
	# 	newstr = newstr.replace(',',' ')
	# 	newstr = newstr.replace('(',' ')
	# 	newstr = newstr.replace(')',' ')
	# 	newstr = newstr.replace('[',' ')
	# 	newstr = newstr.replace(']',' ')
	# 	newstr = newstr.replace('%',' ')
	# 	newstr = newstr.replace('<',' ')
	# 	newstr = newstr.replace('>',' ')
	# 	newstr = newstr.replace(';',' ')
	# 	newstr = newstr.replace(':',' ')
	# 	newstr = newstr.replace('.',' ')
	# 	newstr = newstr.replace('!',' ')
	# 	newstr = newstr.replace('@',' ')
	# 	newstr = newstr.replace('#',' ')
	# 	newstr = newstr.replace('$',' ')
	# 	newstr = newstr.replace('^',' ')
	# 	newstr = newstr.replace('&',' ')
	# 	newstr = newstr.replace('*',' ')
	# 	newstr = newstr.replace('~',' ')
	# 	newstr = newstr.replace('`',' ')
	# 	newstr = newstr.replace('\'',' ')
	# 	for word in newstr.split():
	# 		if not word.isnumeric(): # avoid numeric string 
	# 			a = a + 1
	# 			if not word.lower() in python_s_words:
	# 				b = b + 1
	# 				worksheet.write(row, col, word.lower()) 
	# 				worksheet.write(row, col + 1, 0) 
	# 				row += 1
	# 			else:
	# 				c = c + 1
	# workbook.close()
	# book.close()
	
	word_representation = {}
	google_trained_file = open('glove.42B.300d.txt')
	for line in tqdm(google_trained_file):
		values = line.split()
		word = values[0]
		coefs = np.asarray(values[1:],dtype="float32") # Forgot to write dtype then RAM was getting full
		word_representation[word] = coefs
	google_trained_file.close()
	print('Found %s word vectors.' % len(word_representation))

	# Preparing matrix for word and array for output
	dataset = []
	temp = []

	workbook = xlrd.open_workbook('bio_data.xlsx')
	worksheet = workbook.sheet_by_name("My sheet")

	for row in range(0,worksheet.nrows):
		try:
			temp = []
			word_rep = word_representation[str(worksheet.cell_value(row,0))]
			for f in word_rep: # Earlier doing temp.append(word_rep) which makes dataset shape different [check doing that]
				temp.append(f)
			temp.append(worksheet.cell_value(row,1))
			dataset.append(temp)
		except KeyError:
			continue
			
	print("dataset done")

	# dataset = np.array(dataset)
	random.shuffle(dataset)

	x_data = []
	y_data = []
	for data in dataset:
		x_data.append(data[:-1])
		y_data.append(data[-1])
	print("x_data y_data done")

	x_data = np.array(x_data)
	y_data = np.array(y_data)
	# x_data = np.array(x_data)
	# y_data = np.array(y_data)
	# print(x_data.shape())
	
	print(x_data[0])
	print(y_data[0])
	print(x_data[1])
	print(y_data[1])

	test_size = 0.30
	seed = 7
	x_train, x_test, y_train, y_test = model_selection.train_test_split(x_data, y_data, test_size=test_size, random_state=seed)
	print("data divided into train test")
	# Train the classifier
	print("Model training...")
	model = xgb.XGBClassifier()
	model.fit(x_train,y_train)
	# Save the model 
	filename = 'finalized_model.sav'
	pickle.dump(model, open(filename, 'wb'))
	print("Training done")
	# load the model from disk
	loaded_model = pickle.load(open(filename, 'rb'))
	# Predict
	y_pred = loaded_model.predict(x_test)
	score = accuracy_score(y_test,y_pred)
	print("Accuracy: ",score)
	

if __name__ == "__main__":
	dataset_prepare()