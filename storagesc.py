"""
###############################################################################################################################
#                                                         
#                                                                   Infrastructure Health Check Report                  
#   This script is part of a 6 part script to perform Health check of the infrastructure components(Storage, Compute, Network, Applications)
#   This Script deals with the storage component. The script should be imported to the infra_main.py script and  then
#   storagesc.ontap_report_table(ontap_clusters, storgrid_clusters, eseries_clusters) function should be called from the main function.
# 
#                                              This is and NetApp Internal script                                                   
###############################################################################################################################
"""
# Import Dependencies
import json
import datetime
from urllib3 import disable_warnings
import requests
import storgrid
import eseriessc
import solidfirehc
# disable unsecure HTTP request warning as we dont have the self signed certificate implemented
disable_warnings()

#   Function to fetch credentials


def api_auth(cluster):
    """
    Function to fetch credentials
    usage:  api_auth(<cluster IP/ FQDN>)
    """
    credentials_path = "./secrets/u_storage_credentials.json"
    u_name = ""
    secret = ""
    try:
        with open(credentials_path) as f:
            credentials = json.load(f)
        try:
            u_name = credentials[cluster]["username"]
        except:
            print(
                "Incorrect formatting in credentials file or incorrect cluster IP specified in site file")
        try:
            secret = credentials[cluster]["password"]
        except:
            print(
                "Incorrect formatting in credentials file or incorrect cluster IP specified in site file")
        return (u_name, secret)
    except:
        print("Credentials file does not exist, please check documentation to store the credentials in secrets folder")

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
    url = f"https://{cluster}/api/"
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

#   Function to get Cluster


def get_cluster_status(cluster):
    """
    Get Cluster Name, Version and status

    Usage: get_cluster_status(<Cluster IP/FQDN>)

    """
    res_path = "cluster/"
    fields = "?fields=name,version.full"
    response = na_get_info(cluster, res_path, fields)
    cluster_name = response["name"]
    cluster_version = response["version"]["full"]
    cluster_version = (cluster_version.split(':'))[0].split(' ')[2]
    res_path = "private/cli/cluster"
    fields = "?health=false"
    deg_node_name = []
    response = na_get_info(cluster, res_path, fields)
    if response['records']:
        cluster_status = "Degraded"
        for i in range(0, response["num_records"]):
            deg_node_name += [response['records'][i]['node']]
        return (cluster_name, cluster_version, cluster_status, deg_node_name)
    else:
        cluster_status = "Ok"
        return (cluster_name, cluster_version, cluster_status, deg_node_name)

#   Function to get Service Processor Status


def get_cluster_nodes(cluster):
    """
    Function to get Service Processor Status

    Usage: get_SP_status(<Cluster IP/FQDN>)

    """
    res_path = "cluster/nodes"
    fields = "?fields=name"
    response1 = na_get_info(cluster, res_path, fields)
    node_name = []
    for i in range(0, response1["num_records"]):
        node_name += [response1['records'][i]['name']]
    return (node_name)

#   Function to get Envirnment status


def get_environment_status(cluster):
    """
    Get Envirnment Status (Subsystem Status)

    Usage: get_environment_status(<Cluster IP/FQDN>)

    """
    res_path = "private/cli/system/health/subsystem"
    fields = "?health=!ok"
    response = na_get_info(cluster, res_path, fields)
    subsystem_name = []
    if response['records']:
        environment_status = "Degraded"
        for i in range(0, response["num_records"]):
            subsystem_name += [response["records"][i]["subsystem"]]
        return (environment_status, subsystem_name)
    else:
        environment_status = "Ok"
        return (environment_status, subsystem_name)

#   Function to get Cluster Chassis Status


def get_chassis_status(cluster):
    """
    Get Cluster Chassis Status (FRU Status)

    Usage: get_chassis_status(<Cluster IP/FQDN>)

    """
    res_path = "private/cli/system/chassis/fru"
    fields = f"?fields=fru-name&status=!ok"
    response = na_get_info(cluster, res_path, fields)
    fru_name = []
    if response['records']:
        chassis_status = "Degraded"
        for i in range(0, response["num_records"]):
            fru_name += [response["records"][i]["subsystem"]]
        return(chassis_status, fru_name)
    else:
        chassis_status = "Ok"
        return(chassis_status, fru_name)

#   Function to get Broken disk count


def get_broken_disk(cluster):
    """

    Function to get Broken disk count

    Usage: get_broken_disk(<Cluster IP/FQDN>)

    """
    res_path = "storage/disks"
    fields = "?container_type=broken"
    response = na_get_info(cluster, res_path, fields)
    failed_disk_count = int(response["num_records"])
    return (failed_disk_count)

#   Function to get Aggregate Status


def get_aggregate_status(cluster, nodes):
    """

    Function to get Aggregate Status

    Usage: get_aggregate_status(<Cluster IP/FQDN>, <Cluster Nodes List>)
    """
    aggregate_high = {}
    aggregate_offline = {}
    for node in nodes:

        res_path = "private/cli/aggr"
        fields = f"?state=offline&node={node}"
        response1 = na_get_info(cluster, res_path, fields)
        aggr_offline_count = int(response1["num_records"])
        aggr_offline_name = []
        if (aggr_offline_count != 0):
            for i in range(0, aggr_offline_count):
                aggr_offline_name += [response1["records"][i]["aggregate"]]
            aggregate_offline[node] = {
                "aggr_offline_count": aggr_offline_count, "aggr_offline_name": aggr_offline_name}

        fields = f"?node={node}&percent_used=>85&root=false"
        response2 = na_get_info(cluster, res_path, fields)
        aggr_high_count = int(response2["num_records"])
        aggr_name = []
        if (aggr_high_count != 0):
            for i in range(0, aggr_high_count):
                aggr_name += [response2["records"][i]["aggregate"]]
            aggregate_high[node] = {
                "aggr_high_count": aggr_high_count, "aggr_name": aggr_name}
    return (aggregate_offline, aggregate_high)

#   Function to get Spare disk count


