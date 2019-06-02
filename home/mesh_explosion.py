import os
import itertools
import json
from . import api
import xmltodict,collections

class DataForEachMeshTerm():
    def __init__(self, mesh_terms, query):
        self.mesh_terms = mesh_terms
        self.query = query
        if self.mesh_terms and self.query:
            self.fetchMeshTermdata()

    def get_data_foldername(self,query):
        return "home/data_folder/" + query

    def get_search_term(self):
        return self.query

    def getMeshTermCombinations(self,mesh_terms):
        terms = mesh_terms
        part = ""
        mystr = []
        skip = 0
        for pos in range(0,len(terms)):
            if skip:
                skip = skip - 1
                continue
            if(pos > 1):
                if terms[pos-2] == 'A' and terms[pos-1] == 'N' and terms[pos] == 'D':
                    if len(part) != 0:
                        if part[len(part)-1] == ')':
                            mystr.append(part)
                            part = ""
                            # skip by 4
                            skip = 4
                        else:
                            part += terms[pos-3]
                    else:
                        part += terms[pos-3]
                else:
                    if pos-3 >= 0:
                        part += terms[pos-3]
        part += terms[pos-2]
        part += terms[pos-1]
        part += terms[pos]
        part += ']'    # so lazy to find bug . Just added it :)
        mystr.append(part)

        # get combs of each arr of mystr
        allcomb = []
        for terms in range(0,len(mystr)):

            myterms = mystr[terms].split('OR')
            myterms = [term.replace('(', '') for term in myterms]
            myterms = [term.replace(')', '') for term in myterms]
            myterms = [term.strip() for term in myterms]
            myterms = ['('+term+')' if 'AND' in term else term for term in myterms]


            combs = []
            for i in range(1, len(myterms)+1):
                tmp = [list(x) for x in itertools.combinations(myterms,i)]
                combs.extend(tmp)
            mesh_exps = []
            for comb in combs:
                s = ""
                count = 0
                for term in comb:
                    if count == 0:
                        s += term
                    else:
                        s += " OR " + term
                    count += 1
                mesh_exps.append(s)
            allcomb.append(mesh_exps)
        final = []
        final = allcomb[0]
        for p in range(1,len(allcomb)):
            for x in range(0,len(final)):
                for y in range(0,len(allcomb[p])):
                    final[x] = final[x] + ' AND ' + allcomb[p][y]
        return final

    def fetchMeshTermdata(self):
        # download top 400 documents for each query and keep in a json file.
        # json file helps better access of information in cluster file 
        _retmax = 400
        if self.mesh_terms:
            self.expanded_mesh_terms = self.getMeshTermCombinations(self.mesh_terms)
        else:
            print("No mesh term returned by PUBMED API..")
            return
        if self.expanded_mesh_terms and self.query:
            print("Total expanded meshterms: ",len(self.expanded_mesh_terms))
            print("Getting information for each mesh-term and create a json file...")
            if not os.path.exists(self.get_data_foldername(self.get_search_term())):
                os.mkdir(self.get_data_foldername(self.get_search_term()))
                count = 0
                print('-------------------------------------------------------')
                for term in self.expanded_mesh_terms:
                    print(term)
                    count = count + 1
                    # Getting abstract here
                    _pmids, mtdummy = api.fetch_data(term,_retmax)
                    # Get abs for all ids together
                    ids = ""
                    for pmid in _pmids:
                        ids += str(pmid) + ","
                    data = api.get_abstract(ids)
                    lines = xmltodict.parse(data)
                    
                    id_list = []
                    title_list = []
                    abstract_list = []
                    meshterms = []
                    try:
                        article = lines['PubmedArticleSet']['PubmedArticle']
                    except KeyError:
                        continue

                    for obj in article:
                        text = ""
                        title = ""
                        citation = obj['MedlineCitation']
                        pmid = citation['PMID']['#text']
                        mesh_heading = []
                        id_list.append(pmid)
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

                        # Mesh terms associated with a pmid 
                        temp = ""
                        if('MeshHeadingList' in citation):
                            for ob in citation['MeshHeadingList']['MeshHeading']:
                                if('DescriptorName' in ob):
                                    temp = ob['DescriptorName']['#text']
                                if ('QualifierName' in ob):
                                    if(type(ob['QualifierName']) is list):
                                        for qualifier in ob['QualifierName']:
                                            mesh_heading.append(temp+'/'+qualifier['#text'])
                                    else:
                                        mesh_heading.append(temp+'/'+ob['QualifierName']['#text'])
                                else:
                                    mesh_heading.append(temp)
                        title_list.append(title)
                        abstract_list.append(text)
                        meshterms.append(mesh_heading)
                        
                    # build json object with relevent fields from abstract xml
                    jObject = {}
                    jObject['queryId'] = count
                    jObject['query'] = term
                    jObject['articleIds'] = id_list
                    jObject['titles'] = title_list
                    jObject['abstracts'] = abstract_list
                    jObject['meshterms'] = meshterms

                    with open(self.get_data_foldername(self.get_search_term())+"/"+str(count)+'.json', 'w') as outfile:
                        json.dump(jObject, outfile)
            else:
                print("Folder named [ {} ] exists inside data_folder. Please remove.".format(self.query))
        else:
            print("Either no mesh terms or no query received")

