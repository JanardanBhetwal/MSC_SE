import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mscteachers.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if len(sys.argv) == 1:
        sys.argv.append('runserver')
        sys.argv.append('127.0.0.1:7188')
    elif len(sys.argv) == 2 and sys.argv[1] == 'runserver':
        sys.argv.append('127.0.0.1:7188')

    execute_from_command_line(sys.argv)
