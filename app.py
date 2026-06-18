import pandas as pd


vehicle_df = pd.read_excel("VEHAPR26.xlsx")
item_df = pd.read_excel("Item list.xlsx")
from flask import Flask,request,redirect,session
from psycopg2.pool import SimpleConnectionPool
import os
import psycopg2
import html

app = Flask(__name__)
app.secret_key = "rsrtc2026"

import os


DATABASE_URL = os.environ.get("DATABASE_URL")
pool = SimpleConnectionPool(
    1,    # minimum connections
    20,   # maximum connections
    DATABASE_URL
)
conn = psycopg2.connect(DATABASE_URL)

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS indents (
    id SERIAL PRIMARY KEY,
    depot TEXT,
    date TEXT,
    vehicle TEXT,
    indent_no TEXT,
    technician TEXT
);
""")

cur.execute("""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'depot_indent_unique'
    ) THEN
        ALTER TABLE indents
        ADD CONSTRAINT depot_indent_unique
        UNIQUE (depot, indent_no);
    END IF;
END $$;
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS indent_items (
    id SERIAL PRIMARY KEY,
    indent_id INTEGER,
    lf_no TEXT,
    part_no TEXT,
    item_name TEXT,
    source TEXT,
    qty TEXT,
    rate TEXT,
    total TEXT
);
""")

conn.commit()

cur.close()
conn.close()

def get_conn():
    return pool.getconn()


DEPOTS = [
"ABU ROAD","AJAYMERU","AJMER","ALWAR","ANOOPGARH","BANSWARA","BARAN",
"BARMER","BEAWAR","BHARATPUR","BHILWARA","BIKANER","BUNDI","CHITTORGARH",
"CHURU","DAUSA","DELUXE","DHOLPUR","DEEDWANA","DUNGARPUR","FALNA",
"GANGANAGAR","HANUMANGARH","HINDAUN","JAIPUR","JAISALMER","JALORE",
"JHALAWAR","JHUNJHUNU","JODHPUR","KARAULI","KHETRI","KOTA","KOTPUTLI",
"LOHAGARH","MATSAYA NAGAR","NAGAUR","PALI","PHALODI","PRATAPGARH",
"RAJSAMAND","SARDAR SHAHAR","SAWAIMADHOPUR","SHAHPURA","SHRIMADHOPUR",
"SIKAR","SIROHI","TIJARA","TONK","UDAIPUR","VAISHALI NAGAR",
"VIDYADHAR NAGAR","CWS AJMER","CWS JAIPUR","CWS JODHPUR","KEKRI"
]

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>RSRTC Store Indent System (SIS)</title>
<link rel="stylesheet" href="/static/style.css">
</head>

<body>

<div class="box">

<h2>
RSRTC STORE INDENT SYSTEM (SIS)
</h2>

<p><span class="small-text">Developed & Designed</span>
<br>
by Hitesh Mishra
</p>

<a href="/login" class="login-link">
Login Here
</a>

</div>

</body>
</html>
"""

@app.route("/login", methods=["GET","POST"])
def login():

    error = ""

    if request.method=="POST":

        userid = request.form.get("userid","").upper()
        password = request.form.get("password","")

        if userid == "ADMIN" and password == "admin123":

            session["user"] = "ADMIN"
            session["role"] = "admin"

            return redirect("/admin_report")

        if userid == "SUPERVISOR" and password == "supervisor123":

            session["user"] = "SUPERVISOR"
            session["role"] = "supervisor"

            return redirect("/supervisor_report")

        if userid in DEPOTS and password == userid.lower():

            session["user"] = userid
            session["role"] = "depot"

            return redirect(f"/user/{userid}")

        error = "❌ Invalid User ID or Password"

    return f"""
<!DOCTYPE html>
<html>

<head>

<title>Login</title>

<link rel="stylesheet" href="/static/style.css">

</head>

<body>

<div class="box">

<h2>SIS LOGIN</h2>

<p style="
background:#ffe6e6;
color:red;
padding:10px;
border-radius:5px;
text-align:center;
font-weight:bold;
">

{error}

</p>

<form method="post">

<input
name="userid"
placeholder="User ID">

<br><br>

<input
type="password"
name="password"
placeholder="Password">

<br><br>

<button type="submit">

Login

</button>

</form>

</div>

</body>

</html>
"""

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

@app.route("/user/<depot>")
def user(depot):
    if "user" not in session:
        return redirect("/login")

    if session.get("user") != depot:
        return redirect("/login")
    return f"""
<!DOCTYPE html>
<html>
<head>

<title>{depot}</title>

<link rel="stylesheet"
href="/static/style.css">

<style>

.topbar{{
text-align:right;
padding:15px;
}}

.container{{
display:flex;
justify-content:center;
gap:20px;
margin-top:30px;
flex-wrap:wrap;
}}

.card{{
background:white;
width:300px;
padding:20px;
border-radius:10px;
box-shadow:0 0 10px #ccc;
text-align:center;
}}

.card a{{
display:block;
padding:12px;
margin:10px 0;
background:#003d80;
color:white;
text-decoration:none;
border-radius:5px;
}}

.card h2{{
color:#003d80;
}}

</style>

</head>
<script>

window.history.pushState(null, "", window.location.href);

window.onpopstate = function () {{

    if(confirm("Do you want to Logout ?")){{

        window.location.href="/login";

    }}else{{

        window.history.pushState(null, "", window.location.href);

    }}

}};

</script>

<body>

<div class="topbar">

<a href="/logout"
style="
background:#dc3545;
color:white;
padding:10px 20px;
text-decoration:none;
border-radius:5px;
font-weight:bold;
display:inline-block;
margin-bottom:15px;
">

🚪 Logout

</a>

</div>

<div style="
background:#003d80;
color:white;
padding:15px;
border-radius:10px;
text-align:center;
font-size:24px;
font-weight:bold;
margin-bottom:20px;
">

Welcome To {depot} Depot

</div>
<div class="container">

<div class="card">

<h2>Indent Detail</h2>

<a href="/Indent Detail(Item wise)/{depot}">
Open
</a>

</div>

<div class="card">

<h2>Report</h2>

<a href="/Report/{depot}">
Open
</a>

</div>

</div>

</body>
</html>
"""


