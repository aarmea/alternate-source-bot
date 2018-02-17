import json
import subprocess
import time

from storage import Session, Article, Source

# TODO: Later, do a crawl of known news sites (maybe in a separate script)

session = Session()

READABILITY_PATH = "/usr/bin/readability-scrape"
REQUEST_WAIT_TIME = 5 # seconds

for source in session.query(Source.hostname).all():
    # TODO: Spawn a thread/process per news site
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
