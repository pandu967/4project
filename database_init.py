from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from database_setup import *

engine = create_engine('sqlite:///itemcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Delete Categories if exisitng.
session.query(Section).delete()
# Delete Items if exisitng.
session.query(Lists).delete()
# Delete Users if exisitng.
session.query(Person).delete()

# Create sample users
Person1 = Person(name="venkatesh",
             email="venkatesh.y@gmail.com",
             picture='https://pbs.twimg.com/profile_images'
                 '/892067670970978305/_K34MGL8_400x400.jpg')
session.add(Person1)
session.commit()


# Create sample categories
Section1 = Section(name="SAMSUNG",
                     person_id=1)
session.add(Section1)
session.commit()

Section2 = Section(name="IPHONE",
                     person_id=1)
session.add(Section2)
session.commit

Section3 = Section(name="NOKIA",
                     person_id=1)
session.add(Section3)
session.commit()

Section4 = Section(name="HTC",
                     person_id=1)
session.add(Section4)
session.commit()

Section5 = Section(name="BLACKBERRY",
                     person_id=1)
session.add(Section5)
session.commit()


# Populate a category with items for testing


# Using different users for items also
list1 = Lists(name="SAMSUNG",
              date=datetime.datetime.now(),
              description="6 GB RAM | 32 GB ROM | Expandable Upto"
              " 256 GB 5.99 inch Full HD+ Display 20MP Rear Camera"
              " | 12MP Front Camera 5000 mAh Li Polymer Battery"
              " Qualcomm Snapdragon 625 Processor",
              picture="https://encrypted-tbn0.gstatic.com/images?"
              "q=tbn:ANd9GcT2rRaBeyU29NX8UxN9JVA6W9HXsgo"
              "LI5D1JWfeB05Fgd1uRI13FSU7W-o",
              section_id=2,
              person_id=1)
session.add(list1)
session.commit()

list2 = Lists(name="IPHONE",
              date=datetime.datetime.now(),
              description="3 GB RAM | 256 GB ROM | No Expandable"
              " 256 GB 5.50 inch Full HD+ Display 24MP Rear Camera"
              " | 12MP Front Camera 3000 mAh Li Polymer Battery"
              " powered by quad-core processor",
              picture="https://encrypted-tbn0.gstatic.com/images?"
              "q=tbn:ANd9GcRGGL5agX3C7wVq4H5DZ1RK"
              "ujzZLOO40IFLRksa0AkuQYAvHfBCXw",
              section_id=3,
              person_id=1)
session.add(list2)
session.commit()

list3 = Lists(name="NOKIA",
              date=datetime.datetime.now(),
              description="4 GB RAM | 256 GB ROM | Expandable Upto"
              " 256 GB 5.50 inch Full HD+ Display 13MP Rear Camera"
              " | 16MP Front Camera 3000 mAh Li Polymer Battery"
              " powered by octa-core processo",
              picture="https://encrypted-tbn0.gstatic.com/"
              "images?q=tbn:ANd9GcRGn-YNSGzyYNVvNQEaT3D_"
              "qxkuT-KiPUjarnW_ekvt50We6IZ5QQ",
              section_id=1,
              person_id=1)
session.add(list3)
session.commit()

print("Your database has been populated with sample data!")
