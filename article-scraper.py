import json
import multiprocessing
import subprocess
import time

from storage import Session, Article, Source

# TODO: Later, do a crawl of known news sites (maybe in a separate script)

READABILITY_PATH = "/usr/bin/readability-scrape"
REQUEST_WAIT_TIME = 5 # seconds

# Scraping is mostly I/O-bound right now, so this is fine
SCRAPE_PROCESSES = multiprocessing.cpu_count() * 2

def scrapeArticlesFromSource(source):
    session = Session()
    for article in session.query(Article).filter(
            Article.source_hostname == source.hostname,
            Article.text.is_(None)).all():

        print(article.url)
        readabilityProcess = subprocess.run(
                [READABILITY_PATH, "--json", article.url],
                stdout=subprocess.PIPE)
        readabilityOutput = json.loads(readabilityProcess.stdout)

        newTitle = readabilityOutput["title"]
        if article.title != newTitle:
            print("Changing title to: " + newTitle)
            article.title = newTitle

        article.text = readabilityOutput["textContent"]

        session.commit()
        time.sleep(REQUEST_WAIT_TIME)

multiprocessing.Pool(SCRAPE_PROCESSES).map(scrapeArticlesFromSource,
        Session().query(Source.hostname).all())
