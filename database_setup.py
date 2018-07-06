from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine


Base = declarative_base()


class Person(Base):
    __tablename__ = 'person'

    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    email = Column(String(300), nullable=False)
    picture = Column(String(300))


class Section(Base):
    __tablename__ = 'section'

    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    person_id = Column(Integer, ForeignKey('person.id'))
    person = relationship(Person, backref="section")

    @property
    def serializes(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id
        }


class Lists(Base):
    __tablename__ = 'lists'

    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String(300))
    picture = Column(String(300))
    section_id = Column(Integer, ForeignKey('section.id'))
    section = relationship(
               Section, backref=backref('lists', cascade='all, delete'))
    person_id = Column(Integer, ForeignKey('person.id'))
    person = relationship(Person, backref="lists")

    @property
    def serializes(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'picture': self.picture,
            'section': self.section.name
        }


engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.create_all(engine)
