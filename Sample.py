import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from typing import List, Optional


def create_meeting_invite(
    organizer_email: str,
    attendees: List[str],
    start_time: str,
    end_time: str,
    subject: str,
    location: str,
    description: str = ""
) -> Optional[str]:
    """
    Generates an .ics calendar invite content in iCalendar format.

    Args:
        organizer_email (str): Email address of the organizer.
        attendees (List[str]): List of attendee email addresses.
        start_time (str): Start time in ISO format (e.g., "2025-05-20T14:00:00").
        end_time (str): End time in ISO format (e.g., "2025-05-20T15:00:00").
        subject (str): Meeting subject/title.
        location (str): Meeting location.
        description (str, optional): Meeting description.

    Returns:
        Optional[str]: The iCalendar content string or None if error occurs.
    """
    try:
        uid = f"{datetime.utcnow().timestamp()}@demo.agent"
        dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dtstart = datetime.fromisoformat(start_time).strftime("%Y%m%dT%H%M%SZ")
        dtend = datetime.fromisoformat(end_time).strftime("%Y%m%dT%H%M%SZ")

        attendee_lines = "\n".join([f"ATTENDEE;CN={email}:mailto:{email}" for email in attendees])

        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AgentFoundry//MeetingScheduler//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
SUMMARY:{subject}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
LOCATION:{location}
DESCRIPTION:{description}
ORGANIZER;CN=Organizer:mailto:{organizer_email}
{attendee_lines}
STATUS:CONFIRMED
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT10M
ACTION:DISPLAY
DESCRIPTION:Reminder
END:VALARM
END:VEVENT
END:VCALENDAR
"""
        return ics_content
    except Exception as e:
        print(f"Error creating .ics content: {e}")
        return None


def save_ics_file(ics_content: str, filename: str = "meeting_invite.ics") -> Optional[str]:
    """
    Saves the .ics content to a local file.

    Args:
        ics_content (str): The content of the .ics calendar invite.
        filename (str): The filename to save the invite as.

    Returns:
        Optional[str]: The full path to the saved file or None if error occurs.
    """
    try:
        with open(filename, "w") as f:
            f.write(ics_content)
        return os.path.abspath(filename)
    except Exception as e:
        print(f"Error saving .ics file: {e}")
        return None


def send_email_with_ics(
    sender_email: str,
    sender_password: str,
    recipients: List[str],
    subject: str,
    body: str,
    ics_file_path: str,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587
) -> bool:
    """
    Sends an email with an .ics calendar invite attached.

    Args:
        sender_email (str): Sender's email address.
        sender_password (str): Sender's email password or app password.
        recipients (List[str]): List of recipient email addresses.
        subject (str): Subject of the email.
        body (str): Body text of the email.
        ics_file_path (str): Path to the .ics file to attach.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port.

    Returns:
        bool: True if email sent successfully, False otherwise.
    """
    try:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.set_content(body)

        with open(ics_file_path, "rb") as f:
            ics_data = f.read()
            msg.add_attachment(
                ics_data,
                maintype="text",
                subtype="calendar",
                filename=os.path.basename(ics_file_path)
            )

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("Email sent successfully.")
            return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def generate_and_send_invite(
    organizer_email: str,
    attendees: List[str],
    start_time: str,
    end_time: str,
    subject: str,
    location: str,
    description: str,
    sender_email: str,
    sender_password: str
) -> bool:
    """
    Orchestrates the full invite flow: generate .ics, save it, and send via email.

    Args:
        organizer_email (str): Email of the meeting organizer.
        attendees (List[str]): Email addresses of attendees.
        start_time (str): Meeting start time (ISO format).
        end_time (str): Meeting end time (ISO format).
        subject (str): Meeting title.
        location (str): Meeting location.
        description (str): Meeting description.
        sender_email (str): Email to send from.
        sender_password (str): Email password or app password.

    Returns:
        bool: True if full process succeeds, False otherwise.
    """
    try:
        ics_content = create_meeting_invite(
            organizer_email, attendees, start_time, end_time, subject, location, description
        )
        if not ics_content:
            raise Exception("ICS content generation failed.")

        file_path = save_ics_file(ics_content)
        if not file_path:
            raise Exception("Saving .ics file failed.")

        return send_email_with_ics(
            sender_email,
            sender_password,
            attendees,
            subject,
            f"Hi,\n\nPlease find the meeting invite attached.\n\n{description}",
            file_path
        )
    except Exception as e:
        print(f"Failed to send meeting invite: {e}")
        return False
