#!/usr/bin/env python

from abipy.lumi.deltaSCF import DeltaSCF
from abipy.core.structure import Structure
import sys,os
import yaml
from pymongo import MongoClient
import numpy as np
import argparse
import configparser
import json
import warnings
warnings.filterwarnings("ignore") # to get rid of deprecation warnings
import logging

def create_dict_from_nc_files(t2_path,t3_path,t4_path,t5_path,name,computation_tag,additional_tag,bulk_prim_stru):

    delta_SCF=DeltaSCF.from_four_points_file([t2_path,t3_path,t4_path,t5_path])

    dict_results=delta_SCF.get_dict_results()
    dict_stru_gs=delta_SCF.structuregs.as_dict()
    dict_stru_ex=delta_SCF.structureex.as_dict()
    dict_forces_gs = delta_SCF.forces_gs.tolist()
    dict_forces_ex = delta_SCF.forces_ex.tolist()
    structure_formula=delta_SCF.structuregs.formula
    if len(bulk_prim_stru) != 0:
        dict_stru_bulk=Structure.from_file(bulk_prim_stru).as_dict()
    else:
        dict_stru_bulk=None

    for i in range(len(dict_stru_gs["sites"])):
        forces_wo_units=np.array(dict_stru_gs["sites"][i]['properties']["cartesian_forces"])
        dict_stru_gs["sites"][i]['properties']={}

    for i in range(len(dict_stru_ex["sites"])):
        forces_wo_units=np.array(dict_stru_ex["sites"][i]['properties']["cartesian_forces"])
        dict_stru_ex["sites"][i]['properties']={}

    d={ "Name": name, # to change
        "Formula": structure_formula,
        "Bulk_structure":dict_stru_bulk,
        "Computation_tag": computation_tag,      # to change, allows to filter computations by tag.  ('test', 'convergence', 'final')
        "Additional_tag":   additional_tag,
        "Delta_SCF_results": dict_results,
        "Stru_gs": dict_stru_gs,
        "Stru_ex": dict_stru_ex,
        "Forces_gs":delta_SCF.forces_gs.tolist(),
        "Forces_ex":delta_SCF.forces_ex.tolist(),
        }

    return d


def create_dict_from_work(work_filepath,site_index,name,computation_tag,additional_tag,bulk_prim_stru):

    delta_SCF=DeltaSCF.from_json_file(work_filepath+"/outdata/lumi.json")

    with open(work_filepath+"/t0/abipy_meta.json") as f:
        meta_data_gs=json.load(f)
    with open(work_filepath+"/t1/abipy_meta.json") as f:
        meta_data_ex=json.load(f)

    dict_results=delta_SCF.get_dict_results()
    dict_stru_gs=delta_SCF.structuregs.as_dict()
    dict_stru_ex=delta_SCF.structureex.as_dict()
    dict_forces_gs = delta_SCF.forces_gs.tolist()
    dict_forces_ex = delta_SCF.forces_ex.tolist()
    structure_formula=delta_SCF.structuregs.formula
    if len(bulk_prim_stru) != 0:
        dict_stru_bulk=Structure.from_file(bulk_prim_stru).as_dict()
    else:
        dict_stru_bulk=None

    for i in range(len(dict_stru_gs["sites"])):
        forces_wo_units=np.array(dict_stru_gs["sites"][i]['properties']["cartesian_forces"])
        dict_stru_gs["sites"][i]['properties']={}

    for i in range(len(dict_stru_ex["sites"])):
        forces_wo_units=np.array(dict_stru_ex["sites"][i]['properties']["cartesian_forces"])
        dict_stru_ex["sites"][i]['properties']={}

    d={ "Name": name, # to change
        "Formula": structure_formula,
        "Bulk_structure":dict_stru_bulk,
        "Defect_site" : site_index, # to change mannualy now.
        "Computation_tag": computation_tag,      # to change, allows to filter computations by tag.  ('test', 'convergence', 'final')
        "Additional_tag":   additional_tag,
        "Delta_SCF_results": dict_results,
        "Stru_gs": dict_stru_gs,
        "Stru_ex": dict_stru_ex,
        "Forces_gs":delta_SCF.forces_gs.tolist(),
        "Forces_ex":delta_SCF.forces_ex.tolist(),
        "Meta_data_gs":meta_data_gs,
        "Meta_data_ex":meta_data_ex,
        }

    return d

