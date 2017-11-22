import sys
import time

from lxml import etree
import requests
import sqlalchemy

from storage import Session, Article, Story

def getOrCreateArticle(xmlArticle, story):
    url = xmlArticle.find("link").text
    try:
        article = session.query(Article).filter(Article.url==url).one()
    except sqlalchemy.orm.exc.NoResultFound:
        title = xmlArticle.find("title").text
        article = Article(url=url, title=title, story_id=story.id)
        session.add(article)

    return article

session = Session()

GOOGLE_NEWS_URL = "https://news.google.com/news/rss/?ned=us&hl=en"
GOOGLE_STORY_URL = "https://news.google.com/news/rss/story/{cluster}?ned=us&hl=en"
CLUSTER_PREFIX = "cluster="
REQUEST_WAIT_TIME = 2 # seconds

googleNewsRequest = requests.get(GOOGLE_NEWS_URL)
googleNewsXml = etree.XML(googleNewsRequest.content)
googleNewsArticles = googleNewsXml.findall(".//item")

for xmlArticle in googleNewsArticles:
    articleGuid = xmlArticle.find("guid").text
    clusterOffset = articleGuid.find(CLUSTER_PREFIX) + len(CLUSTER_PREFIX)
    cluster = articleGuid[clusterOffset:]

    try:
        story = session.query(Story).filter(Story.id==cluster).one()
    except sqlalchemy.orm.exc.NoResultFound:
        story = Story(id=cluster)
        session.add(story)
    print(story)

    article = getOrCreateArticle(xmlArticle, story)
    print(article)

    time.sleep(REQUEST_WAIT_TIME)
    relatedArticlesRequest = requests.get(
            GOOGLE_STORY_URL.format(cluster=article.story_id))

    try:
        relatedArticlesXml = etree.XML(relatedArticlesRequest.content)
    except etree.XMLSyntaxError as error:
        print("XML syntax error:", error)
        print(relatedArticlesRequest.content)
        print()
        continue
    except:
        print("Unexpected error:", sys.exc_info()[0])
        print()
        continue
    relatedArticles = relatedArticlesXml.findall(".//item")

    for relatedXmlArticle in relatedArticles:
        relatedArticle = getOrCreateArticle(relatedXmlArticle, story)
        print(relatedArticle)

    print()

session.commit()
