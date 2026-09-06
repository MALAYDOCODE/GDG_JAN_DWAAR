import os
import sqlite3
import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from google import genai
from geopy.geocoders import Nominatim


load_dotenv()


app = Flask(__name__)


CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*"
        }
    }
)


app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY",
    "jandwaar-hackathon-secret-key"
)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


jwt = JWTManager(app)


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


DATABASE = os.path.join(
    BASE_DIR,
    "jandwaar.db"
)


UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


client = None


if GEMINI_API_KEY:
    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

    except Exception as error:
        print(
            "Gemini initialization error:",
            error
        )

        client = None


geolocator = Nominatim(
    user_agent="jandwaar"
)


def get_db():

    db = sqlite3.connect(
        DATABASE
    )

    db.row_factory = sqlite3.Row

    return db


def create_database():

    db = get_db()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            original_text TEXT NOT NULL,
            english_text TEXT,
            language TEXT,
            category TEXT,
            department TEXT,
            location TEXT,
            status TEXT DEFAULT 'Submitted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
        """
    )

    count = db.execute(
        "SELECT COUNT(*) AS count FROM faqs"
    ).fetchone()["count"]

    if count == 0:

        faqs = [
            (
                "How can I register a complaint?",
                "Login to your account and submit your complaint using text or voice."
            ),
            (
                "How can I check my complaint status?",
                "Login and enter your complaint ID in the complaint status section."
            ),
            (
                "Can I submit a complaint in Hindi?",
                "Yes. Hindi complaints can be translated into English."
            ),
            (
                "Can I submit a complaint using voice?",
                "Yes. You can record your complaint and convert it into text."
            ),
            (
                "Will I receive a complaint ID?",
                "Yes. Every registered complaint receives a unique complaint ID."
            )
        ]

        db.executemany(
            """
            INSERT INTO faqs
            (question, answer)
            VALUES (?, ?)
            """,
            faqs
        )

    db.commit()

    db.close()


def get_location_name(
    latitude,
    longitude
):

    try:

        result = geolocator.reverse(
            f"{latitude}, {longitude}",
            language="en",
            zoom=18,
            addressdetails=True,
            timeout=10
        )

        if not result:
            return "Location not found"

        address = result.raw.get(
            "address",
            {}
        )

        locality = (
            address.get("suburb")
            or address.get("neighbourhood")
            or address.get("quarter")
            or address.get("city_district")
            or address.get("town")
            or address.get("village")
        )

        city = (
            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or address.get("village")
        )

        state = address.get(
            "state"
        )

        country = address.get(
            "country"
        )

        parts = []

        if locality:
            parts.append(
                locality
            )

        if city and city != locality:
            parts.append(
                city
            )

        if state:
            parts.append(
                state
            )

        if country:
            parts.append(
                country
            )

        if parts:
            return ", ".join(parts)

        return result.address

    except Exception as error:

        print(
            "Location error:",
            error
        )

        return "Location not found"


def translate_to_english(text):

    if not client:
        return text

    try:

        prompt = f"""
Translate this citizen complaint into clear English.

If it is already English, return it unchanged.

Do not add explanations.
Do not summarize.
Do not change the meaning.

Complaint:

{text}
"""

        result = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if result.text:
            return result.text.strip()

    except Exception as error:

        print(
            "Translation error:",
            error
        )

    return text


def analyze_complaint(
    text,
    category,
    location
):

    result = {
        "english_text": text,
        "category": category or "Other",
        "severity": "Normal",
        "summary": text,
        "location": location or "Not provided"
    }

    if not client:
        return result

    try:

        prompt = f"""
You are an AI assistant for JanDwaar.

Analyze this citizen complaint.

Complaint:
{text}

Selected category:
{category}

Location:
{location}

Return exactly:

CATEGORY: <category>
SEVERITY: <Low/Medium/High/Critical>
SUMMARY: <one short sentence>

