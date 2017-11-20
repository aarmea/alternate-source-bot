from lxml import etree
import requests

GOOGLE_NEWS_URL = "https://news.google.com/news/rss/?ned=us&hl=en"
GOOGLE_STORY_URL = "https://news.google.com/news/rss/story/{cluster}?ned=us&hl=en"
CLUSTER_PREFIX = "cluster="

googleNewsRequest = requests.get(GOOGLE_NEWS_URL)
googleNewsXml = etree.XML(googleNewsRequest.content)
googleNewsArticles = googleNewsXml.findall(".//item")

def formatArticle(article):
    return article.find("title").text + ": " + article.find("link").text

for article in googleNewsArticles:
    print(formatArticle(article))

    articleGuid = article.find("guid").text
    clusterOffset = articleGuid.find(CLUSTER_PREFIX) + len(CLUSTER_PREFIX)
    cluster = articleGuid[clusterOffset:]
    print(cluster)

    relatedArticlesRequest = requests.get(GOOGLE_STORY_URL.format(cluster=cluster))
    relatedArticlesXml = etree.XML(relatedArticlesRequest.content)
    relatedArticles = relatedArticlesXml.findall(".//item")

    for relatedArticle in relatedArticles:
        print("\t" + formatArticle(relatedArticle))
