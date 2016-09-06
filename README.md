# Udacity Item Catalog  

The project can be found in **/vagrant/catalog**, and a vagrant virtual machine must be set up in the **/vagrant** directory.  

## Creating the database:  
A SQLite database is already created, under the name **itemcatalog.db**. This can be deleted and re-created, by running the following files with Python 2.7:  
* **python db_setub.py** (Creates the database)  
* **python db_test.py** (Populates the database)  

## Running the application:
Run the **application.py** file using Python 2.7, with the following command:  
* **python application.py**  
The web application should be found at **https://localhost:8000**  

## Using the application:  
The first page(which can be accessed at any time by pressing the big **Item Catalog** button) displays The categories and latest items found in the catalog. By clicking on a category name, the app will display the items within that category. By clicking on a item name, the user will be redirected to that item's page, where its name and description will be displayed.  
By clicking on the **Login** button, a Google+ authentication page will be displayed, and the user can login/signup. While logged in, the user will be able to log out, add a new item to the catalog, and edit or delete the items that he/she already added. When trying to modify someone else's items, an error will pop up, redirecting the user to a blank page.  
The application provides JSON representations for the items in the catalog. To access a specific item's JSON representation, go to **localhost:8000/catalog/item/[item_name]/JSON**, where [item_name] is the name of that item.