@app.route("/Indent Detail(Item wise)/<depot>")
def make_indent(depot):

    depot_vehicles = vehicle_df[
        vehicle_df["NAME"].str.upper() == depot.upper()
    ]

    vehicle_options = ""

    for v in depot_vehicles["VEH_NO"]:
        vehicle_options += f'<option value="{v}">'

    lf_options = ""
    part_options = ""
    item_options = ""
    

    master_options = ""

    for _, r in item_df.iterrows():

        lf = str(r["LFNo"])
        part = str(r["PartNo"])
        item = str(r["PartDesc"])

        import html

        master_options += f'''
        <option value="{html.escape(lf)} | {html.escape(part)} | {html.escape(item)}">
        '''



    for _, r in item_df.iterrows():

        lf = str(r["LFNo"])
        part = str(r["PartNo"])
        item = str(r["PartDesc"])

        lf_options += f'<option value="{html.escape(lf)}">'
        part_options += f'<option value="{html.escape(part)}">'
        item_options += f'<option value="{html.escape(item)}">'

    # AUTO FILL MASTER

    item_master = []

    for _, r in item_df.iterrows():

        item_master.append({
            "lf": str(r["LFNo"]),
            "part": str(r["PartNo"]),
            "item": str(r["PartDesc"])
        })

    import json
    item_master_json = json.dumps(item_master)

    return f"""
<!DOCTYPE html>
<html>

<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Make Indent</title>

<style>

body{{
    font-family:Segoe UI, Arial;
    background:linear-gradient(135deg,#dfe9f3,#ffffff);
    margin:0;
    padding:20px;
}}

.box{{
    background:white;
    max-width:1200px;
    margin:auto;
    padding:25px;
    border-radius:20px;
    box-shadow:0 10px 25px rgba(0,0,0,0.15);
}}

.header{{
    background:linear-gradient(90deg,#003d80,#005ecb);
    color:white;
    padding:18px;
    border-radius:12px;
    text-align:center;
    margin-bottom:20px;
    font-size:22px;
    font-weight:bold;
}}

.back{{
    background:#003d80;
    color:white;
    padding:10px 18px;
    text-decoration:none;
    border-radius:8px;
    font-weight:bold;
    display:inline-block;
    margin-bottom:15px;
}}

.back:hover{{
    background:#005ecb;
}}

label{{
    font-weight:600;
    color:#003d80;
}}

input,select{{
    width:100%;
    padding:12px;
    border:1px solid #cfd8dc;
    border-radius:8px;
    font-size:15px;
    margin-top:5px;
    margin-bottom:12px;
    box-sizing:border-box;
}}

input:focus,
select:focus{{
    border:2px solid #005ecb;
    outline:none;
    box-shadow:0 0 8px rgba(0,94,203,0.3);
}}

h3{{
    background:#eef5ff;
    padding:10px;
    border-radius:8px;
    color:#003d80;
}}

table{{
    width:100%;
    border-collapse:collapse;
    margin-top:15px;
    border-radius:10px;
}}

@media(max-width:768px){{

table{{
    display:block;
    overflow-x:auto;
    white-space:nowrap;
}}

table td:nth-child(1) select{{
    min-width:120px;
}}

table td:nth-child(2) input{{
    min-width:140px;
}}

table td:nth-child(3) input{{
    min-width:100px;
}}

table td:nth-child(4) input{{
    min-width:340px;
}}

table td:nth-child(5) select{{
    min-width:140px;
}}

table td:nth-child(6) input{{
    min-width:100px;
}}

table td:nth-child(7) input{{
    min-width:100px;
}}

table td:nth-child(8) input{{
    min-width:120px;
}}

table td:nth-child(9) button{{
    min-width:50px;
}}

}}

table th{{
    background:#003d80;
    color:white;
    padding:12px;
    text-align:center;
}}

table td{{
    border:1px solid #ddd;
    padding:8px;
    background:white;
}}

table tr:nth-child(even){{
    background:#f8fbff;
}}

.addbtn{{
    background:#005ecb;
    color:white;
    padding:12px 20px;
    border:none;
    border-radius:8px;
    font-weight:bold;
    cursor:pointer;
}}

.addbtn:hover{{
    background:#0048a0;
}}

.delbtn{{
    background:#dc3545;
    color:white;
    border:none;
    border-radius:6px;
    padding:8px 10px;
    cursor:pointer;
}}

.delbtn:hover{{
    background:#b02a37;
}}

.grandbox{{
    background:#fff8e1;
    border:2px solid #ffc107;
    padding:15px;
    margin-top:20px;
    border-radius:10px;
    text-align:center;
    font-size:22px;
    font-weight:bold;
    color:#e65100;
}}

.savebtn{{
    width:100%;
    background:#28a745;
    color:white;
    border:none;
    padding:15px;
    margin-top:20px;
    font-size:20px;
    font-weight:bold;
    border-radius:10px;
    cursor:pointer;
}}

.savebtn:hover{{
    background:#218838;
}}

</style>

</head>

<body>

<div class="box">

<a href="/user/{depot}" class="back">
← Back
</a>

<div class="header">

<h2>{depot}</h2>

</div>

<form
method="post"
action="/preview_indent"
onsubmit="return validateForm()">

<input type="hidden"
name="depot"
value="{depot}">

<label>Date</label>

<input
type="date"
name="date"
required>

<label>Vehicle Number</label>

<input
list="vehicles"
name="vehicle"
placeholder="Vehicle Number"
autocomplete="off"
required>

<datalist id="vehicles">

{vehicle_options}

</datalist>
<datalist id="lflist">
{lf_options}
</datalist>

<datalist id="partlist">
{part_options}
</datalist>

<datalist id="itemlist">
{item_options}
</datalist>

<datalist id="masterlist">

{master_options}

</datalist>
<label>Indent Number</label>

<input
type="text"
name="indent_no"
autocomplete="off"
placeholder="Indent Number"
required>

<label>Technician Name</label>

<input
type="text"
name="technician"
autocomplete="off"
placeholder="Technician Name"
pattern="[A-Za-z ]+"
required>

<h3>Item Details</h3>

<table id="itemTable">

<tr>
<th style="width:10%">Type</th>
<th style="width:15%">LF No</th>

<th style="width:10%">Part No</th>

<th style="width:30%">Item Name</th>

<th style="width:10%">Source</th>

<th style="width:7%">Qty</th>

<th style="width:8%">Per Item Rate</th>

<th style="width:8%">Total</th>

<th style="width:2%">Action</th>

</tr>

<tr>
<td>
<select name="item_type[]" onchange="changeType(this)">

<option value="LF">LF Item</option>

<option value="RC">RC Assembly</option>

<option value="LP">Local Purchase</option>

<option value="OIL">Oil & Lubricants</option>

</select>
</td>
<td>
<input list="masterlist" name="lf_no[]" oninput="fillFromLF(this)">
</td>

<td>
<input list="masterlist" name="part_no[]" oninput="fillFromPart(this)">
</td>

<td>
<input list="masterlist" name="item_name[]" oninput="fillFromItem(this)">
</td>

<td>
<select name="source[]">
<option>Central Store</option>
<option>Local Purchase</option>
</select>
</td>

<td>
<input
type="number"
name="qty[]"
step="0.1"
min="0.1"
required
onkeyup="calcRow(this)">
</td>

<td>
<input
type="number"
name="rate[]"
step="0.01"
required
onkeyup="calcRow(this)">
</td>

<td>
<input
type="number"
name="total[]"
readonly>
</td>

<td>
<button
type="button"
class="delbtn"
onclick="deleteRow(this)">
X
</button>
</td>

</tr>

</table>

<br>

<button
type="button"
class="addbtn"
onclick="addRow()">

+ ADD ITEM

</button>

<h3>

Grand Total :
₹ <span id="grandTotal">0</span>

</h3>

<button type="submit"
onclick="return confirmIndent()">
PREVIEW & SUBMIT
</button>



</form>

</div>
<script>

function confirmIndent(){{

    let indent =
    document.querySelector(
    '[name="indent_no"]'
    ).value;

    return confirm(
    "क्या Indent Number "
    + indent +
    " की समस्त प्रविष्टियाँ पूर्ण कर ली गई हैं ?"
    );

}}


const itemMaster = {item_master_json};
function fillFromLF(el){{

    let row = el.closest("tr");

    let type =
    row.querySelector('[name="item_type[]"]').value;

    if(type!="LF"){{
        return;
    }}

    let lf = el.value.split("|")[0].trim();
    el.value = lf;

    if(lf === ""){{

        row.querySelector('[name="part_no[]"]').value = "";
        row.querySelector('[name="item_name[]"]').value = "";

        return;
    }}

    let found = false;

    for(let i=0;i<itemMaster.length;i++){{

        if(itemMaster[i].lf == lf){{

            found = true;

            row.querySelector('[name="part_no[]"]').value =
            itemMaster[i].part;

            row.querySelector('[name="item_name[]"]').value =
            itemMaster[i].item;

            break;
        }}
    }}

    if(!found){{

    row.querySelector('[name="part_no[]"]').value = "";
    row.querySelector('[name="item_name[]"]').value = "";
    return;
    }}
}}

function fillFromPart(el){{

    let row = el.closest("tr");
    let type =
    row.querySelector('[name="item_type[]"]').value;

    if(type!="LF"){{
        return;
    }}

    let p = el.value.split("|");

    let part = (p[1] || p[0]).trim();
    el.value = part;

    if(part === ""){{

        row.querySelector('[name="lf_no[]"]').value = "";
        row.querySelector('[name="item_name[]"]').value = "";

        return;
    }}

    let found = false;

    for(let i=0;i<itemMaster.length;i++){{

        if(itemMaster[i].part == part){{

            found = true;

            row.querySelector('[name="lf_no[]"]').value =
            itemMaster[i].lf;

            row.querySelector('[name="item_name[]"]').value =
            itemMaster[i].item;

            break;
        }}
    }}

    if(!found){{

        row.querySelector('[name="lf_no[]"]').value = "";
        row.querySelector('[name="item_name[]"]').value = "";

        return;
    }}

}}

function fillFromItem(el){{

    let row = el.closest("tr");
    let type =
    row.querySelector('[name="item_type[]"]').value;

    if(type!="LF"){{
        return;
    }}

    let p = el.value.split("|");

    let item = (p[2] || p[0]).trim();
    el.value = item;

    if(item === ""){{

        row.querySelector('[name="lf_no[]"]').value = "";
        row.querySelector('[name="part_no[]"]').value = "";

        return;
    }}

    let found = false;

    for(let i=0;i<itemMaster.length;i++){{

        if(itemMaster[i].item == item){{

            found = true;

            row.querySelector('[name="lf_no[]"]').value =
            itemMaster[i].lf;

            row.querySelector('[name="part_no[]"]').value =
            itemMaster[i].part;

            break;
        }}
    }}

    if(!found){{

        row.querySelector('[name="lf_no[]"]').value = "";
        row.querySelector('[name="part_no[]"]').value = "";
        return;
    }}

}}



function validateLF(el){{

    let found = false;

    for(let i=0;i<itemMaster.length;i++){{

        if(itemMaster[i].lf == el.value.trim()){{
            found = true;
            break;
        }}
    }}

    if(!found && el.value.trim()!=""){{

        alert("Invalid LF Number");

        el.value="";

        fillFromLF(el);
    }}
}}

function validatePart(el){{

    let found = false;

    for(let i=0;i<itemMaster.length;i++){{

        if(itemMaster[i].part == el.value.trim()){{
            found = true;
            break;
        }}
    }}

    if(!found && el.value.trim()!=""){{

        alert("Invalid Part Number");

        el.value="";

        fillFromPart(el);
    }}
}}

function validateItem(el){{

    let found = false;

    for(let i=0;i<itemMaster.length;i++){{

        if(itemMaster[i].item == el.value.trim()){{
            found = true;
            break;
        }}
    }}

    if(!found && el.value.trim()!=""){{

        alert("Invalid Item Name");

        el.value="";

        fillFromItem(el);
    }}
}}

function changeType(el){{

    let row = el.closest("tr");

    let type = el.value;

    let lf = row.querySelector('[name="lf_no[]"]');
    let part = row.querySelector('[name="part_no[]"]');
    let item = row.querySelector('[name="item_name[]"]');

    if(type=="LF"){{

        lf.value="";
        part.value="";
        item.value="";

        lf.readOnly=false;
        part.readOnly=false;
        item.readOnly=false;
        lf.setAttribute("list","masterlist");
        part.setAttribute("list","masterlist");
        item.setAttribute("list","masterlist");
        let source =
        row.querySelector('[name="source[]"]');

        source.innerHTML = `
        <option>Central Store</option>
        <option>Local Purchase</option>
        `;
            }}
        

    if(type=="RC"){{

        lf.value="RC";
        part.value="RC";
        item.value="";

        lf.readOnly=true;
        part.readOnly=true;
        item.readOnly=false;
        lf.removeAttribute("list");
        part.removeAttribute("list");
        item.removeAttribute("list");
        item.setAttribute("autocomplete","off");
        

        let source =
        row.querySelector('[name="source[]"]');

        source.innerHTML = `
        <option>Central Workshop</option>
        `;

        source.value = "Central Workshop";
            }}

    if(type=="LP"){{

        lf.value="LP";
        part.value="LP";
        item.value="";

        lf.readOnly=true;
        part.readOnly=true;
        item.readOnly=false;
        lf.removeAttribute("list");
        part.removeAttribute("list");
        item.removeAttribute("list");
        item.setAttribute("autocomplete","off");

        let source =
        row.querySelector('[name="source[]"]');

        source.innerHTML = `
        <option>Local Purchase</option>
        `;

        source.value = "Local Purchase";
            }}

    if(type=="OIL"){{

        lf.value="OIL";
        part.value="OIL";
        item.value="";

        lf.readOnly=true;
        part.readOnly=true;
        item.readOnly=false;
        lf.removeAttribute("list");
        part.removeAttribute("list");
        item.removeAttribute("list");
        item.setAttribute("autocomplete","off");

        let source =
        row.querySelector('[name="source[]"]');

        source.innerHTML = `
        <option>Central Store</option>
        <option>Local Purchase</option>
        `;
            }}
}}

function validateForm(){{

    let totals =
    document.getElementsByName("total[]");

    for(let i=0;i<totals.length;i++){{

        if(
            totals[i].value == "" ||
            Number(totals[i].value) <= 0
        ){{

            alert(
            "Please fill item quantity again and Total."
            );

            return false;
        }}
    }}

    return true;
}}
function addRow(){{

let table =
document.getElementById("itemTable");

let row =
table.insertRow();

row.innerHTML = `

<td>
<select name="item_type[]" onchange="changeType(this)">

<option value="LF">LF Item</option>

<option value="RC">RC Assembly</option>

<option value="LP">Local Purchase</option>

<option value="OIL">Oil & Lubricants</option>

</select>
</td>
<td>
<input list="masterlist" name="lf_no[]" oninput="fillFromLF(this)">
</td>

<td>
<input list="masterlist" name="part_no[]" oninput="fillFromPart(this)">
</td>

<td>
<input list="masterlist" name="item_name[]" oninput="fillFromItem(this)">
</td>
<td>
<select name="source[]">
<option>Central Store</option>
<option>Local Purchase</option>
</select>
</td>

<td>
<input type="number"
name="qty[]"
step="0.1"
min="0.1"
required
onkeyup="calcRow(this)">
</td>

<td>
<input type="number"
name="rate[]"
step="0.01"
required
onkeyup="calcRow(this)">
</td>

<td>
<input type="number"
name="total[]"
readonly>
</td>

<td>
<button
type="button"
class="delbtn"
onclick="deleteRow(this)">
X
</button>
</td>

`;

}}

function deleteRow(btn){{

btn.parentNode.parentNode.remove();

calculateGrand();

}}

function calcRow(el){{

let row =
el.parentNode.parentNode;

let qty =
row.cells[5]
.querySelector("input").value || 0;

let PerItemRate =
row.cells[6]
.querySelector("input").value || 0;

row.cells[7]
.querySelector("input").value =
(qty * PerItemRate).toFixed(2);

calculateGrand();

}}

function calculateGrand(){{

let totals =
document.getElementsByName("total[]");

let grand = 0;

for(let i=0;i<totals.length;i++){{

grand +=
Number(totals[i].value || 0);

}}

document
.getElementById("grandTotal")
.innerHTML = grand.toFixed(2);

}}
 


</script>

</body>

</html>
"""
import json

