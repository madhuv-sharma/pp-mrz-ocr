import cv2
import json
import pytesseract
import re


pytesseract.pytesseract.tesseract_cmd = "C:/Users/pc/AppData/Local/Tesseract-OCR/tesseract.exe" # Location of 'tesseract.exe' file
tessdata_dir_config = '--tessdata-dir "C:/Users/pc/AppData/Local/Tesseract-OCR/tessdata"' # Location of 'tessdata' folder
file_loc = r"D:\COLLEGE APPLICATIONS\PP_Front.png" # Input Image Location


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
		print(txt)
		if c==4 or (re.search('\w\d\d\d\d\d\d\d', txt) != None and re.search('\d\d\d\d\d\d', txt) != None):
			break
		img = cv2.rotate(img, cv2.cv2.ROTATE_90_CLOCKWISE)
		c+=1
	cv2.imshow("Result", img)
	cv2.waitKey(0)
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
	nat = fixLetters(lines[1][10:13])
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
	return (json.dumps(dic), 1)


def main():
	try:
		img_c = cv2.imread(file_loc)
		img = getMCR(img_c)
		data, f = getText(img)
		if f==0:
			print("Please Enter a clear Image!")
			return
		file = open('output.json', 'w')
		json.dump(data, file, indent = 4)
	except Exception as e:
		print(e)


if __name__ == '__main__':
	main()