#!/usr/bin/env python
import os
import sys
import django

def main():
    """Run migrations to create database tables."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'streamflix.settings')
    django.setup()
    
    # Import and run the migration commands
    from django.core.management import call_command
    
    print("Making migrations...")
    call_command('makemigrations', 'movies')
    
    print("Running migrations...")
    call_command('migrate')
    
    print("Migrations complete!")
    print("You can now start the server with: python manage.py runserver")

if __name__ == '__main__':
    main()
