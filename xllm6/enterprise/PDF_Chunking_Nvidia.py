# Input PDF for this script: https://drive.google.com/file/d/1Daa9oZJm4-b6NqUsVGxK2euemcFnf8jH/

# https://pymupdf.readthedocs.io/en/latest/page.html#Page.find_tables
# https://stackoverflow.com/questions/56155676/how-do-i-extract-a-table-from-a-pdf-file-using-pymupdf

import fitz  # PyMuPDF


def update_item_ID(k, entity_idx, type, table_ID): 

    idx = entity_idx[k]
    if type == 'Data':
        # table: data row
        flag = 'TD' # 
    elif type == 'Note':
        # table: labels
        flag = 'TL'
    idx_list = list(idx)
    idx_list[1] = flag + str(table_ID)
    entity_idx[k] = tuple(idx_list) 

    return(entity_idx)


def detect_table(xLLM_entity):

    # detect and flag simple pseudo-tables

    entity_txt  = xLLM_entity[0]                   
    entity_type = xLLM_entity[1] 
    entity_idx  = xLLM_entity[2]
    table_ID = -1
    table_flag = False

    for k in range(1, len(entity_type)):

        type = entity_type[k]
        text = entity_txt[k]
        old_text = entity_txt[k-1]
        old_type = entity_type[k-1]
  
        if ( (
               (type == 'Data' and old_type == 'Note') or
               (type == 'Note' and old_type == 'Data') or 
               (type == 'Data' and old_type == 'Data')
             ) 
             and old_text.count('|') == text.count('|')
             and text.count('|') > 2
           ):
            print("detected table", table_ID + 1)
            if not table_flag:
                table_ID += 1
                table_flag = True
            idx = entity_idx[k]
            old_idx = entity_idx[k-1]
            
            # update item_ID (idx[1] and old_idx[1]) in current and previous row
            # item_ID starts with letter D if data, or N if labels 

            update_item_ID(k, entity_idx, type, table_ID) 
            update_item_ID(k-1, entity_idx, old_type, table_ID)

        else:
            #table_ID = -1
            table_flag = False
                
    return(xLLM_entity)


def cprint_page(xLLM_entity, OUT):

    entity_txt  = xLLM_entity[0]                   
    entity_type = xLLM_entity[1] 
    entity_idx  = xLLM_entity[2]

    for k in range(len(entity_type)):

        type = entity_type[k]
        text = entity_txt[k]
        text = text.strip()
        text = text.replace("  ", " ")
        text = text.replace(" |", "|")
        text = text.replace("| ", "|")
        text = text.replace("||","|")
        text = text.encode('unicode-escape').decode('ascii')
        text = text.replace('\\u2022', '•')
        text = text.replace('\\u2013', '--')
        text = text.replace('\\u2014', '--')
        text = text.replace('\\u2019', "'")
        text = text.replace('\\u201c', '"')
        text = text.replace('\\u201d', '"')

        idx  = entity_idx[k]
        doc_ID   = idx[3]
        block_ID = idx[0] 
        item_ID  = idx[1] 
        sub_ID   = idx[2] 
        pn = idx[4]   # page number
        fs = idx[5]   # font size
        fc = idx[6]   # font color
        ft = idx[7]   # font typeface
        #- print(k, type, idx, text) 
        OUT.write(f"{type:<8}{block_ID:>3}{item_ID:>5}{sub_ID:>3}{pn:>3}"
                  f"{fs:>5}{fc:>9} {ft:<20}{text:<80}\n")
        
    OUT.write("\n")
    return()


def update_page(text, type, entity, idx): 

    entity_txt  = entity[0] 
    entity_type = entity[1] 
    entity_idx  = entity[2]
    block_ID = idx[0]
    item_ID  = idx[1]
    sub_ID   = idx[2]
    k = len(entity_txt)
    if k > 0:
        old_type = entity_type[k-1]
        old_idx = entity_idx[k-1]
        old_block_ID = old_idx[0]
        old_item_ID  = old_idx[1]
        old_sub_ID   = old_idx[2]
    else:
        old_type = ""
        old_block_ID = ""
        old_item_ID  = ""
        old_sub_ID   = ""
    if type in ('Note', 'Data'):
        sep = "|"
    else:
        sep = " "

    if (type == old_type and block_ID == old_block_ID
          and item_ID == old_item_ID and sub_ID == old_sub_ID):  
       new_text = entity_txt[k-1] + text + sep
       entity_txt[k-1] = new_text
    else:
        entity_txt.append(sep + text + sep)
        entity_type.append(type)
        entity_idx.append(idx)
    return(entity)


