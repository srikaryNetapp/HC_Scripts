
Set-Location "C:\HC_Scripts\"
#star-process C:\Users\Administrator\AppData\Local\Programs\Python\Python39\python.exe "./infra_main.py" -wait

$filelocation = "C:\HC_Scripts\Output\InfraHC.html"
Function mail-Mod() {

    

    $From = "Allianz.InfraHCreport@allianz.com.au"

    $To = "ng-AllianzMS@netapp.com"
    #$To = "kprathyu@netapp.com"

    $Attachment = $filelocation
    $Subject = "Allianz Infrastructure Heath-Check Report"

    $msgBody = "Please find attached report"

    $SMTPServer = "10.90.36.17"

    Send-MailMessage -From $From -to $To -Subject $Subject -Body $msgBody -BodyAsHtml -SmtpServer $SMTPServer -Attachments $Attachment

    Write-Host "Report Sent"

}
mail-Mod