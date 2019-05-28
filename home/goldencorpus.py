import os
from . import api
import xmltodict, collections
from . import mesh_explosion
import xlrd

class GoldenCorpus():

    def __init__(self):
        pass

    def get_corpus_folder(self,query):
        return "home/golden_corpus/" + query
    
    def get_rel_docs_pmid(self,query,filepath,geneset):
        rel_doc = []
        # For every unique query we create this file (useful when same query searched)
        path = "home/goldenpmids/"+query+"/goldenpmid.txt"
        if os.path.exists(path):
            rdoc = open(path,"r")
        else:
            self.create_relevant_docs(query,filepath,geneset)
            rdoc = open(path,"r")
        arr = rdoc.read().split('\n')
        for v in arr:
            if v != '':
                rel_doc.append(int(v,10))
        rdoc.close()
        return rel_doc

    def preprocess(self,abstract):
        content = abstract.replace('\n', ' ')
        content = content.replace('(', ' ')
        content = content.replace(')', ' ')
        content = content.replace('.', ' ')
        content = content.replace(',', ' ')
        content = ' '.join(content.split())
        content = content.lower()

        return content

    def checkRelevance(self,abstract, genes):
        abs = self.preprocess(abstract)
        for gene in genes:
            if gene and gene+" " in abs:
                return True,gene
        # for row in range(0,genes.nrows):
        #     for col in range(0,genes.ncols):
        #         if row != 0 and col!=0 and col != 1 and col!=8 and col!=9 and col!=10 and col!=11 and col!=12 and genes.cell_value(row,col):
        #             if str(genes.cell_value(row,col))+" " in abs:
        #                 return True,genes.cell_value(row,col) 
        
        return False,""

    def fetchData(self,query,count):
        print("Fetchdata called..")
        pmids, mesh_terms = api.fetch_data(query,count)
        print("Total pmid got:----------------------------------> ",len(pmids))
        if count > 1:
            if self.saveGoldenCorpus(pmids,query):
                return True, mesh_terms
        # any other case return false
        return False, mesh_terms

    def saveGoldenCorpus(self, pmids, query):
        print("Save golden corpus called..")
        _genefile = []
        if not os.path.exists(self.get_corpus_folder(query)):
            os.mkdir(self.get_corpus_folder(query))
            #  Download abs as a group of 200
            if len(pmids):
                slist = []
                count = 0
                doccount = 1

                total_parts = int(len(pmids)/200)
                for cid in pmids:
                    if count < 200:
                        slist.append(cid)
                        count+=1
                        continue
                    else:
                        ids = ""
                        for pmid in slist:
                            ids += str(pmid) + ","
                        print("Downloading part " + str(doccount) + " of " + str(total_parts))
                        data = api.get_abstract(ids)
                        slist = []
                        count = 0
                        doccount+=1
                        self.split_abstracts(query, data)

                if count > 0:
                    ids = ""
                    for pmid in slist:
                        ids += str(pmid) + ","
                    data = api.get_abstract(ids)
                    self.split_abstracts(query, data)
                print("Download done.")
                return True
            else:
                print("No data found!")
                return False
        else:
            print("Corpus exists.")
            return True

    def create_relevant_docs(self,query,filepath, geneset):
        print("Corpus creating.......")
        
        rel_docs = []
        if filepath:
            path = "home/" + filepath
            if os.path.exists(path):
                # For txt file type 
                with open(path,'r') as fp:
                    genelist = fp.read().split('\n')
        elif len(geneset) > 0:
            genelist = geneset.split(',')
            # incase user forget , then split by space
            if len(genelist) == 1:
                genelist = genelist[0].split()
        else:
            print("Corpus not done: neither file nor gene set given")

        # print(genelist)
        golden_folder_name = self.get_corpus_folder(query)
        for _file in os.listdir(golden_folder_name):
            # with open(golden_folder_name+"/"+_file, 'r') as rf:
            #     content = self.preprocess(rf.read())
            #     result,gene = self.checkRelevance(content,genelist)
            #     if result:
            rel_docs.append(int(_file))
        # Keep rel docs in a file for reuse 
        path = "home/goldenpmids/" + query
        if not os.path.exists(path):
            os.mkdir(path)
        print(path)
        realdoc = open(path+"/goldenpmid.txt","w")
        for element in rel_docs:
            realdoc.write('%d\n' % element)
        realdoc.close()
        print("Corpus done..")


    def split_abstracts(self,query, data):

        lines = xmltodict.parse(data)   
        article = lines['PubmedArticleSet']['PubmedArticle']
        if(type(article) is list):
            for obj in article:
                text = ""
                title = ""
                citation = obj['MedlineCitation']
                pmid = citation['PMID']['#text']
                # print(pmid)

                # title extraction
                if('ArticleTitle' in citation['Article']):
                    if(type(citation['Article']['ArticleTitle']) is list):
                        title = citation['Article']['ArticleTitle'][0]
                    elif(type(citation['Article']['ArticleTitle']) is str):
                        title = citation['Article']['ArticleTitle']
                    elif(type(citation['Article']['ArticleTitle']) is collections.OrderedDict):
                        title = citation['Article']['ArticleTitle']['#text']

                # abstract extraction
                if('Abstract' in citation['Article']):
                    abstracts = citation['Article']['Abstract']
                    if('AbstractText' in abstracts):
                        if(type(abstracts['AbstractText']) is list):
                            for abs in abstracts['AbstractText']:
                                if(type(abs) is collections.OrderedDict):
                                    if('#text' in abs):
                                        text += abs['#text']
                                elif(abs is not None):
                                    text += abs
                        elif(type(abstracts['AbstractText']) is collections.OrderedDict):
                            if('#text' in abstracts['AbstractText']):
                                text += abstracts['AbstractText']['#text']
                        elif(type(abstracts['AbstractText']) is str):
                            text += abstracts['AbstractText']
                title += text
                if(title):
                    wf = open(self.get_corpus_folder(query) + "/" + pmid, 'w')
                    wf.write(title)
                    wf.close()
        else:
            text = ""
            title = ""
            citation = article['MedlineCitation']
            pmid = citation['PMID']['#text']
            print(pmid)

            # title extraction
            if('ArticleTitle' in citation['Article']):
                if(type(citation['Article']['ArticleTitle']) is list):
                    title = citation['Article']['ArticleTitle'][0]
                elif(type(citation['Article']['ArticleTitle']) is str):
                    title = citation['Article']['ArticleTitle']
                elif(type(citation['Article']['ArticleTitle']) is collections.OrderedDict):
                    title = citation['Article']['ArticleTitle']['#text']

            # abstract extraction
            if('Abstract' in citation['Article']):
                abstracts = citation['Article']['Abstract']
                if('AbstractText' in abstracts):
                    if(type(abstracts['AbstractText']) is list):
                        for abs in abstracts['AbstractText']:
                            if(type(abs) is collections.OrderedDict):
                                if('#text' in abs):
                                    text += abs['#text']
                            elif(abs is not None):
                                text += abs
                    elif(type(abstracts['AbstractText']) is collections.OrderedDict):
                        if('#text' in abstracts['AbstractText']):
                            text += abstracts['AbstractText']['#text']
                    elif(type(abstracts['AbstractText']) is str):
                        text += abstracts['AbstractText']
            title += text
            if(title):
                wf = open(self.get_corpus_folder(query) + "/" + pmid, 'w')
                wf.write(title)
                wf.close()

