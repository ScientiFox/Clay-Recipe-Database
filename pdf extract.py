###
#   Script to extract clay recipe data from PDF downloads of favorites from glazy
###

#Standard
import math,time,random

#File handling
import glob,pickle

#Reading PDFs
import pymupdf,pymupdf4llm

#Regex processing
import re

#processing bytes images
import io
from PIL import Image

#Load from  local files
files = glob.glob("/pdfs/*.pdf")

#function to turn a set of lines from a segment of text into list of ingredients and amounts
def to_rep(seg,u,l):

    #replace out 'Testing' and multilines
    seg = re.sub("Testing","",seg)
    seg = re.sub("\n\n+","\n",seg)

    #Divide by line
    lns = seg.split("\n")
    lns = lns[u:l] #grab relevant lines

    rep = {} #Recipe dictionary
    cur_ing = '' #Current ingredient string
    i = 0 #index
    while i < len(lns): #Looping over all selectedlines
        try: #Try getting a float from this line, if so- it's an amount following an ingredient
            rep[cur_ing] = float(lns[i]) #Pop that value into the current ingredient list
            cur_ing = '' #clear for enxt ingredient
        except: #Otherwise,
            cur_ing = cur_ing + lns[i] #a new ingredient
        i+=1 #Increment over section

    #Return ingredients list
    return rep

#Convert a string to a searchable form
def make_searchable(st):
    st = st.lower() #All lower case
    st = re.sub("[^\w△-]","",st) #Remove whitespace and special characters
    return st #Return the new search-ready string

#little function to sanitize a string
reg_sani = lambda st: re.sub("([\(\[\{\)\]\}\*\-\&\.\?\+\^\$\|])","§\\1",st)


reps = {} #lookup of all identified recipes

