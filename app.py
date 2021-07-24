from flask import Flask, request, Response, jsonify
from flask_ngrok import run_with_ngrok
import cv2
import json
import numpy as np
import pytesseract
import re


pytesseract.pytesseract.tesseract_cmd = "C:/Users/pc/AppData/Local/Tesseract-OCR/tesseract.exe" # Location of 'tesseract.exe' file
tessdata_dir_config = '--tessdata-dir "C:/Users/pc/AppData/Local/Tesseract-OCR/tessdata"' # Location of 'tessdata' folder
app = Flask(__name__)
run_with_ngrok(app)


def error_handle(error_message, code=1, status=500, mimetype='application/json'):
    return Response(json.dumps({"success" : False, "message": error_message, "code": code }), status=status, mimetype=mimetype)


def success_handle(output, status=200, mimetype='application/json'):
	return Response(output, status=status, mimetype=mimetype)


def automatic_brightness_and_contrast(img, clip_hist_percent=1):
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	hist = cv2.calcHist([gray],[0],None,[256],[0,256])
	hist_size = len(hist)
	accumulator = []
	accumulator.append(float(hist[0]))
	for index in range(1, hist_size):
		accumulator.append(accumulator[index -1] + float(hist[index]))
	maximum = accumulator[-1]
	clip_hist_percent *= (maximum/100.0)
	clip_hist_percent /= 2.0
	minimum_gray = 0
	while accumulator[minimum_gray] < clip_hist_percent:
		minimum_gray += 1
	maximum_gray = hist_size -1
	while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
		maximum_gray -= 1
	alpha = 255 / (maximum_gray - minimum_gray)
	beta = -minimum_gray * alpha
	auto_result = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
	return auto_result


def getMCR(img):
	img = automatic_brightness_and_contrast(img)
	c=0
	while True:
		txt = pytesseract.image_to_string(img)
		if c==4 or (re.search('\w\d\d\d\d\d\d', txt) != None and re.search('\d\d\d\d\d\d', txt) != None):
			break
		img = cv2.rotate(img, cv2.cv2.ROTATE_90_CLOCKWISE)
		c+=1
	return img


def removeJunk(txt):
	return txt.replace('<','').replace(' ','')


def fixDigits(txt):
	data = [('A','-'),('B',8),('C','-'),('D',0),('E',3),('F',7),('G',6),('H',8),('I',1),('J','-'),('K',8),('L','-'),('M','-'),('N','-'),('O',0),('P',9),('Q',2),('R','-'),('S',5),('T',7),('U',0),('V','-'),('W','-'),('X','-'),('Y',5),('Z',2)]
	for t in data:
		txt = txt.replace(t[0], str(t[1]))
	return txt


def fixLetters(txt):
	data = [(0,'O'),(1,'I'),(2,'Z'),(3,'-'),(4,'A'),(5,'S'),(6,'G'),(7,'T'),(8,'B'),(9,'-')]
	for t in data:
		txt = txt.replace(str(t[0]), t[1])
	return txt


def getText(img):
	text = pytesseract.image_to_string(img, lang="OCRB", config=tessdata_dir_config)
	text = text[text.find(r'P<'):]
	indices = [0, 44]
	lines = [text[index:] for index in indices]
	if len(lines[0]) < 35:
		return ({},0)
	lines[1] = lines[1].replace('\n','')
	if len(lines[1]) < 28:
		return ({},0)
	doc_type = lines[0][0]
	# print(doc_type)
	pp_type = removeJunk(lines[0][1])
	# print(pp_type)
	iss_country = lines[0][2:5]
	# print(iss_country)
	temp = re.findall(r'\w+', lines[0][5:])
	sur_name = fixLetters(temp[0])
	# print(sur_name)
	first_name = fixLetters(temp[1])
	# print(first_name)
	pp_no = removeJunk(lines[1][:9])
	# print(pp_no)
	nat = lines[1][10:13]
	# print(nat)
	dob = fixDigits(lines[1][13:19])
	# print(dob)
	sex = fixLetters(lines[1][20])
	# print(sex)
	exp = fixDigits(lines[1][21:27])
	# print(exp)
	dic = {
		"Document Type" : doc_type,
		"Passport Type" : pp_type,
		"Issuing Country" : iss_country,
		"Surname" : sur_name,
		"First Name" : first_name,
		"Passport Number" : pp_no,
		"Nationality" : nat,
		"Date Of Birth(YYMMDD)" : dob,
		"Sex" : sex,
		"Expiry Date(YYMMDD)" : exp
	}
	return (json.dumps(dic, indent = 4), 1) 


@app.route('/')
def welcome():
	return 'Welcome!'


@app.route('/index')
def index():
	return '''
	/api/getData to get JSON reponse containing passport information'''


@app.route("/api/getData", methods=['POST', 'GET'])
def getData():
	if request.method == 'POST':
		try:	
			if 'file' not in request.files:
				return error_handle('Please send image file.')
			file = request.files.get('file')
			npimg = np.fromfile(file, np.uint8)
			img_c = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
			img = getMCR(img_c)
			data, f = getText(img)
			if f==0:
				return error_handle("Please Enter a clear Image!")
			return success_handle(data)
		except Exception as e:
			return error_handle(e)
	return '''
		<!DOCTYPE HTML>
		<title>PP MRZ Scanner</title>
		<h1>Upload an Image</h1>
		<form method=post enctype=multipart/form-data>
		<input type=image name=file>
		<input type=submit value=Upload>
		</form>
		'''


app.run()