"""Date utility functions for calendar app."""

import datetime
import argparse
from Foundation import NSDate


def parse_date(date_str):
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")


def get_date_range(from_date, to_date):
    """Get the start and end dates for the specified range."""
    # If no dates provided, use today
    if not from_date:
        from_date = datetime.datetime.now()
        from_date = datetime.datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0)
    else:
        from_date = datetime.datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0)

    if not to_date:
        to_date = from_date
        to_date = datetime.datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)
    else:
        to_date = datetime.datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)

    # Convert to NSDate
    start_date = NSDate.dateWithTimeIntervalSince1970_(from_date.timestamp())
    end_date = NSDate.dateWithTimeIntervalSince1970_(to_date.timestamp())

    return start_date, end_date