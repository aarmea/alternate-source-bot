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

CHANGED_TITLE_TEMPLATE = \
"""When I first saw this article from {source}, its title was:
> {title}

"""

RESPONSE_TEMPLATE = \
"""Here are some other articles about this story:

{formattedArticles}

-----

I am a bot trying to encourage a balanced news diet.

These are all of the articles I think are about this story. I do not select or
sort articles based on any opinions or perceived biases, and neither I nor my
creator advocate for or against any of these sources or articles. It is your
responsibility to determine what is factually correct.
"""

ARTICLE_TEMPLATE = "* {source}: [{title}]({url})"

BANNED_TEMPLATE = \
"""I was banned from {subreddit}. Here's what I would have said in response to
[this post]({url}):

-----

"""


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
        article = session.query(Article).get(strippedUrl)
        if article is None:
            continue

        # Do we know enough about this link?
        if (article.story is None or
                len(article.story.articles) < MINIMUM_ARTICLES):
            continue

        printWithPid("Replying to https://reddit.com/" + post.id + " : " + post.url)

        changedTitleString = ""
        if post.title != article.title:
            changedTitleString = CHANGED_TITLE_TEMPLATE.format(
                    source=article.source.nameOrHostname(),
                    title=article.title)

        formattedArticles = list()
        for relatedArticle in article.story.articles:
            if article.url == relatedArticle.url:
                continue

            formattedArticles.append(ARTICLE_TEMPLATE.format(
                source=relatedArticle.source.nameOrHostname(),
                title=relatedArticle.title, url=relatedArticle.url))

        responseString = changedTitleString + RESPONSE_TEMPLATE.format(
                formattedArticles="\n".join(formattedArticles))

        try:
            if post.subreddit.user_is_banned:
                logTitle = textwrap.shorten(
                        "[Banned] {subreddit}: {title}".format(
                            subreddit=post.subreddit.url, title=post.title),
                        width=TITLE_CUTOFF)
                logText = BANNED_TEMPLATE.format(subreddit=post.subreddit.url,
                        url=post.shortlink) + responseString
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
        except praw.exceptions.ClientException as e:
            printWithPid(e)
            return
        except Exception as e:
            printWithPid(e)

if __name__ == "__main__":
    replyProcess()
