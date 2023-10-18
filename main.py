import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tokenize import TreebankWordTokenizer
# from fuzzywuzzy import fuzz
from flask import Flask, render_template, request
import PyPDF2  # Import PyPDF2 for PDF text extraction
from werkzeug.utils import secure_filename  # Import secure_filename for secure file uploads
import os  # Import os for file operations
import pdfplumber

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def edit_distance(s, t):
    n = len(s)
    m = len(t)
    prev = [j for j in range(m + 1)]
    curr = [0] * (m + 1)

    for i in range(1, n + 1):
        curr[0] = i
        for j in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                curr[j] = prev[j - 1]
            else:
                mn = min(1 + prev[j], 1 + curr[j - 1])
                curr[j] = min(mn, 1 + prev[j - 1])
        prev = curr.copy()
    return prev[m]

def modify1(paragraph, names):
    variations = []
    def generate_variations(input_list):
        nonlocal variations
        for name in input_list:
            name_parts = name.split()
            first_letters = [part[0] for part in name_parts]
            n = len(name_parts)
            recur(name_parts, first_letters, 0, n, "", False)
        return [variation.lower() for variation in variations]


    def recur(name_parts, first_letters, i, n, st, flag):
        nonlocal variations
        if i == n:
            variations.append(st)
            return
        if flag is False:
            st2 = st
            st3 = st
            st += " " + name_parts[i]
            st3 += ". " + name_parts[i]
            st2 += first_letters[i].upper()
            recur(name_parts, first_letters, i + 1, n, st, True)
            recur(name_parts, first_letters, i + 1, n, st3, True)
            recur(name_parts, first_letters, i + 1, n, st2, False)

    original_list = names.copy()
    result = generate_variations(original_list)
    for i in variations:
        names.append(i)
    prefixes = ["dr", "md", "mr", "ms", "mrs", "doctor", "mister", "miss", "missus", "md.", "dr.", "mr.", "mrs.", "miss", "prof", "prof.", "sir", "Md"]
    names2 = [name_part.lower() for name in names for name_part in name.split()]
    print(names2)
    names2.extend(prefixes)
    print(variations)


    # # Split the paragraph into sentences,
    # from nltk.tokenize import sent_tokenize, word_tokenize

    # Tokenize the paragraphs into sentences
    sentences = sent_tokenize(paragraph[0])

    # Tokenize each sentence into words and treat commas as separate words
    tokenizer = TreebankWordTokenizer()
    words = [tokenizer.tokenize(sentence) for sentence in sentences]

    print(words)
    for j in range(len(words)):
        for i in range(len(words[j])):
            # print(i , words[j][i])
            if words[j][i]=='@':
                print(i, words[j][i-1])
                words[j][i-1]='<NAME>'
            # if "-" in words[j][i]:
            #     w1=words[j][i].split("-")
            #     words[j][i]=w1[0]
            #     words[j].insert(i+1, "-")
            #     words[j].insert(i+, w1[1])
            # if words[j][i]=="(" and words[j][i+1]==")":
            # if words[j][i]=="(" and words[j][i+1]==")":
    #             break the list into two parts using this as sepeartor and remove the symbols


    # print(words)
    # print(names2)
    if "." in names2:
        names2.remove(".")
    def checkdist(word):
        # print(word)
        n=len(word)
        if len(word) <= 1:
            return False
        if len(word)<=2:
            return word in names2
        if word=="" or len(word)<=2:
            return False
        x=[]
        for i in names2:
            if abs(len(i)-len(word))>n//4:
                continue
            if edit_distance(word, i)<=n//4:
                return True
            x.append([i, edit_distance(word, i)])
        # print(word, ":" ,x)
        return False
    # print("names2 :" ,names2)
    for i in range(len(words)):
        print(i)
        j = 0
        while j < len(words[i]):
            if checkdist(words[i][j].lower()):
                Flag = True
                while j < len(words[i]) and checkdist(words[i][j].lower()):
                    words[i][j] = ""
                    if j != len(words[i]) - 1:
                        j += 1
                        Flag=True
                    else:
                        Flag=False
                    # print("aaaa")
                if Flag:
                    words[i][j - 1] = "<NAME>"
                else:
                    words[i][j] = "<NAME>"
                if checkdist(words[i][j].lower()):
                    words[i][j] = " "
            j += 1
    # print("words:" , words)
            # else:else
            #     print(words[i][j].lower())




    for x in words:
        while "" in x:
            x.remove("")
    # Reconvert sentences to a paragraph and add "."
    sentences = [" ".join(sentence).strip() for sentence in words if any(sentence)]
    paragraph = " ".join(sentences)
    # print(words)
    # print(paragraph)
    # replace (cid:127) with \n
    paragraph = paragraph.replace("( cid:127 )", "\n")  # Replace "cid:127" with a newline character
    # paragraph = paragraph
    return paragraph

def extract_text_from_pdf(pdf_file):
    pdf_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            # page_text = page_text.replace("( cid:127 )", "\n")  # Replace "cid:127" with a newline character

            pdf_text += page_text + '\n'  # Add line breaks to separate pages
    # split using ( cid:127 )
    # print(pdf_text)
    # pdf_text= pdf_text.split("( cid:127 )")
    return pdf_text

@app.route('/', methods=['GET', 'POST'])
def index():
    modified_paragraph = None

    if request.method == 'POST':
        paragraph_input = request.form['paragraph_input']
        names_input = request.form['names_input']
        pdf_file = request.files['pdf_file']

        if pdf_file:
            pdf_text = extract_text_from_pdf(pdf_file)
            paragraph_input += "\n" + pdf_text

        pinput = [str(paragraph_input)]
        names_input = names_input.split(';')
        modified_paragraph = modify1(pinput, names_input)

    return render_template('index.html', modified_paragraph=modified_paragraph)



if __name__ == '__main__':
    app.run(debug=True, port=8000)




# from flask import Flask
# app = Flask(__name__)
# @app.route('/')
# def index():
#     return "Hello World"
# if __name__ == "__main__":
#     app.run(debug = True)
#2751ab3d678ff0277ae80f9e8a74f218cfc70fe9a9cdc7bb1c137d7e47e33d53