Do not add anything else.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        output = (
            response.text.strip()
            if response.text
            else ""
        )

        for line in output.splitlines():

            line = line.strip()

            if line.upper().startswith(
                "CATEGORY:"
            ):

                result["category"] = (
                    line.split(
                        ":",
                        1
                    )[1].strip()
                )

            elif line.upper().startswith(
                "SEVERITY:"
            ):

                result["severity"] = (
                    line.split(
                        ":",
                        1
                    )[1].strip()
                )

            elif line.upper().startswith(
                "SUMMARY:"
            ):

                result["summary"] = (
                    line.split(
                        ":",
                        1
                    )[1].strip()
                )

    except Exception as error:

        print(
            "Analysis error:",
            error
        )

    return result


create_database()


@app.route("/")
def home():

    return jsonify(
        {
            "name": "JanDwaar",
            "status": "Backend is working",
            "database": "Connected",
            "gemini": (
                "Configured"
                if client
                else "Not configured"
            )
        }
    )


@app.route(
    "/api/register",
    methods=["POST"]
)
def register():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify(
            {
                "success": False,
                "message": "Invalid request"
            }
        ), 400

    name = str(
        data.get(
            "name",
            ""
        )
    ).strip()

    email = str(
        data.get(
            "email",
            ""
        )
    ).strip().lower()

    phone = str(
        data.get(
            "phone",
            ""
        )
    ).strip()

    password = str(
        data.get(
            "password",
            ""
        )
    )

    if not name or not password:

        return jsonify(
            {
                "success": False,
                "message": "Name and password are required"
            }
        ), 400

    if len(password) < 6:

        return jsonify(
            {
                "success": False,
                "message": "Password must contain at least 6 characters"
            }
        ), 400

    user_id = (
        "JD-"
        + uuid.uuid4().hex[:8].upper()
    )

    password_hash = generate_password_hash(
        password
    )

    db = get_db()

    try:

        db.execute(
            """
            INSERT INTO users
            (
                user_id,
                name,
                email,
                phone,
                password
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                email if email else None,
                phone,
                password_hash
            )
        )

        db.commit()

    except sqlite3.IntegrityError:

        db.close()

        return jsonify(
            {
                "success": False,
                "message": "Email already registered"
            }
        ), 409

    db.close()

    return jsonify(
        {
            "success": True,
            "message": "Registration successful",
            "user_id": user_id
        }
    ), 201


@app.route(
    "/api/login",
    methods=["POST"]
)
def login():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify(
            {
                "success": False,
                "message": "Invalid request"
            }
        ), 400

    user_id = str(
        data.get(
            "user_id",
            ""
        )
    ).strip()

    password = str(
        data.get(
            "password",
            ""
        )
    )

    db = get_db()

    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    ).fetchone()

    db.close()

    if not user:

        return jsonify(
            {
                "success": False,
                "message": "Invalid user ID or password"
            }
        ), 401

    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify(
            {
                "success": False,
                "message": "Invalid user ID or password"
            }
        ), 401

    token = create_access_token(
        identity=user["user_id"]
    )

    return jsonify(
        {
            "success": True,
            "token": token,
            "user": {
                "user_id": user["user_id"],
                "name": user["name"]
            }
        }
    )


@app.route(
    "/api/profile",
    methods=["GET"]
)
@jwt_required()
def profile():

    user_id = get_jwt_identity()

    db = get_db()

    user = db.execute(
        """
        SELECT
            user_id,
            name,
            email,
            phone,
            created_at
        FROM users
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    ).fetchone()

    db.close()

    if not user:

        return jsonify(
            {
                "success": False,
                "message": "User not found"
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "user": dict(user)
        }
    )


@app.route(
    "/api/location",
    methods=["POST"]
)
def location():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify(
            {
                "success": False,
                "message": "Location data is missing"
            }
        ), 400

    latitude = data.get(
        "latitude"
    )

    longitude = data.get(
        "longitude"
    )

    try:

        latitude = float(
            latitude
        )

        longitude = float(
            longitude
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            {
                "success": False,
                "message": "Invalid coordinates"
            }
        ), 400

    if not -90 <= latitude <= 90:

        return jsonify(
            {
                "success": False,
                "message": "Invalid latitude"
            }
        ), 400

    if not -180 <= longitude <= 180:

        return jsonify(
            {
                "success": False,
                "message": "Invalid longitude"
            }
        ), 400

    location_name = get_location_name(
        latitude,
        longitude
    )

    return jsonify(
        {
            "success": True,
            "latitude": latitude,
            "longitude": longitude,
            "location": location_name
        }
    )