def get_spare_disk(cluster, nodes):
    """

    Function to get Spare disk count

    Usage: get_spare_disk(<Cluster IP/FQDN>, <Cluster Nodes List>)
    """
    spare_disk_dict = {}
    for node in nodes:

        res_path = "private/cli/storage/aggregate/spare"
        fields = f"?fields=disk&original_owner={node}"
        response1 = na_get_info(cluster, res_path, fields)
        spare_disk_count = int(response1["num_records"])
        spare_disk_dict[node] = {
            "spare_disk_count": spare_disk_count}
    return (spare_disk_dict)

#   Function to get offline Highly Utilized volumes


def get_volume_status(cluster):
    """

    Function to get offline and high utilization volumes

    """
    res_path = "private/cli/volume"
    fields = f"?state=offline"
    response1 = na_get_info(cluster, res_path, fields)
    offline_vol_count = int(response1["num_records"])
    offline_vol = []
    if offline_vol_count != 0:
        for i in range(0, offline_vol_count):
            offline_vol += [response1["records"][i]["volume"]]
    fields = f"?fields=total,used,max-autosize,autosize-mode&state=online&vsroot=false"
    response2 = na_get_info(cluster, res_path, fields)
    vol_count = response2["num_records"]
    high_util_vol_name = []
    high_util_vol_count = 0
    for i in range(0, vol_count):
        vol_auto_mode = response2["records"][i]["autosize_mode"]
        if vol_auto_mode == "off":
            vol_total = int(response2["records"][i]["total"])
            vol_used = int(response2["records"][i]["used"])
            vol_percent = int((vol_used/vol_total)*100)

            if vol_percent >= 90:
                high_util_vol_name += [response2["records"][i]["volume"]]
                high_util_vol_count += 1

        else:
            vol_max_autosize = int(response2["records"][i]["max_autosize"])
            vol_used = int(response2["records"][i]["used"])
            vol_percent = int((vol_used/vol_max_autosize)*100)
            if vol_percent >= 90:
                high_util_vol_name += [response2["records"][i]["volume"]]
                high_util_vol_count += 1
    return (offline_vol_count, offline_vol, high_util_vol_count, high_util_vol_name)

#   Function to get Port in down state


def get_port_status(cluster, nodes):
    """

    Function toget Port in down state

    Usage: get_port_status(<Cluster IP/FQDN>, <Cluster Nodes List>)
    """
    port_down_dict = {}
    exception_port_path = './exception_port.txt'
    with open(exception_port_path) as f:
        exception_port = f.read().splitlines()
    for node in nodes:
        res_path = "private/cli/network/port"
        fields = f"?up_admin=true&link=down&node={node}"
        response1 = na_get_info(cluster, res_path, fields)
        #port_down_count = int(response1["num_records"])
        port_down_count = 0
        port_down_name = []
        for i in range(0, int(response1["num_records"])):
            pt_name = response1["records"][i]["port"]
            ex_string = f"{pt_name} is down in {node}"
            if(ex_string not in exception_port):
                port_down_name += [response1["records"][i]["port"]]
        port_down_count = len(port_down_name)
        if port_down_count != 0 :
            port_down_dict[node] = {
                "port_down_count": port_down_count, "port_down_name": port_down_name}
    return(port_down_dict)

#   Function to get LIF in down state


def get_lif_status(cluster, nodes):
    """

    Function to get LIF in down state

    Usage: get_lif_status(<Cluster IP/FQDN>, <Cluster Nodes List>)

    """
    exception_lif_path = './exception_lif.txt'
    with open(exception_lif_path) as f:
        exception_lifs = f.read().splitlines()
    lif_down_dict = {}
    for node in nodes:
        res_path = "private/cli/network/interface"
        fields = f"?status-oper=down&status-admin=up&home-node={node}"
        response1 = na_get_info(cluster, res_path, fields)
        #lif_down_count = int(response1["num_records"])
        lif_down_count = 0
        lif_down_name = []
        for i in range(0, response1["num_records"]):
            if(response1["records"][i]["lif"] not in exception_lifs):
                lif_down_name += [response1["records"][i]["lif"]]
        lif_down_count = len(lif_down_name)
        if lif_down_count != 0:
            lif_down_dict[node] = {"lif_down_count": lif_down_count, "lif_down_name": lif_down_name}
    return(lif_down_dict)

#   Function to get Snapmirror status and Lag time


def get_snapmirror_status(cluster):
    """

    get Snapmirror status and Lag time

    Usage: get_snapmirror_status(<Cluster IP/FQDN>)

    """
    unhealthy_snapmirror_source_path = []
    high_lag_snapmirror_source_path = []
    res_path = "snapmirror/relationships"
    fields = f"?healthy=false&fields=source.path"
    response1 = na_get_info(cluster, res_path, fields)
    unhealthy_snapmirror_count = int(response1["num_records"])
    if unhealthy_snapmirror_count != 0:
        for i in range(0, unhealthy_snapmirror_count):
            unhealthy_snapmirror_source_path += [
                response1["records"][i]["source"]["path"]]
    res_path = "private/cli/snapmirror"
    fields = f"?healthy=true&lag_time=>24:00:00"
    response2 = na_get_info(cluster, res_path, fields)
    high_lag_snapmirror_count = int(response2["num_records"])
    if high_lag_snapmirror_count != 0:
        for i in range(0, high_lag_snapmirror_count):
            high_lag_snapmirror_source_path += [
                response2["records"][i]["source_path"]]
    return (unhealthy_snapmirror_count, unhealthy_snapmirror_source_path, high_lag_snapmirror_count, high_lag_snapmirror_source_path)

#   Function to get IFGRP status


def get_ifgrp_status(cluster):
    """

    Function to get IFGRP status

    Usage: get_ifgrp_status(<Cluster IP/FQDN>)

    """
    res_path = "private/cli/ifgrp"
    fields = f"?activeports=!full"
    response = na_get_info(cluster, res_path, fields)
    ifgrp_node = []
    if response['records']:
        ifgrp_status = "Degraded"
        for i in range(0, response["num_records"]):
            ifgrp_node += [response['records'][i]['node']]
        return (ifgrp_status, ifgrp_node)
    else:
        ifgrp_status = "Ok"
        return (ifgrp_status, ifgrp_node)

#   Function to get Protocol Services status


