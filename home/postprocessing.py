import os
import json
from . import mesh_explosion
import operator
from random import randint
import xlrd


class PostProcessing():

    def __init__(self):
        pass

    def getTitleAbs(self,index,json_no,query):
        # open json
        dfet = mesh_explosion.DataForEachMeshTerm(None,None)
        data_folder_name = dfet.get_data_foldername(query)
        f = open(data_folder_name+"/"+str(json_no)+".json", 'r')
        json_object = json.load(f)
        f.close()
        abstracts = json_object["abstracts"]
        titles = json_object["titles"]
        mesh_terms = json_object["meshterms"]
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

    def gene_cloud(self,term_id,gene_file_name,search_term):
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
        path = ("home/gene_list.xlsx")
        wb = xlrd.open_workbook(path)
        sheet = wb.sheet_by_index(0)
        for row in range(0,sheet.nrows):
            for col in range(0,sheet.ncols):
                if row != 0 and col!=0 and col != 1 and col!=8 and col!=9 and col!=10 and col!=11 and col!=12 and sheet.cell_value(row,col):
                    if sheet.cell_value(row,col):
                        gene_obj = {}
                        gene_obj["index"] = c
                        c = c + 1
                        gene = str(sheet.cell_value(row,col))
                        match = 0
                        for obj in children:
                            if obj["name"] == gene:
                                match = 1
                                break
                        if match == 0:
                            gene_obj["name"] = gene
                            gene_obj["count"] = data.count(gene)
                            gene_obj["value"] = gene_obj["count"]
                            alltitle = []
                            allpmids = []
                            for _i in range(0, len(data_abstract)):
                                if data_abstract[_i].find(gene) >= 0:
                                    alltitle.append(data_title[_i])
                                    allpmids.append(data_pmids[_i])
                                elif data_title[_i].find(gene) >= 0:
                                    alltitle.append(data_title[_i])
                                    allpmids.append(data_pmids[_i])
                            gene_obj["children"] = None
                            gene_obj["title"] = alltitle
                            gene_obj["pmids"] = allpmids
                            children.append(gene_obj)
                else:
                    if c > 10000:
                        break
            if c > 10000:
                break
        root["name"] = "Gene cloud"
        root["value"] = 1000
        root["count"] = 1
        root["title"] = "Its root"
        root["pmids"] = 0
        root["children"] = children
        # print(root)
        return 1,root

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

    def generelation(self,term_id,gene_file_name,search_term):
        file_name = "home/data_folder/"+search_term+"/"+str(term_id)+'.json'
        
        with open(file_name, 'r') as f:
            json_object = json.load(f)

        data_abstract = json_object["abstracts"]
        data_title = json_object["titles"]
        meshterms = json_object["meshterms"]

        abstracts = ""
        for _i in range(0,len(data_abstract)):
            abstracts = abstracts+data_title[_i]+data_abstract[_i]
            for _j in range(0, len(meshterms[_i])):
                abstracts += meshterms[_i][_j]

        content = abstracts.replace('\n', ' ')
        content = content.replace('.', ' ')
        content = content.replace(',', ' ')
        content = content.lower()

        data = content.split()

        filepointer = open(gene_file_name,'r')
        genefile_arr = filepointer.read().lower().split('\n')

        gene_dict = {}
        for _i in range(0, len(genefile_arr)):
            new_list = []

    def get_entities(self,query,json_arr):
        if len(json_arr) < 0:
            return 0,None
        else:
            abstracts = []
            for json_id in json_arr:
                try:
                    path = "home/data_folder/"+query+"/"+str(json_id)+'.json'
                    with open(path,'r') as f:
                        json_object = json.load(f)
                        abstracts.extend(json_object["abstracts"])
                except FileNotFoundError:
                    continue
            if len(abstracts) > 0:
                # call entity recognition model here

                disese = ["hello"]
                protein = ["hi"]
                rna = ["hehe"]
                dna = ["huhu"]
                
                entities = {}
                entities["disese"] = disese
                entities["protein"] = protein
                entities["rna"] = rna
                entities["dna"] = dna
                return 1, entities
            else:
                return 0,None
                            