#loop over all PDFs
for f in files:

    #Load in markdown style interpretation of the file - best for name extract step
    fmd = pymupdf4llm.to_markdown(f)
    fmd = re.sub("\n\n+","\n",fmd) #clear multiline spaces

    #Find the names of recipes with regex based on spacing and whitespace with header tags and bold format
    nmes = re.findall("# \*\*(.*)\*\*\S*\n\S*##",fmd)
    nmes = [re.sub("\*\*","",nme) for nme in nmes]    #Remove bolding tags from names

    #Open PDF more standard (not markdown on this oen)
    doc = pymupdf.open(f)

    txt = "" #Base full-text string
    imgs = [] #List of images on this file
    im_names = {} #names of images

    #Looping over every page in the doc
    for page in doc:

        text = page.get_text() #Grab this page's text
        txt = txt + text + "\n" #Add to full text

        #Search for identified recipe names in this page
        nop = [nme for nme in nmes if make_searchable(nme) in make_searchable(text)]

        #Grab out images on this page
        p_imgs = [(pi['xref'],pi['bbox']) for pi in page.get_image_info(xrefs=True)]

        #If no images
        if len(p_imgs) == 0:
            pass #skip
        elif len(p_imgs) == len(nop): #Otherwise, if images for each name on the page
            for i in range(len(nop)): #for each name on page
                n = nop[i] #Get name
                pi = p_imgs[i] #get image

                im = doc.extract_image(pi[0]) #peel out image
                tosearch = make_searchable(n) #make name searchable

                im_st = io.BytesIO(im['image']) #read bytes image
                im_dec = Image.open(im_st) #open image proper
                im_dec.save("imgs/"+tosearch+".png") #Save to local directory
                im_names[n] = "imgs/"+tosearch+".png" #Update this recipe name's listing with save location

        #If one image on page, but two recipe names on it
        elif len(p_imgs) == 1 and len(nop) == 2:
            yLC = p_imgs[0][1][1] #Check if image is closer to top or bottom of page
            if yLC < 54.0: #if closer to top- for the first recipe
                n = nop[0]
            else: #other wise, for the second recipe
                n = nop[1]
            pi = p_imgs[0] #grab the image
            im = doc.extract_image(pi[0]) #pull image data
            tosearch = make_searchable(n) #make name searchable

            im_st = io.BytesIO(im['image']) #read bytes image
            im_dec = Image.open(im_st) #open image proper
            im_dec.save("imgs/"+tosearch+".png") #Save to local directory
            im_names[n] = "imgs/"+tosearch+".png" #Update this recipe name's listing with save location
        else: #Other numbers of images on the page versus recipes are indeterminate, since the
            pass #  'length' and space of recipes is impractical to pin down.

    #section text copy 
    s_txt = txt+""

    nmes_in_txt = [] #List of names as-formatted extracted from the text
    for i in range(len(nmes)): #Going though the proper names
        nme = nmes[i] #get the next name

        #Search for a searchable-form match actually in the text and before a △ segment to get the in-text name
        in_tx = re.findall(reg_sani(nme).replace("§","\\").replace(" ","\s*")+"\s*△",s_txt)[0]

        #Find evertything between the in-text name and the start of the next section
        s_txt = re.findall(reg_sani(in_tx).replace("§","\\")+"([\s\S]*)",s_txt)[0]

        #update the in-text names with the trailing △ blanked
        nmes_in_txt = nmes_in_txt + [in_tx.replace("\n△","")]

        #If the name is found in the images, update the in-text to point to it, too
        if nme in im_names:
            im_names[nmes_in_txt[-1]] = im_names[nme]

    #Former extract, for posterity
    #nmes_in_txt = [re.findall(reg_sani(nme).replace("§","\\").replace(" ","\s*"),txt)[0] for nme in nmes]

    #Sanitize all the in-text names and replace the placeholder with the \
    nmes_in_txt = [reg_sani(nme).replace("§","\\") for nme in nmes_in_txt]

    #grab another processing section text bit
    s_txt = txt+""

    lst = [] #list of elements 

    for i in range(len(nmes_in_txt)-1): #for every name found in the text:
        #extract an entry between the name itself and the next name
        entry = re.findall("("+nmes_in_txt[i]+"[\s]*?△[\s\S]*?)"+nmes_in_txt[i+1]+"[\s]*?△",s_txt)

        #Iteratively pull out each captured entry, to handle partial repeats of names
        s_txt = re.findall(reg_sani(entry[0]).replace("§","\\")+"([\s\S]*)",s_txt)[0]

        #Add entry to the list
        lst = lst + [entry[0]]

    #Grab out the last entry (since it has no i+1 to extract between)
    entry = re.findall("("+nmes_in_txt[len(nmes_in_txt)-1]+"[\s\S]*)",s_txt)
    lst = lst + [entry[0]]

    #Now that we have the recipe sections divided, we can extract the information we need
    i = 0
    for rep in lst: #For each recipe
        if rep != '':
            #Peel out the name
            nme = re.findall("([\s\S]*?)△",rep)

            if len(nme)>1: #If multiple options, output- something's probably wrong
                print(nme)
                input("chk")
            nme = re.sub("\n"," ",nme[0]) #Remove newlines
            nme = nme.strip() #remove whitespace

            tosearch = make_searchable(nme) #Searchable version of the name

            #Extract ingredients- content between 'Amount' and totals sum
            ingr = re.findall("Amount\n[\s\S]+?Total",rep)
            ext = re.findall("Total[\s\S]+?Total",rep) #Extras are after the total sum line

            #Cone is IDs by △ and either the link or other names field
            cone = re.findall("(△[\s\S]+?)(https:|Other Names)",rep)[0][0].replace("\n"," ")
            print(cone) #report

            #Link IDd by URL start
            link = re.findall("(https://.*)\n",rep)[0]

            #Description between URL digits and Material tag
            desc = re.findall("\d*/\d*/\d*\n([\s\S]*)\nMaterial",rep)

            #Type, surface, and transparency all packed together before a if present\n
            tpe = re.findall("Type (.*?)(Status|Transparency|Surface|Type|\n)",rep)[0][0]
            surf = re.findall("Surface (.*?)(Status|Transparency|Surface|Type|\n)",rep)            
            transp = re.findall("Transparency (.*?)(Status|Transparency|Surface|Type|\n)",rep)

            #Check if non-empty transparency, add if present
            if len(transp) > 0:
                transp = transp[0][0]
            else:
                transp = ""

            #Check surface and add if present
            if len(surf) > 0:
                surf = surf[0][0]
            else:
                surf = ""

            #Grab description
            if desc != []:
                desc = desc[0]

            #Process ingredients to proper lookup
            if ingr != []:
                ingr = to_rep(ingr[0],1,-1)
            else:
                ingr = {}

            #Process extras to proper lookup
            if ext != []:
                ext = to_rep(ext[0],2,-1)
            else:
                ext = {}

            #If there's a connected image, grab its location
            if nme in im_names:
                im_nme = im_names[nme]
            else: #If not, None
                im_nme = None

            #Build the data for the recipe entry
            data = {"name":nme,"base":ingr,"extras":ext,"cone":cone,"link":link,"type":tpe,"surface":surf,"description":desc,"page":f,"transparency":transp,"imname":im_nme}
            cde = link.split("\\")[-1] #Grab the lookup key as the link
            reps[cde] = data #put into recipes

            #Working prent
            print("NAME:",nme)
            print(len(rep.split("\n")))

            #If no name, pause- there's trouble
            if nme == "":
                print("---",f)
                print(rep)
                input()

        else: #Otherwise if an empty recipe segment selected move on
            pass

        i+=1 #Increment counter

#Final processing- make searchable text for all recipes
for rep in reps:
    dat = reps[rep] #Grab the data
    searchable = {} #Make search lookup

    #For each type of data as its own category, make a searchable list
    searchable["name"] = make_searchable(dat['name'])
    searchable["cone"] = make_searchable(dat['cone'])
    searchable["type"] = make_searchable(dat['type'])
    searchable["surface"] = make_searchable(dat['surface'])
    searchable["transparency"] = make_searchable(dat['transparency'])
    searchable["base"] = [make_searchable(a) for a in dat['base']]
    searchable["extras"] = [make_searchable(a) for a in dat['extras']]

    #Add the searching string sets to the recipe
    reps[rep]['searchable'] = searchable

#Save the whole lookup as a pickle
f_out = open("glazy_reps.pi",'wb')
pickle.dump(reps,f_out)