@app.route(
    "/api/analyse",
    methods=["POST"]
)
@jwt_required()
def analyse():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify(
            {
                "success": False,
                "message": "Invalid request"
            }
        ), 400

    complaint = str(
        data.get(
            "message",
            data.get(
                "complaint",
                ""
            )
        )
    ).strip()

    language = str(
        data.get(
            "language",
            ""
        )
    ).strip()

    category = str(
        data.get(
            "category",
            ""
        )
    ).strip()

    location_name = str(
        data.get(
            "location",
            ""
        )
    ).strip()

    if not complaint:

        return jsonify(
            {
                "success": False,
                "message": "Complaint cannot be empty"
            }
        ), 400

    english_text = translate_to_english(
        complaint
    )

    analysis = analyze_complaint(
        english_text,
        category,
        location_name
    )

    return jsonify(
        {
            "success": True,
            "original_text": complaint,
            "english_text": english_text,
            "language": language,
            "category": analysis["category"],
            "severity": analysis["severity"],
            "summary": analysis["summary"],
            "location": analysis["location"]
        }
    )


@app.route(
    "/api/complaints",
    methods=["POST"]
)
@jwt_required()
def create_complaint():

    user_id = get_jwt_identity()

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify(
            {
                "success": False,
                "message": "Invalid request"
            }
        ), 400

    complaint = str(
        data.get(
            "complaint",
            data.get(
                "message",
                ""
            )
        )
    ).strip()

    language = str(
        data.get(
            "language",
            ""
        )
    ).strip()

    category = str(
        data.get(
            "category",
            ""
        )
    ).strip()

    department = str(
        data.get(
            "department",
            ""
        )
    ).strip()

    location_name = str(
        data.get(
            "location",
            ""
        )
    ).strip()

    if not complaint:

        return jsonify(
            {
                "success": False,
                "message": "Complaint cannot be empty"
            }
        ), 400

    english_text = translate_to_english(
        complaint
    )

    analysis = analyze_complaint(
        english_text,
        category,
        location_name
    )

    final_category = (
        analysis["category"]
        or category
        or "Other"
    )

    complaint_id = (
        "CMP-"
        + uuid.uuid4().hex[:10].upper()
    )

    db = get_db()

    db.execute(
        """
        INSERT INTO complaints
        (
            complaint_id,
            user_id,
            original_text,
            english_text,
            language,
            category,
            department,
            location
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            complaint_id,
            user_id,
            complaint,
            english_text,
            language,
            final_category,
            department,
            location_name
        )
    )

    db.commit()

    db.close()

    return jsonify(
        {
            "success": True,
            "message": "Complaint registered successfully",
            "complaint_id": complaint_id,
            "original_text": complaint,
            "english_text": english_text,
            "language": language,
            "category": final_category,
            "department": department,
            "location": location_name,
            "severity": analysis["severity"],
            "summary": analysis["summary"],
            "status": "Submitted"
        }
    ), 201


@app.route(
    "/api/complaints",
    methods=["GET"]
)
@jwt_required()
def get_complaints():

    user_id = get_jwt_identity()

    db = get_db()

    complaints = db.execute(
        """
        SELECT
            complaint_id,
            original_text,
            english_text,
            language,
            category,
            department,
            location,
            status,
            created_at,
            updated_at
        FROM complaints
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (
            user_id,
        )
    ).fetchall()

    db.close()

    return jsonify(
        {
            "success": True,
            "complaints": [
                dict(item)
                for item in complaints
            ]
        }
    )


@app.route(
    "/api/complaints/<complaint_id>",
    methods=["GET"]
)
@jwt_required()
def get_complaint(
    complaint_id
):

    user_id = get_jwt_identity()

    db = get_db()

    complaint = db.execute(
        """
        SELECT
            complaint_id,
            original_text,
            english_text,
            language,
            category,
            department,
            location,
            status,
            created_at,
            updated_at
        FROM complaints
        WHERE complaint_id = ?
        AND user_id = ?
        """,
        (
            complaint_id,
            user_id
        )
    ).fetchone()

    db.close()

    if not complaint:

        return jsonify(
            {
                "success": False,
                "message": "Complaint not found"
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "complaint": dict(
                complaint
            )
        }
    )


