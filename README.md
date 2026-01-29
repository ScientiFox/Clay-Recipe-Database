<img width="1000" alt="image" src="https://github.com/user-attachments/assets/2442ecbd-d203-43fc-8bd2-15c9a59b9c6a" />

## Clay Recipe Database

This project implements a searchable, local database of recipes for ceramin materials (clay, glazes, and the like), based on drawing an initial database from downloaded PDFs from https://glazy.org/, and presenting them in a searchable UI, along with the option to add new, personal recipes to the database. 

The browser-based UI allows for searching by category- name, cone, material type, finish, and such. The software comprises two parts- a server to browser component which implements the lookup, visualization, and recipe addition components; and a pdf extraction component, which builds an initial list of recipes from those in the downloaded favorites files using extensive regex, and extracts their corresponding images as possible. The UI allows for end-user upload of personal sample images, and also attempts to open Glazy and download fresh sample images if none could be reliably extracted from the PDF for that glaze. 

