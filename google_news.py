from urllib.parse import urlparse
import sys
import time

from lxml import etree
import requests

from storage import Session, Article, GoogleStory, Source

GOOGLE_NEWS_URL = "https://news.google.com/news/rss/?ned=us&hl=en"
GOOGLE_STORY_URL = "https://news.google.com/news/rss/story/{cluster}?ned=us&hl=en"
CLUSTER_PREFIX = "cluster="
REQUEST_WAIT_TIME = 2 # seconds
SCRAPE_WAIT_TIME = 300 # seconds

def _getOrCreateArticle(session, xmlArticle, story):
    url = xmlArticle.find("link").text

    hostname = urlparse(url).hostname.lower()
    if hostname.find("www.") == 0:
        hostname = hostname[4:]

    source = session.query(Source).filter_by(hostname=hostname).one_or_none()
    if source is None:
        source = Source(hostname=hostname, name="")
        session.add(source)

    article = session.query(Article).filter_by(url=url).one_or_none()
    if article is None:
        title = xmlArticle.find("title").text
        article = Article(url=url, title=title, story_id=story.id,
                source_hostname=source.hostname)
        session.add(article)
    else:
        article.story_id = story.id

    return article

def _scrape():
    print("Scraping Google News at " + GOOGLE_NEWS_URL)

    session = Session()
    googleNewsRequest = requests.get(GOOGLE_NEWS_URL)
    googleNewsXml = etree.XML(googleNewsRequest.content)
    googleNewsArticles = googleNewsXml.findall(".//item")

    for xmlArticle in googleNewsArticles:
        articleGuid = xmlArticle.find("guid").text
        clusterOffset = articleGuid.find(CLUSTER_PREFIX) + len(CLUSTER_PREFIX)
        cluster = articleGuid[clusterOffset:]

        story = session.query(GoogleStory).filter_by(id=cluster).one_or_none()
        if story is None:
            story = GoogleStory(id=cluster)
            session.add(story)
        print(story)

        article = _getOrCreateArticle(session, xmlArticle, story)
        print(article)

        time.sleep(REQUEST_WAIT_TIME)
        relatedArticlesRequest = requests.get(
                GOOGLE_STORY_URL.format(cluster=article.story_id))

        try:
            relatedArticlesXml = etree.XML(relatedArticlesRequest.content)
        except etree.XMLSyntaxError as error:
            print("XML syntax error:", error)
            print(relatedArticlesRequest.content)
            continue
        except:
            print("Unexpected error:", sys.exc_info()[0])
            continue

        relatedArticles = relatedArticlesXml.findall(".//item")

        for relatedXmlArticle in relatedArticles:
            relatedArticle = _getOrCreateArticle(session, relatedXmlArticle, story)
            print(relatedArticle)

        session.commit()

    session.commit()

def scrapeProcess():
    print("-- Starting Google News scraper --")
    while True:
        try:
            _scrape()
        except Exception as e:
            print(e)

        time.sleep(SCRAPE_WAIT_TIME)

if __name__ == "__main__":
    scrapeProcess()
