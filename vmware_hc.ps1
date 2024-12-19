
###############################################################################################################################
#                                                         
#                                                          Infrastructure Health Check Report                  
#   This script is part of a 6 part script to perform Health check of the infrastructure components(Storage, Compute, Network, Application)
#   This Script deals with the VMware component. The script should be called as a subprocess from to the infra_main.py script and  then
# 
#                                              This is and NetApp Internal script                                                   
###############################################################################################################################

############################################
#   Function to Read the list of Vcenters
############################################

#'------------------------------------------------------------------------------
#'Read the list of Vcenters
#'------------------------------------------------------------------------------
Function Read-vcenters() {

  [String]$site1_vcenter = "C:\HC_Scripts\site1_vcenter.txt"
  [String]$site2_vcenter = "C:\HC_Scripts\site2_vcenter.txt"
  $script:vcservers = @()
  $vcs = ""
  try {
    $vcs = Get-Content -Path $site1_vcenter -ErrorAction Stop
    $script:vcservers += $vcs
  }
  Catch {
    echo "File $site1_vcenter Does not Exist"
    Exit -1
  }
  try {
    $vcs = Get-Content -Path $site2_vcenter -ErrorAction Stop
    $script:vcservers += $vcs
  }
  Catch {
    echo "File $site2_vcenter Does not Exist"
    Exit -1
  }
}

############################################
#   Function to return HTML Body
############################################

Function HTML-Body($script:ESXi_report_dt, $script:Alarm_report_dt, $script:Datastore_report_dt) {
  #echo $script:Alarm_report_dt
  $report_body = "
    <div>
    <h3 style='color : #464A46; font-size : 21px' align="" left ""> ESXi Host Report </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> VCenter </B></TH>
                <TH><B> ESXi Host </B></TH>
                <TH><B> Overall Status </B></TH>
                <TH><B> Connection State </B></TH>
                <TH><B> Config Issues </B></TH>
                <TH><B> CPU Usage </B></TH>
                <TH><B> CPU Max </B></TH>
                <TH><B> Memory usage </B></TH>
                <TH><B> Memory Max </B></TH>
            </TR>
            $script:ESXi_report_dt
        </Table>
    <h3 style='color : #464A46; font-size : 21px' align="" left ""> Alarms </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> VCenter </B></TH>
                <TH><B> Status </B></TH>
                <TH><B> Alarm </B></TH>
                <TH><B> Entity </B></TH>
                <TH><B> Entity Type </B></TH>
                <TH><B> Time </B></TH>
                <TH><B> Acknowledged </B></TH>
                <TH><B> Acknowledged By </B></TH>
                <TH><B> Acknowledgment Time </B></TH>
            </TR>
            $script:Alarm_report_dt
        </Table>
    <h3 style='color : #464A46; font-size : 21px' align="" left ""> Datastores </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> Vcenter </B></TH>
                <TH><B> Datacenter </B></TH>
                <TH><B> Datastore </B></TH>
                <TH><B> State </B></TH>
                <TH><B> Percenatge  Free </B></TH>
                <TH><B> UsedGB </B></TH>
                <TH><B> FreeGB </B></TH>
            </TR>
            $script:Datastore_report_dt
        </Table>
    <h3 style='color : #464A46; font-size : 21px' align="" left ""> VM Report </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> Vcenter </B></TH>
                <TH><B> VM Name </B></TH>
                <TH><B> Guest Hostname </B></TD>
                <TH><B> ESXi Hostname </B></TD>
                <TH><B> Overall Status </B></TH>
                <TH><B> Connection State </B></TH>
                <TH><B> Power State </B></TH>
                <TH><B> Total NICs </B></TH>
                <TH><B> Disconnected NICs </B></TH>
                <TH><B> Tools Status </B></TH>
                <TH><B> Tools Version </B></TH>
                <TH><B> CPU utilization </B></TH>
                <TH><B> Memory utilization </B></TH>
            </TR>
            $script:VM_report_dt
        </Table>
    <h3 style='color : #464A46; font-size : 21px' align="" left ""> Snapshots (older than 3 days) </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> Vcenter </B></TH>
                <TH><B> VMName </B></TH>
                <TH><B> Snapshot name </B></TD>
                <TH><B> Created On </B></TH>
                <TH><B> Description </B></TH>
            </TR>
            $script:Snapshot_report_dt
        </Table>
    <h3 style='color : #464A46; font-size : 21px' align="" left ""> CDROMs connected </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> Vcenter </B></TH>
                <TH><B> CDROM Mounted ON(VM Name)  </B></TH>
            </TR>
            $script:CDROM_report_dt
        </Table>

    </div>  
  "
  return $report_body
}
#HTML-Body###############################################################UnHash it for mail body###################################################################################

