"""Date utility functions for calendar app."""

import argparse
import datetime
import pytz
import zoneinfo
from typing import Optional, List, Dict, Any, Tuple

from Foundation import NSDate


def parse_date(date_str):
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        msg = f"Invalid date format: {date_str}. Use YYYY-MM-DD."
        raise argparse.ArgumentTypeError(msg)


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


def get_current_datetime(timezone: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the current date and time, optionally in a specific timezone.
    
    Args:
        timezone: Optional timezone name (e.g., 'America/New_York', 'Europe/London')
                 If not provided, uses the system's local timezone.
    
    Returns:
        A dictionary containing date and time information
    """
    # Get current time in UTC
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    
    # Get local timezone if none provided
    if timezone is None:
        local_tz = datetime.datetime.now().astimezone().tzinfo
        now_local = now_utc.astimezone(local_tz)
        timezone_name = str(local_tz)
    else:
        try:
            tz = zoneinfo.ZoneInfo(timezone)
            now_local = now_utc.astimezone(tz)
            timezone_name = timezone
        except Exception as e:
            return {
                "error": f"Invalid timezone: {timezone}. Error: {str(e)}",
                "valid_format": "Use IANA timezone names like 'America/New_York' or 'Europe/London'"
            }
    
    # Format results
    return {
        "date": {
            "year": now_local.year,
            "month": now_local.month,
            "day": now_local.day,
            "weekday": now_local.strftime("%A"),
            "iso_date": now_local.date().isoformat(),
        },
        "time": {
            "hour": now_local.hour,
            "minute": now_local.minute,
            "second": now_local.second,
            "iso_time": now_local.time().isoformat(timespec="seconds"),
        },
        "timezone": {
            "name": timezone_name,
            "utc_offset": now_local.strftime("%z"),
            "utc_offset_hours": float(now_local.utcoffset().total_seconds() / 3600),
        },
        "iso_datetime": now_local.isoformat(timespec="seconds"),
        "unix_timestamp": int(now_utc.timestamp()),
    }


def convert_timezone(
    dt_str: str, 
    from_timezone: str, 
    to_timezone: str,
    dt_format: str = "%Y-%m-%d %H:%M:%S"
) -> Dict[str, Any]:
    """
    Convert a datetime from one timezone to another.
    
    Args:
        dt_str: Datetime string to convert
        from_timezone: Source timezone (IANA format, e.g., 'America/New_York')
        to_timezone: Target timezone (IANA format, e.g., 'Europe/London')
        dt_format: Format of the input datetime string (default: "%Y-%m-%d %H:%M:%S")
    
    Returns:
        A dictionary with conversion results
    """
    try:
        # Parse the input datetime string
        dt = datetime.datetime.strptime(dt_str, dt_format)
        
        # Make it timezone-aware with the source timezone
        try:
            source_tz = zoneinfo.ZoneInfo(from_timezone)
        except Exception as e:
            return {
                "error": f"Invalid source timezone: {from_timezone}. Error: {str(e)}",
                "valid_format": "Use IANA timezone names like 'America/New_York' or 'Europe/London'"
            }
        
        source_dt = dt.replace(tzinfo=source_tz)
        
        # Convert to the target timezone
        try:
            target_tz = zoneinfo.ZoneInfo(to_timezone)
        except Exception as e:
            return {
                "error": f"Invalid target timezone: {to_timezone}. Error: {str(e)}",
                "valid_format": "Use IANA timezone names like 'America/New_York' or 'Europe/London'"
            }
        
        target_dt = source_dt.astimezone(target_tz)
        
        # Return formatted result
        return {
            "original": {
                "datetime": dt_str,
                "timezone": from_timezone,
                "iso_datetime": source_dt.isoformat(),
            },
            "converted": {
                "datetime": target_dt.strftime(dt_format),
                "timezone": to_timezone,
                "iso_datetime": target_dt.isoformat(),
                "date": target_dt.date().isoformat(),
                "time": target_dt.time().isoformat(timespec="seconds"),
            },
            "offset_hours": float(target_dt.utcoffset().total_seconds() / 3600) - 
                           float(source_dt.utcoffset().total_seconds() / 3600),
        }
    except ValueError as e:
        return {
            "error": f"Invalid datetime format: {e}",
            "valid_format": f"Use format: {dt_format}"
        }


def list_common_timezones() -> Dict[str, Any]:
    """
    Get a list of common timezones grouped by region.
    
    Returns:
        A dictionary with timezone information grouped by region
    """
    timezones_by_region = {}
    
    for tz_name in sorted(pytz.common_timezones):
        region = tz_name.split('/', 1)[0] if '/' in tz_name else "Other"
        
        if region not in timezones_by_region:
            timezones_by_region[region] = []
        
        # Get current time in this timezone
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        tz = pytz.timezone(tz_name)
        now_local = now_utc.astimezone(tz)
        
        timezones_by_region[region].append({
            "name": tz_name,
            "utc_offset": now_local.strftime("%z"),
            "utc_offset_hours": float(now_local.utcoffset().total_seconds() / 3600),
            "current_time": now_local.strftime("%H:%M:%S"),
        })
    
    return {
        "regions": sorted(timezones_by_region.keys()),
        "timezones_by_region": timezones_by_region,
        "total_count": len(pytz.common_timezones),
    }