@app.route("/preview_indent", methods=["POST"])
def preview_indent():

    depot = request.form.get("depot","")
    date = request.form.get("date","")
    vehicle = request.form.get("vehicle","")
    indent_no = request.form.get("indent_no","")
    technician = request.form.get("technician","")

    rows = ""

    grand_total = 0

    lf_list = request.form.getlist("lf_no[]")
    part_list = request.form.getlist("part_no[]")
    item_list = request.form.getlist("item_name[]")
    qty_list = request.form.getlist("qty[]")
    rate_list = request.form.getlist("rate[]")
    total_list = request.form.getlist("total[]")
    source_list = request.form.getlist("source[]")
    item_type_list = request.form.getlist("item_type[]")

    for i in range(len(item_list)):

        rows += f"""

        <tr>
        <td>{item_type_list[i]}</td>
        <td>{lf_list[i]}</td>
        <td>{part_list[i]}</td>
        <td>{item_list[i]}</td>
        <td>{source_list[i]}</td>
        <td>{qty_list[i]}</td>
        <td>{rate_list[i]}</td>
        <td>{total_list[i]}</td>
        </tr>

        """

        try:
            grand_total += float(total_list[i])
        except:
            pass

    return f"""
<head>

<title>Indent Preview</title>

<style>

body{{
    font-family:Arial;
    background:#f4f6f9;
    margin:0;
    padding:20px;
}}

.container{{
    max-width:1200px;
    margin:auto;
    background:white;
    padding:20px;
    border-radius:10px;
    box-shadow:0 0 10px rgba(0,0,0,0.15);
}}

.titlebox{{
    background:#0d47a1;
    color:white;
    text-align:center;
    padding:20px;
    font-size:30px;
    font-weight:bold;
    border-radius:8px;
    margin-bottom:20px;
}}

.infobox{{
    background:#f8f9fa;
    padding:15px;
    border-radius:8px;
    margin-bottom:20px;
    line-height:35px;
    font-size:16px;
}}

table{{
    width:100%;
    border-collapse:collapse;
}}

th{{
    background:#0d47a1;
    color:white;
    padding:10px;
}}

td{{
    padding:10px;
    border:1px solid #ddd;
    text-align:center;
}}

.totalbox{{
    margin-top:20px;
    background:#e8f5e9;
    padding:15px;
    font-size:22px;
    font-weight:bold;
    border-radius:8px;
}}

.btnarea{{
    margin-top:25px;
    text-align:center;
}}

.editbtn{{
    background:#ff9800;
    color:white;
    border:none;
    padding:12px 25px;
    font-size:18px;
    border-radius:5px;
    cursor:pointer;
    margin-right:10px;
}}

.savebtn{{
    background:#28a745;
    color:white;
    border:none;
    padding:12px 25px;
    font-size:18px;
    border-radius:5px;
    cursor:pointer;
}}

.editbtn:hover{{
    opacity:.9;
}}

.savebtn:hover{{
    opacity:.9;
}}

</style>

</head>
    <html>
    
<body>

<div class="container">

<div class="titlebox">
INDENT PREVIEW
</div>

<div class="infobox">

<b>Depot :</b> {depot}<br>

<b>Date :</b> {date}<br>

<b>Vehicle :</b> {vehicle}<br>

<b>Indent No :</b> {indent_no}<br>

<b>Technician :</b> {technician}

</div>

<table>

<tr>
<th>Type</th>
<th>LF No</th>
<th>Part No</th>
<th>Item Name</th>
<th>Source</th>
<th>Qty</th>
<th>Rate</th>
<th>Total</th>
</tr>

{rows}

</table>

<div class="totalbox">
Grand Total : ₹ {grand_total}
</div>

<form method="post" action="/save_indent">

<input type="hidden" name="depot" value="{depot}">
<input type="hidden" name="date" value="{date}">
<input type="hidden" name="vehicle" value="{vehicle}">
<input type="hidden" name="indent_no" value="{indent_no}">
<input type="hidden" name="technician" value="{technician}">


{"".join([f'<input type="hidden" name="item_type[]" value="{x}">' for x in item_type_list])}

{"".join([f'<input type="hidden" name="lf_no[]" value="{html.escape(str(x))}">' for x in lf_list])}
{"".join([f'<input type="hidden" name="part_no[]" value="{html.escape(str(x))}">' for x in part_list])}

{"".join([f'<input type="hidden" name="item_name[]" value="{html.escape(str(x))}">' for x in item_list])}

{"".join([f'<input type="hidden" name="qty[]" value="{x}">' for x in qty_list])}

{"".join([f'<input type="hidden" name="rate[]" value="{x}">' for x in rate_list])}

{"".join([f'<input type="hidden" name="total[]" value="{x}">' for x in total_list])}

{"".join([f'<input type="hidden" name="source[]" value="{x}">' for x in source_list])}

<div class="btnarea">

<button
type="button"
class="editbtn"
onclick="history.back()">

EDIT AGAIN

</button>

<button
type="submit"
class="savebtn">

FINAL SAVE

</button>

</div>

</form>

</div>

</body>
    </html>
    """