############################################
#   Function to Connect to Vcenter
############################################

Function Setup-Connection($script:vcserver) {
  $cred_path = "C:\HC_Scripts\secrets\u_vmware_credentials.json"
  If (-Not(Test-Path -Path $cred_path)) {
    Exit -1
  }
  try {
    $Credential = Get-Content -Path $cred_path | ConvertFrom-Json
  }
  catch {
    Exit -1    
  }
  $u_name = $Credential.$script:vcserver.username
  $u_pass = $Credential.$script:vcserver.password
  try {
    #    Set-PowerCLIConfiguration -Scope User -ParticipateInCEIP $false                       Only for First Run
    connect-VIServer $vcserver -User $u_name -Password $u_pass -ErrorAction Stop | Out-Null
    Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false -ErrorAction Stop | Out-Null
  }
  catch {
    continue
  }
}
############################################
#   Function to DisConnect from Vcenter
############################################

Function Disconnect-Vcenter($script:vcserver) {
  try {
    disconnect-viserver $script:vcserver -confirm:$false
  }
  catch {
    Exit -1
  }
}


############################################
#   Function to get ESXi Host Report data
############################################

Function ESX-Data($script:vcserver) {
  Setup-Connection($script:vcserver)
  $ESXi_Report = @()
  $HTMLesx = ""
  $ESXis = Get-VMHost -Server $script:vcserver
  foreach ($ESXi in $ESXis) {

    $allinfo = '' | select-Object VCenter, Esx, OverallStatus, Connection_State, Config_issues, CPU_Utilization, CPU_Max, CPU_Min, Memory_Utilization, Mem_Max, Mem_Min
    $ESXi_name = $ESXi.ExtensionData
    $esxinfoconstat = (Get-Vmhost -Name $ESXi).ConnectionState
    $cpu_usage = (Get-Stat -Entity (Get-VMHost $ESXi) -Stat cpu.usage.average -MaxSamples 1 -IntervalMins 5)
    $memory_usage = (Get-Stat -Entity (Get-VMHost $ESXi) -Stat mem.usage.average -MaxSamples 1 -IntervalMins 5)
    if ($esxinfoconstat -eq "Connected") {
      $allinfo.CPU_Utilization = ($cpu_usage.Value)
      $allinfo.Memory_Utilization = ($memory_usage.Value)
    }
    else {
      $allinfo.CPU_Utilization = ""
      $allinfo.Memory_Utilization = ""
    }
    $statsesx = Get-Stat -Entity $ESXi -start (get-date).AddDays(-1) -Finish (Get-Date) -MaxSamples 1000 -stat "cpu.usage.average", "mem.usage.average"
    $statsesx | Group-Object -Property Entity | % {
      $cpuesx = $_.Group | where { $_.MetricId -eq "cpu.usage.average" } | Measure-Object -Property value -Average -Maximum -Minimum
      $memesx = $_.Group | where { $_.MetricId -eq "mem.usage.average" } | Measure-Object -Property value -Average -Maximum -Minimum
      $allinfo.CPU_Max = [int]$cpuesx.Maximum
      $allinfo.CPU_Min = [int]$cpuesx.Minimum
      $allinfo.Mem_Max = [int]$memesx.Maximum
      $allinfo.Mem_Min = [int]$memesx.Minimum
    }
    $allinfo.VCenter = $script:vcserver
    $allinfo.Esx = $ESXi_name.name
    $allinfo.OverallStatus = $ESXi_name.Summary.OverallStatus
    $allinfo.Connection_State = $esxinfoconstat
    $allinfo.Config_issues = $ESXi_name.configissue.FullFormattedMessage
    $ESXi_Report += $allinfo
  }

  foreach ($Entry in $ESXi_Report) {

    if ($Entry.OverallStatus -eq "green") {
      $OverallStatus = "<TD bgcolor=#33FFBB>$($Entry.OverallStatus)</TD>"
    }
    elseif ($Entry.OverallStatus -eq "yellow") {
      $OverallStatus = "<TD bgcolor=#EFF613>$($Entry.OverallStatus)</TD>"
    }
    else {
      $OverallStatus = "<TD bgcolor=#FA8074>$($Entry.OverallStatus)</TD>"
    } 
    if ($Entry.Connection_State -ne "connected") {
      $Connection_State = "<TD bgcolor=#FA8074>$($Entry.Connection_State)</TD>"
    }
    else {
      $Connection_State = "<TD bgcolor=#33FFBB>$($Entry.Connection_State)</TD>"
    }
    if ($Entry.Config_issues -ne $null) {
      $Config_issues = "<TD bgcolor=#EFF613>$($Entry.Config_issues)</TD>"
    }
    else {
      $Config_issues = "<TD bgcolor=#33FFBB>NA</TD>"
    }
    if ($Entry.CPU_Utilization -ge "90") {
      $CPU_Utilization = "<TD bgcolor=#FA8074>$($Entry.CPU_Utilization)%</TD>"
    }
    else {
      $CPU_Utilization = "<TD bgcolor=#33FFBB>$($Entry.CPU_Utilization)%</TD>"
    }
    if ($Entry.CPU_Max -ge "90") {
      $CPU_Max = "<TD bgcolor=#FA8074>$($Entry.CPU_Max)%</TD>"
    }
    else {
      $CPU_Max = "<TD bgcolor=#33FFBB>$($Entry.CPU_Max)%</TD>"
    }
    if ($Entry.Memory_Utilization -ge "90") {
      $Memory_Utilization = "<TD bgcolor=#FA8074>$($Entry.Memory_Utilization)%</TD>"
    }
    else {
      $Memory_Utilization = "<TD bgcolor=#33FFBB>$($Entry.Memory_Utilization)%</TD>"
    }
    if ($Entry.Mem_Max -ge "90") {
      $Mem_Max = "<TD bgcolor=#FA8074>$($Entry.Mem_Max)%</TD>"
    }
    else {
      $Mem_Max = "<TD bgcolor=#33FFBB>$($Entry.Mem_Max)%</TD>"
    }
    $HTMLesx += "
      <TR>
        <TD>$($Entry.VCenter)</TD>
        <TD>$($Entry.Esx)</TD>
        $OverallStatus
        $Connection_State
        $Config_issues
        $CPU_Utilization
        $CPU_Max
        $Memory_Utilization
        $Mem_Max
      </TR>
      "
  }
  Disconnect-Vcenter($script:vcserver)
  return $HTMLesx
}

