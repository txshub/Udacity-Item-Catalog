from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Category, Item

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

def populateCategory():

    countries = Category(name="Countries")
    instruments = Category(name="Instruments")
    games = Category(name="Games")

    session.add(countries)
    session.add(instruments)
    session.add(games)
    session.commit()

    print "Added categories!"

def populateItems():

    countries = session.query(Category).filter_by(name="Countries").one()
    instruments = session.query(Category).filter_by(name="Instruments").one()
    games = session.query(Category).filter_by(name="Games").one()

    flag = Item(name="Flag", description="The flag of a country", category_id=countries.id)
    map = Item(name="Map", description="The Map of a country", category_id=countries.id)
    session.add(flag)
    session.add(map)
    session.commit()

    print "Added countries items!"

    guitar = Item(name="Guitar", description="6 string instrument", category_id=instruments.id)
    drums = Item(name="Drums", description="Percution instrument", category_id=instruments.id)
    violin = Item(name="Violin", description="4 string instrument", category_id=instruments.id)
    session.add(guitar)
    session.add(drums)
    session.add(violin)
    session.commit

    print "Added instruments items!"

    cod4 = Item(name="Call of Duty 4", description="FPS", category_id=games.id)
    rl = Item(name="Rocket League", description="Racing + Football", category_id=games.id)
    session.add(cod4)
    session.add(rl)
    session.commit()

    print "Added games items!"


populateCategory()
populateItems()
