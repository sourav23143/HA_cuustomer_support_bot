"""
Seed demo data into MongoDB.

Idempotent: uses replace_one with upsert=True so running
multiple times will not create duplicates.

Usage:
    python scripts/seed_demo_data.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.db.mongodb import get_database


# ────────────────────────────────────────────────────────────
# Demo Users (15 patients)
# ────────────────────────────────────────────────────────────
USERS = [
    {
        "_id": "U1001",
        "name": "Sourav Kumar",
        "email": "sourav.kumar@demo.com",
        "phone": "+91-9876543001",
        "role": "patient",
        "language": "English",
        "city": "Jaipur",
        "created_at": datetime(2026, 8, 1, 10, 0, 0),
    },
    {
        "_id": "U1002",
        "name": "Priya Gupta",
        "email": "priya.gupta@demo.com",
        "phone": "+91-9876543002",
        "role": "patient",
        "language": "Hindi",
        "city": "Mumbai",
        "created_at": datetime(2026, 8, 2, 11, 0, 0),
    },
    {
        "_id": "U1003",
        "name": "Rahul Verma",
        "email": "rahul.verma@demo.com",
        "phone": "+91-9876543003",
        "role": "patient",
        "language": "English",
        "city": "Delhi",
        "created_at": datetime(2026, 8, 3, 9, 30, 0),
    },
    {
        "_id": "U1004",
        "name": "Ananya Singh",
        "email": "ananya.singh@demo.com",
        "phone": "+91-9876543004",
        "role": "patient",
        "language": "English",
        "city": "Bangalore",
        "created_at": datetime(2026, 8, 4, 14, 0, 0),
    },
    {
        "_id": "U1005",
        "name": "Mohammed Ali",
        "email": "mohammed.ali@demo.com",
        "phone": "+91-9876543005",
        "role": "patient",
        "language": "English",
        "city": "Hyderabad",
        "created_at": datetime(2026, 8, 5, 8, 0, 0),
    },
    {
        "_id": "U1006",
        "name": "Deepika Reddy",
        "email": "deepika.reddy@demo.com",
        "phone": "+91-9876543006",
        "role": "patient",
        "language": "English",
        "city": "Chennai",
        "created_at": datetime(2026, 8, 6, 12, 0, 0),
    },
    {
        "_id": "U1007",
        "name": "Vikram Patel",
        "email": "vikram.patel@demo.com",
        "phone": "+91-9876543007",
        "role": "patient",
        "language": "Gujarati",
        "city": "Pune",
        "created_at": datetime(2026, 8, 7, 10, 30, 0),
    },
    {
        "_id": "U1008",
        "name": "Neha Sharma",
        "email": "neha.sharma@demo.com",
        "phone": "+91-9876543008",
        "role": "patient",
        "language": "Hindi",
        "city": "Jaipur",
        "created_at": datetime(2026, 8, 8, 16, 0, 0),
    },
    {
        "_id": "U1009",
        "name": "Arjun Das",
        "email": "arjun.das@demo.com",
        "phone": "+91-9876543009",
        "role": "patient",
        "language": "Bengali",
        "city": "Kolkata",
        "created_at": datetime(2026, 8, 9, 11, 0, 0),
    },
    {
        "_id": "U1010",
        "name": "Kavita Iyer",
        "email": "kavita.iyer@demo.com",
        "phone": "+91-9876543010",
        "role": "patient",
        "language": "English",
        "city": "Kochi",
        "created_at": datetime(2026, 8, 10, 9, 0, 0),
    },
    {
        "_id": "U1011",
        "name": "Ravi Shankar",
        "email": "ravi.shankar@demo.com",
        "phone": "+91-9876543011",
        "role": "patient",
        "language": "English",
        "city": "Lucknow",
        "created_at": datetime(2026, 8, 11, 13, 0, 0),
    },
    {
        "_id": "U1012",
        "name": "Sneha Menon",
        "email": "sneha.menon@demo.com",
        "phone": "+91-9876543012",
        "role": "patient",
        "language": "Malayalam",
        "city": "Trivandrum",
        "created_at": datetime(2026, 8, 12, 15, 0, 0),
    },
    {
        "_id": "U1013",
        "name": "Aditya Joshi",
        "email": "aditya.joshi@demo.com",
        "phone": "+91-9876543013",
        "role": "patient",
        "language": "Marathi",
        "city": "Nagpur",
        "created_at": datetime(2026, 8, 13, 10, 0, 0),
    },
    {
        "_id": "U1014",
        "name": "Fatima Khan",
        "email": "fatima.khan@demo.com",
        "phone": "+91-9876543014",
        "role": "patient",
        "language": "Urdu",
        "city": "Bhopal",
        "created_at": datetime(2026, 8, 14, 11, 30, 0),
    },
    {
        "_id": "U1015",
        "name": "Sanjay Nair",
        "email": "sanjay.nair@demo.com",
        "phone": "+91-9876543015",
        "role": "patient",
        "language": "English",
        "city": "Indore",
        "created_at": datetime(2026, 8, 15, 14, 0, 0),
    },
]


# ────────────────────────────────────────────────────────────
# Demo Doctors (7)
# ────────────────────────────────────────────────────────────
DOCTORS = [
    {
        "_id": "D1001",
        "name": "Dr. Priya Sharma",
        "specialization": "General Physician",
        "languages": ["English", "Hindi"],
        "availability": "online",
        "rating": 4.8,
        "experience_years": 12,
    },
    {
        "_id": "D1002",
        "name": "Dr. Amit Verma",
        "specialization": "Cardiologist",
        "languages": ["English", "Hindi"],
        "availability": "online",
        "rating": 4.9,
        "experience_years": 15,
    },
    {
        "_id": "D1003",
        "name": "Dr. Sunita Patel",
        "specialization": "Dermatologist",
        "languages": ["English", "Gujarati", "Hindi"],
        "availability": "offline",
        "rating": 4.7,
        "experience_years": 8,
    },
    {
        "_id": "D1004",
        "name": "Dr. Rajesh Kumar",
        "specialization": "Pediatrician",
        "languages": ["English", "Hindi"],
        "availability": "online",
        "rating": 4.6,
        "experience_years": 10,
    },
    {
        "_id": "D1005",
        "name": "Dr. Meena Iyer",
        "specialization": "Psychiatrist",
        "languages": ["English", "Tamil", "Hindi"],
        "availability": "busy",
        "rating": 4.8,
        "experience_years": 14,
    },
    {
        "_id": "D1006",
        "name": "Dr. Sanjay Gupta",
        "specialization": "Orthopedic",
        "languages": ["English", "Hindi"],
        "availability": "online",
        "rating": 4.5,
        "experience_years": 20,
    },
    {
        "_id": "D1007",
        "name": "Dr. Nisha Reddy",
        "specialization": "ENT Specialist",
        "languages": ["English", "Telugu", "Hindi"],
        "availability": "online",
        "rating": 4.7,
        "experience_years": 9,
    },
]


# ────────────────────────────────────────────────────────────
# Demo Consultations
# ────────────────────────────────────────────────────────────
CONSULTATIONS = [
    # Scenario 1: Doctor didn't join (U1001 — main demo scenario)
    {
        "_id": "C1001",
        "patient_id": "U1001",
        "doctor_id": "D1001",
        "status": "failed",
        "patient_joined": True,
        "doctor_joined": False,
        "scheduled_at": datetime(2026, 8, 30, 19, 30, 0),
        "started_at": datetime(2026, 8, 30, 19, 30, 0),
        "ended_at": None,
        "notes": None,
    },
    # Scenario 2: Successful consultation (U1002)
    {
        "_id": "C1002",
        "patient_id": "U1002",
        "doctor_id": "D1002",
        "status": "completed",
        "patient_joined": True,
        "doctor_joined": True,
        "scheduled_at": datetime(2026, 8, 28, 14, 0, 0),
        "started_at": datetime(2026, 8, 28, 14, 2, 0),
        "ended_at": datetime(2026, 8, 28, 14, 25, 0),
        "notes": "Routine cardiac checkup. No issues found.",
    },
    # Scenario 3: Payment failed (U1003)
    {
        "_id": "C1003",
        "patient_id": "U1003",
        "doctor_id": "D1003",
        "status": "scheduled",
        "patient_joined": False,
        "doctor_joined": False,
        "scheduled_at": datetime(2026, 8, 31, 16, 0, 0),
        "started_at": None,
        "ended_at": None,
        "notes": None,
    },
    # Scenario 4: Cancelled consultation (U1004)
    {
        "_id": "C1004",
        "patient_id": "U1004",
        "doctor_id": "D1004",
        "status": "cancelled",
        "patient_joined": False,
        "doctor_joined": False,
        "scheduled_at": datetime(2026, 8, 29, 10, 0, 0),
        "started_at": None,
        "ended_at": None,
        "notes": "Patient cancelled due to scheduling conflict.",
    },
    # Scenario 5: Pending payment (U1005)
    {
        "_id": "C1005",
        "patient_id": "U1005",
        "doctor_id": "D1005",
        "status": "scheduled",
        "patient_joined": False,
        "doctor_joined": False,
        "scheduled_at": datetime(2026, 9, 1, 11, 0, 0),
        "started_at": None,
        "ended_at": None,
        "notes": None,
    },
    # Active consultation in progress (U1011)
    {
        "_id": "C1006",
        "patient_id": "U1011",
        "doctor_id": "D1006",
        "status": "in_progress",
        "patient_joined": True,
        "doctor_joined": True,
        "scheduled_at": datetime(2026, 8, 31, 10, 0, 0),
        "started_at": datetime(2026, 8, 31, 10, 2, 0),
        "ended_at": None,
        "notes": None,
    },
    # Second failed consultation for refund demo (U1005)
    {
        "_id": "C1007",
        "patient_id": "U1005",
        "doctor_id": "D1007",
        "status": "failed",
        "patient_joined": True,
        "doctor_joined": False,
        "scheduled_at": datetime(2026, 8, 27, 15, 0, 0),
        "started_at": datetime(2026, 8, 27, 15, 0, 0),
        "ended_at": None,
        "notes": None,
    },
    # Consultation for compensation demand user (U1010)
    {
        "_id": "C1008",
        "patient_id": "U1010",
        "doctor_id": "D1002",
        "status": "failed",
        "patient_joined": True,
        "doctor_joined": False,
        "scheduled_at": datetime(2026, 8, 29, 18, 0, 0),
        "started_at": datetime(2026, 8, 29, 18, 0, 0),
        "ended_at": None,
        "notes": None,
    },
]


# ────────────────────────────────────────────────────────────
# Demo Payments
# ────────────────────────────────────────────────────────────
PAYMENTS = [
    # U1001: Paid but doctor didn't join
    {
        "_id": "P1001",
        "patient_id": "U1001",
        "consultation_id": "C1001",
        "amount": 499,
        "currency": "INR",
        "status": "success",
        "payment_method": "UPI",
        "created_at": datetime(2026, 8, 30, 19, 25, 0),
        "updated_at": datetime(2026, 8, 30, 19, 25, 0),
    },
    # U1002: Successful payment for completed consultation
    {
        "_id": "P1002",
        "patient_id": "U1002",
        "consultation_id": "C1002",
        "amount": 299,
        "currency": "INR",
        "status": "success",
        "payment_method": "Card",
        "created_at": datetime(2026, 8, 28, 13, 55, 0),
        "updated_at": datetime(2026, 8, 28, 13, 55, 0),
    },
    # U1003: Payment failed
    {
        "_id": "P1003",
        "patient_id": "U1003",
        "consultation_id": "C1003",
        "amount": 499,
        "currency": "INR",
        "status": "failed",
        "payment_method": "UPI",
        "created_at": datetime(2026, 8, 31, 15, 50, 0),
        "updated_at": datetime(2026, 8, 31, 15, 50, 0),
    },
    # U1004: Refunded after cancellation
    {
        "_id": "P1004",
        "patient_id": "U1004",
        "consultation_id": "C1004",
        "amount": 399,
        "currency": "INR",
        "status": "refunded",
        "payment_method": "Card",
        "created_at": datetime(2026, 8, 29, 9, 50, 0),
        "updated_at": datetime(2026, 8, 29, 10, 30, 0),
    },
    # U1005: Pending payment
    {
        "_id": "P1005",
        "patient_id": "U1005",
        "consultation_id": "C1005",
        "amount": 599,
        "currency": "INR",
        "status": "pending",
        "payment_method": "UPI",
        "created_at": datetime(2026, 9, 1, 10, 50, 0),
        "updated_at": datetime(2026, 9, 1, 10, 50, 0),
    },
    # U1011: Active consultation payment
    {
        "_id": "P1006",
        "patient_id": "U1011",
        "consultation_id": "C1006",
        "amount": 349,
        "currency": "INR",
        "status": "success",
        "payment_method": "UPI",
        "created_at": datetime(2026, 8, 31, 9, 55, 0),
        "updated_at": datetime(2026, 8, 31, 9, 55, 0),
    },
    # U1005: Payment for failed refund consultation
    {
        "_id": "P1007",
        "patient_id": "U1005",
        "consultation_id": "C1007",
        "amount": 499,
        "currency": "INR",
        "status": "success",
        "payment_method": "Card",
        "created_at": datetime(2026, 8, 27, 14, 50, 0),
        "updated_at": datetime(2026, 8, 27, 14, 50, 0),
    },
    # U1010: Payment for compensation demand scenario
    {
        "_id": "P1008",
        "patient_id": "U1010",
        "consultation_id": "C1008",
        "amount": 499,
        "currency": "INR",
        "status": "success",
        "payment_method": "UPI",
        "created_at": datetime(2026, 8, 29, 17, 55, 0),
        "updated_at": datetime(2026, 8, 29, 17, 55, 0),
    },
]


# ────────────────────────────────────────────────────────────
# Demo User Activities
# ────────────────────────────────────────────────────────────
ACTIVITIES = [
    # U1001: Doctor didn't join flow
    {
        "_id": "A1001",
        "user_id": "U1001",
        "activity_type": "payment_completed",
        "consultation_id": "C1001",
        "description": "Payment of ₹499 completed via UPI for consultation C1001.",
        "timestamp": datetime(2026, 8, 30, 19, 25, 0),
    },
    {
        "_id": "A1002",
        "user_id": "U1001",
        "activity_type": "consultation_joined",
        "consultation_id": "C1001",
        "description": "Patient joined consultation C1001.",
        "timestamp": datetime(2026, 8, 30, 19, 30, 0),
    },
    {
        "_id": "A1003",
        "user_id": "U1001",
        "activity_type": "doctor_not_joined",
        "consultation_id": "C1001",
        "description": "Assigned doctor Dr. Priya Sharma did not join consultation C1001.",
        "timestamp": datetime(2026, 8, 30, 19, 34, 0),
    },
    {
        "_id": "A1004",
        "user_id": "U1001",
        "activity_type": "support_contacted",
        "consultation_id": "C1001",
        "description": "Patient contacted support regarding failed consultation.",
        "timestamp": datetime(2026, 8, 30, 19, 40, 0),
    },
    # U1002: Successful flow
    {
        "_id": "A1005",
        "user_id": "U1002",
        "activity_type": "payment_completed",
        "consultation_id": "C1002",
        "description": "Payment of ₹299 completed via Card for consultation C1002.",
        "timestamp": datetime(2026, 8, 28, 13, 55, 0),
    },
    {
        "_id": "A1006",
        "user_id": "U1002",
        "activity_type": "consultation_joined",
        "consultation_id": "C1002",
        "description": "Patient joined consultation C1002.",
        "timestamp": datetime(2026, 8, 28, 14, 0, 0),
    },
    # U1003: Payment failed
    {
        "_id": "A1007",
        "user_id": "U1003",
        "activity_type": "payment_failed",
        "consultation_id": "C1003",
        "description": "Payment of ₹499 failed via UPI for consultation C1003.",
        "timestamp": datetime(2026, 8, 31, 15, 50, 0),
    },
    # U1004: Cancellation
    {
        "_id": "A1008",
        "user_id": "U1004",
        "activity_type": "consultation_cancelled",
        "consultation_id": "C1004",
        "description": "Patient cancelled consultation C1004.",
        "timestamp": datetime(2026, 8, 29, 9, 45, 0),
    },
    # U1005: Refund request scenario
    {
        "_id": "A1009",
        "user_id": "U1005",
        "activity_type": "payment_completed",
        "consultation_id": "C1007",
        "description": "Payment of ₹499 completed via Card for consultation C1007.",
        "timestamp": datetime(2026, 8, 27, 14, 50, 0),
    },
    {
        "_id": "A1010",
        "user_id": "U1005",
        "activity_type": "doctor_not_joined",
        "consultation_id": "C1007",
        "description": "Assigned doctor Dr. Nisha Reddy did not join consultation C1007.",
        "timestamp": datetime(2026, 8, 27, 15, 5, 0),
    },
    # U1006: Login issue
    {
        "_id": "A1011",
        "user_id": "U1006",
        "activity_type": "login_attempt",
        "consultation_id": None,
        "description": "Failed login attempt — OTP not received.",
        "timestamp": datetime(2026, 8, 31, 8, 0, 0),
    },
    {
        "_id": "A1012",
        "user_id": "U1006",
        "activity_type": "login_attempt",
        "consultation_id": None,
        "description": "Failed login attempt — OTP expired.",
        "timestamp": datetime(2026, 8, 31, 8, 5, 0),
    },
    # U1007: Profile update
    {
        "_id": "A1013",
        "user_id": "U1007",
        "activity_type": "profile_updated",
        "consultation_id": None,
        "description": "User updated profile phone number.",
        "timestamp": datetime(2026, 8, 30, 10, 0, 0),
    },
    # U1010: Compensation demand user
    {
        "_id": "A1014",
        "user_id": "U1010",
        "activity_type": "payment_completed",
        "consultation_id": "C1008",
        "description": "Payment of ₹499 completed via UPI for consultation C1008.",
        "timestamp": datetime(2026, 8, 29, 17, 55, 0),
    },
    {
        "_id": "A1015",
        "user_id": "U1010",
        "activity_type": "doctor_not_joined",
        "consultation_id": "C1008",
        "description": "Assigned doctor Dr. Amit Verma did not join consultation C1008.",
        "timestamp": datetime(2026, 8, 29, 18, 5, 0),
    },
    {
        "_id": "A1016",
        "user_id": "U1010",
        "activity_type": "support_contacted",
        "consultation_id": "C1008",
        "description": "Patient contacted support demanding compensation.",
        "timestamp": datetime(2026, 8, 29, 18, 15, 0),
    },
    # U1011: Active consultation
    {
        "_id": "A1017",
        "user_id": "U1011",
        "activity_type": "payment_completed",
        "consultation_id": "C1006",
        "description": "Payment of ₹349 completed via UPI for consultation C1006.",
        "timestamp": datetime(2026, 8, 31, 9, 55, 0),
    },
    {
        "_id": "A1018",
        "user_id": "U1011",
        "activity_type": "consultation_joined",
        "consultation_id": "C1006",
        "description": "Patient joined consultation C1006.",
        "timestamp": datetime(2026, 8, 31, 10, 0, 0),
    },
]


async def seed():
    """Seed all demo data into MongoDB using upsert for idempotency."""
    settings = get_settings()
    db = get_database(settings)

    collections_data = [
        ("users", USERS),
        ("doctors", DOCTORS),
        ("consultations", CONSULTATIONS),
        ("payments", PAYMENTS),
        ("user_activity", ACTIVITIES),
    ]

    print("=" * 60)
    print("  Seeding Demo Data into MongoDB")
    print(f"  Database: {settings.MONGODB_DATABASE}")
    print("=" * 60)

    for collection_name, records in collections_data:
        collection = db[collection_name]
        upserted = 0
        for record in records:
            result = await collection.replace_one(
                {"_id": record["_id"]}, record, upsert=True
            )
            if result.upserted_id or result.modified_count > 0:
                upserted += 1

        count = await collection.count_documents({})
        print(f"  [OK] {collection_name:25s} -> {upserted:3d} upserted, {count:3d} total")

    # Create indexes for faster queries
    await db["consultations"].create_index("patient_id")
    await db["payments"].create_index("consultation_id")
    await db["payments"].create_index("patient_id")
    await db["user_activity"].create_index([("user_id", 1), ("timestamp", -1)])
    await db["support_conversations"].create_index("user_id")
    await db["support_messages"].create_index("conversation_id")
    await db["support_tickets"].create_index("idempotency_key", unique=True, sparse=True)
    await db["support_tickets"].create_index("user_id")

    print("\n  [OK] Indexes created")
    print("=" * 60)
    print("  Seeding complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
