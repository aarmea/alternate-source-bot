import textwrap
from urllib.parse import urlparse

import praw
import sqlalchemy

from storage import Session, Article, Submission
from util import printWithPid

ACTIVE_SUB_NAME = "all"
LOG_SUB_NAME = "alt_source_bot_log"
MINIMUM_ARTICLES = 5
TITLE_CUTOFF = 300

def _replyLoop():
    printWithPid("-- Starting Reddit reply loop --")

    session = Session()
    reddit = praw.Reddit()
    activeSub = reddit.subreddit(ACTIVE_SUB_NAME)
    logSub = reddit.subreddit(LOG_SUB_NAME)

    for post in activeSub.stream.submissions():
        parsedUrl = urlparse(post.url)
        strippedUrl = parsedUrl._replace(query="", fragment="").geturl()

        # Did we already comment on this post?
        if session.query(Submission).filter_by(source_id=post.id).count() > 0:
            continue

        # Do we know about this link?
        article = session.query(
                Article).filter_by(url=strippedUrl).one_or_none()
        if article is None:
            continue

        # Do we know enough about this link?
        if len(article.story.articles) < MINIMUM_ARTICLES:
            continue

        printWithPid("Replying to https://reddit.com/" + post.id + " : " + post.url)
        response = list()

        if post.title != article.title:
            response.append("When I first saw this article from {source},"
                    .format(source=article.source.nameOrHostname()))
            response.append("its title was:")
            response.append("> " + article.title)
            response.append("")

        response.append("Here are some other articles about this story:")
        response.append("")

        for relatedArticle in article.story.articles:
            if article.url == relatedArticle.url:
                continue

            response.append("* {source}: [{title}]({url})".format(
                source=relatedArticle.source.nameOrHostname(),
                title=relatedArticle.title, url=relatedArticle.url))

        response.append("")
        response.append("-----")
        response.append("")
        response.append("I am a bot trying to encourage a balanced news diet.")
        response.append("")
        response.append("""These are all of the articles I think are about this
                story. I do not select or sort articles based on any opinions or
                perceived biases, and neither I nor my creator advocate for or
                against any of these sources or articles. It is your responsibility
                to determine what is factually correct.""")
        responseString = "\n".join(response)

        try:
            if post.subreddit.user_is_banned:
                logTitle = textwrap.shorten(
                        "[Banned] {subreddit}: {title}".format(
                            subreddit=post.subreddit.url, title=post.title),
                        width=TITLE_CUTOFF)
                logText = """I was banned from {subreddit}. Here's what I would
                    have said in response to [this submission]({url}):
                    \n\n-----\n\n{response}""".format(
                            subreddit=post.subreddit.url, url=post.shortlink,
                            response=responseString)
                logSub.submit(logTitle, selftext=logText)
            else:
                comment = post.reply(responseString)

                # TODO: Keep track of the article and story that created this
                submission = Submission(source_id=post.id,
                        response_id=comment.id)
                session.add(submission)
                session.commit()
        except praw.exceptions.APIException as e:
            printWithPid(e)

def replyProcess():
    while True:
        try:
            _replyLoop()
        except Exception as e:
            printWithPid(e)

if __name__ == "__main__":
    replyProcess()
