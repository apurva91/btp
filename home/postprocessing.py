import os
import json
from . import mesh_explosion
import operator
from random import randint
import xlrd
from . import entity_recognition as enrecog
import re


class PostProcessing():

    def __init__(self):
        pass

    def getTitleAbs(self,index,json_no,query):
        # open json
        dfet = mesh_explosion.DataForEachMeshTerm(None,None)
        data_folder_name = dfet.get_data_foldername(query)
        with open(data_folder_name+"/"+str(json_no)+".json", 'r') as f:
            json_object = json.load(f)
            abstracts = json_object["abstracts"]
            titles = json_object["titles"]
            toptitles,topabs, completeabstracts = self.split_abstracts(index,abstracts,titles)
            return toptitles, topabs, completeabstracts

    def split_abstracts(self,index,abstracts,titles):
        count = 0
        trimmedabstracts = []
        completeabstracts = [] # nedded for Gene tagging
        trimmedtitles = []
        while(count < 10 and index < len(abstracts)):
            trimmedabstracts.append(self.getProcessedAbs(abstracts[index]))
            trimmedtitles.append(self.getProcessedTitle(titles[index]))
            completeabstracts.append(abstracts[index])
            index += 1
            count += 1
        return trimmedtitles,trimmedabstracts,completeabstracts
    def getalltrimmed(self,json_no,query):
        with open("home/data_folder/"+ query+ "/" + str(json_no)+".json", 'r') as f:
            json_object = json.load(f)
            abstracts = json_object["abstracts"]
            titles = json_object["titles"]
            return self.split_all_abstracts(abstracts,titles)
    def split_all_abstracts(self,abstracts,titles):
        trimmedabs = []
        absarr = [] # nedded for Gene tagging
        trimmedtitles = []
        for index in range(0,len(abstracts)):
            trimmedabs.append(self.getProcessedAbs(abstracts[index]))
            trimmedtitles.append(self.getProcessedTitle(titles[index]))
            absarr.append(abstracts[index])
        return trimmedtitles,trimmedabs,absarr

    def getProcessedAbs(self, abstract):
        abs = ""
        i = 0
        c = 0
        divide = 0
        while(c < 2 and i < len(abstract)):
            if(abstract[i] == '\n'):
                i += 1
                continue
            abs += abstract[i]
            divide += 1
            if((divide >= 80 and abstract[i] == ' ') or divide >= 93):
                if(c == 0):
                    abs += '\n'
                c += 1
                divide = 0
            i += 1
        return abs

    def getProcessedTitle(self, title):
        data = ""
        i = 0
        divide = 0
        while(i < len(title)):
            if(title[i] == '\n'):
                i += 1
                continue
            data += title[i]
            divide += 1
            if(divide >= 80 and title[i] == ' ' or divide >= 93):
                data += '\n'
                divide = 0
            i += 1
        return data

    def term_tagging(self,optimized_terms):
       
        term_dict = {}
        for terms in optimized_terms:
            for term in terms:
                i = 0
                count=0
                st = ""
                while i<len(term):
                    if term[i] == '"':
                        count += 1
                        if count%2==0:
                            self.countoccurrences(term_dict,st) 
                        st = ""
                    else:
                        st += term[i]
                    i += 1
        print(term_dict)
        sorted_dict = sorted(term_dict.items(), key=operator.itemgetter(1),reverse=True)
        print(sorted_dict)
        return sorted_dict

    def countoccurrences(self,store,value):
        try:
            store[value] = store[value] + 1
        except KeyError as e:
            store[value] = 1
        return

    def gene_cloud_dictionary_based(self,term_id,gene_file_name,search_term):
        print("Gene cloud called..")
        file_name = "home/data_folder/"+search_term+"/"+str(term_id)+'.json'
        try:
            with open(file_name, 'r') as f:
                json_object = json.load(f)
        except FileNotFoundError:
            return 0,None

        data_abstract = json_object["abstracts"]
        data_title = json_object["titles"]
        data_pmids = json_object["articleIds"]

        abstracts = ""
        for _i in range(0,len(data_abstract)):
            abstracts = abstracts+data_title[_i]+data_abstract[_i]

        content = abstracts.replace('\n', ' ')
        content = content.replace('.', ' ')
        content = content.replace(',', ' ')
        content = content.lower()

        data = content.split()


        root = {}
        children = [] 
        c = 0

        # For text file
        # filepointer = open(gene_file_name,'r')
        # genefile_arr = filepointer.read().lower().split('\n')
        # for gene in genefile_arr:
        #     if gene:
        #         gene_obj = {}
        #         gene_obj["index"] = c
        #         c = c + 1
        #         gene_obj["name"] = gene
        #         gene_obj["count"] = data.count(gene)
        #         gene_obj["value"] = 20 + gene_obj["count"]
        #         alltitle = []
        #         allpmids = []
        #         for _i in range(0, len(data_abstract)):
        #             if data_abstract[_i].find(gene) >= 0:
        #                 alltitle.append(data_title[_i])
        #                 allpmids.append(data_pmids[_i])
        #             elif data_title[_i].find(gene) >= 0:
        #                 alltitle.append(data_title[_i])
        #                 allpmids.append(data_pmids[_i])
        #         gene_obj["children"] = None
        #         gene_obj["title"] = alltitle
        #         gene_obj["pmids"] = allpmids
        #         children.append(gene_obj)
        # root["name"] = "Gene cloud"
        # root["value"] = 100
        # root["count"] = 1
        # root["title"] = "Its root"
        # root["pmids"] = 0
        # root["children"] = children
        # close file

        # For xlsx file
        # path = ("home/gene_list.xlsx")
        # wb = xlrd.open_workbook(path)
        # sheet = wb.sheet_by_index(0)
        # for row in range(0,sheet.nrows):
        #     for col in range(0,sheet.ncols):
        #         if row != 0 and col!=0 and col != 1 and col!=8 and col!=9 and col!=10 and col!=11 and col!=12 and sheet.cell_value(row,col):
        #             if sheet.cell_value(row,col):
        #                 gene_obj = {}
        #                 gene_obj["index"] = c
        #                 c = c + 1
        #                 gene = str(sheet.cell_value(row,col))
        #                 match = 0
        #                 for obj in children:
        #                     if obj["name"] == gene:
        #                         match = 1
        #                         break
        #                 if match == 0:
        #                     gene_obj["name"] = gene
        #                     gene_obj["count"] = data.count(gene)
        #                     gene_obj["value"] = gene_obj["count"]
        #                     alltitle = []
        #                     allpmids = []
        #                     for _i in range(0, len(data_abstract)):
        #                         if data_abstract[_i].find(gene) >= 0:
        #                             alltitle.append(data_title[_i])
        #                             allpmids.append(data_pmids[_i])
        #                         elif data_title[_i].find(gene) >= 0:
        #                             alltitle.append(data_title[_i])
        #                             allpmids.append(data_pmids[_i])
        #                     gene_obj["children"] = None
        #                     gene_obj["title"] = alltitle
        #                     gene_obj["pmids"] = allpmids
        #                     children.append(gene_obj)
        #         else:
        #             if c > 10000:
        #                 break
        #     if c > 10000:
        #         break
        # root["name"] = "Gene cloud"
        # root["value"] = 1000
        # root["count"] = 1
        # root["title"] = "Its root"
        # root["pmids"] = 0
        # root["children"] = children
        # print(root)
        # return 1,root

    def gene_cloud(self,query,json_arr):
        if len(json_arr) < 0:
            return 0,None
        else:
            all_json_abstracts = []
            gene_objects = {}
            for json_id in json_arr:
                try:
                    path = "home/data_folder/"+query+"/"+str(json_id)+'.json'
                    with open(path,'r') as f:
                        json_object = json.load(f)
                        abstracts = json_object["abstracts"]
                        all_json_abstracts.extend(abstracts)
                        pmids = json_object["articleIds"]
                        titles = json_object["titles"]
                        for index in range(0,len(abstracts)):
                            diseases,genes,proteins = enrecog.entity_recog_rb(abstracts[index])
                            for gene in genes:
                                try:
                                    gene_objects[gene.lower()]["title"].append(titles[index])
                                    gene_objects[gene.lower()]["pmids"].append(pmids[index])
                                except KeyError:
                                    obj = {}
                                    obj["name"] = gene
                                    obj["children"] = None
                                    obj["title"] = []
                                    obj["pmids"] = []
                                    obj["title"].append(titles[index])
                                    obj["pmids"].append(pmids[index])
                                    gene_objects[gene.lower()] = obj
                            # break      
                except FileNotFoundError:
                    continue
                break

            # Make a long string of abstracts for counting entities
            absstring = ""
            for i in range(len(all_json_abstracts)):
                absstring += " "
                absstring += all_json_abstracts[i]
            absstring = absstring.lower()
            # filter out some genes and add count value
            key_list = list(gene_objects.keys())
            for key in key_list:
                occur = absstring.count(key.lower())
                if occur < 5 or len(key) < 4:
                    # print("deleted: ",key)
                    del(gene_objects[key])
                else:
                    gene_objects[key.lower()]["value"] = occur 
            # create children array
            children = []
            for key, value in gene_objects.items():
                children.append(value)
            # create root node
            root = {}
            root["name"] = "Gene cloud"
            root["value"] = 1000
            root["title"] = "Its root"
            root["pmids"] = []
            root["children"] = children
            if len(children) > 0:
                return 1,root
            else:
                print("No genes found !!")
                return 0,None

    def mesh_cloud(self,term_id,search_term):
        print("Mesh cloud called..")
        file_name = "home/data_folder/"+search_term+"/"+str(term_id)+'.json'
        try:
            with open(file_name, 'r') as f:
                json_object = json.load(f)
        except FileNotFoundError:
            return 0,None

        mesh_terms_matrix = json_object["meshterms"]
        
        meshobject = {}
        for row in mesh_terms_matrix:
            for meshterm in row:
                if meshterm in meshobject:
                    meshobject[meshterm] += 1
                else:
                    meshobject[meshterm] = 1
        root = {}
        children = []
        for meshterm , frequency in meshobject.items():
            new_list = {}
            new_list["name"] = meshterm
            new_list["value"] = frequency
            new_list["children"] = None
            children.append(new_list)
        root["name"] = "Mesh cloud"
        root["value"] = 1000
        root["children"] = children
        # print(root)
        return 1,root
    
    def entityrelation(self,query,json_arr):
        
        if len(json_arr) < 0:
            return 0,None
        else:
            all_json_abstracts = []
            disease_obj = {}
            gene_obj = {}
            protein_obj = {}
            for json_id in json_arr:
                try:
                    path = "home/data_folder/"+query+"/"+str(json_id)+'.json'
                    print(path)
                    with open(path,'r') as f:
                        json_object = json.load(f)
                        abstracts = json_object["abstracts"]
                        all_json_abstracts.extend(abstracts)
                        pmids = json_object["articleIds"]
                        for index in range(0,len(abstracts)):
                            diseases,genes,proteins = enrecog.entity_recog_rb(abstracts[index])
                            for disease in diseases:
                                try:
                                    disease_obj[disease.lower()]["neighbour"].append(int(pmids[index]))
                                except KeyError:
                                    disease_obj[disease.lower()] = {} # needed as multi level initialization not 
                                    disease_obj[disease.lower()]["neighbour"] = []
                                    disease_obj[disease.lower()]["neighbour"].append(int(pmids[index]))
                                    disease_obj[disease.lower()]["type"] = "disease"
                            for gene in genes:
                                try:
                                    gene_obj[gene.lower()]["neighbour"].append(int(pmids[index]))
                                except KeyError:
                                    gene_obj[gene.lower()] = {}
                                    gene_obj[gene.lower()]["neighbour"] = []
                                    gene_obj[gene.lower()]["neighbour"].append(int(pmids[index]))
                                    gene_obj[gene.lower()]["type"] = "gene"
                            for protein in proteins:
                                try:
                                    protein_obj[protein.lower()]["neighbour"].append(int(pmids[index]))
                                except KeyError:
                                    protein_obj[protein.lower()] = {}
                                    protein_obj[protein.lower()]["neighbour"] = []
                                    protein_obj[protein.lower()]["neighbour"].append(int(pmids[index]))
                                    protein_obj[protein.lower()]["type"] = "protein"
                            # break      
                except FileNotFoundError:
                    continue
                # system can't handle all data : Need more RAM
                break
            # Make a long string of abstracts for counting entities
            absstring = ""
            for i in range(len(all_json_abstracts)):
                absstring += " "
                absstring += all_json_abstracts[i]
            absstring = absstring.lower()

            # remove some objects 
            key_list = list(disease_obj.keys())
            for key in key_list:
                occur = absstring.count(key.lower())
                if occur < 5:
                    del(disease_obj[key])
            key_list = list(gene_obj.keys())
            for key in key_list:
                occur = absstring.count(key.lower())
                if occur < 5:
                    del(gene_obj[key])
            key_list = list(protein_obj.keys())
            for key in key_list:
                occur = absstring.count(key.lower())
                if occur < 5:
                    del(protein_obj[key])

            # protein-protein relation
            p_prelation = {} 
            p_pnodes = {}
            p_plinks = {}
            findex = 0
            # create nodes array
            for fkey, fvalue in protein_obj.items():
                p_pnodes[fkey.lower()] = {"index": findex, "label": fkey.lower(), "type": "circle","links": []}
                p_plinks[fkey.lower()] = {"source": findex,"target": []}
                sindex = 0
                for skey, svalue in protein_obj.items():
                    if sindex > findex: # taking care of 1-2 and 2-1 cases
                        common = set(fvalue["neighbour"]).intersection(set(svalue["neighbour"]))
                        if len(common) > 0:
                            p_pnodes[fkey.lower()]["links"].append(sindex)
                            p_plinks[fkey.lower()]["target"].append(sindex)
                    sindex += 1
                findex += 1
            for key,val in p_pnodes.items():
                try:
                    p_prelation["nodes"].append(val)
                except KeyError:
                    p_prelation["nodes"] = []
                    p_prelation["nodes"].append(val)
            # create links array
            p_prelation["links"] = []
            for key, val in p_plinks.items():
                try:                    
                    for target in val["target"]:
                        p_prelation["links"].append({"source": val["source"],"target": target})
                except KeyError:
                    continue

            # gene-protein relation
            g_prelation = {} 
            g_pnodes = {}
            g_plinks = {}
            # create single object
            extended_geneobj = gene_obj 
            extended_geneobj.update(protein_obj)

            findex = 0
            for fkey, fvalue in extended_geneobj.items():
                g_pnodes[fkey.lower()] = {"index": findex, "label": fkey.lower(), "links": []}
                if fvalue["type"] == "protein":
                    g_pnodes[fkey.lower()]["type"] = "circle"
                else:
                    g_pnodes[fkey.lower()]["type"] = "square"
                g_plinks[fkey.lower()] = {"source": findex,"target": []}
                sindex = 0
                for skey, svalue in extended_geneobj.items():
                    if fvalue["type"] != svalue["type"]: # only gene to protein 
                        common = set(fvalue["neighbour"]).intersection(set(svalue["neighbour"]))
                        if len(common) > 0:
                            g_pnodes[fkey.lower()]["links"].append(sindex)
                            g_plinks[fkey.lower()]["target"].append(sindex)
                    sindex += 1
                findex += 1
            # add nodes to list
            for key,val in g_pnodes.items():
                try:
                    g_prelation["nodes"].append(val)
                except KeyError:
                    g_prelation["nodes"] = []
                    g_prelation["nodes"].append(val)
            g_prelation["links"] = []
            for key, val in g_plinks.items():
                try:                    
                    for target in val["target"]:
                        g_prelation["links"].append({"source": val["source"],"target": target})
                except KeyError:
                    continue

            # disease protein relation
            d_prelation = {} 
            d_pnodes = {}
            d_plinks = {}
            # create single object
            extended_diseaseobj = disease_obj 
            extended_diseaseobj.update(protein_obj)

            findex = 0
            for fkey, fvalue in extended_diseaseobj.items():
                d_pnodes[fkey.lower()] = {"index": findex, "label": fkey.lower(), "links": []}
                if fvalue["type"] == "protein":
                    d_pnodes[fkey.lower()]["type"] = "circle"
                else:
                    d_pnodes[fkey.lower()]["type"] = "square"
                d_plinks[fkey.lower()] = {"source": findex,"target": []}
                sindex = 0
                for skey, svalue in extended_diseaseobj.items():
                    if fvalue["type"] != svalue["type"]: # only gene to protein 
                        common = set(fvalue["neighbour"]).intersection(set(svalue["neighbour"]))
                        if len(common) > 0:
                            d_pnodes[fkey.lower()]["links"].append(sindex)
                            d_plinks[fkey.lower()]["target"].append(sindex)
                    sindex += 1
                findex += 1
            # add nodes to list
            for key,val in d_pnodes.items():
                try:
                    d_prelation["nodes"].append(val)
                except KeyError:
                    d_prelation["nodes"] = []
                    d_prelation["nodes"].append(val)
            d_prelation["links"] = []
            for key, val in d_plinks.items():
                try:                    
                    for target in val["target"]:
                        d_prelation["links"].append({"source": val["source"],"target": target})
                except KeyError:
                    continue
            # Final data for visualization using d3js
            data ={}
            data["pprelation"] = p_prelation
            data["gprelation"] = g_prelation
            data["dprelation"] = d_prelation

            return 1,data

    def get_entities(self,query,json_arr,option):
        if len(json_arr) < 0:
            return 0,None
        else:
            abstracts = []
            pmids = []
            titles = []
            for json_id in json_arr:
                try:
                    path = "home/data_folder/"+query+"/"+str(json_id)+'.json'
                    with open(path,'r') as f:
                        json_object = json.load(f)
                        abstracts.extend(json_object["abstracts"])
                        pmids.extend(json_object["articleIds"])
                        titles.extend(json_object["titles"])
                except FileNotFoundError:
                    continue
                # system can't handle all data : Need more RAM
                break 
            # Make a long string of abstracts for entity recognition
            abs = ""
            for i in range(len(abstracts)):
                abs += " "
                abs += abstracts[i]
            # print(abs)
            if len(abs) > 0:
                # call entity recognition model here
                entities = {}
                disease = []
                gene = []
                protein = []
                if option == 1:
                    disease,gene,protein = enrecog.entity_recog_nn(abs)
                elif option == 2:
                    disease,gene,protein = enrecog.entity_recog_rb(abs)
                if disease:
                    disease = list(disease)
                    entities["disease"] = disease
                if gene:
                    gene = list(gene)
                    entities["gene"] = gene
                if protein:
                    protein = list(protein)
                    entities["protein"] = protein
                if len(disease):
                    for rog in disease:
                        toreplace = "<span class='disease-highlight' data-toggle=\"tooltip\" title=\"Disease\">\g<0></span>"
                        if len(rog) > 2:
                            pattern = re.escape(rog)
                            for index in range(len(abstracts)):
                                abstracts[index] = re.sub(pattern,toreplace,abstracts[index])
                                titles[index] = re.sub(pattern,toreplace,titles[index])
                if len(protein):
                    for pro in protein:
                        toreplace = "<span class='protein-highlight' data-toggle=\"tooltip\" title=\"Protein\">\g<0></span>"
                        if len(pro) > 2:
                            pattern = re.escape(pro)
                            for index in range(len(abstracts)):
                                abstracts[index] = re.sub(pattern,toreplace,abstracts[index])
                                titles[index] = re.sub(pattern,toreplace,titles[index])
                if len(gene):
                    for _g in gene:
                        toreplace = "<span class='gene-highlight' data-toggle=\"tooltip\" title=\"Gene\">\g<0></span>"
                        if len(_g) > 2:
                            pattern = re.escape(_g)
                            for index in range(len(abstracts)):
                                abstracts[index] = re.sub(pattern,toreplace,abstracts[index])
                                titles[index] = re.sub(pattern,toreplace,titles[index])
                
                data = zip(titles,abstracts,pmids)
                return 1, entities,data
            else:
                return 0,None
                            
