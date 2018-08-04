import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from settings import Settings

Engine = create_engine(Settings["STORAGE"]["connection_string"])
Base = declarative_base()

class Source(Base):
    __tablename__ = "sources"

    hostname = sa.Column(sa.String, primary_key=True)
    name = sa.Column(sa.String)

    articles = relationship("Article", back_populates="source")
    # TODO: Fields for issues with sources

    def nameOrHostname(self):
        if self.name:
            return self.name
        else:
            return self.hostname

class Article(Base):
    __tablename__ = "articles"

    url = sa.Column(sa.String, primary_key=True)
    title = sa.Column(sa.String)

    story_id = sa.Column(sa.String, sa.ForeignKey("stories.id"))
    story = relationship("GoogleStory", uselist=False,
            back_populates="articles")

    source_hostname = sa.Column(sa.String, sa.ForeignKey("sources.hostname"))
    source = relationship("Source", uselist=False, back_populates="articles")

    text = sa.Column(sa.String)
    retrieved = sa.Column(sa.DateTime)

    def __repr__(self):
        return "<Article(url='{url}', story_id='{story_id}')>".format(
                url=self.url, story_id=self.story_id)

class GoogleStory(Base):
    __tablename__ = "stories"

    id = sa.Column(sa.String, primary_key=True)
    articles = relationship("Article", back_populates="story")

    def __repr__(self):
        return "<GoogleStory(id='{id}')>".format(id=self.id)

class Submission(Base):
    __tablename__ = "submissions"

    # Reddit post/comment containing a news URL
    source_id  = sa.Column(sa.String, primary_key=True)

    # This bot's response
    response_id = sa.Column(sa.String, nullable=False)

    # TODO: Foreign key(s) for the article(s) that was/were referenced

Base.metadata.create_all(Engine)
Session = sa.orm.sessionmaker(bind=Engine)