def get_services_status(cluster):
    """

    Function to get Protocol Services status

    Usage: get_lun_status(<Cluster IP/FQDN>)

    """
    res_path = "svm/svms"
    fields = ""
    response1 = na_get_info(cluster, res_path, fields)
    cifs_vserver = []
    nfs_vserver = []
    iscsi_vserver = []
    if response1['records']:
        res_path = "private/cli/vserver/cifs/check"
        fields = ""
        response = na_get_info(cluster, res_path, fields)
        if response['records']:
            fields = f"?cifs-status=!running"
            response = na_get_info(cluster, res_path, fields)

            if response['records']:
                cifs_status = "Degraded"
                for i in range(0, response["num_records"]):
                    cifs_vserver += [response['records'][i]['vserver']]
            else:
                cifs_status = "Ok"
        else:
            cifs_status = "NA"
        res_path = "private/cli/vserver/nfs"
        fields = ""
        response = na_get_info(cluster, res_path, fields)
        if response['records']:
            fields = f"?v3=!enabled"
            response = na_get_info(cluster, res_path, fields)
            if response['records']:
                nfs_status = "Degraded"
                for i in range(0, response["num_records"]):
                    nfs_vserver += [response['records'][i]['vserver']]
            else:
                nfs_status = "Ok"
        else:
            nfs_status = "NA"
        res_path = "private/cli/vserver/iscsi"
        fields = ""
        response = na_get_info(cluster, res_path, fields)
        if response['records']:
            fields = f"?status-admin=!up"
            response = na_get_info(cluster, res_path, fields)
            if response['records']:
                iscsi_status = "Degraded"
                for i in range(0, response["num_records"]):
                    iscsi_vserver += [response['records'][i]['vserver']]
            else:
                iscsi_status = "Ok"
        else:
            iscsi_status = "NA"
        return (cifs_status, cifs_vserver, nfs_status, nfs_vserver, iscsi_status, iscsi_vserver)
    else:
        cifs_status = "NA"
        nfs_status = "NA"
        iscsi_status = "NA"
        return (cifs_status, cifs_vserver, nfs_status, nfs_vserver, iscsi_status, iscsi_vserver)


#   Function to get offline Highly Utilized LUNs
def get_lun_status(cluster, nodes):
    """

    get offline and high Utilized LUNs

    Usage: get_lun_status(<Cluster IP/FQDN>, <Cluster Nodes List>)

    """
    lun_offline_dict = {}
    lun_high_dict = {}
    for node in nodes:
        res_path = "private/cli/lun"
        fields = f"?state=offline&node={node}"
        response1 = na_get_info(cluster, res_path, fields)
        offline_lun_count = int(response1["num_records"])
        offline_lun = []
        if offline_lun_count != 0:
            for i in range(0, offline_lun_count):
                offline_lun += [response1["records"][i]["lun"]]
            lun_offline_dict[node] = {
                "offline_lun_count": offline_lun_count, "offline_lun": offline_lun}
        fields = f"?fields=size,size-used&state=online&node={node}"
        response2 = na_get_info(cluster, res_path, fields)
        lun_count = int(response2["num_records"])
        high_util_lun_name = []
        lun_volume = []
        high_util_lun_count = 0
        if lun_count != 0:
            for i in range(0, lun_count):
                lun_volume += [response2["records"][i]["volume"]]
                lun_size = int(response2["records"][i]["size"])
                lun_space_used = int(response2["records"][i]["size_used"])
                lun_percent = int((lun_space_used / lun_size)*100)
                if (lun_percent >= 95):
                    high_util_lun_name += [response2["records"][i]["lun"]]
            high_util_lun_count = len(high_util_lun_name)
            if (high_util_lun_count != 0):
                lun_high_dict[node] = {
                    "high_util_lun_count": high_util_lun_count, "high_util_lun_name": high_util_lun_name}
    return (lun_offline_dict, lun_high_dict)

#   Function to get ACP status


def get_acp_status(cluster):
    """

    Function to get ACP status

    Usage: get_acp_status(<Cluster IP/FQDN>)

    """
    res_path = "private/cli/acp"
    fields = f"?connection-status=!active"
    response = na_get_info(cluster, res_path, fields)
    acp_deg_node = []
    if response['records']:
        acp_status = "Degraded"
        for i in range(0, response["num_records"]):
            acp_deg_node += [response['records'][i]['node']]
        return (acp_status, acp_deg_node)
    else:
        acp_status = "Ok"
        return (acp_status, acp_deg_node)

#   Function to get Service Processor Status


def get_SP_status(cluster):
    """
    Function to get Service Processor Status

    Usage: get_SP_status(<Cluster IP/FQDN>)

    """
    res_path = "cluster/nodes"
    fields = "?service_processor.state=online"
    response1 = na_get_info(cluster, res_path, fields)
    if response1['records']:
        fields = "?service_processor.state=!online"
        response = na_get_info(cluster, res_path, fields)
        SP_down_node = []
        if response['records']:
            SP_status = "Degraded"
            for i in range(0, response["num_records"]):
                SP_down_node = response['records'][i]['name']
            return (SP_status, SP_down_node)
        else:
            SP_status = "Ok"
            return (SP_status, SP_down_node)
    else:
        SP_status = "NA"
        SP_down_node = ["NA"]
        return (SP_status, SP_down_node)

# Function to check Licenses


def get_license_status(cluster):
    """
    Function to check Licenses

    Usage: get_license_status(<Cluster IP/FQDN>)
    """
    res_path = "private/cli/system/license/entitlement-risk"
    fields = "?risk=!low,!unlicensed"
    response = na_get_info(cluster, res_path, fields)
    licenses = []
    if response['records']:
        entilement_risk = "At Risk"
        for i in range(0, response["num_records"]):
            licenses += [response['records'][i]['package']]
        return (entilement_risk, licenses)
    else:
        entilement_risk = "No Risk"
        return (entilement_risk, licenses)

# Function to check Config Backup


