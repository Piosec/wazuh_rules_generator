from flask import Flask, render_template, request, redirect,  url_for
from flask_bootstrap import Bootstrap
import json
import requests
import html
import xml.etree.ElementTree as ET
from xml.dom import minidom

app = Flask(__name__)
Bootstrap(app)


headers = ['level','id','maxsize','frequency','timeframe','ignore','overwrite','noalert']
def getConfig():
    json = checkJson()
    print(json['api'])
    host = json['api']['host']	
    username = json['api']['username']	
    password = json['api']['password']	
    return host,username,password

def getRules(host,username,password):
	url =  "https://"+host+":55000/rules?offset=0"
	response = requests.get(url, auth=(username,password), verify=False)
	return response.json()

def checkJson():
    try:
        config_file = open("config.json","r")
        json_data = json.load(config_file)
    except FileNotFoundError:
    	return render_template('error.html', error='The requested file doesn\'t exits.')
    except ValueError:		
    	return render_template('error.html', error='The json isn\'t correct, please check it.')	
    	#return redirect(url_for('error', error='The json isn\'t correct, please check it.'))	
    except:		
    	return render_template('error.html', error='A strange error occured, I don\'t know why..')	
    return json_data

def getRulesInformations(data):
	data = data['data']
	items = data['items']
#	for item in items:
#		rule_id = item['id']
#		rule_description = item['description']
#		rule_status = item['status']
	return items

def filter_post_data(key,data):
    #sanitized = html.escape(data)
    sanitized = (data)
    if sanitized not in  ["",None,"level"]:     
        if key in ["id","ignore"] and int(sanitized) in range(1,1000000):
            return key,sanitized
        elif key == "level" and int(sanitized) in range(0,17):
            return key,sanitized
        elif key in ["maxsize","frequency"] and int(sanitized) in range(1,10000):
            return key,sanitized
        elif key == "timeframe" and int(sanitized) in range(1,100000):
            return key,sanitized
        elif key == "overwrite" and sanitized in ["yes","no","Overwrite"]:
            return key,sanitized
        elif key == "noalert":
            return key,sanitized
        elif key == "options" and sanitized == "Options":
            return key,"empty"
        else:
            return key,sanitized
    else:
        return key,"empty"

def construct_xml(form):
    rule = ET.Element('rule')
    for key,data in form.items():
        key, sanitized = filter_post_data(key,data)
        if sanitized in ['Overwrite','No alert','level','Options','empty']:
            continue
        elif key in headers:
            rule.set(str(key),str(sanitized))
        elif sanitized not in ['']:
            elem = ET.SubElement(rule,key)
            elem.text = sanitized
        else:
            continue
    return ET.tostring(rule, method='xml')

@app.route('/',methods=['GET'])
def index():
	host,username,password = getConfig()	
	response = getRules(host,username,password)
	items = getRulesInformations(response)
	return render_template('index.html', items=items)

@app.route('/generate',methods=['POST','GET'])
def generate():
    if request.method == 'POST':
        xml = construct_xml(request.form)
        f_xml = open('new_rule.xml','w')
        f_xml.write(xml.decode('utf-8'))
        f_xml.close()
        return redirect('/generate')
    else:
        try:
            f_xml = open('new_rule.xml','r')
        except FileNotFoundError:
            return render_template('error.html', error='The requested file doesn\'t exits.')
        except:
            return render_template('error.html', error='An error occured during writing the content into the xml file.')
        xml = minidom.parse(f_xml)
        return render_template('generate.html',content=html.unescape(xml.toprettyxml()))


@app.route('/config',methods=['GET','POST'])
def config():
    if request.method == 'POST':
        json_data = request.form
        json_data = json_data.get('config') 
        update_json = open('config.json','w')
        update_json.write(json_data)
        update_json.close()
        content=json_data
    elif request.method == 'GET':
        json_data = checkJson()	
        json_data = json.dumps(json_data, indent=2, sort_keys=True)
        content=json_data
    else:
    	return render_template('error.html', error='The requested method is not available.')
    
    return render_template('config.html', content=content)

@app.route('/error',methods=['GET'])
def error():
    return render_template('error.html',error='An error :)')

if __name__ == '__main__':
	app.run(debug=True)
