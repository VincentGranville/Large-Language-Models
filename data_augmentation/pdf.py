# https://www.geeksforgeeks.org/working-with-pdf-files-in-python/
# https://www.geeksforgeeks.org/how-to-extract-images-from-pdf-in-python/
# https://www.geeksforgeeks.org/how-to-extract-pdf-tables-in-python/
# https://stackoverflow.com/questions/2196621/how-to-extract-formatted-text-content-from-pdf
# https://www.freecodecamp.org/news/extract-data-from-pdf-files-with-python/

# importing required modules
import PyPDF2
 
# creating a pdf file object
pdfFileObj = open('abi-test.pdf', 'rb')
 
# creating a pdf reader object
pdfReader = PyPDF2.PdfReader(pdfFileObj)
 
# printing number of pages in pdf file
print(len(pdfReader.pages))
 
# creating a page object
pageObj = pdfReader.pages[0]
 
# extracting text from page
print(pageObj.extract_text())
 
# closing the pdf file object
pdfFileObj.close()