############################################
#   Function to get Alarms
############################################

Function Get-TriggeredAlarms($script:vcserver) {

  Setup-Connection($script:vcserver)
  $rootFolder = Get-Folder -Server $script:vcserver "Datacenters"
  $alarms = @()
  foreach ($triggered_alarm in $rootFolder.ExtensionData.TriggeredAlarmState) {
    $alarm = "" | Select-Object VC, EntityType, Alarm, Entity, Status, Time, Acknowledged, AckBy, AckTime
    $alarm.VC = $script:vcserver
    $alarm.Alarm = (Get-View -Server $script:vcserver $triggered_alarm.Alarm).Info.Name
    $entity = Get-View -Server $script:vcserver $triggered_alarm.Entity
    $alarm.Entity = (Get-View -Server $script:vcserver $triggered_alarm.Entity).Name
    $alarm.EntityType = (Get-View -Server $script:vcserver $triggered_alarm.Entity).GetType().Name
    $alarm.Status = $triggered_alarm.OverallStatus
    $alarm.Time = $triggered_alarm.Time
    $alarm.Acknowledged = $triggered_alarm.Acknowledged
    $alarm.AckBy = $triggered_alarm.AcknowledgedByUser
    $alarm.AckTime = $triggered_alarm.AcknowledgedTime
    $alarms += $alarm
  }
  Foreach ($Entry in $alarms) {
    
    if ($Entry.Status -eq "yellow") {
      $Alarm_Status = "<TD bgcolor=#EFF613>$($Entry.Status)</TD>"
    }
    elseif ($Entry.Status -eq "red") {
      $Alarm_Status = "<TD bgcolor=#FA8074>$($Entry.Status)</TD>"
    }
    else {
      $Alarm_Status = "<TD>$($Entry.Status)<TD> "
    }
    $HTMLesx += "
      <TR>
        <TD>$($Entry.VC)</TD>
        $Alarm_Status
        <TD>$($Entry.Alarm)</TD>
        <TD>$($Entry.Entity)</TD>
        <TD>$($Entry.EntityType)</TD>
        <TD>$($Entry.Time)</TD>
        <TD>$($Entry.Acknowledged)</TD>
        <TD>$($Entry.AckBy)</TD>
        <TD>$($Entry.AckTime)</TD>
      </TR>
      " 
  }
  Disconnect-Vcenter($script:vcserver)
  return $HTMLesx
}