def get_config_bkp_status(cluster):
    """
    Function to check Config Backup
 
    Usage: get_config_bkp_status(<Cluster IP/FQDN>)
    """
    dt = datetime.date.today() #.strftime("%Y-%m-%d")
    td_today = dt.strftime("%Y-%m-%d")
    dt_ys = dt - datetime.timedelta(days=1)
    dt_ys = dt_ys.strftime("%Y-%m-%d")
    res_path = "private/cli/system/configuration/backup"
    fields = f"?time=>{dt_ys}T00:00:00"
    response = na_get_info(cluster, res_path, fields)
    last_daily_bkp = []
    for i in range(0, response["num_records"]):
        if "daily" in response['records'][i]['backup']:
            last_daily_bkp += [response['records'][i]['backup']]
    try:
        if last_daily_bkp[0]:
            last_daily_bkp = list(set(last_daily_bkp))
            #print(last_daily_bkp)
            last_daily_bkp.sort(reverse = True)
            last_daily_bkp = list(last_daily_bkp)[0]
            if td_today in last_daily_bkp:
                daily_backup_status = "Ok"
                return (daily_backup_status, last_daily_bkp)
            else:
                daily_backup_status = f"No Daily Backup for {dt}"
                return (daily_backup_status, last_daily_bkp)
        else:
            daily_backup_status = f"No Daily Backup for {dt}"
            return (daily_backup_status, last_daily_bkp)
    except:
        daily_backup_status = "error"
        return (daily_backup_status, last_daily_bkp)

#   Function to Generate Cluster Report table


def ontap_report_table(ontap_clusters, storgrid_clusters, eseries_clusters, solidfire_clusters):
    """

    Generate Ontap Report table

    Usage: ontap_report_table(clusters)s


    """
    ontap_data_1_dt = ""
    ontap_data_2_dt = ""
    storagegrid_dt = ""
    eseries_dt = ""
    solidfire_dt = ""
    with open("./eseries_old.json") as f:
        eseries_old = json.load(f)

    if storgrid_clusters:
        for grid in storgrid_clusters:
            try:
                storagegrid_dt += storgrid.storagegrid_data(grid)
            except:
                continue
    if eseries_clusters:
        for eseries in eseries_clusters:
            if eseries in eseries_old:
                try:
                    eseries_name = eseries_old[eseries]["Name"]
                    eseries_dt += eseriessc.eseries_old_data(
                        eseries, eseries_name)
                except:
                   print(f"Error with {eseries}")
                   continue
            else:
                continue
    if solidfire_clusters:
        solidfire_dt = solidfirehc.main(solidfire_clusters)

    if ontap_clusters:
        for cluster in ontap_clusters:
            try:
                nodes = get_cluster_nodes(cluster)
                ontap_data_1_dt += ontap_data_1(cluster, nodes)
                ontap_data_2_dt += ontap_data_2(cluster, nodes)
            except:
                print("Error on Ontap section")
                continue
    cluster_report_body = f"""
    <div>
    <h3 style='color : #464A46; font-size : 21px' align="" left ""> Ontap  - Part1 </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> Cluster Name </B></TH>
                <TH><B> ONTAP version </B></TH>
                <TH><B> Hardware Status </B></TH>
                <TH><B> Cluster Status </B></TH>
                <TH><B> Aggr status </B></TH>
                <TH><B> Spare Disk Status </B></TH>
                <TH><B> Vol Status </B></TH>
                <TH><B> Port Status </B></TH>
                <TH><B> LIF status </B></TH>
                <TH><B> Snapmirror Status </B></TH>
            </TR>
            {ontap_data_1_dt}
        </Table>
    <h3 style='color : #464A46; font-size : 21px' align="" left ""> Ontap  - Part2 </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> Cluster Name </B></TH>
                <TH><B> Ifgrp Status </B></TH>
                <TH><B> CIFS/NFS/iSCSI </B></TH>
                <TH><B> LUN Status </B></TH>
                <TH><B> ACP Status </B></TH>
                <TH><B> SP Status </B></TH>
                <TH><B> Licenses / Certificates </B></TH>
                <TH><B> Cluster Config Bkp </B></TH>
            </TR>
            {ontap_data_2_dt}
        </Table>
    
    {solidfire_dt}
    </div>
    """
    return cluster_report_body

#   Function to assemble Ontap table 1 Data


