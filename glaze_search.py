###
#
# Glaze Database Lookup
#   The server-side utilities for the glaze lookup, with a primary database
#   extracted from Glazy favorites pdf downloads, and with user-input custom
#   additions
#
#   Supports searching the database, making display cards of the recipe when
#   retreiving an entry, and adding new entries
#
###

#Standards
import math,time,random

#File-handling
import glob,pickle
import pymupdf,pymupdf4llm
import re

#Web interface
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import urllib.request

#JS stuff
import asyncio,websockets
import webbrowser

#Make the chrome driver to grab missing images
options = webdriver.ChromeOptions()
options.add_argument("--headless=new") #Run headless
#Try to make the selenium browser, report error otherwise
try:
    cService = webdriver.ChromeService(executable_path='./chromedriver')
    driver = webdriver.Chrome(service = cService,options=options)
except:
    warnings.warn("Selenium failed- probably no internet? Maybe an incompatible chromedriver version")


#Serving on localhost port 8080
HOST = "127.0.0.1"
PORT = 8080

#Grab the archive pickle
files = glob.glob("*.pi")

#open and read in the recipes pickle
f = open(files[0],"rb")
reps = pickle.load(f)
f.close()

#Global to persistently hold a custom recipe before committing to the database
global current_rep

#Utility to construct an ingredients list for a display card
def make_card_list(base,extra):
    S = ""
    #loop over each ingredient and make a table entry for it
    for ing in base:
        S = S + "<tr><td>"+ing+"</td><td>"+str(base[ing])+"</td></tr>"
    for ing in extra:
        S = S + "<tr><td>+"+ing+"</td><td>"+str(extra[ing])+"</td></tr>"

    #Return the list element text
    return S

#Convert a standard string into a searchable one
def make_searchable(st):
    st = st.lower() #Make to lower case only
    st = re.sub("[^\w△-]","",st) #Remove all characters but letters, △, and -
    return st

#Function to run a search through all entries
def search(find,cat,reps):

    to_find = make_searchable(find) #Make the search string a searchable match string

    results = [] #search results

    #If not a proper category supplied
    if not(cat in ['name', 'cone', 'type', 'surface', 'base', 'extras']):
        for r in reps: #For each entry, check if the text is in the description
            if to_find in make_searchable(str(reps[r]['description'])):
                results = results + [r] #Add to result if so
    else: #If a proper category
        for r in reps: #for each recipe
            if type(reps[r]['searchable'][cat]) != list: #Check if the category isn't a list type
                if to_find in reps[r]['searchable'][cat]: #if not, see if search term in the category
                    results = results + [r] #Add to results if so
            else: #If a list categoy
                if True in [to_find in v for v in reps[r]['searchable'][cat]]: #Check all in the list
                    results = results + [r] #and add if found
    return results

#Function to pull a record by name
def pull_record(name,reps):
    for r in reps: #Looping over all recipes
        if reps[r]['name'] == name: #if a name match
            return r,reps[r] #Return the record's entry key and value
    return None #Otherwise return nothing

#Function to make an ingredients list in HTML
def make_ingredients(base,extras):
    ingr_out = "" #Base string
    for ing in base: #For each ingredient, add a list element
        ingr_out = ingr_out + "<tr><td>"+ str(ing) +"</td><td>"+ str(base[ing]) +"</td></tr>"
    ingr_out = ingr_out + "<thead><tr><th>Extras:</th><th></th></tr></thead>"
    for ing in extras: #Do the same for the extras
        ingr_out = ingr_out + "<tr><td>"+ str(ing) +"</td><td>"+ str(extras[ing]) +"</td></tr>"
    return ingr_out

