
# How to run our code

Steps for setting up the softare.

```
sudo apt-get install python3 python3-pip
sudo apt-get install python3-venv
virtualenv -p python3 project_env
source project_env/bin/activate
git clone https://github.com/apurva91/btp
cd btp
pip install -r requirements.txt
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.0/en_ner_jnlpba_md-0.2.0.tar.gz
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.0/en_ner_bionlp13cmd-0.2.0.tar.gz
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.0/en_ner_bc5cdr_md-0.2.0.tar.gz
python manage.py migrate
mkdir home/goldenpmids home/golden_corpus home/data_folder
```

Steps for running the software

```
source project_env/bin/activate
cd btp
python manage.py runserver
```

Visit http://localhost:8000 on your browser to use the software.


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