############################################
#   Function to get Datastonre Info
############################################

Function Datastore-Info($script:vcserver) {

  Setup-Connection($script:vcserver)
  function UsedSpace($DatStor) {
    [math]::Round(($DatStor.CapacityMB - $DatStor.FreeSpaceMB) / 1024, 2)
  }

  function FreeSpace($DatStor) {
    [math]::Round($DatStor.FreeSpaceMB / 1024, 2)
  }

  function PercFree($DatStor) {
    [math]::Round((100 * $DatStor.FreeSpaceMB / $DatStor.CapacityMB), 0)
  }
  $DS_Info = ""
  $DStores = @()
  $datacenter = get-datacenter
  foreach ($dc in $datacenter) {
    $Datastores = $dc | Get-Datastore
    ForEach ($Datastore in $Datastores) {
      $DS_Info = "" | Select-Object Vcenter, Datacenter, Datastore, State, UsedGB, FreeGB, PercFree
      $DS_Info.Datastore = $Datastore.Name
      $DS_Info.UsedGB = UsedSpace $Datastore
      $DS_Info.FreeGB = FreeSpace $Datastore
      $DS_Info.PercFree = PercFree $Datastore
      $DS_Info.State = $Datastore.State
      $DS_Info.Vcenter = $script:vcserver
      $DS_Info.Datacenter = $dc
      $DStores += $DS_Info
    }

    Foreach ($Entry in $DStores) {

      if ($Entry.State -ne "Available") {
        $DS_State = "<TD bgcolor=#EFF613>$($Entry.State)</TD>"
      }
      else {
        $DS_State = "<TD bgcolor=#33FFBB>$($Entry.State)</TD>"
      }
      
      if ($Entry.PercFree -le "10") {
        $DS_PercFree = "<TD bgcolor=#FA8074>$($Entry.PercFree)%</TD>"
      }
      elseif ($Entry.PercFree -le "20") {
        $DS_PercFree = "<TD bgcolor=#EFF613>$($Entry.PercFree)%</TD>"
      }
      else {
        $DS_PercFree = "<TD bgcolor=#33FFBB>$($Entry.PercFree)%</TD>"
      }
      $HTMLDS += "
        <TR>
          <TD>$($Entry.Vcenter)</TD>
          <TD>$($Entry.Datacenter)</TD>
          <TD>$($Entry.Datastore)</TD>
          $DS_State
          $DS_PercFree
          <TD>$($Entry.UsedGB)</TD>
          <TD>$($Entry.FreeGB)</TD>
        </TR>
        " 
    }
  }
  Disconnect-Vcenter($script:vcserver)
  return $HTMLDS
}

############################################
#   Function to get VM Info
############################################

