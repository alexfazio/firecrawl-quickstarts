__doc__ = """Module for interacting with the supabase database using SQLAlchemy."""

from datetime import datetime, timedelta
from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, Text, ARRAY, text, Boolean
)
from sqlalchemy.orm import sessionmaker, declarative_base
from logging_config import setup_database_logging
from sqlalchemy.exc import SQLAlchemyError

# Configure logging using centralized configuration
logger = setup_database_logging()

Base = declarative_base()

class Paper(Base):
    """SQLAlchemy model for storing research papers from the Hugging Face daily papers page.
    Each paper entry includes its URL, title, authors, abstract, associated URLs (PDF, arXiv, GitHub),
    publication and submission dates, as well as current engagement metrics (upvotes and comments)."""
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
    upvotes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    notification_sent = Column(Boolean, default=False)
    extraction_success = Column(Boolean, default=True)
    extraction_error = Column(Text, nullable=True)
    last_extraction_attempt = Column(DateTime, default=datetime.now)


class Database:
    """Class for interacting with the database using SQLAlchemy."""
    CURRENT_SCHEMA_VERSION = 2

    def __init__(self, connection_string, skip_version_check=False):
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
        self.session_factory = sessionmaker(bind=self.engine)
        logger.info("Database initialization complete")

        # Only check version if not skipped
        if not skip_version_check:
            self._check_schema_version()
        
    def _check_schema_version(self):
        """Verify database schema version is compatible."""
        session = self.session_factory()
        try:
            # Create version table if it doesn't exist
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Get current version
            result = session.execute(text(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
            ))
            db_version = result.scalar() or 0
            
            if db_version == 0:
                # New database, set initial version
                session.execute(text(
                    "INSERT INTO schema_version (version) VALUES (:version)"
                ), {"version": self.CURRENT_SCHEMA_VERSION})
                session.commit()
            elif db_version < self.CURRENT_SCHEMA_VERSION:
                logger.error(
                    "Database schema version %d is older than required version %d. "
                    "Please run migrations.",
                    db_version, self.CURRENT_SCHEMA_VERSION
                )
                raise RuntimeError("Database schema needs migration")
            elif db_version > self.CURRENT_SCHEMA_VERSION:
                logger.error(
                    "Database schema version %d is newer than supported version %d. "
                    "Please update the application.",
                    db_version, self.CURRENT_SCHEMA_VERSION
                )
                raise RuntimeError("Database schema version not supported")
                
            logger.info("Database schema version: %d", db_version)
            
        except Exception as e:
            logger.error("Error checking schema version: %s", str(e))
            raise
        finally:
            session.close()

    def get_all_papers(self):
        """Get all papers from the database"""
        logger.info("Fetching all papers from database")
        session = self.session_factory()
        try:
            papers = session.query(Paper).all()
            logger.info("Retrieved %d papers from database", len(papers))
            return papers
        except Exception as e:
            logger.error("Error fetching papers: %s", str(e))
            raise
        finally:
            session.close()

    def add_paper(self, paper_data):
        """Add or update a paper and its current metrics.
        
        Returns:
            bool: True if this is a new paper, False if it's an update
        """
        logger.info("Adding/updating paper: %s", paper_data['url'])
        session = self.session_factory()
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

            # Create/update the paper entry with metrics
            paper = Paper(
                url=paper_data["url"],
                title=paper_data["paper_title"],
                authors=paper_data["authors"].split(", "),
                abstract=paper_data["abstract_body"],
                pdf_url=paper_data["view_pdf_url"],
                arxiv_url=paper_data["view_arxiv_page_url"],
                github_url=paper_data["github_repo_url"],
                publication_date=publication_date,
                submission_date=submission_date,
                upvotes=paper_data["number_of_upvotes"],
                comments=paper_data["number_of_comments"]
            )
            
            logger.debug("Merging paper data for %s", paper_data['url'])
            session.merge(paper)
            session.commit()
            logger.info("Successfully %s paper for %s", 
                       'added' if is_new_paper else 'updated', paper_data['url'])
            
            return is_new_paper
        except Exception as e:
            logger.error("Error adding/updating paper %s: %s", paper_data['url'], str(e))
            raise
        finally:
            session.close()

    def update_notification_status(self, url: str, status: bool) -> bool:
        """Update the notification status for a paper. Returns True if successful."""
        logger.info("Updating notification status for %s to %s", url, status)
        session = self.session_factory()
        try:
            paper = session.query(Paper).filter(Paper.url == url).first()
            if not paper:
                logger.error("Paper not found: %s", url)
                return False
            paper.notification_sent = status
            session.commit()
            logger.info("Successfully updated notification status")
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error("Error updating notification status: %s", str(e))
            return False
        finally:
            session.close()

    def get_failed_extractions(self, min_age_hours: int = 1):
        """Get papers that failed extraction and haven't been retried recently."""
        logger.info("Fetching failed extractions older than %d hours", min_age_hours)
        session = self.session_factory()
        try:
            retry_cutoff = datetime.now() - timedelta(hours=min_age_hours)
            papers = session.query(Paper).filter(
                Paper.extraction_success == False,
                Paper.last_extraction_attempt < retry_cutoff
            ).all()
            logger.info("Found %d failed extractions eligible for retry", len(papers))
            return papers
        except SQLAlchemyError as e:
            logger.error("Error fetching failed extractions: %s", str(e))
            return []
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
        
        logger.info("Test completed successfully! ✅")
        
    except (SQLAlchemyError, ValueError) as e:
        logger.error("Test failed! ❌ Error: %s", str(e))

# TODO: stream the DB contents to a Notion database a la Chief AI Officer database