#Function to make a recipe card
def make_card(name,reps):

    #Grab the recipe based on name
    rep = pull_record(name,reps)

    #If there's no record, not and return empty HTML
    if rep == None:
        print("No record found, sorry.")
        return ""
    else: #otherwise

        #Open the card template
        temp_f = open("card_temp.html",'r')
        template = "\n".join(temp_f.readlines()) #Read it in
        temp_f.close()

        #Grab the URL if available and actual reciper
        url = rep[0]
        recip = rep[1]

        #Grab the core values from the recipe
        name = recip["name"]
        cone = recip["cone"]
        link = recip["link"]
        tpe = recip["type"]
        surf = recip["surface"]
        transp = recip["transparency"]
        imname = recip["imname"] #imname points to the associated image file location

        #Build the list of ingredients 
        ingr_list = make_ingredients(recip["base"],recip["extras"])

        #Build the HTML itself
        html_out = template+""

        #Populate the core values
        html_out = html_out.replace("{type}",tpe)
        html_out = html_out.replace("{name}",name)
        html_out = html_out.replace("{cone}",cone)
        html_out = html_out.replace("{surface}",surf)
        html_out = html_out.replace("{transparency}",transp)
        html_out = html_out.replace("{ingredients}",ingr_list)

        #Make a real link to the website
        html_out = html_out.replace("{link}","<a href=\""+link+"\" target=\"_blank\">"+link.split("/")[-1]+"</a>")

        #If there's an image available
        if imname != None:
            html_out = html_out.replace("{imname}",imname) #Pop it in
        else: #Otherwise, try to fetch it
            URL = link #Grab the glazy page
            try: #try to get the webpage to load
                driver.get(URL) #Ask selenium to load the page
                num = URL.split("/")[-1] #Get the index number

                t = time.time() #Timer for delay
                runFlag = True #While grabbing images
                to_get = None #Fetched image pointer
                while time.time()-t < 4.5 and runFlag: #For 4.5s or until finding something
                    try: #try searching the elements for images
                        elems = driver.find_elements(By.TAG_NAME,"img")
                        for elem in elems: #For images found
                            src = elem.get_attribute("src") #Grab the image source
                            if num in src: #If the source has the glaze's number, it's a picture of it!
                                print(src) #Note the image
                                to_get = src #grab that image
                                runFlag = False #flag to stop loop
                                break #break loop
                    except: #On failure, pass, probably no internet
                        pass
                    time.sleep(0.5) #Smoothness delay
            except: #If the page couldn't be retreived,
                to_get = None #pass on with nothing found

            #If we found something
            if to_get != None:

                #Make a local name for the image in our files
                name = "./dwn/"+to_get.split("/")[-1]

                #Download the image asset into its proper location
                urllib.request.urlretrieve(to_get,"./dwn/"+to_get.split("/")[-1])

                #Put the image location into the output html
                html_out = html_out.replace("{imname}","./dwn/"+to_get.split("/")[-1])                

                #Update the recipe to the image we now have
                reps[url]["imname"] = "dwn/"+to_get.split("/")[-1]

                #Save the updated recipe list
                f_out = open("glazy_reps.pi",'wb')
                pickle.dump(reps,f_out)
                f_out.close()

            #If we didn't find anything
            else:
                #Use the placeholder
                html_out = html_out.replace("{imname}","wufface.jpeg")

        #Return the generated recipe card HTML
        return html_out

#Helper function to check if something can be converted to an int
def could_int(st):
    try:
        int(st)
        return True
    except:
        return False