Function VM-Info($script:vcserver) {
  
  Setup-Connection($script:vcserver)
  $vmall = Get-Folder -Type VM -Server $script:vcserver | get-vm
  $vms = ""
  $VMrepo = @()
  foreach ($vme in $vmall) {
    $nic_con = 0
    $vm = $vme.ExtensionData
    $vms = "" | Select-Object Vcenter, VMName, Guest_Hostname, ESXi_Host, OverallStatus, ConnectionState, PowerState, TotalNics, DisconnectedNics, ToolsStatus, ToolsVersion, CPUutilization, CPUMax, CPUMin, MemoryUtilization, MemMax, MemMin
    $vms.Vcenter = $script:vcserver
    $vms.VMName = $vm.Name
    $vms.Guest_Hostname = $vm.guest.hostname
    $vms.ESXi_Host = (Get-Vm -Name $vm.Name).VMHost.Name
    $Vms.OverAllStatus = $vm.summary.OverallStatus
    $Vms.ConnectionState = $vm.summary.runtime.connectionstate
    $vms.PowerState = $vm.summary.runtime.powerState
    $vms.TotalNics = $vm.summary.config.numEthernetCards
    try {
      $adp = Get-VM -Name $vm.Name -Server $script:vcserver | Get-NetworkAdapter
      foreach ($ad in $adp) {
        if ($ad.ConnectionState.Connected -eq $false) {
          $nic_con += 1
        }
      }
    }
    catch {
      $ErrorMessage = $_.Exception.Message
      $ErrorMessage
      $nic_con = "NA"
    }
    if ($nic_con -gt $vm.summary.config.numEthernetCards) {
      $nic_con = "Cant find - multiple VMs with same name exist"
    }
    $vms.DisconnectedNics = $nic_con
    if ($vms.PowerState -eq 'poweredOn') {
      $vms.CPUutilization = (Get-Stat -Entity $vme -Server $script:vcserver -MaxSamples 1 -stat "cpu.usage.average"-IntervalMins 5  -ErrorAction SilentlyContinue).Value
      $vms.MemoryUtilization = (Get-Stat -Entity $vme -Server $script:vcserver -MaxSamples 1 -stat "mem.usage.average"-IntervalMins 5  -ErrorAction SilentlyContinue).Value
      try {
        $stats = Get-Stat -Entity $vme -Server $script:vcserver -start (get-date).AddDays(-1) -Finish (Get-Date)-MaxSamples 100 -stat "cpu.usage.average", "mem.usage.average"  
        $stats | Group-Object -Property Entity | % {
          $cpuvm = $_.Group | where { $_.MetricId -eq "cpu.usage.average" } | Measure-Object -Property value -Average -Maximum -Minimum
          $memvm = $_.Group | where { $_.MetricId -eq "mem.usage.average" } | Measure-Object -Property value -Average -Maximum -Minimum
          $vms.CPUMax = [int]$cpuvm.Maximum
          $vms.CPUMin = [int]$cpuvm.Minimum
          $vms.MemMax = [int]$memvm.Maximum
          $vms.MemMin = [int]$memvm.Minimum  
        }
      }
      catch {
        $ErrorMessagevm = $_.Exception.Message
        $ErrorMessagevm
      }
    }
    $vms.ToolsStatus = $vm.guest.toolsstatus
    $vms.ToolsVersion = $vm.config.tools.toolsversion
    $VMrepo += $vms
  }
  Foreach ($Entry in $VMrepo) {
    if ($Entry.OverallStatus -eq 'green') {
      $VM_OverallStatus = "<TD bgcolor=#33FFBB>$($Entry.OverallStatus)</TD>"
    }
    elseif ($Entry.OverallStatus -eq 'yellow') {
      $VM_OverallStatus = "<TD bgcolor=#EFF613>$($Entry.OverallStatus)</TD>"
    }
    elseif ($Entry.OverallStatus -eq 'red') {
      $VM_OverallStatus = "<TD bgcolor=#FA8074>$($Entry.OverallStatus)</TD>"
    }
    else {
      $VM_OverallStatus = "<TD bgcolor=#FA8074>$($Entry.OverallStatus)</TD>"
    }
    if ($Entry.ConnectionState -eq 'Connected') {
      $VM_ConnectionState = "<TD bgcolor=#33FFBB>$($Entry.ConnectionState)</TD>"
    }
    else {
      $VM_ConnectionState = "<TD bgcolor=#FA8074>$($Entry.ConnectionState)</TD>"
    }
    if ($Entry.DisconnectedNics -gt "0") {
      $VM_DisconnectedNics = "<TD bgcolor=#EFF613>$($Entry.DisconnectedNics)</TD>"
    }
    elseif ($Entry.DisconnectedNics -eq "NA") {
      $VM_DisconnectedNics = "<TD bgcolor=#EFF613>NA</TD>"
    }
    elseif ($Entry.DisconnectedNics -eq "Cant find - multiple VMs with same name exist") {
      $VM_DisconnectedNics = "<TD bgcolor=#EFF613>$($Entry.DisconnectedNics)</TD>"
    }
    else {
      $VM_DisconnectedNics = "<TD>$($Entry.DisconnectedNics)</TD>"
    }
    if ($Entry.ToolsStatus -ne 'toolsOk') {
      $VM_ToolsStatus = "<TD bgcolor=#EFF613>$($Entry.ToolsStatus)</TD>"
    }
    else {
      $VM_ToolsStatus = "<TD>$($Entry.ToolsStatus)</TD>"
    }
    if ($Entry.CPUutilization -eq $null) {
      $VM_CPUutilization = "<TD bgcolor=#EFF613>NA</TD>"
    }
    elseif ($Entry.CPUutilization -ge "90") {
      $VM_CPUutilization = "<TD bgcolor=#FA8074>$($Entry.CPUutilization)%</TD>"
    }
    else {
      $VM_CPUutilization = "<TD bgcolor=#33FFBB>$($Entry.CPUutilization)%</TD>"
    }
    if ($Entry.Memoryutilization -eq $null) {
      $VM_Memoryutilization = "<TD bgcolor=#EFF613>NA</TD>"
    }
    elseif ($Entry.Memoryutilization -ge "90") {
      $VM_Memoryutilization = "<TD bgcolor=#FA8074>$($Entry.Memoryutilization)%</TD>"
    }
    else {
      $VM_Memoryutilization = "<TD bgcolor=#33FFBB>$($Entry.Memoryutilization)%</TD>"
    }
    $HTMLVM += "
      <TR>
        <TD>$($Entry.Vcenter)</TD>
        <TD>$($Entry.VMName)</TD>
        <TD>$($Entry.Guest_Hostname)</TD>
        <TD>$($Entry.ESXi_Host)</TD>
        $VM_OverallStatus
        $VM_ConnectionState
        <TD>$($Entry.PowerState)</TD>
        <TD>$($Entry.TotalNics)</TD>
        $VM_DisconnectedNics
        $VM_ToolsStatus
        <TD>$($Entry.ToolsVersion)</TD>
        $VM_CPUutilization
        $VM_Memoryutilization
      </TR>
      "
  }
  Disconnect-Vcenter($script:vcserver)
  return $HTMLVM
}