def create_dicts_from_flow(flow_path,name=None,computation_tag=None,additional_tag=None,bulk_prim_stru=None):

    files=os.listdir(flow_path)

    work_dirs=[]
    for file in files:
        if file.startswith("w"):
            work_dirs.append(file)

    dicts=[]
    for i,work_dir in enumerate(work_dirs):
        d=create_dict_from_work(flow_path+"/"+work_dir,site_index=i,name=name,computation_tag=computation_tag,
                                additional_tag=additional_tag,bulk_prim_stru=bulk_prim_stru)
        dicts.append(d)

    return dicts


def read_yaml_configs(filename: str) -> (str, int, str, str, str):
    assert filename.split('.')[-1] == 'yaml'
    with open(filename) as file:
        configs = yaml.load(file, Loader=yaml.SafeLoader)
        
    return configs['host'], configs['port'], configs['username'], configs['password'], configs['database']


def read_args_connect_insert_entry(config,logger,section,args,from_flow=True):
    database=config[section]['database']
    collection=config[section]['collection']
    flow_path=config[section]['flow_path']
    name=config[section]['name']
    computation_tag=config[section]['computation_tag']
    additional_tag=config[section]['additional_tag']
    credentials_path=config[section]['credentials_path']
    bulk_prim_stru=config[section]['bulk_prim_stru']

    if config[section]['t2_path'] is not None:
        t2=config[section]['t2_path']
        t3=config[section]['t3_path']
        t4=config[section]['t4_path']
        t5=config[section]['t5_path']


    logger.info("__________Name : %s __________ \n",name)
    logger.info("Connecting to the database : %s \n", database)

    ##### CONNECT ######
    HOST, PORT, USERNAME, PASSWORD, DATABASE = read_yaml_configs(credentials_path)
    client = MongoClient(host=HOST, port=PORT, username=USERNAME, password=PASSWORD, authSource=DATABASE, authMechanism='SCRAM-SHA-1')

    db=client[database]
    my_collection=db[collection]

    logger.info("Extracting data from : %s \n", flow_path)
    
    if from_flow==True:
        dicts=create_dicts_from_flow(flow_path,
                     name=name,
                     computation_tag=computation_tag,
                     additional_tag=additional_tag,
                     bulk_prim_stru=bulk_prim_stru)
    else:
        dicts=[create_dict_from_nc_files(t2_path=t2,t3_path=t3,t4_path=t4,t5_path=t5,
                     name=name,
                     computation_tag=computation_tag,
                     additional_tag=additional_tag,
                     bulk_prim_stru=bulk_prim_stru)]



    for d in dicts:
        logger.info("Delta SCF main results : %s \n ", d["Delta_SCF_results"])

        if args.dry_mode == True :
            logger.info("Dry mode, nothing done.")
        else:
            my_collection.insert_many(dicts)
            logger.info("Data added to the collection : %s \n", collection,)

def main():
    
    ##### PARSER SETUP###### 
    config = configparser.ConfigParser(allow_no_value=True)
    parser=argparse.ArgumentParser(description='''Script to extract data frow a LumiWork workflow and send it to a DB. Use : python export_to_db.py -i args.ini
                                                ''')

    parser.add_argument('--init_file','-i', help=" path to the init file")
    parser.add_argument('--dry-mode','-d', action="store_true", help="Dry mode run, print infos without sending to the DB.")
         
    args=parser.parse_args()

    ##### WARNING IF LOG EXISTS #####

    if os.path.isfile('export.log'):
        print("\n export.log file already exists, continuing might create duplicate entries... \n" )
        answer = input("Continue? [yes/no]")
        if answer.lower() in ["y","yes"]:
            pass
        elif answer.lower() in ["n","no"]:
            return
        else:
            return

    ##### PRINT AND LOG SETUP######

    file_handler = logging.FileHandler(filename='export.log')
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(message)s',
        handlers=handlers,
        )

    logger = logging.getLogger()

    ##### MAIN ######

    logger.info("\n Reading init file... \n")
    config.read(str(args.init_file))
    

    for section in config.sections():
        if len(config[section]['flow_path']) != 0:
            from_flow=True
        else:
            from_flow=False
        
        read_args_connect_insert_entry(config,logger,section,args,from_flow)




if __name__ == '__main__':
    sys.exit(main())
