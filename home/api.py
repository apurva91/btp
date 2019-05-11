import requests
import xmltodict

def get_proxy():
    http_proxy  = "http://tanmo174101028:4TvZz67q@202.141.80.22:3128/"
    https_proxy  = "https://tanmo174101028:4TvZz67q@202.141.80.22:3128/"
    ftp_proxy   = "ftp://tanmo174101028:4TvZz67q@202.141.80.22:3128/"

    proxyDict = {
        "http"  : http_proxy,
        "https" : https_proxy,
        "ftp"   : ftp_proxy
    }
    return proxyDict

def query_information(query,retmax):
    proxyDict = get_proxy()
    _url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&api_key=8a5dbb9e8cf82bf8f7d80e2c180b4d4d3c09&term={}&retmax={}&retmode=json'
    # _res = requests.get(_url.format(query,retmax)).json()
    _res = requests.get(_url.format(query,retmax),proxies=proxyDict).json()
    return _res

def get_abstract(_ids):
    proxyDict = get_proxy()
    abstracturl = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&api_key=8a5dbb9e8cf82bf8f7d80e2c180b4d4d3c09&id={}&retmode=xml&rettype=abstract'
    # idabstract = requests.get(abstracturl.format(_ids)).text
    idabstract = requests.get(abstracturl.format(_ids),proxies=proxyDict).text
    return idabstract

def fetch_data(query,_retmax):
    _res = query_information(query,_retmax)
    _pmids = _res['esearchresult']['idlist']
    _mesh_terms = _res['esearchresult']['querytranslation']
    # print('pmids: ',_pmids)
    return _pmids , _mesh_terms



