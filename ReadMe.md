
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

1. Install Django from django website
	- Create 'project' < you select a name > [ I have given 'searchtool' ]
	- Create a 'App' inside your project < again your choice > [ I gave 'home' ]
	- You create all python files for your app in app folder
	Note: 
		* You can think a website as 'project'
		* All the different pages like About, Contact, Projects, Careers etc are 'App'

2. URL :
	- Django has two URLs file 
		- Navigating to each App
		- Navigating inside an App

3. VIEW of App:
	- This is the main file you will be working with
	- For each of the URL you must create a View Function or Class [See documentation for each]
	- In view you do all the heavy work and return a rendered Html page with dynamic data that you have got after user data processing
	- To reduce content of View file, you can create new files and import into view file

2. Now run the project by typing :
	- [ python manage.py runserver ] in the terminal
	- Then goto browser and type [ localhost:8000 ]

## Work flow of Django framework 
Steps:
	1. User enters a URL in the browser
	2. Django match that url in both the url files 
	3. Once a url matches, corresponding view Function or Class is triggered 
	4. Finally browser shows received rendered Html page

That's it. For more, goto official Django website :)


# Documentation

## Structure of our code

NOTE: Do not goto seachtool folder inside searchtool project. This folder contains all settings

### home/urls.py
	- contains all the urls of our app 'home'
	- If you want to add new functionality you modify this url file only

### home/views.py

This contains functions corresponding to each url. I will describe parameters, other function calling and return value.