@app.route("/save_indent", methods=["POST"])
def save_indent():

    valid_lf = set(item_df["LFNo"].astype(str))
    valid_part = set(
        item_df["PartNo"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    valid_item = set(item_df["PartDesc"].astype(str))

    item_types = request.form.getlist("item_type[]")

    for i, lf in enumerate(request.form.getlist("lf_no[]")):

        if item_types[i] != "LF":
            continue

        if lf and lf not in valid_lf:
            return "Invalid LF Number"

    part_list = request.form.getlist("part_no[]")

    for i, part in enumerate(part_list):

        if item_types[i] != "LF":
            continue

        part = str(part).strip()

        if part and part not in valid_part:

            return f"""
            Invalid Part Number<br><br>

            FORM = {repr(part)}
            """

    item_list = request.form.getlist("item_name[]")

    for i, item in enumerate(item_list):

        if item_types[i] != "LF":
            continue

        if item and item not in valid_item:
            return "Invalid Item Name"

    depot = request.form.get("depot", "")
    date = request.form.get("date", "")
    vehicle = request.form.get("vehicle", "").strip()
    valid_vehicles = set(vehicle_df["VEH_NO"].astype(str).str.strip())
    if vehicle not in valid_vehicles:
        return """
        <script>
        alert('Invalid Vehicle Number');
        history.back();
        </script>
        """
    indent_no = request.form.get("indent_no", "")
    technician = request.form.get("technician", "")

    record = {
        "depot": depot,
        "date": date,
        "vehicle": vehicle,
        "indent_no": indent_no,
        "technician": technician,
        "items": []
    }

    lf_list = request.form.getlist("lf_no[]")
    part_list = request.form.getlist("part_no[]")
    item_list = request.form.getlist("item_name[]")
    source_list = request.form.getlist("source[]")
    qty_list = request.form.getlist("qty[]")
    rate_list = request.form.getlist("rate[]")
    total_list = request.form.getlist("total[]")

    for i in range(len(item_list)):

        if not item_list[i].strip():
            continue

        record["items"].append({
            "lf_no": lf_list[i],
            "part_no": part_list[i],
            "item_name": item_list[i],
            "source": source_list[i],
            "qty": qty_list[i],
            "rate": rate_list[i],
            "total": total_list[i]
        })

    if len(record["items"]) == 0:
        return "Please Add At Least One Item"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM indents
        WHERE depot=%s AND indent_no=%s
        """,
        (depot, indent_no)
    )

    if cur.fetchone():

        cur.close()
        pool.putconn(conn)

        return "Indent Number Already Exists"

    cur.execute(
        """
        INSERT INTO indents
        (depot,date,vehicle,indent_no,technician)
        VALUES (%s,%s,%s,%s,%s)
        RETURNING id
        """,
        (
            depot,
            date,
            vehicle,
            indent_no,
            technician
        )
    )

    indent_id = cur.fetchone()[0]

    for item in record["items"]:

        cur.execute(
            """
            INSERT INTO indent_items
            (
                indent_id,
                lf_no,
                part_no,
                item_name,
                source,
                qty,
                rate,
                total
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                indent_id,
                item["lf_no"],
                item["part_no"],
                item["item_name"],
                item["source"],
                item["qty"],
                item["rate"],
                item["total"]
            )
        )

    conn.commit()

    cur.close()
    pool.putconn(conn)

    return f"""
    <!DOCTYPE html>
    <html>

    <head>

    <meta http-equiv="refresh"
    content="2;url=/Indent Detail(Item wise)/{depot}">

    <link rel="stylesheet"
    href="/static/style.css">

    </head>

    <body>

    <div class="box">

    <h2 style="color:green;">
    ✓ Indent Saved Successfully
    </h2>

    <p>
    Returning To Indent Page...
    </p>

    </div>

    </body>

    </html>
    """

@app.route("/Report/<depot>")
def report(depot):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        i.date,
        i.indent_no,
        i.vehicle,
        i.technician,
        d.source,
        d.lf_no,
        d.part_no,
        d.item_name,
        d.qty,
        d.rate,
        d.total
    FROM indents i
    JOIN indent_items d
    ON i.id = d.indent_id
    WHERE i.depot = %s
    ORDER BY i.id DESC
    """, (depot,))

    db_rows = cur.fetchall()

    cur.close()
    pool.putconn(conn)

    from_date = request.args.get("from_date","")
    to_date = request.args.get("to_date","")
    vehicle = request.args.get("vehicle","")
    item = request.args.get("item","")
    source = request.args.get("source","")

    # VEHICLE LIST

    vehicle_set = set()

    for row in vehicle_df.itertuples():

        if str(row.NAME).strip().upper() == depot.strip().upper():

            vehicle_set.add(str(row.VEH_NO).strip())

    
    vehicle_options = ""

    for v in sorted(vehicle_set):

        vehicle_options += f"""
        <option value="{v}">
        """
    
    item_options = ""

    for row in item_df.itertuples():

        lf = str(row.LFNo)
        part = str(row.PartNo)
        item_name = str(row.PartDesc)

        display = f"{lf} | {part} | {item_name}"

        item_options += f'''
        <option value="{display}">
        '''

    filtered = []

    for row in db_rows:

        row_date = str(row[0])
        row_indent = str(row[1])
        row_vehicle = str(row[2])

        row_technician = str(row[3])
        row_source = str(row[4])

        row_lf = str(row[5])
        row_part = str(row[6])
        row_item = str(row[7])
        row_qty = str(row[8])
        row_rate = str(row[9])
        row_total = str(row[10])

        if from_date and row_date < from_date:
            continue

        if to_date and row_date > to_date:
            continue

        if vehicle and vehicle.lower() not in row_vehicle.lower():
            continue

        if item:

            item_search = item.lower().split("|")[0].strip()

            if (
                item_search not in row_lf.lower()
                and item_search not in row_part.lower()
                and item_search not in row_item.lower()
            ):
                continue
        if source and source.lower() != row_source.lower():
            continue
 
        filtered.append(row)
    page = int(request.args.get("page", 1))

    per_page = 50

    total_records = len(filtered)

    start = (page - 1) * per_page

    end = start + per_page

    page_records = filtered[start:end]

    rows = ""

    for row in page_records:

        rows += f"""
        <tr>

        <td>{row[0]}</td>

        <td>
        <a href="/indent_detail/{depot}/{row[1]}">
        {row[1]}
        </a>
        </td>

        <td>{row[2]}</td>

        <td>{row[3]}</td>
        <td>{row[4]}</td>  
        <td>{row[5]}</td>  
        <td>{row[6]}</td>  
        <td>{row[7]}</td>  
        <td>{row[8]}</td>  
        <td>{row[9]}</td>  
        <td>{row[10]}</td> 

        </tr>
        """

    total_pages = max(
        1,
        (total_records + per_page - 1) // per_page
    )

    pagination = ""

    start_page = max(1, page - 5)
    end_page = min(total_pages, page + 5)

    for p in range(start_page, end_page + 1):

        if p == page:

            pagination += f"""
            <span style="
            padding:8px 12px;
            background:#003d80;
            color:white;
            margin:2px;
            border-radius:5px;">
            {p}
            </span>
            """

        else:

            pagination += f"""
            <a href="?page={p}&from_date={from_date}&to_date={to_date}&vehicle={vehicle}&item={item}&source={source}"
            style="
            padding:8px 12px;
            background:#eee;
            margin:2px;
            border-radius:5px;
            text-decoration:none;">
            {p}
            </a>
            """       
    if rows == "":

        rows = """

        <tr>

        <td colspan="11"
        style="text-align:center;color:red;font-weight:bold;">

        No Record Found

        </td>

        </tr>

        """

    return f"""

    <!DOCTYPE html>

    <html>

    <head>

    <title>{depot} Report</title>

    <style>

    body{{
        font-family:Arial;
        background:#eef2f7;
        padding:20px;
    }}

    .box{{
        background:white;
        width:95%;
        margin:auto;
        padding:25px;
        border-radius:15px;
        box-shadow:0 0 15px rgba(0,0,0,.15);
    }}

    .summary{{
        background:#003d80;
        color:white;
        padding:15px;
        border-radius:10px;
        margin-bottom:20px;
        font-size:20px;
        font-weight:bold;
    }}

    table{{
        width:100%;
        border-collapse:collapse;
    }}

    td{{
        border:1px solid #ddd;
        padding:6px;
        font-size:12px;
    }}

    th{{
        background:#003d80;
        color:white;
        padding:6px;
        font-size:12px;
    }}

    input{{
        padding:10px;
        margin:5px;
    }}

    button{{
        padding:10px 20px;
        background:green;
        color:white;
        border:none;
        border-radius:5px;
        cursor:pointer;
    }}

    a{{
        text-decoration:none;
        color:#003d80;
        font-weight:bold;
    }}

    @media print {{
        form,.noprint {{
            display:none;
        }}
    }}

    </style>

    </head>

    <body>

    <div class="box">

    <a href="/user/{depot}"
    class="noprint"
    style="
    background:#003d80;
    color:white;
    padding:10px 20px;
    text-decoration:none;
    border-radius:5px;
    display:inline-block;
    margin-bottom:15px;
    ">

    ← Back To Dashboard

    </a>

    <h2>{depot} REPORT</h2>

    <div class="summary">

    Total Records : {len(filtered)}

    </div>

    <form method="get"
    autocomplete="off">

    From Date

    <input
    type="date"
    name="from_date"
    value="{from_date}">

    To Date

    <input
    type="date"
    name="to_date"
    value="{to_date}">

    Vehicle

    <input
    list="vehiclelist"
    name="vehicle"
    autocomplete="off"
    value="{vehicle}"
    placeholder="Vehicle Number">

    <datalist id="vehiclelist">

    {vehicle_options}

    </datalist>

    Item

    <input
    list="itemlist"
    name="item"
    value="{item}"
    placeholder="LF / Part / Item">

    <datalist id="itemlist">

    {item_options}

    </datalist>
    Source

    <select name="source">

    <option value="">All</option>

    <option value="Central Store"
    {"selected" if source=="Central Store" else ""}>
    Central Store
    </option>

    <option value="Central Workshop"
    {"selected" if source=="Central Workshop" else ""}>
    Central Workshop
    </option>

    <option value="Local Purchase"
    {"selected" if source=="Local Purchase" else ""}>
    Local Purchase
    </option>

    </select>

    <button type="submit">

    Search

    </button>

    <button
    type="button"
    onclick="window.print()">

    Print

    </button>

    </form>

    <table>

    <tr>

    <th>Date</th>
    <th>Indent No</th>
    <th>Vehicle</th>
    <th>Technician</th>
    <th>Source</th>
    <th>LF No</th>
    <th>Part No</th>
    <th>Item Name</th>
    <th>Qty</th>
    <th>Rate</th>
    <th>Total</th>

    </tr>

    {rows}

    </table>
    <div style="
    text-align:center;
    margin-top:20px;
    ">

    {pagination}

    </div>

    </div>

    </body>

    </html>

    """


@app.route("/indent_detail/<depot>/<indent_no>")
def indent_detail(depot, indent_no):
    
    source = request.args.get("source","")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT depot,date,vehicle,indent_no,technician,id
    FROM indents 
    WHERE depot=%s AND indent_no=%s 
    """, (depot, indent_no))

    record = cur.fetchone()

    if not record:
        cur.close()
        pool.putconn(conn)
        return "Indent Not Found"

    cur.execute("""
    SELECT
    lf_no,
    part_no,
    item_name,
    source,
    qty,
    rate,
    total
    FROM indent_items
    WHERE indent_id=%s
    """, (record[5],))

    items = cur.fetchall()

    cur.close()
    pool.putconn(conn)
    if source == "admin":

        back_link = "/admin_report"

    else:

        back_link = f"/Report/{depot}"
    rows = ""

    grand_total = 0

    for item in items:

        try:
            grand_total += float(item[6] or 0)
        except:
            pass

        rows += f"""

        <tr>

        <td>{item[0]}</td>
        <td>{item[1]}</td>
        <td>{item[2]}</td>
        <td>{item[3]}</td>
        <td>{item[4]}</td>
        <td>{item[5]}</td>
        <td>{item[6]}</td>

        </tr>

        """

    return f"""

    <!DOCTYPE html>
    <html>

    <head>

    <title>{indent_no}</title>

    <style>

    body{{
    font-family:Arial;
    background:#eef2f7;
    padding:20px;
    }}

    .box{{
    background:white;
    max-width:1300px;
    margin:auto;
    padding:25px;
    border-radius:15px;
    }}

    table{{
    width:100%;
    border-collapse:collapse;
    }}

    th,td{{
    border:1px solid #ddd;
    padding:10px;
    }}

    th{{
    background:#003d80;
    color:white;
    }}

    .btn{{
    background:green;
    color:white;
    border:none;
    padding:10px 20px;
    border-radius:5px;
    cursor:pointer;
    text-decoration:none;
    }}

    .info{{
    margin:15px 0;
    }}

    .info p{{
    margin:6px 0;
    }}

    @media print {{
        .noprint {{
            display:none;
        }}
    }}

    </style>

    </head>

    <body>

    <div class="box">

    <div class="noprint">

    <a href="{back_link}"
    class="btn">

    ← Back

    </a>

    <button
    class="btn"
    onclick="window.print()">

    Print

    </button>

    </div>

    <h2>RSRTC INDENT DETAIL</h2>

    <div class="info">

    <p><b>Depot :</b> {record[0]}</p>

    <p><b>Date :</b> {record[1]}</p>

    <p><b>Vehicle :</b> {record[2]}</p>

    <p><b>Indent No :</b> {record[3]}</p>

    <p><b>Technician :</b> {record[4]}</p>

    </div>

    <table>

    <tr>

    <th>LF No</th>
    <th>Part No</th>
    <th>Item Name</th>
    <th>Source</th>
    <th>Qty</th>
    <th>Rate</th>
    <th>Total</th>

    </tr>

    {rows}

    </table>

    <h2>

    Grand Total : ₹ {grand_total:,.2f}

    </h2>

    </div>

    </body>

    </html>

    """

