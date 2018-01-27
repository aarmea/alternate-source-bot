import praw
import sqlalchemy
from urllib.parse import urlparse

from storage import Session, Article, Submission

# SUB_NAME = "alt_source_bot_test"
SUB_NAME = "all"
MINIMUM_ARTICLES = 4

def replyLoop():
    dbSession = Session()
    reddit = praw.Reddit()

    for post in reddit.subreddit(SUB_NAME).stream.submissions():
        parsedUrl = urlparse(post.url)
        strippedUrl = parsedUrl._replace(query="", fragment="").geturl()
        print(post.id + ": " + post.url)

        if dbSession.query(Submission).filter_by(source_id=post.id).count() > 0:
            print("Response exists, skipping")
            continue

        try:
            article = dbSession.query(Article).filter_by(url=strippedUrl).one()
        except sqlalchemy.orm.exc.NoResultFound:
            print("Article not found in database, skipping")
            continue

        if len(article.story.articles) < MINIMUM_ARTICLES:
            print("Not enough related articles to post, skipping")
            continue

        if post.subreddit.user_is_banned:
            print("User is banned from subreddit, skipping")
            continue

        response = list()
        response.append("Here are some other articles about this story:")
        response.append("")
        for relatedArticle in article.story.articles:
            if relatedArticle.source.name:
                sourceName = relatedArticle.source.name
            else:
                sourceName = relatedArticle.source.hostname
            response.append("* {sourceName}: [{title}]({url})".format(
                sourceName=sourceName, title=relatedArticle.title,
                url=relatedArticle.url))
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

        print(responseString)

        try:
            comment = post.reply(responseString)
        except praw.exceptions.APIException as e:
            print(e)
            continue

        submission = Submission(source_id=post.id, response_id=comment.id)
        dbSession.add(submission)
        dbSession.commit()

while True:
    try:
        replyLoop()
    except Exception as e:
        print(e)
