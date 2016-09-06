from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Helper functions

def catName(cat_id):
    cat = session.query(Category).filter_by(id=cat_id).one()
    return cat.name


@app.route('/')
@app.route('/catalog/')
def showLatest():
    """The main page, showing the latest items added"""
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.id.desc()).limit(10)
    title = "Latest items"
    return render_template('showitems.html', categories=categories, items=items, title=title, latest=True, catName=catName)


@app.route('/catalog/category/<string:category_name>/')
def showCategory(category_name):
    """The page displaying the items from a specific category"""
    categories = session.query(Category.name).all()
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item.name).filter_by(category_id=category.id)
    title = category_name
    return render_template('showitems.html', categories=categories, items=items, title=title)


@app.route('/catalog/new/', methods=['GET', 'POST'])
def newItem():
    """The form used to add a new item"""
    categories = session.query(Category).all()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category_id = request.form['category']

        if not (category_id):
            error = "Make sure the item it's within a category!"
            flash(error)
            return render_template('newitem.html', categories=categories)

        try:
            existent = session.query(Item).filter_by(name=name).one()
        except:
            existent = None
        if existent:
            error = "There is already one item with the same name!"
            flash(error)
            return render_template('newitem.html', categories=categories)

        newItem = Item(name=name, description=description, category_id=category_id)
        session.add(newItem)
        session.commit()
        flash("Item successfuly added!")
        category_name = catName(category_id)
        return redirect(url_for('showCategory', category_name=category_name))
    else:
        return render_template('newitem.html', categories=categories)


@app.route('/catalog/item/<string:item_name>/')
def showItem(item_name):
    """The page displaying a specific item"""
    item = session.query(Item).filter_by(name=item_name).one()
    return render_template('item.html', item=item)


@app.route('/catalog/item/<string:item_name>/edit/', methods=['GET', 'POST'])
def editItem(item_name):
    """The form used to edit an item"""
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(name=item_name).one()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category_id = request.form['category']

        try:
            existent = session.query(Item).filter_by(name=name).one()
        except:
            existent = None
        if existent and not name == item.name:
            error = "There is already one item with the same name!"
            flash(error)
            return render_template('edititem.html', categories=categories, item=item)

        item.name = name
        item.description = description
        item.category_id = category_id
        session.add(item)
        session.commit()
        flash("Item successfully edited!")
        category_name = catName(category_id)
        return redirect(url_for('showCategory', category_name=category_name))
    else:
        return render_template('edititem.html', categories=categories, item=item)


@app.route('/catalog/item/<string:item_name>/delete/', methods=['GET', 'POST'])
def deleteItem(item_name):
    """The form used to delete an item"""
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(name=item_name).one()
    if request.method == 'POST':
        category_name = catName(item.category_id)
        session.delete(item)
        session.commit()
        flash("Item successfuly deleted!")
        return redirect(url_for('showCategory', category_name=category_name))
    else:
        return render_template('deleteitem.html', item=item)


if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)