def ontap_data_1(cluster, nodes):
    """
    Function to assemble Ontap table 1 Data

    Usage: ontap_data_1(<cluster IP/FQDN>)

    """
    cluster_name, cluster_version, cluster_status, deg_node_name = get_cluster_status(
        cluster)
    environment_status, subsystem_name = get_environment_status(cluster)
    chassis_status, fru_name = get_chassis_status(cluster)
    failed_disk_count = get_broken_disk(cluster)
    aggregate_offline, aggregate_high = get_aggregate_status(cluster, nodes)
    spare_disk_dict = get_spare_disk(cluster, nodes)
    offline_vol_count, offline_vol, high_util_vol_count, high_util_vol_name = get_volume_status(
        cluster)
    port_down_dict = get_port_status(cluster, nodes)
    lif_down_dict = get_lif_status(cluster, nodes)
    unhealthy_snapmirror_count, unhealthy_snapmirror_source_path, high_lag_snapmirror_count, high_lag_snapmirror_source_path = get_snapmirror_status(
        cluster)

    #   Data Formatting for Cluster Status
    if cluster_status == "Ok":
        cluster_status = f"<TD bgcolor=#33FFBB> {cluster_status} </TD>"
    else:
        dg_node = ""
        for node in deg_node_name:
            dg_node += f"<TR><TD bgcolor=#FA8074> {node} </TD></TR>"
        cluster_status = f"""
        <TD bgcolor=#FA8074>
        <a class="trigger_popup_{cluster_name}_status">{cluster_status}</a>
        <div class="hover_bkgr_{cluster_name}_status">
        <span class="helper"></span>
        <div>
            <div class="popupCloseButton">&times;</div>
            <table>
                <TR>
                    <TH><B> Degraded Nodes </B></TH>
                </TR>
                {dg_node}
            </table>
        </div>
    </div>
    </TD>
        """

    #   Data Formatting for Hardware Status
    hw_status = "<TD bgcolor=#EFF613s> NA </TD>"
    if environment_status == "Ok":
        environment_status = f"<TD bgcolor=#33FFBB> Subsystem: {environment_status} </TD>"
    else:
        dg_subsystem = ""
        for sub_sys in subsystem_name:
            dg_subsystem += f"<TR><TD bgcolor=#FA8074> {sub_sys} </TD></TR>"
        environment_status = f"""
        
        <TD bgcolor=#FA8074>
        <a class="trigger_popup_{cluster_name}_subsys">{environment_status}</a>
        <div class="hover_bkgr_{cluster_name}_subsys">
        <span class="helper"></span>
        <div>
            <div class="popupCloseButton">&times;</div>
            <table>
                <TR>
                    <TH><B> Degraded SubSystem </B></TH>
                </TR>
                {dg_subsystem}
            </table>
        </div>
    </div>
    </TD>        
    
        """
    if chassis_status == "Ok":
        chassis_status = f"<TD bgcolor=#33FFBB> Chassis: {chassis_status} </TD>"
    else:
        dg_fru = ""
        for fru in fru_name:
            dg_fru += f"<TR><TD bgcolor=#FA8074> {fru} </TD></TR>"
        chassis_status = f"""
        <TD bgcolor=#FA8074>
        <a class="trigger_popup_{cluster_name}_fru">{chassis_status}</a>
        <div class="hover_bkgr_{cluster_name}_fru">
        <span class="helper"></span>
        <div>
            <div class="popupCloseButton">&times;</div>
            <table>
                <TR>
                    <TH><B> Degraded FRU </B></TH>
                </TR>
                {dg_fru}
            </table>
        </div>
    </div>
    </TD>  
        """
    failed_disk_status = ""
    if failed_disk_count == 0:
        failed_disk_status = "<TD bgcolor=#33FFBB> No Failed disk </TD>"
    else:
        failed_disk_status = f"<TD bgcolor=#FA8074> Failed Disk Count: {failed_disk_count} </TD>"
    hw_status = f"""
    <TD>
    <table>
        <TR>
            {environment_status}
        </TR>
        <TR>
            {chassis_status}
        </TR>
        <TR>
            {failed_disk_status}
        </TR>
    </table>
    </TD>
    """
    offline_vol_list = ""
    high_util_vol_list = ""
    if (offline_vol_count != 0 and high_util_vol_count != 0):
        for offline_vol_name in offline_vol:
            offline_vol_list += f"<TR><TD bgcolor=#FA8074> {offline_vol_name} </TD></TR>"
        for high_util_vol in high_util_vol_name:
            high_util_vol_list += f"<TR><TD bgcolor=#FA8074> {high_util_vol} </TD></TR>"
        vol_status = f"""
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_vol">{offline_vol_count} Volume Offline<br>{high_util_vol_count} Volume > 90% </a>
            <div class="hover_bkgr_{cluster_name}_vol">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> Offline Volumes </B></TH>
                        {offline_vol_list}
                        <TH><B> Volumes > 90% </B></TH>
                        {high_util_vol_list}
                    </TR>
                </table>
            </div>
        </div>
        </TD>        
        """
    elif (offline_vol_count != 0 and high_util_vol_count == 0):
        for offline_vol_name in offline_vol:
            offline_vol_list += f"<TR><TD bgcolor=#FA8074> {offline_vol_name} </TD></TR>"
        vol_status = f"""
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_vol">{offline_vol_count} Volume Offline </a>
            <div class="hover_bkgr_{cluster_name}_vol">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> Offline Volumes </B></TH>
                    </TR>
                    {offline_vol_list}
                </table>
            </div>
        </div>
        </TD>        
        """
    elif (offline_vol_count == 0 and high_util_vol_count != 0):
        for high_util_vol in high_util_vol_name:
            high_util_vol_list += f"<TR><TD bgcolor=#FA8074> {high_util_vol} </TD></TR>"
        vol_status = f"""
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_vol">{high_util_vol_count} Volume > 90% </a>
            <div class="hover_bkgr_{cluster_name}_vol">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> Volumes > 90% </B></TH>
                    </TR>
                    {high_util_vol_list}
                </table>
            </div>
        </div>
        </TD>        
        """
    else:
        vol_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    # Snapmirror status
    snapmirror_status = ""
    if(unhealthy_snapmirror_count != 0):
        unhealthy_snapmirror_list = ""
        for unhealthy_snapmirror in unhealthy_snapmirror_source_path:
            unhealthy_snapmirror_list += f"<TR><TD bgcolor=#FA8074> {unhealthy_snapmirror} </TD></TR>"
        snapmirror_error_status = f"""
        <TD bgcolor=#FA8074>
        <a class="trigger_popup_{cluster_name}_snaperror">{unhealthy_snapmirror_count} Unhealthy Snapmirror</a>
        <div class="hover_bkgr_{cluster_name}_snaperror">
        <span class="helper"></span>
        <div>
            <div class="popupCloseButton">&times;</div>
            <table>
                <TR>
                    <TH><B> Degraded Snapmirror </B></TH>
                </TR>
                {unhealthy_snapmirror_list}
            </table>
        </div>
    </div>
    </TD>  
        """
    else:
        snapmirror_error_status = "<TD bgcolor=#33FFBB> Snapmirror Health: Ok </TD>"
    if(high_lag_snapmirror_count != 0):
        snapmirror_lag_list = ""
        for high_lag_snapmirror in high_lag_snapmirror_source_path:
            snapmirror_lag_list += f"<TR><TD bgcolor=#FA8074> {high_lag_snapmirror} </TD></TR>"
        snapmirror_lag_status = f"""
        <TD bgcolor=#FA8074>
        <a class="trigger_popup_{cluster_name}_snaplag">{high_lag_snapmirror_count} Snapmirror Lag > 24Hrs </a>
        <div class="hover_bkgr_{cluster_name}_snaplag">
        <span class="helper"></span>
        <div>
            <div class="popupCloseButton">&times;</div>
            <table>
                <TR>
                    <TH><B> Lag Time > 24Hrs </B></TH>
                </TR>
                {snapmirror_lag_list}
            </table>
        </div>
    </div>
    </TD>  
        """
    else:
        snapmirror_lag_status = "<TD bgcolor=#33FFBB> Snapmirror Lag < 24Hrs</TD>"

    snapmirror_status = f"""
    <TD>
    <table>
        <TR>
            {snapmirror_error_status}
        </TR>
        <TR>
            {snapmirror_lag_status}
        </TR>
    </table>
    </TD>
    """