####################################################
#   Function to get Snapshots older than 3 days
####################################################

Function Stale-Snapshot($script:vcserver) {
  Setup-Connection($script:vcserver)
  $snapobjc = @()
  $snap = ""
  $snap = Get-Folder -Type VM -Server $script:vcserver | get-vm | Get-Snapshot | Where { $_.Created -lt (Get-Date).AddDays(-3) }
  #$snap = Get-Folder -Type VM -Server $script:vcserver | get-vm | Get-Snapshot
  foreach ($s in $snap) {
    $snapobj = '' | select-Object VCenter, vm, Snapshot_Name, created, description
    $snapobj.VCenter = $script:vcserver
    $snapobj.vm = $s.vm
    $snapobj.Snapshot_Name = $s.name
    $snapobj.created = $s.created
    $snapobj.description = $s.description
    $snapobjc += $snapobj
  }
  Foreach ($Entry in $snapobjc) {
    $HTMLSnap += "
      <TR>
        <TD>$($Entry.VCenter)</TD>
        <TD>$($Entry.vm)</TD>
        <TD>$($Entry.Snapshot_Name)</TD>
        <TD>$($Entry.created)</TD>
        <TD>$($Entry.description)</TD>
      </TR>
      "
  }
  Disconnect-Vcenter($script:vcserver)
  return $HTMLSnap
}


############################################
#   Function to get Connected CDROMS
############################################

Function Connected-CDROM($script:vcserver) {
  
  Setup-Connection($script:vcserver)
  $cdobj = @()
  $cdrom_connected = Get-Folder -Type VM -Server $vcnt2 | Get-vm | where { $_ | get-cddrive | where { $_.ConnectionState.Connected -eq "true" } }
  foreach ($cdrom in $cdrom_connected) {
    $cdo = '' | Select-Object Vcenter, Name
    $cdo.Vcenter = $script:vcserver
    $cdo.Name = $cdrom.Name
    $cdobj += $cdo
  }
  Foreach ($Entry in $cdobj) {
    $HTML_CDROM += "
      <TR>
        <TD>$($Entry.Vcenter)</TD>
        <TD>$($Entry.Name)</TD>
      </TR>
      "
  }
  return $HTML_CDROM
}

#Main Body Below
$script:ESXi_report_dt = ""
Read-vcenters
ForEach ($script:vcserver in $script:vcservers) {
  $script:ESXi_report_dt += ESX-Data $script:vcserver
  $script:Alarm_report_dt += Get-TriggeredAlarms $script:vcserver
  $script:Datastore_report_dt += Datastore-Info $script:vcserver 
  $script:VM_report_dt += VM-Info $script:vcserver
  $script:Snapshot_report_dt += Stale-Snapshot $script:vcserver
  $script:CDROM_report_dt += Connected-CDROM($script:vcserver)
  #VM-Info($script:vcserver)
}
HTML-Body $script:ESXi_report_dt $script:Alarm_report_dt $script:Datastore_report_dt

