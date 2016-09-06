from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Category, Item, User

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

def populateCategory():

    books = Category(name="Books")
    instruments = Category(name="Instruments")
    games = Category(name="Games")

    session.add(books)
    session.add(instruments)
    session.add(games)
    session.commit()

    print "Added categories!"

def populateUsers():
    usr2 = User(name="User 2", email="user2@gmail.com")
    usr3 = User(name="User 3", email="user3@gmail.com")

    session.add(usr2)
    session.add(usr3)
    session.commit()

    print "Added users!"

def populateItems():

    books = session.query(Category).filter_by(name="Books").one()
    instruments = session.query(Category).filter_by(name="Instruments").one()
    games = session.query(Category).filter_by(name="Games").one()

    lotr = Item(name="Lord of the rings", description="One of the best fantasy trilogy, written by JRR Tolkien", category_id=books.id, user_id=2)
    rc = Item(name="Robinson crusoe", description="Written by Daniel Defoe", category_id=books.id, user_id=3)
    session.add(lotr)
    session.add(rc)
    session.commit()

    print "Added countries items!"

    drums = Item(name="Drums", description="Percution instrument", category_id=instruments.id, user_id=2)
    violin = Item(name="Violin", description="4 string instrument", category_id=instruments.id, user_id=3)
    session.add(drums)
    session.add(violin)
    session.commit

    print "Added instruments items!"

    cod4 = Item(name="Call of Duty 4", description="FPS", category_id=games.id, user_id=2)
    rl = Item(name="Rocket League", description="Racing + Football", category_id=games.id, user_id=3)
    session.add(cod4)
    session.add(rl)
    session.commit()

    print "Added games items!"

populateUsers()
populateCategory()
populateItems()