@app.route("/admin_report")
def admin_report():
    if session.get("role") != "admin":
        return redirect("/login")
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        i.depot,
        i.date,
        i.vehicle,
        i.indent_no,
        i.technician,
        d.lf_no,
        d.part_no,
        d.item_name,
        d.source,
        d.qty,
        d.rate,
        d.total
    FROM indents i
    JOIN indent_items d
    ON i.id = d.indent_id
    ORDER BY i.id DESC
    """)

    data = cur.fetchall()

    cur.close()
    pool.putconn(conn)

    depot = request.args.get("depot","")
    from_date = request.args.get("from_date","")
    to_date = request.args.get("to_date","")
    vehicle = request.args.get("vehicle","")
    item = request.args.get("item","")
    source = request.args.get("source","")

    filtered = []

    for r in data:

        if depot and r[0] != depot:
            continue

        if from_date and str(r[1]) < from_date:
            continue
 
        if to_date and str(r[1]) > to_date:
            continue

        if vehicle and vehicle.lower() not in str(r[2]).lower():
            continue
        if source and str(r[8]).lower() != source.lower():
            continue

        if item:

            item_search = item.lower().split("|")[0].strip()

            search_text = f"{r[5]} {r[6]} {r[7]}".lower()

            if item_search not in search_text:
                continue

        filtered.append(r)
    page = int(request.args.get("page", 1))

    per_page = 100

    total_records = len(filtered)

    start = (page - 1) * per_page

    end = start + per_page

    page_records = filtered[start:end]    
    # ---------- ITEM OPTIONS ----------

   
    item_options = ""

    for _, row in item_df.iterrows():

        lf = str(row["LFNo"])
        part = str(row["PartNo"])
        item_name = str(row["PartDesc"])

        display = f"{lf} | {part} | {item_name}"

        item_options += f'''
        <option value="{display}">
        '''

    # ---------- VEHICLE OPTIONS ----------

    

    vehicle_options = ""

    if depot:

        vehicles = sorted(
            vehicle_df[
                vehicle_df["NAME"].astype(str).str.upper() == depot.upper()
            ]["VEH_NO"].astype(str).unique()
        )

    else:

        vehicles = sorted(
            vehicle_df["VEH_NO"].astype(str).unique()
        )

    for v in vehicles:

        selected = ""

        if v == vehicle:
            selected = "selected"

        vehicle_options += f'''
        <option value="{v}">
        {v}
        </option>
        '''

    depot_list = sorted(DEPOTS)

    depot_options = '<option value="">All Depots</option>'

    for d in depot_list:

        selected = ""

        if d == depot:
            selected = "selected"

        depot_options += f'''
        <option value="{d}" {selected}>
        {d}
        </option>
        '''

    rows = ""

    for row in page_records:

        rows += f"""

        <tr>

        <td>{row[1]}</td>

        <td>{row[0]}</td>

        <td>{row[2]}</td>

        <td>{row[3]}</td>

        <td>{row[4]}</td>

        <td>{row[5]}</td>

        <td>{row[6]}</td>

        <td>{row[7]}</td>

        <td>{row[8]}</td>

        <td>{row[9]}</td>

        <td>{row[10]}</td>
        
        <td>{row[11]}</td>

        </tr>

        """

    total_pages = max(
        1,
        (total_records + per_page - 1) // per_page
    )
    pagination_info = f"""
    <div style="
    text-align:center;
    margin-bottom:10px;
    font-weight:bold;
    font-size:16px;
    ">
    Page {page} of {total_pages}
    </div>
    """
    pagination = ""

    start_page = max(1, page - 5)
    end_page = min(total_pages, page + 5)

    for p in range(start_page, end_page + 1):
        if p == page:

            pagination += f"""
            <span style="
            padding:8px 12px;
            background:#003d80;
            color:white;
            margin:2px;
            border-radius:5px;">
            {p}
            </span>
            """

        else:

            pagination += f"""
            <a href="?page={p}&depot={depot}&from_date={from_date}&to_date={to_date}&vehicle={vehicle}&item={item}&source={source}"
            style="
            padding:8px 12px;
            background:#eee;
            margin:2px;
            border-radius:5px;
            text-decoration:none;">
            {p}
            </a>
            """
    if end_page < total_pages:

        pagination += """
        <span style="
        padding:8px;
        font-weight:bold;
        ">
        ...
        </span>
        """

        pagination += f"""
        <a href="?page={total_pages}&depot={depot}&from_date={from_date}&to_date={to_date}&vehicle={vehicle}&item={item}&source={source}"
        style="
        padding:8px 12px;
        background:#eee;
        margin:2px;
        border-radius:5px;
        text-decoration:none;">
        {total_pages}
        </a>
        """
    if rows == "":

        rows = """

        <tr>

        <td colspan="12"
        style="text-align:center;color:red;font-weight:bold;">

        No Record Found

        </td>

        </tr>

        """

    grand_total = len(filtered)

    return f"""

