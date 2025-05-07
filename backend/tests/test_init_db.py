import os
import subprocess
import pytest
import logging
from unittest.mock import patch, MagicMock, call
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.models.user import User
from app.models.company import Company


def test_init_db_tables_exist(db: Session):
    """Test init_db when tables already exist"""
    
    # Apply patches to simulate that tables exist
    with patch('sqlalchemy.inspect') as mock_inspect, \
         patch('app.db.init_db.logger') as mock_logger:
        
        # Mock inspector to indicate that tables exist
        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector
        
        # Call the function
        init_db(db)
        
        # Check that logger was called with expected message
        mock_logger.info.assert_any_call("Running database migrations...")
        
        # Verify inspect was called
        mock_inspect.assert_called_once()


def test_init_db_tables_dont_exist_but_migrations_succeed(db: Session):
    """Test init_db when tables don't exist but migrations succeed"""
    
    # Create a sequence of responses: first False (no tables), then True (tables created)
    inspector_responses = [MagicMock(), MagicMock()]
    inspector_responses[0].has_table.return_value = False  # First check: no tables
    inspector_responses[1].has_table.return_value = True   # After migration: tables exist
    
    # Apply patches
    with patch('sqlalchemy.inspect') as mock_inspect, \
         patch('subprocess.run') as mock_run, \
         patch('os.path.exists', return_value=True), \
         patch('app.db.init_db.logger') as mock_logger:
        
        # Set up inspector to give different responses on consecutive calls
        mock_inspect.side_effect = inspector_responses
        
        # Mock subprocess result
        mock_process = MagicMock()
        mock_process.stdout = "Migration success"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        # Call the function
        init_db(db)
        
        # Verify migrations were run
        mock_run.assert_called_once()
        
        # Verify log messages
        mock_logger.info.assert_any_call("Tables don't exist. Running migrations with alembic...")
        mock_logger.info.assert_any_call(f"Migration stdout: {mock_process.stdout}")


def test_init_db_missing_alembic_files(db: Session):
    """Test handling of missing Alembic files"""
    
    # Apply patches
    with patch('sqlalchemy.inspect') as mock_inspect, \
         patch('subprocess.run') as mock_run, \
         patch('os.path.exists', return_value=False), \
         patch('app.db.init_db.logger') as mock_logger:
        
        # Mock inspector
        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = False
        mock_inspect.return_value = mock_inspector
        
        # Call the function
        init_db(db)
        
        # Verify error was logged about missing files
        mock_logger.error.assert_called()
        
        # Verify migrations weren't run
        mock_run.assert_not_called()


def test_init_db_migration_error(db: Session):
    """Test handling of migration errors"""
    
    # Apply patches
    with patch('sqlalchemy.inspect') as mock_inspect, \
         patch('subprocess.run') as mock_run, \
         patch('os.path.exists', return_value=True), \
         patch('app.db.init_db.logger') as mock_logger:
        
        # Mock inspector
        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = False
        mock_inspect.return_value = mock_inspector
        
        # Set up subprocess.run to raise an exception
        mock_run.side_effect = Exception("Migration command failed")
        
        # Call the function
        init_db(db)
        
        # Verify exception was caught and logged
        mock_logger.exception.assert_called_once()


def test_init_db_migration_stderr(db: Session):
    """Test handling of migration with stderr output"""
    
    # Apply patches
    with patch('sqlalchemy.inspect') as mock_inspect, \
         patch('subprocess.run') as mock_run, \
         patch('os.path.exists', return_value=True), \
         patch('app.db.init_db.logger') as mock_logger:
        
        # Mock inspector - simulate that tables still don't exist after migration
        inspector_responses = [MagicMock(), MagicMock()]
        inspector_responses[0].has_table.return_value = False  # First check: no tables
        inspector_responses[1].has_table.return_value = True   # After migration: tables exist
        mock_inspect.side_effect = inspector_responses
        
        # Create a mock process result with stderr
        mock_process = MagicMock()
        mock_process.stdout = "Migration output"
        mock_process.stderr = "Migration warning"
        mock_run.return_value = mock_process
        
        # Call the function
        init_db(db)
        
        # Verify stderr was logged (using assert_any_call instead of assert_called_with)
        mock_logger.error.assert_any_call(f"Migration stderr: {mock_process.stderr}")


