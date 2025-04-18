"""Calendar event store for accessing macOS Calendar events and reminders."""

import sys
import time

from EventKit import (
    EKCalendarEventAvailabilityBusy,
    EKEntityTypeEvent,
    EKEntityTypeReminder,
    EKEventStore,
)
from Foundation import NSDate, NSDefaultRunLoopMode, NSRunLoop

from calendar_app.models.formatters import format_event, format_reminder
from calendar_app.utils.date_utils import get_date_range


class CalendarEventStore:
    """Class to handle calendar event store operations."""

    def __init__(self, quiet=False) -> None:
        # Create event store
        self.event_store = EKEventStore.alloc().init()
        self.event_authorized = False
        self.reminder_authorized = False
        self.quiet = quiet
        self.request_authorization()

    def request_authorization(self) -> None:
        """Request access to calendars and reminders."""
        # Authorization result holders
        event_result = {"authorized": False, "complete": False}
        reminder_result = {"authorized": False, "complete": False}

        if not self.quiet:
            print("Requesting access to your calendars and reminders...", file=sys.stderr)

        # Define callbacks
        def event_callback(granted, error) -> None:
            event_result["authorized"] = granted
            event_result["complete"] = True
            if error and not self.quiet:
                print(f"Event authorization error: {error}", file=sys.stderr)

        def reminder_callback(granted, error) -> None:
            reminder_result["authorized"] = granted
            reminder_result["complete"] = True
            if error and not self.quiet:
                print(f"Reminder authorization error: {error}", file=sys.stderr)

        # Request access to calendars
        self.event_store.requestAccessToEntityType_completion_(EKEntityTypeEvent, event_callback)
        # Request access to reminders
        self.event_store.requestAccessToEntityType_completion_(
            EKEntityTypeReminder, reminder_callback
        )

        # Wait for authorization callbacks to complete
        timeout = 10  # seconds
        start_time = time.time()

        if not self.quiet:
            print("Waiting for authorization responses...", file=sys.stderr)
            
        while not (event_result["complete"] and reminder_result["complete"]):
            # Run the run loop for a short time to process callbacks
            NSRunLoop.currentRunLoop().runMode_beforeDate_(
                NSDefaultRunLoopMode, NSDate.dateWithTimeIntervalSinceNow_(0.1)
            )

            # Check for timeout
            if time.time() - start_time > timeout:
                if not self.quiet:
                    print("Timed out waiting for authorization", file=sys.stderr)
                break

        self.event_authorized = event_result["authorized"]
        self.reminder_authorized = reminder_result["authorized"]

        if self.event_authorized and not self.quiet:
            print("Calendar access authorized", file=sys.stderr)

        if self.reminder_authorized and not self.quiet:
            print("Reminders access authorized", file=sys.stderr)

    def get_calendars(self):
        """Get all available calendars."""
        result = {"event_calendars": [], "reminder_calendars": []}

        if self.event_authorized:
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
            for calendar in calendars:
                result["event_calendars"].append(
                    {
                        "title": calendar.title(),
                        "color": f"#{int(calendar.color().redComponent() * 255):02x}{int(calendar.color().greenComponent() * 255):02x}{int(calendar.color().blueComponent() * 255):02x}",
                        "type": "Event",
                    }
                )
        else:
            result["events_error"] = "Calendar access not authorized"

        if self.reminder_authorized:
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)
            for calendar in calendars:
                result["reminder_calendars"].append(
                    {
                        "title": calendar.title(),
                        "color": f"#{int(calendar.color().redComponent() * 255):02x}{int(calendar.color().greenComponent() * 255):02x}{int(calendar.color().blueComponent() * 255):02x}",
                        "type": "Reminder",
                    }
                )
        else:
            result["reminders_error"] = "Reminders access not authorized"

        return result

    def get_events_and_reminders(
        self,
        from_date=None,
        to_date=None,
        calendars=None,
        include_completed=False,
        all_day_only=False,
        busy_only=False,
    ):
        """Get events and reminders for the specified date range."""
        # Get date range
        start_date, end_date = get_date_range(from_date, to_date)

        # Initialize results
        result = {"events": [], "reminders": []}

        # Get calendar events
        if self.event_authorized:
            # Get calendars for filtering
            all_calendars = None
            if calendars:
                all_cal = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
                filtered_calendars = [c for c in all_cal if c.title() in calendars]
                if filtered_calendars:
                    all_calendars = filtered_calendars

            # Create predicate for events between start and end dates
            predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
                start_date, end_date, all_calendars
            )
            events = self.event_store.eventsMatchingPredicate_(predicate)

            # Filter events
            filtered_events = []
            for event in events:
                if all_day_only and not event.isAllDay():
                    continue
                if busy_only and event.availability() != EKCalendarEventAvailabilityBusy:
                    continue
                filtered_events.append(event)

            # Format events
            for event in filtered_events:
                result["events"].append(format_event(event))
        else:
            result["events_error"] = "Calendar access not authorized"

        # Get reminders
        if self.reminder_authorized:
            # Get calendars for filtering
            reminder_calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)
            if calendars:
                reminder_calendars = [c for c in reminder_calendars if c.title() in calendars]

            if reminder_calendars:
                # Create predicate for reminders
                if include_completed:
                    predicate = (
                        self.event_store.predicateForRemindersWithDueDateStarting_ending_calendars_(
                            start_date, end_date, reminder_calendars
                        )
                    )
                else:
                    predicate = self.event_store.predicateForIncompleteRemindersWithDueDateStarting_ending_calendars_(
                        start_date, end_date, reminder_calendars
                    )

                # Fetch reminders with completion handler
                reminders_result = {"reminders": None, "complete": False}

                def reminders_callback(fetchedReminders) -> None:
                    reminders_result["reminders"] = fetchedReminders
                    reminders_result["complete"] = True

                # Fetch reminders
                self.event_store.fetchRemindersMatchingPredicate_completion_(
                    predicate, reminders_callback
                )

                # Wait for reminders fetch to complete
                start_time = time.time()
                timeout = 10  # seconds
                while not reminders_result["complete"]:
                    NSRunLoop.currentRunLoop().runMode_beforeDate_(
                        NSDefaultRunLoopMode, NSDate.dateWithTimeIntervalSinceNow_(0.1)
                    )

                    # Check for timeout
                    if time.time() - start_time > timeout:
                        if not self.quiet:
                            print("Timed out waiting for reminders", file=sys.stderr)
                        break

                # Format reminders
                if reminders_result["reminders"]:
                    for reminder in reminders_result["reminders"]:
                        result["reminders"].append(format_reminder(reminder))
        else:
            result["reminders_error"] = "Reminders access not authorized"

        return result