def convert_pdf_to_json(pdf_path, json_path, doc_ID, text_path):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    content = ""

    # Iterate through the pages
    for page_num in range(len(pdf_document)): 
        OUT.write("\n----------------------------\n")
        OUT.write("Processing page " + str(page_num) + "\n\n")
        print("Page:", page_num)
        page = pdf_document.load_page(page_num) 

        text_data = page.get_text("dict")  # also extract as "json" to get tokens in green font

        tabs = page.find_tables()
        for tabs_index, tab in enumerate(tabs): 
            # iterate over all tables
            index = (page_num, tabs_index)
            table_data = tab.extract()  # extracting tabs[i], the i-th table in this page
            if len(table_data) > 0: 
                # if not, ignore this table (note the important parameter threshold here)
                OUT.write("Table " + str(index) + ":\n")
                for row in table_data:
                    OUT.write(str(row) + "\n")
                OUT.write("\n")
 
        itemize = False
        item_ID = -1
        sub_ID = -1
        block_ID = -1
        item = ""
        fsm = -1 # top level font size in bullet list
        fst = 64 # min title font size (top parameter)
        title = ""
        notes = ""
        old_block_number = -1
        old_font_size = -1
        entity_txt = []
        entity_idx = []
        entity_type = []
        type = ""
        old_text = ""
        old_type = ""

        for block in text_data["blocks"]:
            if block["type"] == 0:  # Text block
                block_number = block["number"]
                for line in block["lines"]:
                    for span in line["spans"]:

                        text = span["text"]
                        font_name = span["font"]
                        font_size = span["size"]
                        font_size = round(font_size,1)
                        font_color = span["color"]

                        if font_size > fst:
                            type = 'Title'
                        elif ord(text[0]) == 8226:
                            itemize = True
                            if fsm == -1:
                                fsm = font_size
                            if font_size > 0.98 * fsm:
                                item_ID += 1 
                                type = 'List'
                            else:
                                sub_ID +=1 
                                type = 'SubList'
                        elif itemize:
                            #- itemize = ((0.99 < font_size/old_font_size < 1.01) and 
                            #-            (not text[0].isupper() or ord(old_text[0]) == 8226))
                            itemize = ((0.99 < font_size/old_font_size < 1.01) or 
                                       (ord(old_text[0]) == 8226)) 

                            if not itemize:
                                item_ID = -1
                                sub_ID = -1
                                block_ID += 1
                                type = 'Note'
                        else:
                            if not text[0].isdigit() and text[0] not in ('$', '+', '-'):
                                type = 'Note'
                            #- elif block_number != old_block_number: 
                            else:
                                type = 'Data' 
                        
                        if block_ID == -1:
                            block_ID += 1 
                        elif ((type not in (old_type, 'List', 'SubList')) or   
                               (not (0.99 < font_size/old_font_size < 1.01))):
                            if (old_text != "" and ord(old_text[0]) != 8226 and 
                                    type not in ('List', 'SubList')): 
                                block_ID += 1

                        idx = (block_ID, item_ID, sub_ID, doc_ID, page_num, font_size, 
                               font_color, font_name, block_number) 
                        entity = (entity_txt, entity_type, entity_idx)
                        update_page(text, type, entity, idx) 

                        old_font_size = font_size
                        old_text = text
                        old_type = type

                    old_block_number = block_number
                      
        entity = detect_table(entity)
        cprint_page(entity, OUT)        

        image_list = page.get_images()
        for image_index, img in enumerate(image_list, start=1):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            size = len(image_bytes)
            ext = base_image["ext"]
            index = (page_num, image_index)
            OUT.write(f"Image {str(index):<8}{str(ext):>5} size = {str(size):>6}\n")
            #- with open(f"image_{page_num + 1}_{image_index}.{ext}", "wb") as image_file:
            #-     image_file.write(image_bytes)

        content += "__P" + str(page_num) + "\n" + page.get_text("json")  # "text", "html", "json"

    # Write the json content to a file
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json_file.write(content)


# --- Main ---

doc_ID = 0 # to identify the PDF doc
filename = 'nvda-f2q24-investor-presentation-final-1'
pdf_path = filename + '.pdf'
json_path = filename + '.json'
text_path = filename + '.txt'

OUT = open(text_path, "wt", encoding="utf-8")
convert_pdf_to_json(pdf_path, json_path, doc_ID, OUT)
OUT.close()


# --- PDF to Images ---

from PIL import Image

pdf_document = fitz.open(pdf_path)
zoom = 2 # to increase the resolution
mat = fitz.Matrix(zoom, zoom)

for page_num in range(len(pdf_document)):
    page = pdf_document.load_page(page_num) 
    pix = page.get_pixmap(matrix = mat)  # or (dpi = 300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    filename = "PDF" + str(page_num) + '.png' # you could change image format accordingly
    img.save(filename) 
    print('Converting PDFs to Image ... ' + filename)


