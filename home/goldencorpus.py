import os
from . import api
import xmltodict, collections
from . import mesh_explosion
import xlrd

class GoldenCorpus():

    def __init__(self,query,filepath):
        self.query = query
        self.filepath = filepath
        self.rel_docs = []
        self.mesh_terms = []

    def get_corpus_folder(self,query):
        return "home/golden_corpus/" + query
        
    def get_mesh_terms(self):
        return self.mesh_terms
    
    def get_rel_docs_pmid(self):
        rel_doc = []
        rdoc = open("home/pmid.txt","r")
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
        # for gene in genes:
        #     if gene and gene+" " in abs:
        #         return True,gene
        for row in range(0,genes.nrows):
            for col in range(0,genes.ncols):
                if row != 0 and col!=0 and col != 1 and col!=8 and col!=9 and col!=10 and col!=11 and col!=12 and genes.cell_value(row,col):
                    if str(genes.cell_value(row,col))+" " in abs:
                        return True,genes.cell_value(row,col) 
        
        return False,""

    def fetchData(self):
        print("Fetchdata called..")
        _pmids, self.mesh_terms = api.fetch_data(self.query,200)
        print("pmid:----------------------------------> ",len(_pmids))
        if self.saveGoldenCorpus(_pmids):
            return True
        else: 
            return False


    def saveGoldenCorpus(self, _pmids):
        print("Save golden corpus called..")
        _genefile = []
        if not os.path.exists(self.get_corpus_folder(self.query)):
            os.mkdir(self.get_corpus_folder(self.query))
            #  Download abs as a group of 200
            if len(_pmids):
                slist = []
                count = 0
                doccount = 1

                total_parts = int(len(_pmids)/200)
                for cid in _pmids:
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
                        self.split_abstracts(self.query, data)

                if count > 0:
                    ids = ""
                    for pmid in slist:
                        ids += str(pmid) + ","
                    data = api.get_abstract(ids)
                    self.split_abstracts(self.query, data)
            else:
                print("No data found!")
                return False
        
            # check relevance and populate get rel_Docset
            print("Download done.")
            print("Relevant docs creating.......")
            if os.path.exists("home/" + self.filepath):
                # _filepointer = open(self.filepath,'r')
                # _genefile = _filepointer.read().split('\n')
                path = ("home/" + self.filepath)
                wb = xlrd.open_workbook(path)
                sheet = wb.sheet_by_index(0)

                abstracts_folder_name = self.get_corpus_folder(self.query)
                for _file in os.listdir(abstracts_folder_name):
                    rf = open(abstracts_folder_name+"/"+_file, 'r')
                    content = self.preprocess(rf.read())
                    result,gene = self.checkRelevance(content,sheet)
                    count = 0
                    if result:
                        count += 1
                        # print("file: ",file)
                        # print("gene found: -- > ", gene)
                        self.rel_docs.append(int(_file))
                realdoc = open("home/pmid.txt","w")
                for element in self.rel_docs:
                    realdoc.write('%d\n' % element)
                realdoc.close()
                print("Corpus done..")
                return True
            else:
                print("Genefile not found...")
                return False
        else:
            print("Corpus exists.")
            return True
        return False
    def split_abstracts(self,query, data):

        lines = xmltodict.parse(data)   
        article = lines['PubmedArticleSet']['PubmedArticle']
        if(type(article) is list):
            for obj in article:
                text = ""
                title = ""
                citation = obj['MedlineCitation']
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

