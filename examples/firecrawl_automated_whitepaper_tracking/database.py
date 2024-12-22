import logging
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, ForeignKey, Text, ARRAY
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler if no handlers exist
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

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
        logger.info("Initializing Database connection")
        if not connection_string:
            logger.error("Database connection string is not set")
            raise ValueError("Database connection string is not set")

        # Ensure sslmode=require is appended
        if '?' not in connection_string:
            connection_string += '?sslmode=require'
        elif 'sslmode' not in connection_string:
            connection_string += '&sslmode=require'

        logger.debug(f"Creating engine with connection string: {connection_string.split('?')[0]}")
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
            logger.info(f"Retrieved {len(papers)} papers from database")
            return papers
        except Exception as e:
            logger.error(f"Error fetching papers: {str(e)}")
            raise
        finally:
            session.close()

    def get_paper_metrics(self, url):
        """Get metrics history for a paper"""
        logger.info(f"Fetching metrics for paper: {url}")
        session = self.Session()
        try:
            metrics = (
                session.query(PaperMetrics)
                .filter(PaperMetrics.paper_url == url)
                .order_by(PaperMetrics.timestamp.desc())
                .all()
            )
            logger.info(f"Retrieved {len(metrics)} metric entries for paper {url}")
            return metrics
        except Exception as e:
            logger.error(f"Error fetching metrics for {url}: {str(e)}")
            raise
        finally:
            session.close()

    def add_paper(self, paper_data):
        """Add or update a paper and its current metrics.
        
        Returns:
            bool: True if this is a new paper, False if it's an update
        """
        logger.info(f"Adding/updating paper: {paper_data['url']}")
        session = self.Session()
        try:
            # Check if paper already exists
            existing_paper = session.query(Paper).filter(
                Paper.url == paper_data["url"]
            ).first()
            
            is_new_paper = existing_paper is None
            action = "Adding new" if is_new_paper else "Updating existing"
            logger.info(f"{action} paper: {paper_data['url']}")

            # Date handling with logging
            try:
                publication_date = datetime(
                    paper_data["utc_publication_date_year"],
                    paper_data["utc_publication_date_month"],
                    paper_data["utc_publication_date_day"]
                )
            except ValueError as e:
                logger.warning(f"Invalid publication date in {paper_data['url']}: {e}")
                publication_date = datetime.now()

            try:
                submission_date = datetime(
                    paper_data["utc_submission_date_year"],
                    paper_data["utc_submission_date_month"],
                    paper_data["utc_submission_date_day"]
                )
            except ValueError as e:
                logger.warning(f"Invalid submission date in {paper_data['url']}: {e}")
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
            logger.debug(f"Merging paper data for {paper_data['url']}")
            session.merge(paper)

            # Add metrics
            metrics = PaperMetrics(
                id=f"{paper_data['url']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                paper_url=paper_data["url"],
                upvotes=paper_data["number_of_upvotes"],
                comments=paper_data["number_of_comments"],
                timestamp=datetime.now()
            )
            logger.debug(f"Adding metrics for {paper_data['url']}: {metrics.upvotes} upvotes, {metrics.comments} comments")
            session.add(metrics)
            session.commit()
            logger.info(f"Successfully {'added' if is_new_paper else 'updated'} paper and metrics for {paper_data['url']}")
            
            return is_new_paper
        except Exception as e:
            logger.error(f"Error adding/updating paper {paper_data['url']}: {str(e)}")
            raise
        finally:
            session.close()


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    # Configure logging for main execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    load_dotenv()
    logger.info("Starting database module directly")
    db = Database(os.getenv("POSTGRES_URL"))
