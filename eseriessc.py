"""
###############################################################################################################################
#                                                         
#                                                          Infrastructure Health Check Report                  
#   This script is part of a 6 part script to perform Health check of the infrastructure components(Storage, Compute, Network, Applications)
#   This Script is a subscript for storage script and deals with the eseries Storage. The script should be imported to the infra_main.py script and  then
#   eseriessc.eseries_data(eseries) function should be called from the Storage script.
# 
#                                              This is and NetApp Internal script                                                   
###############################################################################################################################
"""

# Import Dependencies
import json
import datetime
from urllib3 import disable_warnings
import requests
import subprocess
import os
# disable unsecure HTTP request warning as we dont have the self signed certificate implemented
disable_warnings()

#   Function to fetch credentials


def api_auth(cluster):
    """
    Function to fetch credentials
    usage:  api_auth(<cluster IP/ FQDN>)
    """
    credentials_path = "./secrets/u_eseries_cred.json"
    u_name = ""
    secret = ""
    try:
        with open(credentials_path) as f:
            credentials = json.load(f)
        try:
            u_name = credentials["ESERIES"]["username"]
        except:
            print(
                "Incorrect formatting in credentials file or incorrect cluster IP specified in site file")
        try:
            secret = credentials["ESERIES"]["password"]
        except:
            print(
                "Incorrect formatting in credentials file or incorrect cluster IP specified in site file")
        return (u_name, secret)
    except:
        print("Credentials file does not exist, please check documentation to store the credentials in secrets folder")
    return (u_name, secret)
#   Function to make api calls


def na_get_info(cluster, res_path, fields):
    """
    Function to make api calls

    Usage: na_get_info(<cluster IP/ FQDN>, <Resource Path>, <Fields Requred>)

    """
    header = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'accept': "application/json"
    }
    url = f"https://{cluster}:8443/devmgr/v2/"
    try:
        response = requests.request(
            "GET", (url + res_path + fields), headers=header, auth=api_auth(cluster), verify=False)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as errh:
        raise SystemExit(errh)

    except requests.exceptions.ConnectionError as errc:
        raise SystemExit(errc)

    except requests.exceptions.RequestException as erre:
        raise SystemExit(erre)

#   Function to get eseries Details


def get_eseries_status(cluster):
    """
    Get eseries Name, FW Version and status

    Usage: get_cluster_status(<Cluster IP/FQDN>)

    """
    res_path = "storage-systems"
    fields = ""
    response = na_get_info(cluster, res_path, fields)
    arrays_count = len(response)
    eseries_name = []
    fwversion = []
    health = []
    if arrays_count:
        for i in range(0, arrays_count):
            eseries_name += [response[i]['name']]
            fwversion += [response[i]['fwVersion']]
            health += [response[i]['status']]

    return (arrays_count, eseries_name, fwversion, health)

# Function to format Eseries Data


def eseries_data(cluster):
    """
    Function to format Eseries Data

    Usage: eseries_data(<Cluster IP/FQDN>)

    """
    eseries_dt = ""
    arrays_count, eseries_name, fwversion, health = get_eseries_status(cluster)
    for i in range(0, arrays_count):
        if health[i] != "optimal":
            health_status = f"""<TD bgcolor=#FA8074> {health[i]} </TD>"""
        else:
            health_status = f"""<TD bgcolor=#33FFBB> {health[i]} </TD>"""
        eseries_dt += f"""
            <TR>
                <TD> {eseries_name[i]} </TD>
                <TD> {fwversion[i]} </TD>
                {health_status}
            </TR>
        """
    return eseries_dt


def eseries_old_data(eseries, eseries_name):
    POWERSHELL_PATH= "powershell.exe"
    os.chdir("C:\\Program Files\\StorageManager\\client")

    #firmware_command = f".\\SMcli {eseries} -c 'show Controller [a];' | findstr 'Firmware'"
    firmware_command = f".\\SMcli.exe {eseries} -c 'show Controller [a];' | findstr 'Firmware'"
    fw_command = [POWERSHELL_PATH,firmware_command]
    out = subprocess.run(fw_command, stdout=subprocess.PIPE, stderr = subprocess.PIPE, shell=True,)
    fw_version = "NA"
    err = (out.stderr.decode("utf-8"))
    if (err == ""):
        fw_version = (out.stdout).decode("utf-8")
        fw_version = fw_version.splitlines()[0].split('          ')[1]
    else:
        print(f"Error occured while checking firmware for {eseries}")
    health_status_command = f""".\\SMcli.exe {eseries} -c 'show storageArray healthStatus;' | findstr '='"""
    
    hc_command = [POWERSHELL_PATH, health_status_command]
    out= subprocess.Popen(hc_command, stdout=subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
    hc_status = "NA"
    out.stderr
    err = (out.stderr.read().decode("utf-8"))
    if (err == ""):
        hc_status = (out.stdout.read()).decode("utf-8")
        hc_status = hc_status.splitlines()[0].split('=')[1]
    else:
        print(f"Error occured while checking Health Status for {eseries}")
    health_status = "<TD bgcolor=#FA8074> NA </TD>"
    if hc_status != " optimal.":
        health_status = f"<TD bgcolor=#FA8074> {hc_status} </TD>"
    else:
        health_status = f"<TD bgcolor=#33FFBB> {hc_status} </TD>"
    eseries_dt = f"""
            <TR>
                <TD> {eseries_name} </TD>
                <TD> {fw_version} </TD>
                {health_status}
            </TR>
    """
    os.chdir("C:\\HC_Scripts")
    return eseries_dt



if __name__ == '__main__':
    with open("./eseries_old.json") as f:
        eseries_old = json.load(f)
    eseries = "172.27.18.6"
    eseries_name = eseries_old[eseries]["Name"]
    print(eseries_old_data(eseries, eseries_name))
