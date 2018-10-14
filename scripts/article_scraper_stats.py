from storage import Session, Article

session = Session()

articles = session.query(Article).count()
hasText = session.query(Article).filter(Article.text.isnot(None)).count()
failed = session.query(Article).filter(
        Article.retrieved.isnot(None), Article.text.is_(None)).count()
waiting = session.query(Article).filter(
        Article.retrieved.is_(None), Article.text.is_(None)).count()

if __name__ == "__main__":
    print("Retrieved text:", hasText)
    print("Scrape failed: ", failed)
    print("Waiting:       ", waiting)
    print("-------------------------")
    print("Total:         ", articles)