def test_init_db_migration_tables_still_missing(db: Session):
    """Test handling of migration that fails to create tables"""
    
    # Apply patches
    with patch('sqlalchemy.inspect') as mock_inspect, \
         patch('subprocess.run') as mock_run, \
         patch('os.path.exists', return_value=True), \
         patch('app.db.init_db.logger') as mock_logger:
        
        # Mock inspectors - tables still missing after migration
        inspector_responses = [MagicMock(), MagicMock()]
        inspector_responses[0].has_table.return_value = False  # First check: no tables
        inspector_responses[1].has_table.return_value = False  # After migration: still no tables
        mock_inspect.side_effect = inspector_responses
        
        # Create a mock process result
        mock_process = MagicMock()
        mock_process.stdout = "Migration output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        # Call the function
        init_db(db)
        
        # Verify error was logged
        mock_logger.error.assert_called_with("Tables still don't exist after migration!")


def test_init_db_admin_already_exists(db: Session):
    """Test init_db when admin user already exists"""
    
    # Create admin user in the test database
    admin_email = "admin@saas.com"
    admin = User(
        email=admin_email,
        hashed_password="hashed_password",
        is_admin=True
    )
    db.add(admin)
    db.commit()
    
    # Count users before
    user_count_before = db.query(User).count()
    
    # Apply patches to skip migration checks
    with patch('sqlalchemy.inspect') as mock_inspect:
        # Mock inspector to report tables exist
        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector
        
        # Call the function
        init_db(db)
    
    # Count users after
    user_count_after = db.query(User).count()
    
    # Verify no new users were created
    assert user_count_after == user_count_before
    
    # Clean up
    db.query(User).filter(User.email == admin_email).delete()
    db.commit()


def test_init_db_creates_admin_and_user(db: Session):
    """Test that init_db creates the admin user and member user when needed"""
    
    # Make sure admin doesn't exist
    admin_email = "admin@saas.com"
    member_email = "usuario@ort.com"
    company_name = "ORT"
    
    db.query(User).filter(User.email.in_([admin_email, member_email])).delete()
    db.query(Company).filter(Company.name == company_name).delete()
    db.commit()
    
    # Apply patches to skip migration checks
    with patch('sqlalchemy.inspect') as mock_inspect, \
         patch('app.db.init_db.logger') as mock_logger:
        # Mock inspector to report tables exist
        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector
        
        # Call the function
        init_db(db)
    
    # Verify admin user was created
    admin_user = db.query(User).filter(User.email == admin_email).first()
    assert admin_user is not None
    assert admin_user.is_admin is True
    assert admin_user.company_id is None
    
    # Verify company was created
    company = db.query(Company).filter(Company.name == company_name).first()
    assert company is not None
    assert company.address == "Cuareim 1451"
    assert company.website == "https://www.ort.edu.uy"
    
    # Verify member user was created
    member_user = db.query(User).filter(User.email == member_email).first()
    assert member_user is not None
    assert member_user.is_admin is False
    assert member_user.company_id == company.id
    
    # Clean up
    db.query(User).filter(User.email.in_([admin_email, member_email])).delete()
    db.query(Company).filter(Company.name == company_name).delete()
    db.commit()


def test_init_db_company_exists_creates_users(db: Session):
    """Test that init_db creates users when company already exists"""
    
    # Make sure admin doesn't exist but company does
    admin_email = "admin@saas.com"
    member_email = "usuario@ort.com"
    company_name = "ORT"
    
    db.query(User).filter(User.email.in_([admin_email, member_email])).delete()
    db.query(Company).filter(Company.name == company_name).delete()
    
    # Create the company
    company = Company(
        name=company_name,
        address="Test Address",
        website="https://test.com",
        logo=b"test_logo"
    )
    db.add(company)
    db.commit()
    
    # Apply patches to skip migration checks
    with patch('sqlalchemy.inspect') as mock_inspect, \
         patch('app.db.init_db.logger') as mock_logger:
        # Mock inspector to report tables exist
        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector
        
        # Call the function
        init_db(db)
    
    # Verify admin user was created
    admin_user = db.query(User).filter(User.email == admin_email).first()
    assert admin_user is not None
    assert admin_user.is_admin is True
    
    # Verify company was not changed
    company = db.query(Company).filter(Company.name == company_name).first()
    assert company is not None
    assert company.address == "Test Address"  # Original address preserved
    
    # Verify member user was created
    member_user = db.query(User).filter(User.email == member_email).first()
    assert member_user is not None
    assert member_user.is_admin is False
    assert member_user.company_id == company.id
    
    # Clean up
    db.query(User).filter(User.email.in_([admin_email, member_email])).delete()
    db.query(Company).filter(Company.name == company_name).delete()
    db.commit() 