<!DOCTYPE html>

<html>

<head>
<script>

window.history.pushState(null, "", window.location.href);

window.onpopstate = function () {{

    if(confirm("Do you want to Logout ?")){{

        window.location.href="/login";

    }}else{{

        window.history.pushState(null, "", window.location.href);

    }}

}};

</script>
<title>Admin Report</title>

<style>

body{{
font-family:Arial;
background:#eef2f7;
padding:20px;
}}

.box{{
background:white;
padding:25px;
border-radius:15px;
}}

input,select{{
padding:10px;
margin:5px;
}}

button{{
padding:10px 20px;
background:green;
color:white;
border:none;
border-radius:5px;
cursor:pointer;
}}

tr:hover{{
background:#fff4cc;
}}

a{{
color:#003d80;
font-weight:bold;
text-decoration:none;
}}

a:hover{{
color:red;
}}

table{{
width:100%;
border-collapse:collapse;
margin-top:20px;
}}

td{{
    border:1px solid #ddd;
    padding:6px;
    font-size:12px;
}}

th{{
    background:#003d80;
    color:white;
    padding:6px;
    font-size:12px;
}}

th:nth-child(7),
td:nth-child(7){{
max-width:100px;
overflow-wrap:break-word;
white-space:normal;
}}
.summary{{
background:#003d80;
color:white;
padding:15px;
border-radius:10px;
margin-bottom:20px;
}}

