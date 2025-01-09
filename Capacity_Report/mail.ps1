set-location "C:\Capacity_Report\"
[String]$htmlbody = C:\Users\Administrator\AppData\Local\Programs\Python\Python39\python.exe "C:\Capacity_Report\vol_report.py" -Wait
$outfile = "C:\Capacity_Report\volume_data.xlsx"

Function mail-Mod($htmlbody) {


    $From = "daily-aggr-capacity@allianz.com.au"

    $To = "appam.madhu@netapp.com","kprathyu@netapp.com"

    $Attachment = $outfile

    $Subject = "Allianz Capacity Report - All Volume"

    $msgBody = $htmlbody

    $SMTPServer = "10.90.36.17"

    Send-MailMessage -From $From -to $To -Subject $Subject -Body $msgBody -BodyAsHtml -SmtpServer $SMTPServer

}
mail-Mod($htmlbody)