#Main server response code
async def handle_client(websocket):

    #Holders for the current search results
    current_search_res = {}
    search_res_current = {}

    #Always a try to not crash for every failure
    try:
        async for message in websocket: #looping over the available messages

            #Report the message
            print(message)
            resp = "" #Base response

            #A search request
            if message[0] == "&":
                #Break up the search terms
                terms = message[1:].split(",")
                cat = make_searchable(terms[0]) #Convert the category to the searchable version
                find = terms[1] #Grab the actual search string
                res = search(find,cat,reps) #Execute the search with the supplied category and text

                #Update the holders of the current results
                current_search_res = {n:res[n] for n in range(len(res))}
                search_res_current = {res[n]:n for n in range(len(res))}

                #If there's something to report
                if len(res) > 0:
                    op = "" #Base output list
                    for r in res:
                        #Add a clickable entry for each result
                        op = op + "<div style=\"color:blue;padding:2px;\"onclick=\"sendReq("+str(search_res_current[r])+")\">"+reps[r]['name']+"</div>"

                    #Build full response from the links there and the number of results
                    resp = "&"+"("+str(len(res))+")"+"|"+op
                else: #Otherwise, real simple
                    resp = "&"+"(0)"+"|"+"<i>No Results</i>" #No results, count of 0

            #A card request
            elif message[0] == "%":
                index = int(message[1:]) #Grab the index from the message after the identifying character
                entry = current_search_res[index] #Grab the entry from search results

                #Report it
                print(entry)
                print("  ",reps[entry]['imname'])

                #Get the HTML for the card asspocited with this entry
                card = make_card(reps[entry]['name'],reps)
                resp = "%"+card #Make the response that HTML

            #Entering a new card
            elif message[0] == "$":

                #Load the entry card template
                inp_f = open("inp_card_temp.html",'r') 
                inpl = "\n".join(inp_f.readlines())
                inp_f.close()

                #Send the entry card HTML
                resp = "%"+inpl

            #A new entry 
            elif message[0] == "#":

                #Break up the message after the ID character by the | delimiter
                mg = message[1:].split("|")
                dat = mg[0].split(",") #Break up the core data component by ,

                #Grab the core data from the 
                name = dat[0]
                tpe = dat[1]
                cone = dat[2]
                surface = dat[3]
                transparency = dat[4]
                imglnk  = "dwn/"+dat[5]

                #Ingredients list is everything else on this side of the |
                ingrs = dat[6:]

                #Build a recipe entry
                current_rep = {}
                current_rep["name"] = name
                current_rep["base"] = {ingrs[0::2][i]:ingrs[1::2][i] for i in range(len(ingrs[1::2]))}
                current_rep["extras"] = {}
                current_rep["cone"] = "△"+cone
                current_rep["link"] = ""
                current_rep["type"] = tpe
                current_rep["surface"] = surface
                current_rep["description"] = ""
                current_rep["page"] = ""
                current_rep["transparency"] = transparency
                current_rep["imname"] = imglnk

                #Build the searchable string lists
                searchable = {}
                searchable["name"] = make_searchable(name)
                searchable["cone"] = make_searchable(cone)
                searchable["type"] = make_searchable(tpe)
                searchable["surface"] = make_searchable(surface)
                searchable["transparency"] = make_searchable(transparency)
                searchable["base"] = [make_searchable(a) for a in current_rep["base"]]
                searchable["extras"] = []

                #Finish the resipe entry with the searchable categories
                current_rep["searchable"] = searchable

                #Note that the recipe has been received and stored - Will finalize once the image comes through
                resp = "#"

            #If no identifier character, it's an image
            else:

                #Make an object for the message
                sendObject = message

                #Open a binary file- all the image headers are already embedded
                f_name = "./"+current_rep["imname"] #Location is already made in the current recipe
                f = open(f_name,'wb')
                f.write(sendObject) #Write the opject in
                f.close() #Close the image

                #Make up an entry index from recipe properties (versus the URLs for ones extracted from PDF)
                ent_name = make_searchable(current_rep["name"]+current_rep["cone"]+current_rep["type"]+current_rep["transparency"]+current_rep["surface"])
                reps[ent_name] = current_rep #Put the recipe into the full set of recipes

                #Save the updated recipe object to the local file
                f_out = open("glazy_reps.pi",'wb')
                pickle.dump(reps,f_out)
                f_out.close()

            #Send the response and await
            await websocket.send(resp)

    #When connection dies
    except websockets.exceptions.ConnectionClosed:
        print("CONNECTION CLOSED")
        pass

#Main run function
async def main():

    #Make a websockets server on localhost and 8080
    server = await websockets.serve(handle_client, HOST, PORT)

    #Open the actual browser window to interact
    webbrowser.open("glaze_search.html")

    #Spin until it closes
    await server.wait_closed()

#On run
if __name__ == "__main__":
    asyncio.run(main()) #Do the main loop

#Kill selenium when done
driver.close()


#Old text-only interface
'''
if __name__ == '__main__':

    while True:
        print("Cats: ",['name', 'cone', 'type', 'surface', 'base', 'extras'])
        cat = make_searchable(input("Category?"))
        find = input("Search for?")

        res = search(find,cat,reps)
        nmes = [reps[a]['name'] for a in reps]

        if len(res) > 0:
            n = 0
            while n < len(res):
                print("Results ",n,"-",min(n+20,len(res))," of ",len(res),":")
                i = 0
                for a in res[n:n+20]:
                    print("  ",n+i,reps[a]['name'])
                    i+=1
                inp = input("found it?")
                if (inp in nmes) or could_int(inp):
                    n = len(res)+9999
                    try:
                        make_card(reps[res[int(inp)]]['name'],reps)
                    except:
                        make_card(inp,reps)
                elif inp in ['y','Y','yes','Yes']:
                    n = len(res)+9999
                    inp2 = input("Enter selection:")
                    try:
                        make_card(reps[res[int(inp2)]]['name'],reps)
                    except:
                        make_card(inp2,reps)
                else:
                    n+=20
        else:
            print("No results.")
'''        




