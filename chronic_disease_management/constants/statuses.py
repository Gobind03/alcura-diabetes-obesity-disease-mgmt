"""Status constants for enrollment, care plans, reviews, goals, and alerts."""

from enum import StrEnum


class EnrollmentStatus(StrEnum):
	DRAFT = "Draft"
	ACTIVE = "Active"
	ON_HOLD = "On Hold"
	COMPLETED = "Completed"
	WITHDRAWN = "Withdrawn"


class CarePlanStatus(StrEnum):
	DRAFT = "Draft"
	ACTIVE = "Active"
	UNDER_REVIEW = "Under Review"
	COMPLETED = "Completed"
	CANCELLED = "Cancelled"


class ReviewStatus(StrEnum):
	DRAFT = "Draft"
	SCHEDULED = "Scheduled"
	IN_PROGRESS = "In Progress"
	COMPLETED = "Completed"
	MISSED = "Missed"
	RESCHEDULED = "Rescheduled"
	CANCELLED = "Cancelled"


class GoalStatus(StrEnum):
	NOT_STARTED = "Not Started"
	IN_PROGRESS = "In Progress"
	ACHIEVED = "Achieved"
	PARTIALLY_MET = "Partially Met"
	NOT_MET = "Not Met"
	REVISED = "Revised"


class AlertSeverity(StrEnum):
	INFO = "Info"
	WARNING = "Warning"
	CRITICAL = "Critical"


class AlertStatus(StrEnum):
	OPEN = "Open"
	ACKNOWLEDGED = "Acknowledged"
	RESOLVED = "Resolved"
	DISMISSED = "Dismissed"


class ProtocolStatus(StrEnum):
	DRAFT = "Draft"
	ACTIVE = "Active"
	DEPRECATED = "Deprecated"
