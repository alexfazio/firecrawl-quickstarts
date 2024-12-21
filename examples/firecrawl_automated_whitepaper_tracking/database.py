from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, ForeignKey, Text, ARRAY
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

Base = declarative_base()

class Paper(Base):
    __tablename__ = "papers"
    url = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    authors = Column(ARRAY(String), nullable=False)
    abstract = Column(Text, nullable=False)
    pdf_url = Column(String)
    arxiv_url = Column(String)
    github_url = Column(String)
    publication_date = Column(DateTime, nullable=False)
    submission_date = Column(DateTime, nullable=False)
    metrics = relationship("PaperMetrics", back_populates="paper", cascade="all, delete-orphan")


class PaperMetrics(Base):
    __tablename__ = "paper_metrics"
    id = Column(String, primary_key=True)
    paper_url = Column(String, ForeignKey("papers.url"))
    upvotes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    timestamp = Column(DateTime, nullable=False)
    paper = relationship("Paper", back_populates="metrics")


class Database:
    """Class for interacting with the database using SQLAlchemy."""
    def __init__(self, connection_string):
        if not connection_string:
            raise ValueError("Database connection string is not set")

        # Ensure sslmode=require is appended
        if '?' not in connection_string:
            connection_string += '?sslmode=require'
        elif 'sslmode' not in connection_string:
            connection_string += '&sslmode=require'

        self.engine = create_engine(
            connection_string,
            pool_pre_ping=True  # Pre-ping helps keep connections alive
        )

        # If you want auto table creation, keep this
        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(bind=self.engine)

    def get_all_papers(self):
        """Get all papers from the database"""
        session = self.Session()
        try:
            return session.query(Paper).all()
        finally:
            session.close()

    def get_paper_metrics(self, url):
        """Get metrics history for a paper"""
        session = self.Session()
        try:
            return (
                session.query(PaperMetrics)
                .filter(PaperMetrics.paper_url == url)
                .order_by(PaperMetrics.timestamp.desc())
                .all()
            )
        finally:
            session.close()

    def add_paper(self, paper_data):
        """Add or update a paper and its current metrics.
        
        Returns:
            bool: True if this is a new paper, False if it's an update
        """
        session = self.Session()
        try:
            # Check if paper already exists
            existing_paper = session.query(Paper).filter(
                Paper.url == paper_data["url"]
            ).first()
            
            is_new_paper = existing_paper is None
            
            # Create/update the paper entry
            paper = Paper(
                url=paper_data["url"],
                title=paper_data["paper_title"],
                authors=paper_data["authors"].split(", "),
                abstract=paper_data["abstract_body"],
                pdf_url=paper_data["view_pdf_url"],
                arxiv_url=paper_data["view_arxiv_page_url"],
                github_url=paper_data["github_repo_url"],
                publication_date=datetime(
                    paper_data["utc_publication_date_year"],
                    paper_data["utc_publication_date_month"],
                    paper_data["utc_publication_date_day"]
                ),
                submission_date=datetime(
                    paper_data["utc_submission_date_year"],
                    paper_data["utc_submission_date_month"],
                    paper_data["utc_submission_date_day"]
                )
            )
            session.merge(paper)

            # Add metrics
            metrics = PaperMetrics(
                id=f"{paper_data['url']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                paper_url=paper_data["url"],
                upvotes=paper_data["number_of_upvotes"],
                comments=paper_data["number_of_comments"],
                timestamp=datetime.now()
            )
            session.add(metrics)
            session.commit()
            
            return is_new_paper
        finally:
            session.close()


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()
    db = Database(os.getenv("POSTGRES_URL"))
