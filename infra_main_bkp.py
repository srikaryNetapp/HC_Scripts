import switchhc
import storagesc
import datetime
import json
import sys
import subprocess
#######################################
#   HTML Header and CSS
#######################################

def css_genarator(cluster_names, cluster_nodes):
    css_gen = ""
    css_gen1 = ""
    css_gen2 = ""
    hover_var_list = []
    trg_var_list = []
    pop_button = """
.popupCloseButton {
    background-color: #fff;
    border: 3px solid #999;
    border-radius: 15px;
    cursor: pointer;
    display: inline-block;
    font-family: arial;
    font-weight: bold;
    position: absolute;
    top: -10px;
    right: -10px;
    font-size: 20px;
    line-height: 15px;
    width: 15px;
    height: 15px;
    text-align: center;
}

.popupCloseButton:hover {
    background-color: #ccc;
}   
@-webkit-keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}
            """
    hv = """
    background: rgba(0, 0, 0, 0.4);
    cursor: pointer;
    display: none;
    height: fit-content;
    width: fit-content;
    text-align: center;
    top: 0;
    z-index: 10000;
    -webkit-animation: fadeIn 1s;
    animation: fadeIn 1s;
}    
"""
    hv_help = """
    display: inline-block;
    height: fit-content;
    width: fit-content;
    vertical-align: middle;
}
"""
    hv_div = """
    background-color: #fff;
    box-shadow: 10px 10px 60px #555;
    display: inline-block;
    height: fit-content;
    vertical-align: middle;
    width: fit-content;
    position: relative;
    border-radius: 8px;
    padding: 15px 5%;
    -webkit-animation: fadeIn 1s;
    animation: fadeIn 1s;
}
            """
    trig_val = """
    cursor: pointer;
    font-size: 14px;
    margin: 14px;
    display: inline-block;
}
            """
    for cluster in cluster_names:
        for css_comp in css_comps:
            hover_var = f"""hover_bkgr_{cluster}_{css_comp}"""
            bace_open = "{"
            hover_var_list += [hover_var]
            hover_var_brace = hover_var+bace_open
            trg_var = f"trigger_popup_{cluster}_{css_comp}"
            trg_var_list += [trg_var]
            css_gen1 += f"""
.{hover_var_brace}{hv}
.{hover_var} .helper{bace_open}{hv_help}
.{hover_var}>div{bace_open}{hv_div}
.{trg_var+bace_open}{trig_val}
            """
        node_count = len(cluster_nodes[cluster])
        for i in range(0,node_count):
            node = cluster_nodes[cluster][i]
            for css_node_comp in css_node_comps:
                hover_node_var = f"""hover_bkgr_{cluster}_{node}_{css_node_comp}"""
                bace_open = "{"
                hover_var_list += [hover_node_var]
                hover_var_brace = hover_node_var+bace_open
                trg_node_var = f"trigger_popup_{cluster}_{node}_{css_node_comp}"
                trg_var_list += [trg_node_var]
                css_gen2 += f"""
.{hover_var_brace}{hv}
.{hover_node_var} .helper{bace_open}{hv_help}
.{hover_node_var}>div{bace_open}{hv_div}
.{trg_node_var+bace_open}{trig_val}
            """
    css_gen = css_gen1+css_gen2+pop_button      
    return (css_gen, hover_var_list, trg_var_list)

def script_generator(hover_var_list, trg_var_list):
    script_var = ""
    open_baces = " {"
    close_braces = "});"
    for i in range(0, len(hover_var_list)):
        click_show = f'$(".{trg_var_list[i]}").click(function()'
        click_hide = f'$(".{hover_var_list[i]}").click(function()'
        show_f = f'$(".{hover_var_list[i]}").show();'
        hide_f = f'$(".{hover_var_list[i]}").hide();'
        script_var += f"""
    $(window).load(function(){open_baces}
        {click_show}{open_baces}
            {show_f}
        {close_braces}
        {click_hide}{open_baces}
            {hide_f}
        {close_braces}
        $(".popupCloseButton").click(function(){open_baces}
            {hide_f}
        {close_braces}
    {close_braces}             
        """
    script = f"""
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
        <script>
        {script_var}
        </script>
        <script src="https://www.google.com/jsapi"></script>
    """
    return (script)


