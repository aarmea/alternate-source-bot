from urllib.parse import urlparse
import sys
import time

from lxml import etree
import requests

from storage import Session, Article, GoogleStory, Source
from util import printWithPid

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

    source = session.query(Source).get(hostname)
    if source is None:
        source = Source(hostname=hostname, name="")
        session.add(source)

    article = session.query(Article).get(url)
    if article is None:
        title = xmlArticle.find("title").text
        article = Article(url=url, title=title, story_id=story.id,
                source_hostname=source.hostname)
        session.add(article)
    else:
        article.story_id = story.id

    return article

def _scrape():
    printWithPid("Scraping Google News at " + GOOGLE_NEWS_URL)

    session = Session()
    googleNewsRequest = requests.get(GOOGLE_NEWS_URL)
    googleNewsXml = etree.XML(googleNewsRequest.content)
    googleNewsArticles = googleNewsXml.findall(".//item")

    for xmlArticle in googleNewsArticles:
        articleGuid = xmlArticle.find("guid").text
        clusterOffset = articleGuid.find(CLUSTER_PREFIX) + len(CLUSTER_PREFIX)
        cluster = articleGuid[clusterOffset:]

        story = session.query(GoogleStory).get(cluster)
        if story is None:
            story = GoogleStory(id=cluster)
            session.add(story)
        printWithPid(story)

        article = _getOrCreateArticle(session, xmlArticle, story)
        printWithPid(article)

        time.sleep(REQUEST_WAIT_TIME)
        relatedArticlesRequest = requests.get(
                GOOGLE_STORY_URL.format(cluster=article.story_id))

        try:
            relatedArticlesXml = etree.XML(relatedArticlesRequest.content)
        except etree.XMLSyntaxError as error:
            printWithPid("XML syntax error:", error)
            printWithPid(relatedArticlesRequest.content)
            continue
        except:
            printWithPid("Unexpected error:", sys.exc_info()[0])
            continue

        relatedArticles = relatedArticlesXml.findall(".//item")

        for relatedXmlArticle in relatedArticles:
            relatedArticle = _getOrCreateArticle(session, relatedXmlArticle, story)
            printWithPid(relatedArticle)

        session.commit()

    session.commit()

def scrapeProcess():
    printWithPid("-- Starting Google News scraper --")
    while True:
        try:
            _scrape()
        except Exception as e:
            printWithPid(e)

        time.sleep(SCRAPE_WAIT_TIME)

if __name__ == "__main__":
    scrapeProcess()
