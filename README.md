<img width="1000" alt="image" src="https://github.com/user-attachments/assets/2442ecbd-d203-43fc-8bd2-15c9a59b9c6a" />

## Clay Recipe Database

This project implements a searchable, local database of recipes for ceramin materials (clay, glazes, and the like), based on drawing an initial database from downloaded PDFs from https://glazy.org/, and presenting them in a searchable UI, along with the option to add new, personal recipes to the database. 

The browser-based UI allows for searching by category- name, cone, material type, finish, and such. The software comprises two parts- a server to browser component which implements the lookup, visualization, and recipe addition components; and a pdf extraction component, which builds an initial list of recipes from those in the downloaded favorites files using extensive regex, and extracts their corresponding images as possible. The UI allows for end-user upload of personal sample images, and also attempts to open Glazy and download fresh sample images if none could be reliably extracted from the PDF for that glaze. 

To run the base search, `glaze_search.py` is executed, opening a browser window automatically with search and recipe builder directly accessible.

`pdf_extract.py`, when executed, locates all favorites files in the `pdfs` folder, processes them into recipe objects, and saves a base file containing them (note that running this overwrites the database! This is a plnned update to work around!)

In order to search online and pull down missing images when it can, the system needs Selenium browser with an up to date and correct browser driver. ChromeDriver is included for an example, and is recommended- the driver version needs to match the installed browser version! This is another planned update- to identify the current version, and download the requisite driver on startup.