def html_header_templat(current_time, date, storage_hc_body, vmware_hc_body, switch_hc_body, css_gen, jq_script):
    """
    Define CSS for the HTML report
    Add the HTML header

    """
    css = """
    @import "https://fonts.googleapis.com/css?family=Montserrat:400,700|Raleway:300,400";

    /* colors */


    /* tab setting */


    /* breakpoints */


    /* selectors relative to radio inputs */

    html {
        width: 100%;
        height: 100%;
        position: relative;
    }

    body {
        background: #efefef;
        color: #333;
        font-family: "Raleway";
        height: fit-content;
        width: fit-content;
        font-size: 12px;
        padding: 30px;
    }

    body h1 {
        text-align: center;
        color: #428BFF;
        font-weight: 300;
        padding: 40px 0 20px 0;
        margin: 0;
    }

    .tabs {
        left: 50%;
        -webkit-transform: translateX(-50%);
        transform: translateX(-50%);
        position: relative;
        background: white;
        padding: 50px;
        padding-bottom: 80px;
        width: fit-content;
        height: fit-content;
        box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
        border-radius: 5px;
        min-width: 90%;
    }

    .tabs input[name="tab-control"] {
        display: none;
    }

    .tabs .content section h2,
    .tabs ul li label {
        font-family: "Montserrat";
        font-weight: bold;
        font-size: 18px;
        color: #428BFF;
    }

    .tabs ul {
        list-style-type: none;
        padding-left: 0;
        display: -webkit-box;
        display: flex;
        -webkit-box-orient: horizontal;
        -webkit-box-direction: normal;
        flex-direction: row;
        margin-bottom: 10px;
        -webkit-box-pack: justify;
        justify-content: space-between;
        -webkit-box-align: end;
        align-items: flex-end;
        flex-wrap: wrap;
    }

    .tabs ul li {
        box-sizing: border-box;
        -webkit-box-flex: 1;
        flex: 1;
        width: fit-content;
        padding: 0 10px;
        text-align: center;
    }

    .tabs ul li label {
        -webkit-transition: all 0.3s ease-in-out;
        transition: all 0.3s ease-in-out;
        color: #929daf;
        padding: 5px auto;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
        cursor: pointer;
        -webkit-transition: all 0.2s ease-in-out;
        transition: all 0.2s ease-in-out;
        white-space: nowrap;
        -webkit-touch-callout: none;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }

    .tabs ul li label br {
        display: none;
    }

    .tabs ul li label svg {
        fill: #929daf;
        height: 1.2em;
        vertical-align: bottom;
        margin-right: 0.2em;
        -webkit-transition: all 0.2s ease-in-out;
        transition: all 0.2s ease-in-out;
    }

    .tabs ul li label:hover,
    .tabs ul li label:focus,
    .tabs ul li label:active {
        outline: 0;
        color: #bec5cf;
    }

    .tabs ul li label:hover svg,
    .tabs ul li label:focus svg,
    .tabs ul li label:active svg {
        fill: #bec5cf;
    }

    .tabs .slider {
        position: relative;
        width: 33.3333333333%;
        -webkit-transition: all 0.33s cubic-bezier(0.38, 0.8, 0.32, 1.07);
        transition: all 0.33s cubic-bezier(0.38, 0.8, 0.32, 1.07);
    }

    .tabs .slider .indicator {
        position: relative;
        width: 50px;
        max-width: 100%;
        margin: 0 auto;
        height: 4px;
        background: #428BFF;
        border-radius: 1px;
    }

    .tabs .content {
        margin-top: 30px;
    }

    .tabs .content section {
        display: none;
        -webkit-animation-name: content;
        animation-name: content;
        -webkit-animation-direction: normal;
        animation-direction: normal;
        -webkit-animation-duration: 0.3s;
        animation-duration: 0.3s;
        -webkit-animation-timing-function: ease-in-out;
        animation-timing-function: ease-in-out;
        -webkit-animation-iteration-count: 1;
        animation-iteration-count: 1;
        line-height: 1.4;
        width: fit-content;
    }

    .tabs .content section h2 {
        color: #428BFF;
        display: none;
        width: fit-content;
    }

    .tabs .content section h2::after {
        content: "";
        position: relative;
        display: block;
        width: 30px;
        height: 3px;
        background: #428BFF;
        margin-top: 5px;
        left: 1px;
        width: fit-content;
    }

    .tabs input[name="tab-control"]:nth-of-type(1):checked~ul>li:nth-child(1)>label {
        cursor: default;
        color: #428BFF;
    }

    .tabs input[name="tab-control"]:nth-of-type(1):checked~ul>li:nth-child(1)>label svg {
        fill: #428BFF;
    }

    @media (max-width: 450px) {
        .tabs input[name="tab-control"]:nth-of-type(1):checked~ul>li:nth-child(1)>label {
            background: rgba(0, 0, 0, 0.08);
        }
    }

    .tabs input[name="tab-control"]:nth-of-type(1):checked~.slider {
        -webkit-transform: translateX(0%);
        transform: translateX(0%);
    }

    .tabs input[name="tab-control"]:nth-of-type(1):checked~.content>section:nth-child(1) {
        display: block;
    }

    .tabs input[name="tab-control"]:nth-of-type(2):checked~ul>li:nth-child(2)>label {
        cursor: default;
        color: #428BFF;
    }

    .tabs input[name="tab-control"]:nth-of-type(2):checked~ul>li:nth-child(2)>label svg {
        fill: #428BFF;
    }

    @media (max-width: 450px) {
        .tabs input[name="tab-control"]:nth-of-type(2):checked~ul>li:nth-child(2)>label {
            background: rgba(0, 0, 0, 0.08);
        }
    }

    .tabs input[name="tab-control"]:nth-of-type(2):checked~.slider {
        -webkit-transform: translateX(100%);
        transform: translateX(100%);
    }

    .tabs input[name="tab-control"]:nth-of-type(2):checked~.content>section:nth-child(2) {
        display: block;
    }

    .tabs input[name="tab-control"]:nth-of-type(3):checked~ul>li:nth-child(3)>label {
        cursor: default;
        color: #428BFF;
    }

    .tabs input[name="tab-control"]:nth-of-type(3):checked~ul>li:nth-child(3)>label svg {
        fill: #428BFF;
    }

    @media (max-width: 450px) {
        .tabs input[name="tab-control"]:nth-of-type(3):checked~ul>li:nth-child(3)>label {
            background: rgba(0, 0, 0, 0.08);
        }
    }

    .tabs input[name="tab-control"]:nth-of-type(3):checked~.slider {
        -webkit-transform: translateX(200%);
        transform: translateX(200%);
    }

    .tabs input[name="tab-control"]:nth-of-type(3):checked~.content>section:nth-child(3) {
        display: block;
    }

    @-webkit-keyframes content {
        from {
            opacity: 0;
            -webkit-transform: translateY(5%);
            transform: translateY(5%);
        }
        to {
            opacity: 1;
            -webkit-transform: translateY(0%);
            transform: translateY(0%);
        }
    }

    @keyframes content {
        from {
            opacity: 0;
            -webkit-transform: translateY(5%);
            transform: translateY(5%);
        }
        to {
            opacity: 1;
            -webkit-transform: translateY(0%);
            transform: translateY(0%);
        }
    }

    @media (max-width: 750px) {
        .tabs ul li label {
            white-space: initial;
        }
        .tabs ul li label br {
            display: initial;
        }
        .tabs ul li label svg {
            height: 1.5em;
        }
    }

    @media (max-width: 450px) {
        .tabs ul li label {
            padding: 5px;
            border-radius: 5px;
        }
        .tabs ul li label span {
            display: none;
        }
        .tabs .slider {
            display: none;
        }
        .tabs .content {
            margin-top: 20px;
        }
        .tabs .content section h2 {
            display: block;
        }
    }

    table {
        font-family: "Raleway", Arial, Helvetica, sans-serif;
        /* border-collapse: collapse; */
        table-layout: auto;
        font-size: 12px;
        width: fit-content;
        height: fit-content;
        border-collapse: separate;
        border-spacing: 0;
        color: #17191a;
        white-space: nowrap;
    }


    /* table {
        table-layout: auto;
        white-space: nowrap;
    } */

    th,
    td {
        padding: 5px 10px;
        vertical-align: middle;
    }

    thead {
        background: #2F82F4;
        color: #fff;
        font-size: 11px;
        text-transform: uppercase;
    }

    th:first-child {
        border-top-left-radius: 5px;
        text-align: left;
    }

    th:last-child {
        border-top-right-radius: 5px;
    }

    tbody tr:nth-child(even) {
        background: #f0f0f2;
    }

    td {
        border-bottom: 1px solid #cecfd5;
        border-right: 1px solid #cecfd5;
    }

    td:first-child {
        border-left: 1px solid #cecfd5;
    }

    .book-title {
        color: #395870;
        display: block;
    }

    .text-offset {
        color: #7c7c80;
        font-size: 12px;
    }

    .item-stock,
    .item-qty {
        text-align: center;
    }

    .item-price {
        text-align: right;
    }

    .item-multiple {
        display: block;
    }

    tfoot {
        text-align: right;
    }

    tfoot tr:last-child {
        background: #f0f0f2;
        color: #395870;
        font-weight: bold;
    }

    tfoot tr:last-child td:first-child {
        border-bottom-left-radius: 5px;
    }

    tfoot tr:last-child td:last-child {
        border-bottom-right-radius: 5px;
    }


    /* {
        border: 1px solid #ddd;
        padding: 0px;
    } */

    tr:nth-child(even) {
        background-color: #f2f2f2;
    }

    tr:hover {
        background-color: #ddd;
    }

    th {
        padding-top: 4px;
        padding-bottom: 4px;
        text-align: left;
        background-color: #4b48f1;
        color: white;
    }

    .column {
        float: left;
        padding: 1px;
        height: 30px;
        /* Should be removed. Only for demonstration */
    }

    /* Clear floats after the columns */

    .row:after {
        content: "";
        display: table;
        clear: both;
    }
    """
    css += css_gen 
    html_body = f"""
    <!DOCTYPE html>
    <html lang="en">

    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        {jq_script}
        <title>Infrastructure Health-Check</title>
    </head>
    <style> {css} </style>
    <body>
        <h1> <strong> NSW GovDC - Infrastructure Health Check Report - {date} </strong></h1>
        <H4 style='color : #4CAF50;padding-left: 30px;'><strong> Date - {current_time} </strong></H4>
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
            <input type="radio" id="tab1" name="tab-control" checked />
            <input type="radio" id="tab2" name="tab-control" />
            <input type="radio" id="tab3" name="tab-control" />
            <ul>
                <li title="Storage">
                    <label for="tab1" role="button">
                            <img
                                width="17"
                                hight="17"
                                src="https://image.flaticon.com/icons/svg/873/873135.svg"/><br /><span> Storage </span></label>
                    </li>
                    <li title="Delivery Contents">
                        <label for="tab2" role="button">
                            <img
                                width="20"
                                hight="20"
                                src="https://image.flaticon.com/icons/svg/3208/3208726.svg"/><br /><span> VMware </span></label>
                    </li>
                    <li title="Switches">
                        <label for="tab3" role="button">
                            <img
                                width="20"
                                hight="20"
                                src="https://icon-library.net/images/network-switch-icon/network-switch-icon-8.jpg"/><br /><span> Switches </span></label>
                    </li>
                </ul>

                <div class="slider">
                    <div class="indicator"></div>
                </div>
                <div class="content">
                    <section>
                        <h2>Storage</h2>
                        {storage_hc_body}
                    </section>
                    <section>
                        <h2>VMware</h2>
                        {vmware_hc_body}
                    </section>
                    <section>
                        <h2>Switches</h2>
                        {switch_hc_body}
                    </section>
                </div>
            </div>
        </body>
    </html>                    
    """
    return html_body