@media print {{

form,button{{
display:none;
}}

}}

</style>

</head>

<body>

<div class="box">
<a href="/logout"
style="
background:#003d80;
color:white;
padding:10px 20px;
text-decoration:none;
border-radius:5px;
display:inline-block;
margin-bottom:15px;
font-weight:bold;
">

← Logout

</a>
<a href="/download_database"
style="
background:green;
color:white;
padding:10px 20px;
text-decoration:none;
border-radius:5px;
display:inline-block;
margin-left:10px;
font-weight:bold;
">
⬇ Download Database
</a>
<h2>RSRTC ADMIN REPORT</h2>

<div class="summary">

Total Records : {len(filtered)}


</div>

<form>

<select name="depot">

{depot_options}

</select>

<input
type="date"
name="from_date"
value="{from_date}">

<input
type="date"
name="to_date"
value="{to_date}">

<input
type="text"
name="vehicle"
list="vehiclelist"
value="{vehicle}"
placeholder="Vehicle Number">

<datalist id="vehiclelist">

<option value="">
All Vehicles
</option>

{vehicle_options}

</datalist>

<input
type="text"
name="item"
list="itemlist"
value="{item}"
placeholder="LF No / Part No / Item Name">

<datalist id="itemlist">

{item_options}

</datalist>