#   Node loop required
    aggr_statuses = ""
    spare_disks_stat = ""
    port_statuses = ""
    lif_statuses = ""
    for node in nodes:
        #   Data Formatting for Aggrigate status
        if (node in aggregate_offline and node in aggregate_high):
            aggr_offline_count = aggregate_offline[node]["aggr_offline_count"]
            aggr_offline_name = aggregate_offline[node]["aggr_offline_name"]
            aggr_high_count = aggregate_high[node]["aggr_high_count"]
            aggr_name = aggregate_high[node]["aggr_name"]
            aggr_off_list = ""
            aggr_high_list = ""
            for aggr_off in aggr_offline_name:
                aggr_off_list += f"<TR><TD bgcolor=#FA8074> {aggr_off} </TD></TR>"
            for aggr_hi in aggr_name:
                aggr_high_list += f"<TR><TD bgcolor=#FA8074> {aggr_hi} </TD></TR>"
            aggr_statuses += f"""
            <TR>
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_{node}_aggr">{node}: {aggr_offline_count} Aggregate Offline<br>{aggr_high_count} Aggregate > 85% </a>
            <div class="hover_bkgr_{cluster_name}_{node}_aggr">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> Offline Aggregate </B></TH>
                        {aggr_off_list}
                        <TH><B> Aggregate > 85% </B></TH>
                        {aggr_high_list}
                    </TR>


                </table>
            </div>
        </div>
        </TD>
        </TR>
            """
        elif(node in aggregate_offline and node not in aggregate_high):
            aggr_offline_count = aggregate_offline[node]["aggr_offline_count"]
            aggr_offline_name = aggregate_offline[node]["aggr_offline_name"]
            aggr_off_list = ""
            for aggr_off in aggr_offline_name:
                aggr_off_list += f"<TR><TD bgcolor=#FA8074> {aggr_off} </TD></TR>"
            aggr_statuses += f"""
            <TR>
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_{node}_aggr">{node}:{aggr_offline_count} Aggregate Offline</a>
            <div class="hover_bkgr_{cluster_name}_{node}_aggr">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> Offline Aggregate </B></TH>
                    </TR>
                    {aggr_off_list}
                </table>
                </div>
            </div>
            </TD>
            </TR>
            """

        elif(node not in aggregate_offline and node in aggregate_high):
            aggr_high_count = aggregate_high[node]["aggr_high_count"]
            aggr_name = aggregate_high[node]["aggr_name"]
            aggr_high_list = ""
            for aggr_hi in aggr_name:
                aggr_high_list += f"<TR><TD bgcolor=#FA8074> {aggr_hi} </TD></TR>"
            aggr_statuses += f"""
            <TR>
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_{node}_aggr">{node}:{aggr_high_count} Aggregate > 85% </a>
            <div class="hover_bkgr_{cluster_name}_{node}_aggr">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> Aggregate > 85% </B></TH>
                    </TR>
                    {aggr_high_list}
                </table>
            </div>
        </div>
        </TD>
        </TR>
            """
        else:
            aggr_statuses += f"<TR><TD bgcolor=#33FFBB>{node}: Ok </TD></TR>"
        #   Spare disk
        spare_disks = spare_disk_dict[node]["spare_disk_count"]
        spare_disks_stat += f"<TR><TD> {node}: {spare_disks} </TD>"

        #   Port
        if (bool(port_down_dict)):
            if (node in port_down_dict):
                port_down_count = port_down_dict[node]["port_down_count"]
                port_down_name = port_down_dict[node]["port_down_name"]
                prt_down_list = ""
                for ports in port_down_name:
                    prt_down_list += f"<TR><TD bgcolor=#FA8074> {ports} </TD></TR>"
                port_statuses += f"""
                <TR>
                <TD bgcolor=#FA8074>
                <a class="trigger_popup_{cluster_name}_{node}_port">{node}:{port_down_count} Ports Down </a>
                <div class="hover_bkgr_{cluster_name}_{node}_port">
                <span class="helper"></span>
                <div>
                    <div class="popupCloseButton">&times;</div>
                    <table>
                        <TR>
                            <TH><B> Ports in down state </B></TH>
                        </TR>
                        {prt_down_list}
                    </table>
                </div>
            </div>
            </TD>
            </TR>
            """
            else:
                port_statuses += f"<TR><TD bgcolor=#33FFBB>{node}: Ok </TD></TR>"
        else:
            port_statuses += f"<TR><TD bgcolor=#33FFBB>{node}: Ok </TD></TR>"
        #   Lifs Status
        if (bool(lif_down_dict)):
            if (node in lif_down_dict):
                lif_down_count = lif_down_dict[node]["lif_down_count"]
                lif_down_name = lif_down_dict[node]["lif_down_name"]
                lf_down_list = ""
                for lif in lif_down_name:
                    lf_down_list += f"<TR><TD bgcolor=#FA8074> {lif} </TD></TR>"
                lif_statuses += f"""
                <TR>
                <TD bgcolor=#FA8074>
                <a class="trigger_popup_{cluster_name}_{node}_lif">{node}:{lif_down_count} LIFs Down </a>
                <div class="hover_bkgr_{cluster_name}_{node}_lif">
                <span class="helper"></span>
                <div>
                    <div class="popupCloseButton">&times;</div>
                    <table>
                        <TR>
                            <TH><B> LIFs in down state </B></TH>
                        </TR>
                        {lf_down_list}
                    </table>
                </div>
            </div>
            </TD>
            </TR>
            """
            else:
                lif_statuses += f"<TR><TD bgcolor=#33FFBB>{node}: Ok </TD></TR>"
        else:
            lif_statuses += f"<TR><TD bgcolor=#33FFBB>{node}: Ok </TD></TR>"

    aggr_status = f"""
    <TD>
    <table>
        {aggr_statuses}
    </table>
    </TD>
    """
    spare_disks_status = f"""
    <TD>
    <table>
        {spare_disks_stat}
    </table>
    </TD>
    """
    port_status = f"""
    <TD>
    <table>
        {port_statuses}
    </table>
    </TD>
    """
    lif_status = f"""
    <TD>
    <table>
        {lif_statuses}
    </table>
    </TD>
    """
    # Data formatting in HTML
    cluster_report_data = f"""
        <TR>
            <TD>{cluster_name}</TD>
            <TD>{cluster_version}</TD>
            {hw_status}
            {cluster_status}
            {aggr_status}
            {spare_disks_status}
            {vol_status}
            {port_status}
            {lif_status}
            {snapmirror_status}
        </TR>
        """
    return cluster_report_data


