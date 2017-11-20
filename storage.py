import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Engine = create_engine("sqlite:///articles.db")
Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"

    url = sa.Column(sa.String, primary_key=True)
    title = sa.Column(sa.String)

    story_id = sa.Column(sa.String, sa.ForeignKey("stories.id"))
    story = relationship("Story", back_populates="articles")

    def __repr__(self):
        return "<Article(url='{url}', story_id='{story_id}')>".format(
                url=self.url, story_id=self.story_id)

class Story(Base):
    __tablename__ = "stories"

    id = sa.Column(sa.String, primary_key=True)
    articles = relationship("Article",
            order_by=Article.url, back_populates="story")

    def __repr__(self):
        return "<Story(id='{id}')>".format(id=self.id)

Base.metadata.create_all(Engine)
Session = sa.orm.sessionmaker(bind=Engine)