if __name__ == "__main__":
    #####################################
    #   Import storage list
    #####################################

    with open("./storage_input.json") as f:
        clusters = json.load(f)
    ontap_clusters = clusters["ONTAP"]
    storgrid_clusters = clusters["STORAGEGRID"]
    eseries_clusters = clusters["ESERIES"]


    #####################################
    #   Import switch list
    #####################################

    with open("./switch_input.json") as f:
        switches = json.load(f)
    cumulus_switches = switches["CUMULUS"]
    cisco_switches = switches["CISCO"]
    tme = datetime.datetime.now()
    current_time = tme.strftime("%d/%m/%Y %H:%M:%S")
    date = datetime.date.today()
    #####################################
    #   Import VMware Data
    #####################################

    out = subprocess.check_output(["pwsh", "-File", "./vmware_hc.ps1"],stdin=None, stderr=None, shell=False, universal_newlines=False)
    output = out.decode("utf-8")
    css_jq_path = "./css_jq_comp.txt"
    css_jq_node_path = "./css_jq_node_comp.txt"
    with open(css_jq_path) as f:
        css_comps = f.read().splitlines()
    with open(css_jq_node_path) as f:
        css_node_comps = f.read().splitlines()
    
    
    cluster_names = []
    cluster_nodes = {}
    for cluster in ontap_clusters:
        cluster_name, cluster_version, cluster_status, deg_node_name = storagesc.get_cluster_status(cluster)
        cluster_names += [cluster_name]
        nodes = storagesc.get_cluster_nodes(cluster)
        cluster_nodes[cluster_name] = nodes
    css_gen, hover_var_list, trg_var_list = css_genarator(cluster_names, cluster_nodes)
    jq_script = script_generator(hover_var_list, trg_var_list)

    storage_hc_body = storagesc.ontap_report_table(ontap_clusters, storgrid_clusters, eseries_clusters)
    vmware_hc_body = output
    switch_hc_body = switchhc.cumulus_table(cumulus_switches, cisco_switches)
    htmlout = html_header_templat(current_time, date, storage_hc_body,
                                  vmware_hc_body, switch_hc_body, css_gen, jq_script)
    filelocation = f"./Output/InfraHC.html"
    with open(filelocation, 'w') as file:
        file.write(htmlout)
    subprocess.call("./sms.py")

