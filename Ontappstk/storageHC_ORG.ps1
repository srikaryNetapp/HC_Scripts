whoami
<#
This script is an intelectual property of GSSC. It is intended to be used to generate Health-Check report for Ontap systems.
For modification and tuning please reachout to your respective leads.
Usage:
> .\storageHC.ps1
#>
######################################################################################################################
#'Start a timer for logging.
######################################################################################################################

$elapsedTime = [System.Diagnostics.Stopwatch]::StartNew()

######################################################################################################################
#'Function to Get-IsoDateTime.
######################################################################################################################

Function Get-IsoDateTime {
    Return (Get-IsoDate) + " " + (Get-IsoTime)
}

######################################################################################################################
#'Function to Get-IsoDate.
######################################################################################################################

Function Get-IsoDate {
    Return Get-Date -uformat "%Y-%m-%d"
}

######################################################################################################################
#'Function to Get-IsoTime.
######################################################################################################################

Function Get-IsoTime {
    Return Get-Date -Format HH:mm:ss
}

######################################################################################################################
#'Initialization Section. Define Global Variables.
######################################################################################################################

[String]$script:scriptPath = Split-Path($MyInvocation.MyCommand.Path)
[String]$script:scriptSpec = $MyInvocation.MyCommand.Definition
[String]$script:scriptBaseName = (Get-Item $scriptSpec).BaseName
[String]$script:scriptName = (Get-Item $scriptSpec).Name
[String]$script:scriptLogPath = $($scriptPath + "\" + (Get-IsoDate))
[Int]$script:errorCount = 0
$ErrorActionPreference = "Stop"
[String]$outfile = "C:\HC_Scripts\Ontappstk\storage_report_output\" + (Get-IsoDate) + "_StorageHC.html"
#$outfile = "C:\NA-Scripts\storage_report_output\test.html"

######################################################################################################################
#'Ensure that dates are always returned in English
######################################################################################################################

[System.Threading.Thread]::CurrentThread.CurrentCulture = "en-US"

######################################################################################################################
#'Function to Write-Log
######################################################################################################################

Function Write-Log {
    Param(
        [Switch]$Info,
        [Switch]$Error,
        [Switch]$Debug,
        [Switch]$Warning,
        [String]$Message
    )
    #'---------------------------------------------------------------------------
    #'Add an entry to the log file and disply the output. Format: [Date],[TYPE],MESSAGE
    #'---------------------------------------------------------------------------
    [String]$lineNumber = $MyInvocation.ScriptLineNumber
    [Bool]$debugLogging = $False;
    If ($Debug -And (-Not($debugLogging))) {
        Return $Null;
    }
    Try {
        If ($Error) {
            If ([String]::IsNullOrEmpty($_.Exception.Message)) {
                [String]$line = $("`[" + (Get-IsoDateTime) + "`],`[ERROR`],`[LINE $lineNumber`]," + $Message)
            }
            Else {
                [String]$line = $("`[" + (Get-IsoDateTime) + "`],`[ERROR`],`[LINE $lineNumber`]," + $Message + ". Error """ + $_.Exception.Message + """")
            }
        }
        ElseIf ($Info) {
            [String]$line = $("`[" + (Get-IsoDateTime) + "`],`[INFO`]," + $Message)
        }
        ElseIf ($Debug) {
            [String]$line = $("`[" + $(Get-IsoDateTime) + "`],`[DEBUG`],`[LINE $lineNumber`]," + $Message)
        }
        ElseIf ($Warning) {
            [String]$line = $("`[" + (Get-IsoDateTime) + "`],`[WARNING`],`[LINE $lineNumber`]," + $Message)
        }
        Else {
            [String]$line = $("`[" + (Get-IsoDateTime) + "`],`[INFO`]," + $Message)
        }
        #'------------------------------------------------------------------------
        #'Display the console output.
        #'------------------------------------------------------------------------
        If ($Error) {
            If ([String]::IsNullOrEmpty($_.Exception.Message)) {
                Write-Host $($line + ". Error " + $_.Exception.Message) -Foregroundcolor Red
            }
            Else {
                Write-Host $line -Foregroundcolor Red
            }
        }
        ElseIf ($Warning) {
            Write-Host $line -Foregroundcolor Yellow
        }
        ElseIf ($Debug -And $debugLogging) {
            Write-Host $line -Foregroundcolor Magenta
        }
        Else {
            Write-Host $line -Foregroundcolor White
        }
        #'------------------------------------------------------------------------
        #'Append to the log. Omit debug loggging if not enabled.
        #'------------------------------------------------------------------------
        If ($Debug -And $debugLogging) {
            Add-Content -Path "$scriptLogPath.log" -Value $line -Encoding UTF8 -ErrorAction Stop
        }
        Else {
            Add-Content -Path "$scriptLogPath.log" -Value $line -Encoding UTF8 -ErrorAction Stop
        }
        If ($Error) {
            Add-Content -Path "$scriptLogPath.err" -Value $line -Encoding UTF8 -ErrorAction Stop
        }
    }
    Catch {
        Write-Warning "Could not write entry to output log file ""$scriptLogPath.log"". Log Entry ""$Message"""
    }
}

######################################################################################################################
#'Import the PSTK.
######################################################################################################################

Function Modules() {
    [String]$moduleName = "DataONTAP"
    Try {
        Import-Module DataONTAP # -ErrorAction Stop | Out-Null
        Import-Module posh-ssh -ErrorAction Stop | Out-Null
        Get-Module -All | Out-Null
        Write-Log -Info -Message "Imported Module ""$moduleName"""
    }
    Catch {
        Write-Log -Error -Message "Failed importing module ""$moduleName"""
        Exit -1
    }
}

######################################################################################################################
# FUnction to create the HTML Body
######################################################################################################################
Function HTML-Body($current_time, $current_date) {
    $css_fileSpec = "C:\HC_Scripts\Ontappstk\css_template.txt"
    $js_fileSpec = "C:\HC_Scripts\Ontappstk\js_template.txt"
    [String]$css = Get-Content -Path $css_fileSpec
    [String]$js = Get-Content -Path $js_fileSpec
    $clusters = Read-Cluster
    $storage_body = Cluster-ReportTable $clusters
    $html_body =
    @"
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Storage Health-Check</title>
      
  </head>
  $css
  <body>
      <h1> <strong>Allianz BSG2/BSG3 - Storage Health Check Report - $current_time </strong></h1>
      <H4 style='color : #4CAF50;padding-left: 30px;'><strong> Date - $current_date </strong></H4>
      <H5 style='color : #464A46;font-size : 14px;padding-left: 30px;'><strong> Note : This report is for past 24hrs </strong></H5>
      <H4 style='color : #464A46;font-size : 21px;padding-left: 30px;'>Legend </H4>
      <table style='width:auto;padding-left: 30px; background-color: #efefef;word-break: keep-all;'>
          <tr>
              <td bgcolor=#FA8074>Red</td>
              <td style='background-color: white;'>Critical</td>
              <td bgcolor=#EFF613>Yellow</td>
              <td style='background-color: white;'>Warnings</td>
              <td bgcolor=#33FFBB>Green</td>
              <td style='background-color: white;'>OK</td>
          </tr>
      </table>
      <table></table>
<div class="tabs">
<input type="radio" id="tab1" name="tab-control" checked>
          <ul>
              <li title="Storage">
                  <label for="tab1" role="button">
                          <img
                              width="17"
                              hight="17"
                              src="https://image.flaticon.com/icons/svg/873/873135.svg"/><br /><span> Storage </span></label>
                 </li>
              </ul>
              <div class="slider">
                  <div class="indicator"></div>
              </div>
              <div class="content">
                  <section>
                      <h2>Storage</h2>
                          $storage_body
                  </section>
              </div>
          </div>
          $js
      </body>
  </html>
"@
    return $html_body
}
######################################################################################################################
#'Read the list of clusters.
######################################################################################################################

Function Read-Cluster() {
    $clusters = @()
    $Clusters_InputPath = "C:\HC_Scripts\Ontappstk\cluster_input.txt"
    If (-Not(Test-Path -Path $Clusters_InputPath)) {
        Write-Log -Warning -Message "The file ""$Clusters_InputPath"" does not exist"
        Exit -1
    }
    Try {
        $cluster_Input = Get-Content -Path $Clusters_InputPath -ErrorAction Stop
        Write-Log -Info -Message "Read file ""$Clusters_InputPath"""
    }
    Catch {
        Write-Log -Error -Message "Failed reading file ""$Clusters_InputPath"""
        Exit -1
    }
    foreach ($cluster in $cluster_Input) {
        if ($cluster -ne "") {
            $clusters += $Cluster
        }
    }
    return $clusters
}

######################################################################################################################
#'Fetch Cluster Name
######################################################################################################################
Function Cluster-Name($cluster) {
    try {
        Process-cluster $cluster
        $cluster_name = (Get-NcCluster).ClusterName
        Write-Log -Info -Message "Fetching Cluster Name"
    }
    catch {
        Write-Log -Error -Message "Failed to Fetch Cluster Name"
        $cluster_name = "NA"
        [Int]$script:errorCount++
      
        break;
    }
    return $cluster_name
}

######################################################################################################################
#'Connect to Cluster
######################################################################################################################
Function Process-cluster($cluster) {
    try {
        $credential = Get-NcCredential -Controller $cluster -ErrorAction Stop
        Write-Log -Info -Message "Enumerated cached credentials for cluster ""$cluster"""
    }
    catch {
        Write-Log -Error -Message "Failed enumerating cached credentials for cluster ""$cluster"""
        [Int]$script:errorCount++
        Break;
    }
    try {
        Connect-NcController -Name $cluster -HTTPS -Credential $credential.Credential -Timeout 30000 -ErrorAction Stop | Out-Null
  
        Write-Log -Info -Message $("Connected to cluster ""$cluster"" as user """ + $credential.Credential.UserName + """")
    }
    catch {
        Write-Log -Error -Message $("Connected to cluster ""$cluster"" as user """ + $credential.Credential.UserName + """")
  
        [Int]$script:errorCount++
  
        Break;
    }
}
######################################################################################################################
#'Get Nodes.
######################################################################################################################

Function Get-ClusterNodes($cluster) {
    Try {
        Process-cluster $cluster
        $nodes = Get-NcNode -ErrorAction Stop
        Write-Log -Info -Message "Enumerated Nodes on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating nodes on cluster ""$cluster"""
        $node = "NA"
        [Int]$script:errorCount++
    }
    return $nodes
}
######################################################################################################################
#'Get Node Image Version.
######################################################################################################################

Function Get-Clusterimage($cluster) {
    Try {
        Process-cluster $cluster
        $ClusterImage = (Get-NcClusterImage).CurrentVersion | Get-Unique -ErrorAction Stop
        Write-Log -Info -Message "Enumerated Cluster Version on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating Cluster Version on cluster ""$cluster"""
        $node = "NA"
        [Int]$script:errorCount++
    }
    return $ClusterImage
}

######################################################################################################################
#'Get Envirnment Status.
######################################################################################################################
Function Get-EnvStatus($cluster) {
    $Command = "system health subsystem show -health !ok -fields subsystem"
    $credential = Get-NcCredential -Controller $cluster -ErrorAction Stop
    $SessionID = New-SSHSession -ComputerName $cluster -Credential $credential.Credential

    Try {
        $output = Invoke-SSHCommand -Index $sessionid.sessionid -Command $Command -ErrorAction Stop  # Invoke Command Over SSH
        Write-Log -Info -Message $("Executed command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
    }
    Catch {
        Write-Log -Error -Message $("Failed executing command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
        [Int]$script:errorCount++
        Break;
    }
    $output = $output.output
    return $output
}
######################################################################################################################
#'Get Chassis Status.
######################################################################################################################

Function Get-ChassisStatus($cluster) {
    $Command = "system chassis fru show -status !ok -fields fru-name "
    $credential = Get-NcCredential -Controller $cluster -ErrorAction Stop
    $SessionID = New-SSHSession -ComputerName $cluster -Credential $credential.Credential

    Try {
        $output = Invoke-SSHCommand -Index $sessionid.sessionid -Command $Command -ErrorAction Stop  # Invoke Command Over SSH
        Write-Log -Info -Message $("Executed command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
    }
    Catch {
        Write-Log -Error -Message $("Failed executing command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
        [Int]$script:errorCount++
        Break;
    }
    $output = $output.output
    return $output
}
######################################################################################################################
#'Get Failed Disks.
######################################################################################################################

Function Failed-Disk($cluster) {
    Try {
        Process-cluster $cluster
        $failedDisks = Get-NcDisk -ErrorAction Stop | Where-Object { $_.DiskRaidInfo.ContainerType -eq "broken" }

        Write-Log -Info -Message "Enumerated Disks on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating disks on cluster ""$cluster"""
        [Int]$script:errorCount++
        Break;
    }
    return $failedDisks
}
######################################################################################################################
#'Enumerate the cluster health.
######################################################################################################################

Function Cluster-Health($cluster) {
    $Command = "cluster show -health false "
    $credential = Get-NcCredential -Controller $cluster -ErrorAction Stop
    $SessionID = New-SSHSession -ComputerName $cluster -Credential $credential.Credential #Connect Over SSH
    Try {
        $output = Invoke-SSHCommand -Index $sessionid.sessionid -Command $Command # Invoke Command Over SSH
        Write-Log -Info -Message $("Executed Command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
    }
    Catch {
        Write-Log -Error -Message $("Failed Executing Command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
        [Int]$script:errorCount++
        Break;
    }
    $output = $output.output
    return $output
}

######################################################################################################################

#'Enumerate Spare Disks.

######################################################################################################################


Function Spare-Disk($cluster) {


    $count = @()

    $nodeList = @()

    $spareList = @()

    [Int]$nodeSpareCount = 0

    $node = (Get-ClusterNodes($cluster))
    $nodeCount = $node.count

    Try {
     
        Process-cluster $cluster

        $spareDisks = Get-NcAggrspare -ErrorAction Stop # getting aggregate spare disks

        Write-Log -Info -Message "Enumerated spare disks on cluster ""$cluster"""

    }
    Catch {

        Write-Log -Error -Message "Failed enumerating spare disks on cluster ""$cluster"""

        [Int]$script:errorCount++

        Break;

    }

    $spareDiskCount = $spareDisks.count

    $spareDiskOwner = $spareDisks.originalowner

    $script:sd = $null #'checking count of spare disks
    if ($spareDiskCount -ne 0) {

        For ($i = 0; $i -lt $nodeCount; $i++) {

            For ($j = 0; $j -le $spareDiskCount; $j++) {

                If ($nodeCount -lt 2) {

                    If ($node.node -Match $spareDiskOwner[$j]) {

                        $nodeSpareCount = $nodeSpareCount + 1          

                    }

                }
                else {

                    If ($node.node[$i] -Match $spareDiskOwner[$j]) {

                        $nodeSpareCount = $nodeSpareCount + 1

                    }

                }

            }

            $nodeSpareCount = $nodeSpareCount - 1

            $count += "$nodeSpareCount"

            $nodeSpareCount = 0

            #$count

        }
      
        For ($i = 0; $i -lt $nodeCount; $i++) {

            If ($nodeCount -lt 2) {

                $nodeList += $node.Node

                $spareList += $count[$i]

            }
            else {

                $nodeList += $node.Node[$i]

                $spareList += $count[$i]        

            }
        }
    }
    else {
        For ($i = 0; $i -lt $nodeCount; $i++) {

            If ($nodeCount -lt 2) {

                $nodeList += $node.Node

                $spareList += 0

            }
            else {

                $nodeList += $node.Node[$i]

                $spareList += 0       

            }
        }
    }
    return $nodeList, $spareList

}

######################################################################################################################
#'Enumerate Aggregates.
######################################################################################################################

Function aggregate-status($cluster) {
  
    $aggregateOffline = @()
    $aggregateHighUtil = @()
    Try {
   
        Process-cluster $cluster
        $aggregates = Get-NcAggr -ErrorAction Stop
        Write-Log -Info -Message "Enumerated Aggregates on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating aggregates on cluster ""$cluster"""
        [Int]$script:errorCount++
        Break;
    }

    ForEach ($aggregate In $aggregates) {
        If ($aggregate.state -ne "online") {
      
            $aggregateOffline += $aggregate.name
        }
    }
    # checking aggr online/offline
    ForEach ($aggregate In $aggregates) {
        If ($aggregate.used -gt 88 -And !($aggregate.Name.Contains("aggr0")) -And !($aggregate.Name.Contains("root"))) {
            $aggregateHighUtil += $aggregate.name
        }
    }
    return $aggregateOffline, $aggregateHighUtil
}
######################################################################################################################
#'Enumerate Volumes.
######################################################################################################################

Function Get-VolumeStatus($cluster) {
    $volumeOffline = @()
    $volumeHighUtil = @()
    $volume_autogrow_disabled = @()
    $volume_snapdelete_enabled = @()
    Try {
     
        Process-cluster $cluster
        $Volumes = Get-Ncvol -ErrorAction Stop
        Write-Log -Info -Message "Enumerated volumes on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating volumes on cluster ""$cluster"""
        [Int]$script:errorCount++
        Break;
    }
    $LUNVolumes = (Get-NcLun).Volume
    foreach ($volume in $Volumes) {
        If ($Volume.state -ne "online") {
         
            $volumeOffline += $Volume.name
        }
        [Int]$percent_used = $Volume.used
        [String]$volume_type = $volume.VolumeIdAttributes.Type
        If ( $percent_used -gt 88 -And !($Volume.Name.Contains("vol0")) -And !($Volume.Name.Contains("root")) -and $volume_type -notcontains "dp") {
            $volumeHighUtil += $Volume.name
        }
        [String]$vol_autogrow_status = $Volume.VolumeAutosizeAttributes.IsEnabled
        If ($vol_autogrow_status -eq "False" -And !($Volume.Name.Contains("vol0")) -And !($Volume.Name.Contains("root")) -and $volume_type -notcontains "dp") {
            $volume_autogrow_disabled += $Volume.Name
        }
        [String]$vol_snap_delete_status = $Volume.VolumeSnapshotAutodeleteAttributes.IsAutodeleteEnabled
        If ($vol_snap_delete_status -eq "True" -And !($Volume.Name.Contains("vol0")) -And !($Volume.Name.Contains("root")) -and $volume_type -notcontains "dp") {
            $volume_snapdelete_enabled += $Volume.Name
        }
    
    } #checking vol online/offline

    return $volumeOffline, $volumeHighUtil, $volume_autogrow_disabled, $volume_snapdelete_enabled
}

######################################################################################################################
#'Enumerate Ethernet Ports.
######################################################################################################################

Function port-status($cluster) {
  
    $portDown = @()
    $portDownlist = @()
    Try {
        Process-cluster $cluster
        $ports = Get-NcNetPort -ErrorAction Stop
        Write-Log -Info -Message "Enumerated Ports for cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating ports for cluster ""$cluster"""
        [Int]$script:errorCount++
        Break;
    }
    $portExceptionPath = "C:\HC_Scripts\Ontappstk\port_exception.txt"
    If (-Not(Test-Path -Path $portExceptionPath)) {
        Write-Log -Error -Message "The File ""$portExceptionPath"" does not exist"
        [Int]$script:errorCount++
        Break;
    }
    Try {
        $portException = Get-Content -Path $portExceptionPath -ErrorAction Stop
        Write-Log -Info -Message "Read file ""$portExceptionPath"""
    }
    Catch {
        Write-Log -Error -Message "Failed reading file ""$portExceptionPath"""
        [Int]$script:errorCount++
        Break;
    }
    foreach ($port in $ports) {
        if ($port.LinkStatus -eq "down") {
          
            $portName = $port.Port
            $portNode = $port.Node
            $exceptionCheck = "$portName is down In $portNode"
            if ($exceptionCheck -notin $portException) {
                $portDownlist += $exceptionCheck
                $portDown += $portName
            }
        }
    }
    return $portDownlist, $portDown
}

######################################################################################################################
#'Enumerate LUNs.
######################################################################################################################

Function LUNs-Status($cluster) {
    $lunOffline = @()
    $lunHighUtil = @()
    Try {
      
        Process-cluster $cluster
        $luns = Get-NcLun -ErrorAction Stop
        Write-Log -Info -Message "Enumerated LUNs on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating LUNs on cluster ""$cluster"""
        [Int]$script:errorCount++
        Break;
    }
    ForEach ($lun In $luns) {
        if ($lun.state -ne "online") {
            $lunOffline += $lun.path
        }
    }
    ForEach ($lun In $luns) {
      
        [Int64]$lunSize = $lun.Size
        [Int64]$lunUsed = $lun.SizeUsed
        [Int64]$lunPercentUsed = [math]::round(($lunUsed / $lunSize) * 100, 0)
        Write-Log -Info -Message "Percent Used ""$lunPercentUsed"""
        if ($lunPercentUsed -gt 90) {
            $lunHighUtil += $lun.path
        }
    }
    return $lunOffline, $lunHighUtil
}

######################################################################################################################
#'Enumerate network interfaces.
######################################################################################################################

Function Interface-Status($cluster) {
    $InterfaceDownlist = @()
    $lifExceptionPath = "C:\HC_Scripts\Ontappstk\lif_exception.txt"
    Try {
        Process-cluster $cluster
        $Interfaces = Get-NcNetInterface -ErrorAction Stop
        Write-Log -Info -Message "Enumerated Network interfaces on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating Network Interfaces on cluster ""$Cluster"""
        [Int]$script:errorCount++
        Break;
    }
    If (-Not(Test-Path -Path $lifExceptionPath)) {
        Write-Log -Error -Message "The File ""$lifExceptionPath"" does not exist"
        [Int]$script:errorCount++
        Break;
    }
    Try {
        $lifException = Get-Content -Path $lifExceptionPath -ErrorAction Stop
        Write-Log -Info -Message "Read file ""$lifExceptionPath"""
    }
    Catch {
        Write-Log -Error -Message "Failed reading file ""$lifExceptionPath"""
        [Int]$script:errorCount++
        Break;
    }
    ForEach ($Interface in $Interfaces) {
      
        If (($Interface.OpStatus) -eq "down") {
            # checking if opstatus is down
            $InterfaceDown = $Interface.InterfaceName
            if ($InterfaceDown -notin $lifException) {
                $InterfaceDownlist += $InterfaceDown
            }
        }
    }
    return $InterfaceDownlist
}

######################################################################################################################
#'Enumerate SnapMirror lag Times.
######################################################################################################################

Function Snapmirror-Status($cluster) {

    $snapmirrorHighLag = @()
    $snapmirrorUnhealthy = @()
    [int]$LagTimeSeconds = 86400 #24 urs In seconds
    Try {
      
        Process-cluster $cluster
        $snapmirrors = Get-NcSnapmirror -ErrorAction Stop
        Write-Log -Info -Message "Enumerated SnapMirror State and  Lag times on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating SnapMirror State and Lag times on cluster ""$cluster"""
        [Int]$script:errorCount++
        Break;
    }
    foreach ($snapmirror in $snapmirrors) {
        [String]$snapmirrored_state = $snapmirror.ishealthy
      
        if ($snapmirrored_state -ne "True") {
          
            $snapmirrorUnhealthy += $snapmirror.SourceLocation
        }
    }
    foreach ($snapmirror in $snapmirrors) {
        [int]$snapmirrorLag = ($snapmirror.LagTime)
      
        if ($snapmirrorLag -gt $LagTimeSeconds) {
          
            $snapmirrorHighLag += $snapmirror.SourceLocation
        }
    }
    return $snapmirrorUnhealthy, $snapmirrorHighLag
}
######################################################################################################################
#'Enumerate the Ifgrp Status.
######################################################################################################################

Function Get-ifgrpStatus($cluster) {
    $Command = "ifgrp show -activeports !full -fields ifgrp"
    $credential = Get-NcCredential -Controller $cluster -ErrorAction Stop
    $SessionID = New-SSHSession -ComputerName $cluster -Credential $credential.Credential #Connect Over SSH
    Try {
        $output = Invoke-SSHCommand -Index $sessionid.sessionid -Command $Command # Invoke Command Over SSH
        Write-Log -Info -Message $("Executed Command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
    }
    Catch {
        Write-Log -Error -Message $("Failed Executing Command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
        [Int]$script:errorCount++
        Break;
    }
    $output = $output.output
    return $output
}
######################################################################################################################
#'Get Vserver
######################################################################################################################

Function Get-vserver($cluster) {
    $vserverNames = @()
    $vserverStates = @()
    Try {
        Process-cluster $cluster
        $vservers = Get-NcVserver -ErrorAction Stop
        Write-Log -Info -Message "Enumerated Vserver on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating Vserver on cluster ""$cluster"""
        $node = "NA"
        [Int]$script:errorCount++
        Break;
    }
    $cserverexception = "admin", "node", "system"
    foreach ($vserver in $vservers) {
      
        $vserverState = $vserver.OperationalState
        $vserverType = $vserver.VserverType
        if ("running" -notin $vserverState -and $vserverType -notin $cserverexception) {
          
            $vserverStates += $vserverState
            $vserverNames += $vserver.VserverName
        }
   
    }
    return $vserverStates, $vserverNames
}
######################################################################################################################
#'Enumerate the Ifgrp Status.
######################################################################################################################

Function Get-acpStatus($cluster) {
    $Command = " acp show -connection-status !full-connectivity,!active -fields node"
    $credential = Get-NcCredential -Controller $cluster -ErrorAction Stop
    $SessionID = New-SSHSession -ComputerName $cluster -Credential $credential.Credential #Connect Over SSH
    Try {
        $output = Invoke-SSHCommand -Index $sessionid.sessionid -Command $Command # Invoke Command Over SSH
        Write-Log -Info -Message $("Executed Command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
    }
    Catch {
        Write-Log -Error -Message $("Failed Executing Command`: """ + $([String]::Join(" ", $command)) + """ on cluster ""$cluster""")
        [Int]$script:errorCount++
        Break;
    }
    $output = $output.output
    return $output
}
######################################################################################################################

#'Get Service Processor Status

######################################################################################################################


Function Get-SPStatus($cluster) {

    $SPDownNode = @()

    Try {
        Process-cluster $cluster
        $service_processors = Get-NcServiceProcessor -ErrorAction Stop
        Write-Log -Info -Message "Enumerated Service Processor on cluster ""$cluster"""

    }
    Catch {
        Write-Log -Error -Message "Failed enumerating Service Processor on cluster ""$cluster"""
        $node = "NA"
        [Int]$script:errorCount++
    }
    foreach ($service_processor in $service_processors) {
        $sp_status = $service_processor.Status
        [String]$sp_type = $service_processor.Type
        if ($sp_status -contains "unknown" -and $sp_type -ne $null) {
            $SPDownNode += "NA"
        }
        elseif ($sp_status -notcontains "online") {
            $SPDownNode += $service_processor.node
        }
    }
    return $SPDownNode
}
######################################################################################################################
#'Get Config Backups
######################################################################################################################

Function Get-configBackup($cluster) {
    $configBackup_names = @()
    $date_now = Get-Date -uformat "%y-%m-%d"
    $cluster_name = Cluster-Name $cluster
    $cfg_backup_name = "$cluster_name.daily.20$date_now.*.7z"
    Try {
        Process-cluster $cluster
        $configBackups = Get-NcConfigBackup  -Name $cfg_backup_name -ErrorAction Stop
        Write-Log -Info -Message "Enumerated Config Backup on cluster ""$cluster"""
    }
    Catch {
        Write-Log -Error -Message "Failed enumerating Config Backup on cluster ""$cluster"""
        $node = "NA"
        [Int]$script:errorCount++

    }
    $cfgBkpCount = $configBackups.count
    foreach ($configBackup in $configBackups) {
        $configBackup_names += $configBackup.BackupName
    }
    $configBackup_names = $configBackup_names | Get-Unique
    return $cfgBkpCount, $configBackup_names
}
######################################################################################################################
#'Enumerate Cluster tables1
######################################################################################################################
Function Ontap-Data1($cluster) {
  
    $noErrorMsg = "There are no entries matching your query."
    $cluster_name = Cluster-Name $cluster
    $cluster_version = Get-Clusterimage $cluster
    $subsystems = Get-EnvStatus $cluster
    $subsystems = $subsystems.trim()
    $failed_subsystem_table = ""
    if ($subsystems.Contains($noErrorMsg)) {
        $subsystem_status = "<TD bgcolor=#33FFBB> Subsystem: Ok </TD>"
    }
    else {
        foreach ($subsystem in $subsystems) {
            if ($subsystem.contains("--") -or $subsystem.contains("entries were displayed")) {
            }
            else {
                $failed_subsystem_table += "<TR><TD bgcolor=#FA8074s>$subsystem</TD></TR>"
            }
        }
        $subsystem_status = @"
  <TD bgcolor=#FA8074>
      <button type="button" class="collapsible"> Subsystem: Fault </button>
      <div class="errorContent">
      <table>
      $failed_subsystem_table
      </table>
      </div>
  </TD>
"@
    }
    $chassies = Get-ChassisStatus $cluster
    $chassies = $chassies.trim()
    if ($chassies.Contains($noErrorMsg)) {
        $chassis_status = "<TD bgcolor=#33FFBB> Chassis: Ok </TD>"
    }
    else {
        foreach ($chassis in $chassies) {
            if ($chassis.contains("--") -or $chassis.contains("entries were displayed")) {
            }
            else {
                $failed_chassis_table += "<TR><TD bgcolor=#FA8074s>$chassis</TD></TR>"
            }
        }
        $chassis_status = @"
  <TD bgcolor=#FA8074>
      <button type="button" class="collapsible"> Subsystem: Fault </button>
      <div class="errorContent">
      <table>
      $failed_chassis_table
      </table>
      </div>
  </TD>
"@
    }
    [Int]$failedDiskCount = (Failed-Disk $cluster).count
    if ($failedDiskCount -gt 0) {
        $failedDisks = (Failed-Disk $cluster).Name
        $failedDisk_status = "<TD bgcolor=#FA8074> Failed Disk: $failedDiskCount<BR>$failedDisks</TD>"
    }
    else {
        $failedDisk_status = "<TD bgcolor=#33FFBB>Failed Disk: Ok </TD>"
    }
    $hw_status = @"
  <TD>
  <table>
      <TR>
          $subsystem_status
      </TR>
      <TR>
          $chassis_status
      </TR>
      <TR>
          $failedDisk_status
      </TR>
  </table>
  </TD>
"@
    $clusterHealth = Cluster-Health $cluster
    $clusterHealth = $clusterHealth.trim()
    if ($clusterHealth.Contains($noErrorMsg)) {
        $cluster_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    else {
        $cluster_status = "<TD bgcolor=#FA8074> Degraded </TD>"
    }
    $aggregateOfflineTable = "<TR><TH>Offline Aggregates</TH></TR>"
    $aggregateHighUtilTable = "<TR><TH>Aggregates > 88% </TH></TR>"
    $aggregateOffline, $aggregateHighUtil = aggregate-status $cluster
    [Int]$aggregateOffline_count = $aggregateOffline.count
    [Int]$aggregateHighUtil_count = $aggregateHighUtil.count
    if ($aggregateOffline_count -eq 0 -and $aggregateHighUtil_count -eq 0) {
        $aggregate_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    elseif ($aggregateOffline_count -eq 0 -and $aggregateHighUtil_count -ne 0) {
        foreach ($aggr in $aggregateHighUtil) {
            $aggregateHighUtilTable += "<TR><TD bgcolor=#FA8074>$aggr</TD></TR>"
        }
        $aggregate_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> Aggregate > 88%: $aggregateHighUtil_count </button>
          <div class="errorContent">
          <table>
          $aggregateHighUtilTable
          </table>
          </div>
      </TD>
"@
    }
    elseif ($aggregateOffline_count -ne 0 -and $aggregateHighUtil_count -eq 0) {
        foreach ($aggr in $aggregateOffline) {
            $aggregateOfflineTable += "<TR><TD bgcolor=#FA8074>$aggr</TD></TR>"
        }
        $aggregate_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> Aggregate Offline: $aggregateOffline_count </button>
          <div class="errorContent">
          <table>
          $aggregateOfflineTable
          </table>
          </div>
      </TD>
"@
    }
    else {
        foreach ($aggr in $aggregateHighUtil) {
            $aggregateHighUtilTable += "<TR><TD bgcolor=#FA8074>$aggr</TD></TR>"
        }
        foreach ($aggr in $aggregateOffline) {
            $aggregateOfflineTable += "<TR><TD bgcolor=#FA8074>$aggr</TD></TR>"
        }
        $aggregate_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> Aggregate Offline: $aggregateOffline_count :: Aggregate >88%: $aggregateHighUtil_count </button>
          <div class="errorContent">
          <table>
          $aggregateOfflineTable
          $aggregateHighUtilTable
          </table>
          </div>
      </TD>
"@           
    }
    $nodeList, $spareList = Spare-Disk $cluster
    $spare_status = ""
    for ($i = 0; $i -lt $nodeList.count; $i++) {
      
        $node = $nodeList[$i]
        [Int]$spares = $spareList[$i]
        if ($spares -lt 1) {
            $spare_stat += "<TR><TD> $node : $spares </TD></TR>"
        }
        else {
            $spare_stat += "<TR><TD> $node : $spares </TD></TR>"
        }
    }
    $spare_status = @"
  <TD>
  <table>
      <TR>
          $spare_stat
      </TR>
  </table>
  </TD>
"@
    $volumeOffline, $volumeHighUtil, $volume_autogrow_disabled, $volume_snapdelete_enabled = Get-VolumeStatus $cluster
    $volumeOfflineTable = "<TR><TH>Offline Volumes</TH></TR>"
    $volumeHighUtilTable = "<TR><TH>Volumes > 88% </TH></TR>"
    [Int]$volumeOffline_count = $volumeOffline.count
    [Int]$volumeHighUtil_count = $volumeHighUtil.count
    if ($volumeOffline_count -eq 0 -and $volumeHighUtil_count -eq 0) {
        $volume_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    elseif ($volumeOffline_count -eq 0 -and $volumeHighUtil_count -ne 0) {
        foreach ($vol in $volumeHighUtil) {
            $volumeHighUtilTable += "<TR><TD bgcolor=#FA8074>$vol</TD></TR>"
        }
        $volume_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> Volume > 88%: $volumeHighUtil_count </button>
          <div class="errorContent">
          <table>
          $volumeHighUtilTable
          </table>
          </div>
      </TD>
"@
    }
    elseif ($volumeOffline_count -ne 0 -and $volumeHighUtil_count -eq 0) {
        foreach ($vol in $volumeOffline) {
            $volumeOfflineTable += "<TR><TD bgcolor=#FA8074>$vol</TD></TR>"
        }
        $volume_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> Volume Offline: $volumeOffline_count </button>
          <div class="errorContent">
          <table>
          $volumeOfflineTable
          </table>
          </div>
      </TD>
"@
    }
    else {
        foreach ($vol in $volumeHighUtil) {
            $volumeHighUtilTable += "<TR><TD bgcolor=#FA8074>$vol</TD></TR>"
        }
        foreach ($vol in $volumeOffline) {
            $volumeOfflineTable += "<TR><TD bgcolor=#FA8074>$vol</TD></TR>"
        }
        $volume_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> Volume Offline: $volumeOffline_count :: Volume >88%: $volumeHighUtil_count </button>
          <div class="errorContent">
          <table>
          $volumeOfflineTable
          $volumeHighUtilTable
          </table>
          </div>
      </TD>
"@           
    }
    $volume_autogrow_disabled_count = $volume_autogrow_disabled.count
    $volume_snapdelete_enabled_count = $volume_snapdelete_enabled.count
    $volume_autogrow_disabled_table = "<TR><TH>Autogrow Disabled</TH></TR>"
    $volume_snapdelete_enabled_table = "<TR><TH>Auto Snapdelte Enabled</TH></TR>"
    if ($volume_autogrow_disabled_count -eq 0) {
        $volume_autogrow_disabled_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    else {
        foreach ($vol_atg_dis in $volume_autogrow_disabled) {
            $volume_autogrow_disabled_table += "<TR><TD bgcolor=#FA8074>$vol_atg_dis</TD></TR>"
        }
        $volume_autogrow_disabled_status = @"
     <TD bgcolor=#FA8074>
         <button type="button" class="collapsible"> Autogrow Status </button>
         <div class="errorContent">
         <table>
         $volume_autogrow_disabled_table
         </table>
         </div>
     </TD>
"@
    }
    if ($volume_snapdelete_enabled_count -eq 0) {
        $volume_snapdelete_enabled_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    else {
        foreach ($vol_asd_enb in $volume_snapdelete_enabled) {
            $volume_snapdelete_enabled_table += "<TR><TD bgcolor=#FA8074>$vol_asd_enb</TD></TR>"
        }
        $volume_snapdelete_enabled_status = @"
     <TD bgcolor=#FA8074>
         <button type="button" class="collapsible"> Auto Snapdelete Status </button>
         <div class="errorContent">
         <table>
         $volume_snapdelete_enabled_table
         </table>
         </div>
     </TD>
"@
    }

  
    $node_names = (Get-ClusterNodes $cluster).node
    $portDownlist, $portDown = port-status $cluster
    $port_count = $portDown.count
    foreach ($node_name in $node_names) {
        $portDownTable = "<TR><TH>Ports Down</TH></TR>"
        $portDown_count = 0
        if ($port_count -gt 0) {
            for ($i = 0; $i -lt $port_count; $i++) {
                if ($portDownlist[$i].Contains($node_name)) {
                  
                    $portDown_count++
                    $port = $portDown[$i]
                    $portDownTable += "<TR><TD bgcolor=#FA8074> $port </TD></TR>"
                }
            }
            $port_stat += @"
          <TR>
          <TD bgcolor=#FA8074>
              <button type="button" class="collapsible"> $node_name : $portDown_count Ports Down </button>
              <div class="errorContent">
              <table>
                  $portDownTable
              </table>
              </div>
          </TD>
          </TR>
"@      
        }
        else {
            $port_stat += "<TR><TD bgcolor=#33FFBB> $node_name : Ok </TD></TR>"
        }
    }
    $port_status = @"
  <TD>
  <table>
      <TR>
          $port_stat
      </TR>
  </table>
  </TD>
"@
    $InterfaceDown = Interface-Status $cluster
    $interfaceDownCount = $InterfaceDown.count
    $interfaceDownTable = "<TR><TH>LIFs Down</TH></TR>"
    if ($interfaceDownCount -eq 0) {
        $interface_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    else {
        foreach ($interface in $InterfaceDown) {
            $interfaceDownTable += "<TR><TD bgcolor=#FA8074> $interface </TD></TR>"
        }
        $interface_status = @"
          <TD bgcolor=#FA8074>
              <button type="button" class="collapsible"> $interfaceDownCount LIFs Down </button>
              <div class="errorContent">
              <table>
                  $interfaceDownTable
              </table>
              </div>
          </TD>
"@
    }
    $snapmirrorUnhealthy, $snapmirrorHighLag = Snapmirror-Status $cluster
    $snapmirrorUnhealthyCount = $snapmirrorUnhealthy.count
    $snapmirrorHighLagCount = $snapmirrorHighLag.count
    $snapmirrorUnhealthyTable = "<TR><TH> Unhealthy Snapmirror </TH></TR>"
    $snapmirrorHighLagTable = "<TR><TH> Snapmirrorlag > 24hr </TH></TR>"
    if ($snapmirrorUnhealthyCount -eq 0 -and $snapmirrorHighLagCount -eq 0) {
        $snapmirror_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    elseif ($snapmirrorUnhealthyCount -eq 0 -and $snapmirrorHighLagCount -ne 0) {
        foreach ($mirror in $snapmirrorHighLag) {
            $snapmirrorHighLagTable += "<TR><TD bgcolor=#FA8074>$mirror</TD></TR>"
        }
        $snapmirror_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> Snapmirrorlag > 24hr: $snapmirrorHighLagCount </button>
          <div class="errorContent">
          <table>
          $snapmirrorHighLagTable
          </table>
          </div>
      </TD>
"@
    }
    elseif ($snapmirrorUnhealthyCount -ne 0 -and $snapmirrorHighLagCount -eq 0) {
        foreach ($mirror in $snapmirrorUnhealthy) {
            $snapmirrorUnhealthyTable += "<TR><TD bgcolor=#FA8074>$mirror</TD></TR>"
        }
        $snapmirror_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> Unhealthy Snapmirror: $snapmirrorUnhealthyCount </button>
          <div class="errorContent">
          <table>
          $snapmirrorUnhealthyTable
          </table>
          </div>
      </TD>
"@
    }
    else {
        foreach ($mirror in $snapmirrorHighLag) {
            $snapmirrorHighLagTable += "<TR><TD bgcolor=#FA8074>$mirror</TD></TR>"
        }
        foreach ($mirror in $snapmirrorUnhealthy) {
            $snapmirrorUnhealthyTable += "<TR><TD bgcolor=#FA8074>$mirror</TD></TR>"
        }
        $snapmirror_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> Unhealthy Snapmirror: $snapmirrorUnhealthyCount :: Snapmirrorlag > 24hr: $snapmirrorHighLagCount </button>
          <div class="errorContent">
          <table>
          $snapmirrorUnhealthyTable
          $snapmirrorHighLagTable
          </table>
          </div>
      </TD>
"@           
    }
    $cluster_report_data = @"
      <TR>
          <TD>$cluster_name</TD>
          <TD>$cluster_version</TD>
          $hw_status
          $cluster_status
          $aggregate_status
          $spare_status
          $volume_status
          $volume_autogrow_disabled_status
          $port_status
          $interface_status
          $snapmirror_status
      </TR>
"@
    return $cluster_report_data
}

######################################################################################################################
#'Enumerate Cluster table2 data
######################################################################################################################
Function Ontap-Data2($cluster) {
  
    $noErrorMsg = "There are no entries matching your query."
    $cluster_name = Cluster-Name $cluster
    $ifgrps = Get-ifgrpStatus $cluster
    $ifgrps = $ifgrps.trim()
    $failed_ifgrps_table = ""
    if ($ifgrps.Contains($noErrorMsg)) {
        $ifgrps_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    else {
        foreach ($ifgrp in $ifgrps) {
            if ($ifgrp.contains("--") -or $ifgrp.contains("entries were displayed")) {
            }
            else {
                $failed_ifgrps_table += "<TR><TD bgcolor=#FA8074>$ifgrp</TD></TR>"
            }
        }
        $ifgrps_status = @"
  <TD bgcolor=#FA8074>
      <button type="button" class="collapsible"> IFGRP: Degraded </button>
      <div class="errorContent">
      <table>
      $failed_ifgrps_table
      </table>
      </div>
  </TD>
"@
    }
    $vserverStates, $vserverNames = Get-vserver $cluster
    $vserverStatesCount = $vserverStates.count
    if ($vserverStatesCount -gt 0) {
        for ($i = 0; $i -lt $vserverStatesCount; $i++) {
            $vserverName = $vserverNames[$i]
            $vserverState = $vserverStates[$i]
            if ($vserverState -ne $null) {
                $vserver_stat += "<TR><TD bgcolor=#FA8074>$vserverName State: $vserverState </TD></TR>"
            }
            else {
                $vserver_stat += "<TR><TD bgcolor=#FA8074>$vserverName State: NA </TD></TR>"            
            }
        }
        $vserver_status = @"
  <TD>
  <table>
  $vserver_stat
  </table>
  </TD>
"@
    }
    else {
        $vserver_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    $LUNOffline, $LUNHighUtil = LUNs-Status $cluster
    $LUNOfflineTable = "<TR><TH>Offline LUNs</TH></TR>"
    $LUNHighUtilTable = "<TR><TH>LUNs > 90% </TH></TR>"
    [Int]$LUNOffline_count = $LUNOffline.count
    [Int]$LUNHighUtil_count = $LUNHighUtil.count
    if ($LUNOffline_count -eq 0 -and $LUNHighUtil_count -eq 0) {
        $LUN_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    elseif ($LUNOffline_count -eq 0 -and $LUNHighUtil_count -ne 0) {
        foreach ($lun in $LUNHighUtil) {
            $LUNHighUtilTable += "<TR><TD bgcolor=#FA8074>$lun</TD></TR>"
        }
        $LUN_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> LUNs > 90%: $LUNHighUtil_count </button>
          <div class="errorContent">
          <table>
          $LUNHighUtilTable
          </table>
          </div>
      </TD>
"@
    }
    elseif ($LUNOffline_count -ne 0 -and $LUNHighUtil_count -eq 0) {
        foreach ($lun in $LUNOffline) {
            $LUNOfflineTable += "<TR><TD bgcolor=#FA8074>$lun</TD></TR>"
        }
        $LUN_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> LUNs Offline: $LUNOffline_count </button>
          <div class="errorContent">
          <table>
          $LUNOfflineTable
          </table>
          </div>
      </TD>
"@
    }
    else {
        foreach ($lun in $LUNHighUtil) {
            $LUNHighUtilTable += "<TR><TD bgcolor=#FA8074>$lun</TD></TR>"
        }
        foreach ($lun in $LUNOffline) {
            $LUNOfflineTable += "<TR><TD bgcolor=#FA8074>$lun</TD></TR>"
        }
        $LUN_status = @"
      <TD bgcolor=#FA8074>
          <button type="button" class="collapsible"> LUNs Offline: $LUNOffline_count :: LUNs >90%: $LUNHighUtil_count </button>
          <div class="errorContent">
          <table>
          $LUNOfflineTable
          $LUNHighUtilTable
          </table>
          </div>
      </TD>
"@           
    }
    $acps = Get-acpStatus $cluster
    $acps = $acps.trim()
    $failed_acps_table = ""
    if ($acps.Contains($noErrorMsg)) {
        $acps_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    else {
        foreach ($acp in $acps) {
            if ($acp.contains("--") -or $acp.contains("entries were displayed")) {
            }
            else {
                $failed_acps_table += "<TR><TD bgcolor=#FA8074>$acp</TD></TR>"
            }
        }
        $acps_status = @"
  <TD bgcolor=#FA8074>
      <button type="button" class="collapsible"> ACP: Degraded </button>
      <div class="errorContent">
      <table>
      $failed_acps_table
      </table>
      </div>
  </TD>
"@
    }
    $SPDownNode = Get-SPStatus $cluster
    $SPDownCount = $SPDownNode.count
    $SPDownNodeTable = "<TR><TH>Offline SP Node</TH></TR>"

    if ($SPDownNode -ne $null) {
        if ($SPDownNode -notcontains "NA") {
            foreach ($SPDN in $SPDownNode) {
                $SPDownNodeTable += "<TR><TD bgcolor=#FA8074>$SPDN</TD></TR>"
            }
            $sp_status = @"
     <TD bgcolor=#FA8074>
         <button type="button" class="collapsible"> $SPDownCount SP Down </button>
         <div class="errorContent">
         <table>
         $SPDownNodeTable
         </table>
         </div>
     </TD>
"@
        }
        else {
            $sp_status = "<TD bgcolor=#EFF613> Not Present </TD>"
        }

    }
    else {
        $sp_status = "<TD bgcolor=#33FFBB> Ok </TD>"
    }
    $cfgBkpCount, $configBackup_names = Get-configBackup $cluster
    $node_count = (Get-ClusterNodes $cluster).count
    if ($node_count -eq $cfgBkpCount) {
        $cfg_backup_status = "<TD bgcolor=#33FFBB> Last backup: $configBackup_names </TD>"
    }
    else {
        $cfg_backup_status = "<TD bgcolor=#FA8074> Backup count Mis-Match </TD>"
    }
    $cluster_report_data = @"
      <TR>
          <TD>$cluster_name</TD>
          $ifgrps_status
          $vserver_status
          $LUN_status
          $acps_status
          $sp_status
          $autosupport_status
          $cfg_backup_status
      </TR>
"@
    return $cluster_report_data
}
Function Cluster-ReportTable($clusters) {
  
    foreach ($cluster in $clusters) {
        [String]$ontap_data_1_dt += Ontap-Data1 $cluster
        [String]$ontap_data_2_dt += Ontap-Data2 $cluster
    }   
    $cluster_report_body = @"
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
              <TH><B> Vol AutoGrow Status </B></TH>
              <TH><B> Port Status </B></TH>
              <TH><B> LIF status </B></TH>
              <TH><B> Snapmirror Status </B></TH>
          </TR>
          $ontap_data_1_dt
      </Table>
  <h3 style='color : #464A46; font-size : 21px' align="" left ""> Ontap  - Part2 </h3>
  </caption>
      <Table>
          <TR>
              <TH><B> Cluster Name </B></TH>
              <TH><B> Ifgrp Status </B></TH>
              <TH><B> Vserver Status </B></TH>
              <TH><B> LUN Status </B></TH>
              <TH><B> ACP Status </B></TH>
              <TH><B> SP Status </B></TH>
              <TH><B> Cluster Config Bkp </B></TH>
          </TR>
          $ontap_data_2_dt
      </Table>
  </div>
"@
    return $cluster_report_body
}

######################################################################################################################

#'Send Email

######################################################################################################################

Function mail-Mod($outfile, $htmlOut) {

    $date = get-date

    $day = $date.Day

    $month = $date.Month

    $year = $date.Year

    $From = "Allianz.InfraHCreport@nmsintsmtprelay.netapp.com"

    $To = "ng-AllianzMS@netapp.com"

    $Attachment = $outfile

    $Subject = "Allianz Infrastructure Heath-Check Report"

    $msgBody = "Please find attached report"

    $SMTPServer = "172.27.96.27"

    Send-MailMessage -From $From -to $To -Subject $Subject -Body $msgBody -BodyAsHtml -SmtpServer $SMTPServer -Attachments $Attachment

}

######################################################################################################################

#'Delete reports more than 30 Days

######################################################################################################################

Function delete-OldFiles() {

    # Delete all Files in C:\temp older than 30 day(s)
    $Path = "C:\HC_Scripts\Ontappstk\storage_report_output"
    $Daysback = "-30"

    $CurrentDate = Get-Date
    $DatetoDelete = $CurrentDate.AddDays($Daysback)
    Get-ChildItem $Path | Where-Object { $_.LastWriteTime -lt $DatetoDelete } | Remove-Item
}

$current_time = Get-IsoDateTime
$current_date = Get-IsoDate
$htmlOut = HTML-Body $current_time $current_date
Set-Content -Path $outfile -Value $htmlOut
delete-OldFiles
mail-Mod $outfile $htmlOut
#######################################################################################################################