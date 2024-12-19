"""
###############################################################################################################################
#                                                         
#                                                          Infrastructure Health Check Report                  
#   This script is part of a 6 part script to perform Health check of the infrastructure components(Storage, Compute, Network, Applications)
#   This Script deals with the Switches. The script should be imported to the infra_main.py script and  then
#   switchhc.cumulus_table(cumulus_switches, cisco_switches) function should be called from the main function.
# 
#                                              This is and NetApp Internal script                                                   
###############################################################################################################################
"""

"""

Switch Health Check script using paramiko module for SSH session

"""


#####################################
#   Import Dependencies
#####################################




import json
import paramiko
def ssh_command_push(switch, command):
    """

    Function to send commands over ssh session

    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cumulus_credentials_path = "./secrets/u_cumulus_switch_secret.json"
    with open(cumulus_credentials_path) as f:
        cumulus_credentials = json.load(f)
    cisco_credentials_path = "./secrets/u_cisco_switch_secret.json"
    with open(cisco_credentials_path) as f:
        cisco_credentials = json.load(f)
    if switch in cumulus_credentials:
        cumulus_username = cumulus_credentials[switch]["username"]
        cumulus_password = cumulus_credentials[switch]["password"]
        ssh.connect(switch, username=cumulus_username,
                    password=cumulus_password)
    elif switch in cisco_credentials:
        cisco_username = cisco_credentials[switch]["username"]
        cisco_password = cisco_credentials[switch]["password"]
        ssh.connect(switch, username=cisco_username,
                    password=cisco_password)
    else:
        error_msg = f"Error: Credentials for {switch} not found"
        print(error_msg)
        exit

    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
    if ("-j" in command or "json" in command):
        out = ssh_stdout.read()
        err = ssh_stderr.read().decode('utf-8')
        output = json.loads(out)
    else:
        out = ssh_stdout.read()
        err = ssh_stderr.read().decode('utf-8')
        output = out.decode('utf-8').split('\n')
    if (err == ''):
        return output
    else:
        return err


def cumulus_table(cumulus_switches, cisco_switches):
    cumulus_dt = ""
    cisco_dt = ""
    for cumulus_switch in cumulus_switches:
        cumulus_dt += cumulus_data(cumulus_switch)
    for cisco_switch in cisco_switches:
        cisco_dt += cisco_data(cisco_switch)
    switch_table = f"""
    <body><font><h3 style='color : #464A46; font-size : 21px' align="" left "">Cumulus Switches</h3></font><Table>

    </caption>

        <TR>
            <TH><B> Switch </B></TH>
            <TH><B> Version </B></TH>
            <TH><B> HW Health Status </B></TH>
            <TH><B> Interface Status </B></TH>
            <TH><B> Bridge Link Status </B></TH>
        </TR>
        {cumulus_dt}
    </Table>
    </body>
    <body><font><h3 style='color : #464A46; font-size : 21px' align="" left "">Cisco Switches</h3></font><Table>

    </caption>

        <TR>
            <TH><B> Switch </B></TH>
            <TH><B> Version </B></TH>
            <TH><B> HW Health Status </B></TH>
            <TH><B> Interface Status </B></TH>
            <TH><B> VLAN Status </B></TH>
            <TH><B> Port-Channel Status </B></TH>
        </TR>
        {cisco_dt}
    </Table>
    </body>
    """
    return switch_table


def cumulus_data(cumulus_switch):
    # For Hostname
    try:
        command = "net show hostname json"
        hostname = ssh_command_push(cumulus_switch, command)["hostname"]
    except:
        hostname = f"<TD bgcolor=#FA8074>cannot connect to {cumulus_switch}<TD>"
    # For Version
    try:
        command = "net show version json"
        fw_version = ssh_command_push(cumulus_switch, command)["build"]
    except:
        fw_version = f"<TD bgcolor=#FA8074>cannot connect to {cumulus_switch}<TD>"
    # For switch Hardware health
    try:
        command = "sudo smonctl -j"
        sw_health = ssh_command_push(cumulus_switch, command)
    except:
        sw_health = ""
    try:
        command = "net show interface all json"
        sw_interface = ssh_command_push(cumulus_switch, command)
    except:
        sw_interface = ""
    # For Network Bridge link status
    try:
        command = "net show bridge link | grep -w 'DOWN'"
        sw_bridge_down = ssh_command_push(cumulus_switch, command)
        sw_bridge_down.remove('')
    except:
        sw_bridge_down = ""
    # For All bridge connection
    try:
        command = "net show bridge link"
        sw_bridge_all = ssh_command_push(cumulus_switch, command)
        sw_bridge_all.remove('')
    except:
        sw_bridge_all = ""

    # Manupulate data for Switch Hardware health
    sw_faulted_hw = []
    sw_faulted_hw_count = 0
    sw_hw_component_count = len(sw_health)

    sw_health_status = "<TD bgcolor=#33FFBB> OK </TD>"
    if sw_hw_component_count == 0:
        sw_health_status = "<TD bgcolor=#FA8074> Not Available </TD>"
    else:
        for i in range(0, sw_hw_component_count):

            sw_hw_status = sw_health[i]['state']
            if sw_hw_status != "OK":
                sw_faulted_hw += [sw_health[i]['name']]
                sw_faulted_hw_count += 1
        if sw_faulted_hw:
            sw_health_status = f"<TD bgcolor=#FA8074> {sw_faulted_hw_count} Faulted Hardware\n{sw_faulted_hw}</TD>"

    # Manupulate data for interface status
    sw_interface_count = len(sw_interface)
    #interfaces = list(sw_interface.keys())
    down_interface = []
    down_interface_count = 0
    interface_status = ""
    if sw_interface_count:
        for interface in sw_interface:
            int_status = sw_interface[interface]["linkstate"]
            int_mode = sw_interface[interface]["mode"]
            if int_status == "DN" and int_mode == "NotConfigured":
                continue
            elif int_status == "DN":
                down_interface += [interface]
                down_interface_count += 1
        if down_interface_count:
            interface_status = f"<TD bgcolor=#FA8074> {down_interface_count} Interfaces Down:\n{down_interface} </TD>"
        else:
            interface_status = "<TD bgcolor=#33FFBB> OK </TD>"
    else:
        interface_status = "<TD bgcolor=#FA8074> Not Available </TD>"
    # Manupulate data for Bridge status
    down_bridge_count = 0
    down_bridge_name = []
    if sw_bridge_all:
        if sw_bridge_down:
            down_bridge_count = len(sw_bridge_down)
            for i in range(0, down_bridge_count):
                down_bridge_name += [sw_bridge_down[i].split(' ')[1]]
            bridge_link_status = f"<TD bgcolor=#FA8074> {down_bridge_count} Bridge Link Down:\n{down_bridge_name} </TD>"
        else:
            bridge_link_status = "<TD bgcolor=#33FFBB> OK </TD>"
    else:
        bridge_link_status = "<TD bgcolor=#FA8074> Not Available </TD>"

    cumulus_dt = f"""
        <TR>
            <TD> {hostname} </TD>
            <TD> {fw_version} </TD>
            {sw_health_status}
            {interface_status}
            {bridge_link_status}
        </TR>
        """
    return cumulus_dt


def cisco_data(cisco_switch):
    # For the Hostname
    try:
        command = "show hostname"
        nx_hostname = ssh_command_push(cisco_switch, command)[0]
    except:
        nx_hostname = f"<TD bgcolor=#FA8074>cannot connect to {cisco_switch}<TD>"
    # For Cisco FW Version
    try:
        command = "show version | grep 'system:'"
        nx_version = ssh_command_push(cisco_switch, command)
        nx_version.remove('')
        nx_version = nx_version[0].split('    ')[1]      # Get the Version
    except:
        nx_version = f"<TD bgcolor=#FA8074>cannot connect to {cisco_switch}<TD>"
    # For Cisco Switch Envirnment
    try:
        command = "show environment fan | grep 'FAN' | grep -v -i 'Ok'"
        fan_status = ssh_command_push(cisco_switch, command)
        fan_status.remove('')
    except:
        fan_status = "Error"
    try:
        command = "show environment power | grep 'AC' | grep -v -i 'ok'"
        power_status = ssh_command_push(cisco_switch, command)
        power_status.remove('')
    except:
        power_status = "Error"
    try:
        command = " show environment temperature | grep '1        ' | grep  -v -i 'ok'"
        temp_status = ssh_command_push(cisco_switch, command)
        temp_status.remove('')
    except:
        temp_status = "Error"
    # For Interface Down status
    try:
        command = "show interface brief | grep -i 'down' | grep -i -v 'admin' | grep -v -i 'SFP not inserted' | grep -v -i 'Link not connected'"
        nx_inf_down = ssh_command_push(cisco_switch, command)
        nx_inf_down.remove('')
    except:
        nx_inf_down = "Error"
    # For Vlan status
    try:
        command = "show vlan brief | in suspended"
        vlan_down = ssh_command_push(cisco_switch, command)
        vlan_down.remove('')
    except:
        vlan_down = "Error"
    # For Port-channel Summary
    try:
        command = "show port-channel summary | in D | grep 'Eth'"
        pt_ch_down = ssh_command_push(cisco_switch, command)
        pt_ch_down.remove('')
    except:
        pt_ch_down = "Error"
    # Manupulate data for Environment status
    env_status = "<TD bgcolor=#FA8074> Not Available </TD>"
    faulted_subsys = []
    if (fan_status == [] and power_status == [] and temp_status == []):
        env_status = "<TD bgcolor=#33FFBB> OK </TD>"
    else:
        if fan_status != "Error" and power_status != "Error" and temp_status != "Error":
            for i in range(0, len(fan_status)):
                faulted_subsys += [fan_status[i].split('  ')[0]]

            for i in range(0, len(power_status)):
                faulted_subsys += [power_status[i].split('   ')[1]]
            for i in range(0, len(temp_status)):
                faulted_subsys += [temp_status[i].split('        ')[1]]
            env_status = f"<TD bgcolor=#FA8074> {len(faulted_subsys)} Faulted Sub-Systems:\n{faulted_subsys} </TD>"
    # Manupulate Interface status data

    down_inf = []
    if (nx_inf_down == []):
        interface_status = "<TD bgcolor=#33FFBB> OK </TD>"
    elif (nx_inf_down == "Error"):
        interface_status = "<TD bgcolor=#FA8074> Not Available </TD>"
    else:
        for i in range(0, len(nx_inf_down)):
            down_inf += [nx_inf_down[i].split('      ')[0]]
        interface_status = f"<TD bgcolor=#FA8074> {len(down_inf)} Down Interfaces:\n{down_inf} </TD>"
    # For VLAN status

    down_vlan = []
    if (vlan_down == []):
        vlan_status = "<TD bgcolor=#33FFBB> OK </TD>"
    elif vlan_down == "Error":
        vlan_status = "<TD bgcolor=#FA8074> Not Available </TD>"
    else:
        for i in range(0, len(vlan_down)):
            if (vlan_down[i].split(' ')[1] != ''):
                down_vlan += [vlan_down[i].split(' ')[1]]
            elif (vlan_down[i].split('  ')[1] != ''):
                down_vlan += [vlan_down[i].split('  ')[1]]
            else:
                down_vlan += [vlan_down[i].split('    ')[1]]
        vlan_status = f"<TD bgcolor=#FA8074> {len(down_vlan)} Down VLAN:\n{down_vlan} </TD>"
    # For Port-Channel status

    pt_ch_down_count = len(pt_ch_down)
    if (pt_ch_down == []):
        pt_channel_status = "<TD bgcolor=#33FFBB> OK </TD>"
    elif pt_ch_down == "Error":
        pt_channel_status = "<TD bgcolor=#FA8074> Not Available </TD>"
    else:
        ptc_down = '\n'.join(pt_ch_down)
        pt_channel_status = f"<TD bgcolor=#FA8074> {pt_ch_down_count} Port-Channel down:\n{ptc_down} </TD>"

    cisco_dt = f"""
        <TR>
            <TD> {nx_hostname} </TD>
            <TD> {nx_version} </TD>
            {env_status}
            {interface_status}
            {vlan_status}
            {pt_channel_status}
        </TR>
        """

    return cisco_dt