@app.route(
    "/api/faqs",
    methods=["GET"]
)
def get_faqs():

    db = get_db()

    faqs = db.execute(
        """
        SELECT
            id,
            question,
            answer
        FROM faqs
        """
    ).fetchall()

    db.close()

    return jsonify(
        {
            "success": True,
            "faqs": [
                dict(item)
                for item in faqs
            ]
        }
    )


@app.route(
    "/api/query",
    methods=["POST"]
)
def general_query():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify(
            {
                "success": False,
                "message": "Invalid request"
            }
        ), 400

    question = str(
        data.get(
            "question",
            ""
        )
    ).strip()

    if not question:

        return jsonify(
            {
                "success": False,
                "message": "Question is required"
            }
        ), 400

    if not client:

        return jsonify(
            {
                "success": False,
                "message": "Gemini is not configured"
            }
        ), 500

    prompt = f"""
You are the JanDwaar citizen assistant.

Help citizens understand the JanDwaar portal.

You can answer questions about:

- complaint registration
- complaint tracking
- government grievance procedures
- using the JanDwaar website
- general public-service information

Keep answers short and easy to understand.

Do not claim to be an official government authority.

Do not invent complaint status.

Citizen question:

{question}
"""

    try:

        result = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return jsonify(
            {
                "success": True,
                "question": question,
                "answer": (
                    result.text.strip()
                    if result.text
                    else "I could not generate an answer."
                )
            }
        )

    except Exception as error:

        print(
            "Query error:",
            error
        )

        return jsonify(
            {
                "success": False,
                "message": "Unable to process question"
            }
        ), 500


@app.route(
    "/api/voice-complaint",
    methods=["POST"]
)
@jwt_required()
def voice_complaint():

    if not client:

        return jsonify(
            {
                "success": False,
                "message": "Gemini is not configured"
            }
        ), 500

    if "audio" not in request.files:

        return jsonify(
            {
                "success": False,
                "message": "Audio file is required"
            }
        ), 400

    audio = request.files["audio"]

    if not audio.filename:

        return jsonify(
            {
                "success": False,
                "message": "Audio file is empty"
            }
        ), 400

    filename = secure_filename(
        audio.filename
    )

    if not filename:
        filename = "complaint.webm"

    filename = (
        uuid.uuid4().hex
        + "_"
        + filename
    )

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    audio.save(
        filepath
    )

    try:

        uploaded_file = client.files.upload(
            file=filepath
        )

        transcription_result = (
            client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    uploaded_file,
                    """
Transcribe this citizen complaint exactly.

Identify the spoken language automatically.

Return only the spoken words as text.

Do not summarize.
Do not add explanations.
"""
                ]
            )
        )

        original_text = (
            transcription_result.text.strip()
            if transcription_result.text
            else ""
        )

        if not original_text:

            return jsonify(
                {
                    "success": False,
                    "message": "No speech could be detected"
                }
            ), 400

        english_text = translate_to_english(
            original_text
        )

        return jsonify(
            {
                "success": True,
                "transcription": original_text,
                "text": original_text,
                "english_text": english_text
            }
        )

    except Exception as error:

        print(
            "Voice processing error:",
            error
        )

        return jsonify(
            {
                "success": False,
                "message": "Unable to process audio"
            }
        ), 500

    finally:

        if os.path.exists(
            filepath
        ):

            os.remove(
                filepath
            )


@app.route(
    "/api/about",
    methods=["GET"]
)
def about():

    return jsonify(
        {
            "name": "JanDwaar",
            "description": "An AI-powered citizen grievance platform.",
            "features": [
                "Text complaint registration",
                "Voice complaint registration",
                "Hindi to English translation",
                "Complaint tracking",
                "General query assistant",
                "Location detection"
            ]
        }
    )


if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    print(
        "================================"
    )

    print(
        "JAN DWAAR BACKEND"
    )

    print(
        "================================"
    )

    print(
        "Database:",
        DATABASE
    )

    print(
        "Gemini:",
        "Configured"
        if client
        else "Not configured"
    )

    print(
        "Server starting on port:",
        port
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
