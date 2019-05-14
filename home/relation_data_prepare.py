import os,glob
import xlsxwriter 
import xlrd
import json
from . import entity_recognition as enrecog


def getlines(abs):
    # print(abs)
    line = ""
    linearr = []
    for i in range(0,len(abs)-1): # -1 for ignoring last sentence: All rights reserved
        if abs[i] == '.':
            linearr.append(line)
            line = ""
        else:
            line += abs[i]
    return linearr

def data_prepare():
    data_abs = []
    p_plines = []
    g_plines = []
    d_plines = []
    p_pobj = {}
    g_pobj = {}
    d_pobj = {}

    folder_path = '/home/tanmoy/extracellular matrix remodelling/'
    for filename in glob.glob(os.path.join(folder_path, '*.json')):
        with open(filename, 'r') as f:
            json_object = json.load(f)
            data_abs = json_object["abstracts"]
            for abs in data_abs:
                strarr = getlines(abs)
                for line in strarr:
                    diseases,genes,proteins = enrecog.entity_recog_rb(line)
                    proteins = list(proteins)
                    genes = list(genes)
                    diseases = list(diseases)
                    # protein protein relation
                    if len(proteins) > 1:
                        p_plines.append(line)
                        for i in range(0,len(proteins)):
                            for j in range(0,len(proteins)):
                                try:
                                    p_pobj[proteins[i].lower()].add(proteins[j].lower())
                                except KeyError:
                                    p_pobj[proteins[i].lower()] = set()
                                    p_pobj[proteins[i].lower()].add(proteins[j].lower())
                    # gene protein relation
                    if len(genes) > 0 and len(proteins) > 0:
                        g_plines.append(line)
                        for i in range(0,len(genes)):
                            for j in range(0,len(proteins)):
                                try:
                                    g_pobj[genes[i].lower()].add(proteins[j].lower())
                                except KeyError:
                                    g_pobj[genes[i].lower()] = set()
                                    g_pobj[genes[i].lower()].add(proteins[j].lower())
                    # disease protein relation
                    if len(diseases) > 0 and len(proteins) > 0:
                        d_plines.append(line)
                        for i in range(0,len(diseases)):
                            for j in range(0,len(proteins)):
                                try:
                                    d_pobj[diseases[i].lower()].add(proteins[j].lower())
                                except KeyError:
                                    d_pobj[diseases[i].lower()] = set()
                                    d_pobj[diseases[i].lower()].add(proteins[j].lower())
                # one abs
                # break
        # one json
        # break    
    # protein protein relation 
    # create unrelated sentence
    p_punrelated = []
    sentence = ["we didn't find corelation between ", "There is no relation between ", "we tested for "]
    start = 0
    all_proteins = set(p_pobj.keys())
    for key,value in p_pobj.items():
        setdiff = all_proteins.difference(value)
        for gene in setdiff:
            line = sentence[start%3] + key + " and " + gene
            start += 1
            p_punrelated.append(line)
    workbook = xlsxwriter.Workbook('protein_protein.xlsx') 
    worksheet = workbook.add_worksheet("My sheet")
    row = 0
    col = 0
    for line in p_plines:
        worksheet.write(row,col,line)
        worksheet.write(row,col+1,1)
        row += 1
    for line in p_punrelated:
        worksheet.write(row,col,line)
        worksheet.write(row,col+1,0)
        row += 1
    workbook.close()
    print('------------------------protein protein done-------------------------------')

    # gene protein
    # create unrelated sentence
    g_punrelated = []
    sentence = ["we didn't find corelation between ", "There is no relation between ", "we tested for "]
    start = 0
    all_proteins = []
    for key,value in g_pobj.items():
        all_proteins.extend(value)
    all_proteins = set(all_proteins)    
    for key,value in g_pobj.items():
        setdiff = all_proteins.difference(value)
        for gene in setdiff:
            line = sentence[start%3] + key + " and " + gene
            start += 1
            g_punrelated.append(line)
    workbook = xlsxwriter.Workbook('gene_protein.xlsx') 
    worksheet = workbook.add_worksheet("My sheet")
    row = 0
    col = 0
    for line in g_plines:
        worksheet.write(row,col,line)
        worksheet.write(row,col+1,1)
        row += 1
    for line in g_punrelated:
        worksheet.write(row,col,line)
        worksheet.write(row,col+1,0)
        row += 1
    workbook.close()
    print('---------------------------gene protein done----------------------------')

    # disease protein
    # create unrelated sentence
    d_punrelated = []
    sentence = ["we didn't find corelation between ", "There is no relation between ", "we tested for "]
    start = 0
    all_proteins = []
    for key,value in d_pobj.items():
        all_proteins.extend(value)
    all_proteins = set(all_proteins)    
    for key,value in d_pobj.items():
        setdiff = all_proteins.difference(value)
        for gene in setdiff:
            line = sentence[start%3] + key + " and " + gene
            start += 1
            d_punrelated.append(line)
    workbook = xlsxwriter.Workbook('disease_protein.xlsx') 
    worksheet = workbook.add_worksheet("My sheet")
    row = 0
    col = 0
    for line in d_plines:
        worksheet.write(row,col,line)
        worksheet.write(row,col+1,1)
        row += 1
    for line in d_punrelated:
        worksheet.write(row,col,line)
        worksheet.write(row,col+1,0)
        row += 1
    workbook.close()
    print('------------------------disease protein done-------------------------------')




