import csv
import json
import sys
import os
import pprint

pp = pprint.PrettyPrinter(indent=4)
indir = sys.argv[1]
#elastic = sys.argv[2]
outfile = "output.json"
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
            dictlist = handle_scenario(indir+"/"+dir+"/rawdata")
            tdict = {}
            tdict["scenerio-name"] = dir
            tdict["process-name"] = dictlist
            resultdlst.append(tdict)
    return resultdlst

def version_info():
    print "TODO"

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
            process_name = nm[1].strip('.csv')
            sdict = {}
            sdict[p_id] = out
            tdict = {}
            tdict["pid"] = sdict
            mdict.setdefault(process_name, []).append(tdict)
        else:
            process_name = nm[0].strip('.csv')
            sdict = {}
            sdict["value"] = out
            mdict.setdefault(process_name, []).append(sdict)
    return mdict


    print "TODO"

def get_params(dirname):
    lst = dirname.split("-")
    nlst = [lst[1],lst[2]]
    tname = "-".join(nlst)
    workload = ""
    version = ""
    if tname == "workload-idle":
        workload = "workload-idle"
        version = lst[3]
    elif tname == "ui-workload":
        workload = "ui-worload-single-page"
        version = lst[3]
    elif tname == "workload-refresh" and nlst[3] == "vm":
        workload = "workload-refresh-vm"
        version = lst[4]
    elif tname == "workload-refresh" and nlst[3] == "providers":
        workload = "workload-refresh-providers"
        version = lst[4]
    elif tname == "workload-cap":
        workload = "workload-cap-and-util"
        version = lst[-1]
    output = [workload, version]
    return output





res = get_params(indir)
resultdictionary["workload"] = {}
resultdictionary["workload"]["name"] = res[0]
resultdictionary["workload"]["version"] = res[1]
resultdictionary["workload"]["rawdata"] = process_dirs(lstdirs)

#pp.pprint(resultdictionary)

with open('test.json', 'w') as f:
    json.dump(resultdictionary,f)

#curl -XPOST 'localhost:9200/workload-idle/5.7.0.1' -d test.json
#with open('test.json', 'w') as f:
#    out = json.dumps(resultdictionary)
#    output = json.loads(out)
#    json.dump(out, f)




#with open(rawpath+"/"+file) as f:
#    reader = csv.DictReader(f)
#    rows = list(reader)
#with open('test.json', 'w') as f:
#    json.dump(rows, f)