def ontap_data_2(cluster, nodes):
    """
    Function to assemble Ontap table 1 Data

    Usage: ontap_data_2(<cluster IP/FQDN>)

    """
    cluster_name, cluster_version, cluster_status, deg_node_name = get_cluster_status(
        cluster)
    ifgrp_status, ifgrp_node = get_ifgrp_status(cluster)
    cifs_status, cifs_vserver, nfs_status, nfs_vserver, iscsi_status, iscsi_vserver = get_services_status(
        cluster)
    lun_offline_dict, lun_high_dict = get_lun_status(cluster, nodes)
    acp_status, acp_deg_node = get_acp_status(cluster)
    SP_status, SP_down_node = get_SP_status(cluster)
    efficiency_drop = "<TD>TBD</TD>"
    entilement_risk, licenses = get_license_status(cluster)
    daily_backup_status, last_daily_bkp = get_config_bkp_status(cluster)
    
#   Cluster config backup data formatting
    if daily_backup_status =="Ok":
        last_daily_bkp =f"<TD bgcolor=#33FFBB> Backup on: {last_daily_bkp}​​​​​​ </TD>"
    else:
        last_daily_bkp =f"<TD bgcolor=#FA8074> {daily_backup_status}​​​​​​<br>{last_daily_bkp}​​​​​​ </TD>"

    #   IFGRP data formatting
    if ifgrp_status == "Ok":
        ifgrp_status = f"<TD bgcolor=#33FFBB> {ifgrp_status} </TD>"
    else:
        dg_node_ifgrp = ""
        for node in ifgrp_node:
            dg_node_ifgrp += f"<TR><TD bgcolor=#FA8074> {node} </TD></TR>"
        ifgrp_status = f"""
        <TD bgcolor=#FA8074>
        <a class="trigger_popup_{cluster_name}_ifgrp">{ifgrp_status}</a>
        <div class="hover_bkgr_{cluster_name}_ifgrp">
        <span class="helper"></span>
        <div>
            <div class="popupCloseButton">&times;</div>
            <table>
                <TR>
                    <TH><B> Degraded IFGRP Nodes </B></TH>
                </TR>
                {dg_node_ifgrp}
            </table>
        </div>
    </div>
    </TD>
        """

    #   ACP data formatting
    if acp_status == "Ok":
        acp_status = f"<TD bgcolor=#33FFBB> {acp_status} </TD>"
    else:
        dg_node_acp = ""
        for node in acp_deg_node:
            dg_node_acp += f"<TR><TD bgcolor=#FA8074> {node} </TD></TR>"
        acp_status = f"""
        <TD bgcolor=#FA8074>
        <a class="trigger_popup_{cluster_name}_acp">{acp_status}</a>
        <div class="hover_bkgr_{cluster_name}_acp">
        <span class="helper"></span>
        <div>
            <div class="popupCloseButton">&times;</div>
            <table>
                <TR>
                    <TH><B> Degraded ACP Nodes </B></TH>
                </TR>
                {dg_node_acp}
            </table>
        </div>
    </div>
    </TD>
        """
    #   Service processor data formatting
    if SP_status == "NA":
        SP_status = f"<TD> {SP_status} </TD>"
    elif SP_status == "Ok":
        SP_status = f"<TD bgcolor=#33FFBB> {SP_status} </TD>"
    else:
        dg_node_sp = ""
        for node in SP_down_node:
            dg_node_sp += f"<TR><TD bgcolor=#FA8074> {node} </TD></TR>"
        SP_status = f"""
        <TD bgcolor=#FA8074>
        <a class="trigger_popup_{cluster_name}_sp">{SP_status}</a>
        <div class="hover_bkgr_{cluster_name}_sp">
        <span class="helper"></span>
        <div>
            <div class="popupCloseButton">&times;</div>
            <table>
                <TR>
                    <TH><B> Degraded SP Nodes </B></TH>
                </TR>
                {dg_node_sp}
            </table>
        </div>
    </div>
    </TD>
        """

    #   License data formatting
    if entilement_risk == "No Risk":
        entilement_risk = f"<TD bgcolor=#33FFBB> {entilement_risk} </TD>"
    else:
        dg_license = ""
        for lic in licenses:
            dg_license += f"<TR><TD bgcolor=#FA8074> {lic} </TD></TR>"
        entilement_risk = f"""
        <TD bgcolor=#FA8074>
        <a class="trigger_popup_{cluster_name}_License">{entilement_risk}</a>
        <div class="hover_bkgr_{cluster_name}_License">
        <span class="helper"></span>
        <div>
            <div class="popupCloseButton">&times;</div>
            <table>
                <TR>
                    <TH><B> Licenses </B></TH>
                </TR>
                {dg_license}
            </table>
        </div>
    </div>
    </TD>
        """

    #   Protocol status data formatting
    if (cifs_status == "NA" and nfs_status == "NA" and iscsi_status == "NA"):
        protpcol_status = "<TD bgcolor=#EFF613s> NA </TD>"
    else:
        if cifs_status == "NA":
            cifs_status = f"<TD> CIFS: {cifs_status} </TD>"
        elif cifs_status == "Ok":
            cifs_status = f"<TD bgcolor=#33FFBB> CIFS: {cifs_status} </TD>"
        else:
            dg_cifs_vserver = ""
            for cifs_v in cifs_vserver:
                dg_cifs_vserver += f"<TR><TD bgcolor=#FA8074> {cifs_v} </TD></TR>"
            cifs_status = f"""
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_cifs">{cifs_status}</a>
            <div class="hover_bkgr_{cluster_name}_cifs">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> Vserver </B></TH>
                    </TR>
                    {dg_cifs_vserver}
                </table>
            </div>
        </div>
        </TD>        

            """
        if nfs_status == "NA":
            nfs_status = f"<TD> NFS v3: {nfs_status} </TD>"
        elif nfs_status == "Ok":
            nfs_status = f"<TD bgcolor=#33FFBB> NFS v3: {nfs_status} </TD>"
        else:
            dg_nfs_vserver = ""
            for nfs_v in nfs_vserver:
                dg_nfs_vserver += f"<TR><TD bgcolor=#FA8074> {nfs_v} </TD></TR>"
            nfs_status = f"""
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_nfs"> {nfs_status} </a>
            <div class="hover_bkgr_{cluster_name}_nfs">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> Vserver </B></TH>
                    </TR>
                    {dg_nfs_vserver}
                </table>
            </div>
        </div>
        </TD>  
            """
        if iscsi_status == "NA":
            iscsi_status = f"<TD> ISCSI: {iscsi_status} </TD>"
        elif iscsi_status == "Ok":
            iscsi_status = f"<TD bgcolor=#33FFBB> ISCSI: {iscsi_status} </TD>"
        else:
            dg_iscsi_vserver = ""
            for iscsi_v in iscsi_vserver:
                dg_iscsi_vserver += f"<TR><TD bgcolor=#FA8074> {iscsi_v} </TD></TR>"
            iscsi_status = f"""
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_iscsi">{iscsi_status}</a>
            <div class="hover_bkgr_{cluster_name}_iscsi">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> Vserver </B></TH>
                    </TR>
                    {dg_iscsi_vserver}
                </table>
            </div>
        </div>
        </TD>  
            """
        protpcol_status = f"""
        <TD>
        <table>
            <TR>
                {cifs_status}
            </TR>
            <TR>
                {nfs_status}
            </TR>
            <TR>
                {iscsi_status}
            </TR>
        </table>
        </TD>
        """

