
# How to run our code
1. Install Django in your system (globally or inside an environment)
	- Creating python environment
		- install virtualenv with pip [You may get proxy error. Search pip behind proxy]
			- pip install virtualenv or pip3 install virtualenv
		- virtualenv -p python3 envname [It will create a folder named 'envname' in current folder]
			- Here python3 is important since we have used python 3 syntax
	- Activate environment
		- source [path to] envname/bin/activate

2. Make sure to create folders before running the code:

	Inside 'home' folder create folder named 
	-  data_folder
	-  golden_corpus
	-  goldenpmids

3. cd searchtool [you downloaded searchtool folder]
4. python3 manage.py runserver
5. Goto browser and type [ localhost:8000]


# To create your own Django Project

**Installing**
1. Install Django from django website
	- Create 'project' < you select a name > [ I have given 'searchtool' ]
	- Create a 'App' inside your project < again your choice > [ I gave 'home' ]
	- You create all python files for your app in app folder
	Note: 
		* You can think a website as 'project'
		* All the different pages like About, Contact, Projects, Careers etc are 'App'

**Important files**
2. urls files:
	- Django has two URLs file 
		- Navigating to each App
		- Navigating inside an App

3. views file of App:
	- This is the main file you will be working with
	- For each of the URL you must create a View Function or Class [See documentation for each]
	- In view you do all the heavy work and return a rendered Html page with dynamic data that you have got after user data processing
	- To reduce content of View file, you can create new files and import into view file

**Running the project**
2. Now run the project by typing :
	- [ python manage.py runserver ] in the terminal
	- Then goto browser and type [ localhost:8000 ]

# Work flow of Django framework 

- User enters a URL in the browser
- Django match that url in both the url files 
- Once a url matches, corresponding view Function or Class is triggered 
- Finally browser shows received rendered Html page

That's it. For more, goto official Django website :)


# Documentation

## Structure of our code

**NOTE**: Do not goto seachtool folder inside searchtool project. This folder contains all settings

### home/urls.py
- contains all the urls of our app 'home'
- If you want to add new functionality you modify this url file only not other url file

### home/views.py

This contains functions corresponding to each url.

### home/goldencorpus.py

downloads documents for full query , 200 at a time and keep in the file system.

### home/mesh_explosion.py

Computes all combination of queries from full query and for each of the new query, top k(we used k = 400) documents are retrived and kept in a json file for efficient access in cluster file.

### home/cluster.py 

all the json file read and clustered. Then returned top n clusters to view file

### home/postprocessing.py

once cluster is done, all the feature is computed here for requested json file or entire cluster.

## home/entity_recognition.py

scispacy model and rule based model is implemented here. It is used mainly in postprocessing file.


## **_Important_**

Please go through the code starting from __post__ function in __views.py__ file. The code is totally commented.