Source

<select name="source">

<option value="">All</option>

<option value="Central Store"
{"selected" if source=="Central Store" else ""}>
Central Store
</option>

<option value="Central Workshop"
{"selected" if source=="Central Workshop" else ""}>
Central Workshop
</option>

<option value="Local Purchase"
{"selected" if source=="Local Purchase" else ""}>
Local Purchase
</option>

</select>

<button type="submit">

Search

</button>

<button
type="button"
onclick="window.print()">

Print

</button>

</form>
<button
type="button"
onclick="window.print()">

🖨 Print Report

</button>
<table>

<tr>

<th>Date</th>
<th>Depot</th>
<th>Vehicle</th>
<th>Indent No</th>
<th>Technician</th>
<th>LF No</th>
<th>Part No</th>
<th>Item Name</th>
<th>Source</th>
<th>Qty</th>
<th>Rate</th>
<th>Total</th>

</tr>

{rows}

</table>
<div style="
text-align:center;
margin-top:20px;
">

{pagination_info}

{pagination}

</div>
</div>

</body>

</html>

"""

from flask import send_file
import pandas as pd
from datetime import datetime

@app.route("/download_database")
def download_database():

    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_conn()

    query = """
    SELECT
        i.depot,
        i.date,
        i.vehicle,
        i.indent_no,
        i.technician,
        d.lf_no,
        d.part_no,
        d.item_name,
        d.source,
        d.qty,
        d.rate,
        d.total
    FROM indents i
    JOIN indent_items d
    ON i.id = d.indent_id
    ORDER BY i.id DESC
    """

    try:
        df = pd.read_sql(query, conn)

    finally:
        pool.putconn(conn)

    filename = f"RSRTC_DATABASE_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.xlsx"

    df.to_excel(filename, index=False)

    return send_file(
        filename,
        as_attachment=True
    )
@app.route("/supervisor_report")
def supervisor_report():
    if session.get("role") != "supervisor":
        return redirect("/login")
    from datetime import datetime, timedelta

    vehicle = request.args.get("vehicle","")
    from_date = request.args.get("from_date","")
    to_date = request.args.get("to_date","")
    days = request.args.get("days","")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        i.date,
        i.depot,
        i.vehicle,
        i.indent_no,
        d.lf_no,
        d.part_no,
        d.item_name,
        d.qty
    FROM indents i
    JOIN indent_items d
    ON i.id = d.indent_id
    ORDER BY i.id DESC
    """)

    data = cur.fetchall()

    cur.close()
    pool.putconn(conn)

    if days == "7":

        to_date = datetime.today().strftime("%Y-%m-%d")

        from_date = (
            datetime.today() - timedelta(days=7)
        ).strftime("%Y-%m-%d")

    vehicle_options = ""

    vehicles = sorted(
        vehicle_df["VEH_NO"].astype(str).unique()
    )

    for v in vehicles:

        selected = ""

        if v == vehicle:
            selected = "selected"

        depot_name = ""

        try:
            depot_name = vehicle_df[
                vehicle_df["VEH_NO"].astype(str) == str(v)
            ]["NAME"].iloc[0]
        except:
            pass

        vehicle_options += f'''
        <option value="{v}">
        {depot_name} / {v}
        </option>
        '''

    rows = ""
    total_qty = 0

    if vehicle != "":

        for r in data:

            if str(r[2]).lower() != vehicle.lower():
                continue

            if from_date and str(r[0]) < from_date:
                continue

            if to_date and str(r[0]) > to_date:
                continue

            try:
                qty = float(r[7] or 0)
            except:
                qty = 0

            total_qty += qty
            try:
                display_date = datetime.strptime(
                    str(r[0]),
                    "%Y-%m-%d"
                ).strftime("%d-%m-%Y")
            except:
                display_date = r[0]
            rows += f"""
            <tr>

            <td>{display_date}</td>

            <td>{r[1]}</td>

          

            <td>{r[3]}</td>

            <td>{r[4]}</td>

            <td>{r[5]}</td>

            <td>{r[6]}</td>
            <td>{qty}</td>

            </tr>
            """
    if rows == "":

        rows = """
        <tr>
        <td colspan="7"
        style="text-align:center;color:red;font-weight:bold;">
        No Record Found
        </td>
        </tr>
        """    
    return f"""

<!DOCTYPE html>

<html>

<head>
<script>

window.history.pushState(null, "", window.location.href);

window.onpopstate = function () {{

    if(confirm("Do you want to Logout ?")){{

        window.location.href="/login";

    }}else{{

        window.history.pushState(null, "", window.location.href);

    }}

}};

</script>
<title>Supervisor Report</title>

<style>

body{{
font-family:Arial;
background:#eef2f7;
padding:20px;
}}

.box{{
background:white;
padding:25px;
border-radius:15px;
}}

input,select{{
padding:10px;
margin:5px;
}}

button{{
padding:10px 20px;
background:green;
color:white;
border:none;
border-radius:5px;
cursor:pointer;
}}

table{{
width:100%;
border-collapse:collapse;
margin-top:20px;
font-size:14px;
}}

th, td{{
border:1px solid #ddd;
padding:8px;
text-align:left;
}}

th{{
background:#003d80;
color:white;
}}
.summary{{
background:#003d80;
color:white;
padding:15px;
border-radius:10px;
margin-bottom:20px;
}}

@media print {{

form,button,a{{
display:none;
}}

}}

</style>

</head>

<body>

<div class="box">

<a href="/logout"
style="
background:#003d80;
color:white;
padding:10px 20px;
text-decoration:none;
border-radius:5px;
display:inline-block;
margin-bottom:15px;
">

← Logout

</a>

<h2>Vehicle Inspection Report (Supervisor Module)</h2>

<div class="summary">

Vehicle : {vehicle}

<br><br>

Total Quantity : {total_qty}

</div>

<form>

<input
type="text"
name="vehicle"
list="vehiclelist"
placeholder="Type Vehicle Number"
value="{vehicle}">

<datalist id="vehiclelist">

{vehicle_options}

</datalist>

<input
type="date"
name="from_date"
value="{from_date}">

<input
type="date"
name="to_date"
value="{to_date}">

<select name="days">

<option value="">
Custom Date
</option>

<option value="7">
Last 7 Days
</option>

</select>

<button type="submit">

Search

</button>

<button
type="button"
onclick="window.print()">

Print

</button>

</form>

<table>

<tr>

<th>Date</th>
<th>Depot</th>
<th>Indent No</th>
<th>LF No</th>
<th>Part No</th>
<th>Item Name</th>
<th>Qty</th>

</tr>

{rows}

</table>

</div>

</body>

</html>

"""
if __name__ == "__main__":
    app.run()
