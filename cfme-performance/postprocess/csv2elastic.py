import csv
import sys
import os
import re
from elasticsearch import Elasticsearch

indir = sys.argv[1]
lstdirs = os.listdir(indir)

resultdictionary = {}
version = ""
workload = ""


def process_dirs(dirlist):
    resultdlst = []
    for dir in dirlist:
        if dir == "version_info":
            continue
        else:
            tmp_loc = indir + "/" + dir + "/"
            tmp_des = indir + "/" + dir + "/rawdata"
            lst_tmpdir = os.listdir(tmp_loc)
            for i in lst_tmpdir:
                if i.endswith(".csv"):
                    tmp_f = i
            tmp_file = tmp_loc + tmp_f
            os.system("cp %s %s" % (tmp_file, tmp_des))
            dictlist = handle_scenario(indir+"/"+dir+"/rawdata")
            del_file = tmp_des + "/" + tmp_f
            os.system("rm %s" % (del_file))
            tdict = {}
            tdict["scenerio-name"] = dir
            tdict["process-name"] = dictlist
        resultdlst.append(tdict)
    return resultdlst


def version_info():
    print ("TODO")


def handle_scenario(rawpath):
    mdict = {}
    rawfiles = os.listdir(rawpath)
    for file in rawfiles:
        reader = csv.DictReader(open(rawpath+"/"+file))
        rows = list(reader)
        out = rows
        nm = file.split('-')
        len_name = len(nm)
        if len_name == 2:
            p_id = nm[0]
            process_name = nm[1].rstrip('.csv')
            tdict = {}
            tdict["pid"] = p_id
            tdict["value"] = out
            mdict.setdefault(process_name, []).append(tdict)
        else:
            process_name = nm[0].rstrip('.csv')
            sdict = {}
            sdict["value"] = out
            mdict.setdefault(process_name, []).append(sdict)
    return mdict


def get_params(dirname):
    lst = dirname.split("-")
    version = lst[-1].strip("/")
    wld = re.findall(r'\D+', dirname)
    workload = wld[1].strip("-")
    output = [workload, version]
    return output


def es_index():
    host = input("Enter the host: ")
    port = input("Enter the port: ")
    try:
        es = Elasticsearch(hosts=[{'host': host, 'port': port}])
        in_dex = es.index(index=res[0], doc_type='cfme_workload', id=res[1], body=resultdictionary)
    except:
        print ("Error: Failed to establish a new connection")

res = get_params(indir)
resultdictionary["workload"] = {}
resultdictionary["workload"]["name"] = res[0]
resultdictionary["workload"]["version"] = res[1]
resultdictionary["workload"]["rawdata"] = process_dirs(lstdirs)

es_index()
