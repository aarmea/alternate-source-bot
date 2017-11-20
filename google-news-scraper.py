from lxml import etree
import requests

from storage import Session, Article, Story

def makeArticle(xmlArticle, story):
    url = xmlArticle.find("link").text
    title = xmlArticle.find("title").text

    article = Article(url=url, title=title, story_id=story.id)
    session.merge(article)

    return article

session = Session()

GOOGLE_NEWS_URL = "https://news.google.com/news/rss/?ned=us&hl=en"
GOOGLE_STORY_URL = "https://news.google.com/news/rss/story/{cluster}?ned=us&hl=en"
CLUSTER_PREFIX = "cluster="

googleNewsRequest = requests.get(GOOGLE_NEWS_URL)
googleNewsXml = etree.XML(googleNewsRequest.content)
googleNewsArticles = googleNewsXml.findall(".//item")

for xmlArticle in googleNewsArticles:
    articleGuid = xmlArticle.find("guid").text
    clusterOffset = articleGuid.find(CLUSTER_PREFIX) + len(CLUSTER_PREFIX)
    cluster = articleGuid[clusterOffset:]

    story = Story(id=cluster)
    session.merge(story)
    print(story)

    article = makeArticle(xmlArticle, story)
    print(article)

    relatedArticlesRequest = requests.get(
            GOOGLE_STORY_URL.format(cluster=article.story_id))
    relatedArticlesXml = etree.XML(relatedArticlesRequest.content)
    relatedArticles = relatedArticlesXml.findall(".//item")

    for relatedXmlArticle in relatedArticles:
        relatedArticle = makeArticle(relatedXmlArticle, story)
        print(relatedArticle)

    print()

session.commit()
