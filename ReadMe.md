Make sure to create two folder before running the code:

	1. Inside 'home' folder create folder named 'data_folder'
	2. Inside 'home' folder create folder named 'golden_corpus'

Now run the tool by typing :

	1. [ python manage.py runserver ] in the terminal
	2. Then goto browser and type [ localhost:8000 ]

TODO:
	1. Keep reranked abstracts and titles globaly and send it to "getTitleAbs" function 
		rather than reading from json file since it will read old ranked abs and titles 
