"""Healthcare doctype adapter layer.

Provides a stable abstraction over Marley Health / Frappe Healthcare doctypes.
All CDM services should access healthcare data through these adapters rather
than querying Patient, Encounter, Vital Signs, etc. directly.
"""