#   Node loop requireds
    lun_statuses = ""
    for node in nodes:
        if(node in lun_offline_dict):
            offline_lun_count = lun_offline_dict[node]["offline_lun_count"]
            offline_lun = lun_offline_dict[node]["offline_lun"]
            #high_util_lun_count = lun_high_dict[node]["high_util_lun_count"]
            #high_util_lun_name = lun_high_dict[node]["high_util_lun_name"]
            lun_off_list = ""
            #lun_high_list = ""
            for lun_off in offline_lun:
                lun_off_list += f"<TR><TD bgcolor=#FA8074> {lun_off} </TD></TR>"
            # for lun_hi in high_util_lun_name:
            #    lun_off_list += f"<TR><TD bgcolor=#FA8074> {lun_hi} </TD></TR>"
            lun_statuses += f"""
            <TR>
            <TD bgcolor=#FA8074>
            <a class="trigger_popup_{cluster_name}_{node}_lun">{node}: {offline_lun_count} LUNs Offline</a>
            <div class="hover_bkgr_{cluster_name}_{node}_lun">
            <span class="helper"></span>
            <div>
                <div class="popupCloseButton">&times;</div>
                <table>
                    <TR>
                        <TH><B> LUNs Offline </B></TH>
                        {lun_off_list}
                    </TR>


                </table>
            </div>
        </div>
        </TD>
        </TR>
            """
#        elif(node in lun_offline_dict and node not in lun_high_dict):
#            offline_lun_count = lun_offline_dict[node]["offline_lun_count"]
#            offline_lun = lun_offline_dict[node]["offline_lun"]
#            lun_off_list = ""
#            for lun_off in offline_lun:
#                lun_off_list += f"<TR><TD bgcolor=#FA8074> {lun_off} </TD></TR>"
#            lun_statuses += f"""
#            <TR>
#            <TD bgcolor=#FA8074>
#            <a class="trigger_popup_{cluster_name}_{node}_lun">{node}:{offline_lun_count} LUNs Offline</a>
#            <div class="hover_bkgr_{cluster_name}_{node}_lun">
#            <span class="helper"></span>
#            <div>
#                <div class="popupCloseButton">&times;</div>
#                <table>
#                    <TR>
#                        <TH><B> Offline LUNs </B></TH>
#                    </TR>
#                    {lun_off_list}
#                </table>
#                </div>
#            </div>
#            </TD>
#            </TR>
#            """
#        elif(node not in lun_offline_dict and node in lun_high_dict):
#            high_util_lun_count = lun_high_dict[node]["high_util_lun_count"]
#            high_util_lun_name = lun_high_dict[node]["high_util_lun_name"]
#            lun_high_list = ""
#            for lun_hi in high_util_lun_name:
#                lun_high_list += f"<TR><TD bgcolor=#FA8074> {lun_hi} </TD></TR>"
#            lun_statuses += f"""
#            <TR>
#            <TD bgcolor=#FA8074>
#            <a class="trigger_popup_{cluster_name}_{node}_lun">{node}:{high_util_lun_count} LUNs > 95% </a>
#            <div class="hover_bkgr_{cluster_name}_{node}_lun">
#            <span class="helper"></span>
#            <div>
#                <div class="popupCloseButton">&times;</div>
#                <table>
#                    <TR>
#                        <TH><B> LUNs > 95% </B></TH>
#                    </TR>
#                    {lun_high_list}
#                </table>
#            </div>
#        </div>
#        </TD>
#        </TR>
#            """
        else:
            lun_statuses += f"<TR><TD bgcolor=#33FFBB>{node}: Ok </TD></TR>"

    lun_status = f"""
    <TD>
    <table>
        {lun_statuses}
    </table>
    </TD>
    """

    # Data formatting in HTML
    cluster_report_data = f"""
        <TR>
            <TD>{cluster_name}</TD>
            {ifgrp_status}
            {protpcol_status}
            {lun_status}
            {acp_status}
            {SP_status}
            {entilement_risk}
            {last_daily_bkp}
        </TR>
        """
    return cluster_report_data


if __name__ == '__main__':
    solidfire_clusters = []
    ontap_clusters = ["172.27.96.100","172.27.29.100","172.27.129.7"]
    storgrid_clusters = []
    eseries_clusters  = []                                                       
    print(ontap_report_table(
        ontap_clusters, storgrid_clusters, eseries_clusters, solidfire_clusters))