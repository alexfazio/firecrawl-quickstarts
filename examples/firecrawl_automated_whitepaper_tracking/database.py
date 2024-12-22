import logging
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, ForeignKey, Text, ARRAY
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from logging_config import setup_database_logging

# Configure logging using centralized configuration
logger = setup_database_logging()

Base = declarative_base()

class Paper(Base):
    """SQLAlchemy model for storing research papers scraped from the Hugging Face daily papers page.
    Each paper entry includes its URL, title, authors, abstract, associated URLs (PDF, arXiv, GitHub),
    and both publication and submission dates."""
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
    """SQLAlchemy model for tracking engagement metrics from the Hugging Face daily papers page.
    Each entry represents a point-in-time snapshot of a paper's upvotes and comments count,
    with a composite ID format of '{paper_url}_{timestamp}' for tracking historical trends."""
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
        logger.info("Initializing Database connection")
        if not connection_string:
            logger.error("Database connection string is not set")
            raise ValueError("Database connection string is not set")

        # Ensure sslmode=require is appended
        if '?' not in connection_string:
            connection_string += '?sslmode=require'
        elif 'sslmode' not in connection_string:
            connection_string += '&sslmode=require'

        logger.debug("Creating engine with connection string: %s", connection_string.split('?')[0])
        self.engine = create_engine(
            connection_string,
            pool_pre_ping=True  # Pre-ping helps keep connections alive
        )

        logger.info("Creating database tables if they don't exist")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info("Database initialization complete")

    def get_all_papers(self):
        """Get all papers from the database"""
        logger.info("Fetching all papers from database")
        session = self.Session()
        try:
            papers = session.query(Paper).all()
            logger.info("Retrieved %d papers from database", len(papers))
            return papers
        except Exception as e:
            logger.error("Error fetching papers: %s", str(e))
            raise
        finally:
            session.close()

    def get_paper_metrics(self, url):
        """Get metrics history for a paper"""
        logger.info("Fetching metrics for paper: %s", url)
        session = self.Session()
        try:
            metrics = (
                session.query(PaperMetrics)
                .filter(PaperMetrics.paper_url == url)
                .order_by(PaperMetrics.timestamp.desc())
                .all()
            )
            logger.info("Retrieved %d metric entries for paper %s", len(metrics), url)
            return metrics
        except Exception as e:
            logger.error("Error fetching metrics for %s: %s", url, str(e))
            raise
        finally:
            session.close()

    def add_paper(self, paper_data):
        """Add or update a paper and its current metrics.
        
        Returns:
            bool: True if this is a new paper, False if it's an update
        """
        logger.info("Adding/updating paper: %s", paper_data['url'])
        session = self.Session()
        try:
            # Check if paper already exists
            existing_paper = session.query(Paper).filter(
                Paper.url == paper_data["url"]
            ).first()
            
            is_new_paper = existing_paper is None
            action = "Adding new" if is_new_paper else "Updating existing"
            logger.info("%s paper: %s", action, paper_data['url'])

            # Date handling with logging
            try:
                publication_date = datetime(
                    paper_data["utc_publication_date_year"],
                    paper_data["utc_publication_date_month"],
                    paper_data["utc_publication_date_day"]
                )
            except ValueError as e:
                logger.warning("Invalid publication date in %s: %s", paper_data['url'], e)
                publication_date = datetime.now()

            try:
                submission_date = datetime(
                    paper_data["utc_submission_date_year"],
                    paper_data["utc_submission_date_month"],
                    paper_data["utc_submission_date_day"]
                )
            except ValueError as e:
                logger.warning("Invalid submission date in %s: %s", paper_data['url'], e)
                submission_date = datetime.now()

            # Create/update the paper entry
            paper = Paper(
                url=paper_data["url"],
                title=paper_data["paper_title"],
                authors=paper_data["authors"].split(", "),
                abstract=paper_data["abstract_body"],
                pdf_url=paper_data["view_pdf_url"],
                arxiv_url=paper_data["view_arxiv_page_url"],
                github_url=paper_data["github_repo_url"],
                publication_date=publication_date,
                submission_date=submission_date
            )
            logger.debug("Merging paper data for %s", paper_data['url'])
            session.merge(paper)

            # Add metrics
            metrics = PaperMetrics(
                id=f"{paper_data['url']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                paper_url=paper_data["url"],
                upvotes=paper_data["number_of_upvotes"],
                comments=paper_data["number_of_comments"],
                timestamp=datetime.now()
            )
            logger.debug("Adding metrics for %s: %d upvotes, %d comments", 
                        paper_data['url'], metrics.upvotes, metrics.comments)
            session.add(metrics)
            session.commit()
            logger.info("Successfully %s paper and metrics for %s", 
                       'added' if is_new_paper else 'updated', paper_data['url'])
            
            return is_new_paper
        except Exception as e:
            logger.error("Error adding/updating paper %s: %s", paper_data['url'], str(e))
            raise
        finally:
            session.close()


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    logger.info("Starting database module directly")
    
    # Initialize database connection
    db = Database(os.getenv("POSTGRES_URL"))
    
    # Create a test paper entry
    test_paper = {
        "url": "https://test.paper/123",
        "paper_title": "Test Paper for Database Module",
        "authors": "John Doe, Jane Smith",
        "abstract_body": "This is a test paper to verify database functionality.",
        "view_pdf_url": "https://test.paper/123/pdf",
        "view_arxiv_page_url": "https://arxiv.org/abs/test.123",
        "github_repo_url": "https://github.com/test/repo",
        "utc_publication_date_year": 2024,
        "utc_publication_date_month": 3,
        "utc_publication_date_day": 15,
        "utc_submission_date_year": 2024,
        "utc_submission_date_month": 3,
        "utc_submission_date_day": 1,
        "number_of_upvotes": 42,
        "number_of_comments": 7
    }

    try:
        # Test adding a paper
        logger.info("Testing paper addition...")
        is_new = db.add_paper(test_paper)
        logger.info("Paper added successfully (new: %s)", is_new)

        # Test retrieving all papers
        logger.info("Testing paper retrieval...")
        papers = db.get_all_papers()
        logger.info("Retrieved %d papers", len(papers))

        # Test retrieving metrics for the test paper
        logger.info("Testing metrics retrieval...")
        metrics = db.get_paper_metrics(test_paper["url"])
        logger.info("Retrieved %d metrics entries for test paper", len(metrics))
        
        logger.info("Test completed successfully! ✅")
        
    except Exception as e:
        logger.error("Test failed! ❌ Error: %s", str(e))

# TODO: stream the DB contents to a Notion database a la Chief AI Officer database
