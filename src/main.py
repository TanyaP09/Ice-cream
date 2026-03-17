# Import os for environment variables
import os
# Import date for date parsing and validation
from datetime import date

# FastAPI core classes
from fastapi import FastAPI, Depends, HTTPException, Header
# Pydantic for request/response models
from pydantic import BaseModel, EmailStr

# Psycopg for Postgres connections
import psycopg
# Load .env if present
from dotenv import load_dotenv

# Password hashing
from passlib.context import CryptContext
# JWT encode/decode
from jose import jwt, JWTError


# Load env variables from .env file if it exists
load_dotenv()

# Read DB settings from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
# DB port as int
DB_PORT = int(os.getenv("DB_PORT", "5432"))
# DB name
DB_NAME = os.getenv("DB_NAME", "icecream")
# DB user
DB_USER = os.getenv("DB_USER", "icecream_user")
# DB password
DB_PASSWORD = os.getenv("DB_PASSWORD", "icecream_password")

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
# Algorithm for JWT tokens
JWT_ALG = "HS256"

# Create password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize FastAPI app
app = FastAPI(title="Ice Cream Nutrition Tracker API")


# Helper to get a DB connection per request
def get_conn():
    # Connect to Postgres using env settings
    return psycopg.connect(
        # Hostname of DB
        host=DB_HOST,
        # Port of DB
        port=DB_PORT,
        # Database name
        dbname=DB_NAME,
        # Username
        user=DB_USER,
        # Password
        password=DB_PASSWORD,
    )


# Helper: verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Compare raw password with stored hash
    return pwd_context.verify(plain_password, hashed_password)


# Helper: hash password
def hash_password(password: str) -> str:
    # Produce secure bcrypt hash
    return pwd_context.hash(password)


# Helper: create JWT token
def create_token(user_id: int) -> str:
    # Encode user id into JWT token
    return jwt.encode({"userId": user_id}, JWT_SECRET, algorithm=JWT_ALG)


# Dependency: extract userId from Authorization header
def get_current_user_id(authorization: str = Header(default="")) -> int:
    # Expect header: "Bearer <token>"
    parts = authorization.split(" ")
    # Validate header format
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=401, detail="Missing access token")

    # Token is the second part
    token = parts[1]
    try:
        # Decode and verify token signature
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        # Token invalid or expired
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Extract userId from payload
    user_id = payload.get("userId")
    if not user_id:
        # Missing userId is also invalid
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Return user id as int
    return int(user_id)


# Request models
class RegisterRequest(BaseModel):
    # User full name
    name: str
    # Email for login
    email: EmailStr
    # Raw password (will be hashed)
    password: str
    # Optional weight (kg)
    weight: float | None = None
    # Optional height (cm)
    height: float | None = None
    # Optional age
    age: int | None = None
    # Optional sex
    sex: str | None = None
    # Optional region
    region: str | None = None


class LoginRequest(BaseModel):
    # Email for login
    email: EmailStr
    # Password for login
    password: str


class IceCreamCreate(BaseModel):
    # Ice cream name
    name: str
    # Calories per 100g
    calories: float
    # Carbs per 100g
    carbohydrates: float
    # Proteins per 100g
    proteins: float
    # Fats per 100g
    fats: float
    # Sugar per 100g
    sugar: float
    # Risk level (rysk)
    rysk: int


class EntryCreate(BaseModel):
    # Selected ice cream id
    ice_cream_id: int
    # Date of eating
    eaten_date: date
    # Amount in grams
    amount_grams: float


@app.get("/health")
def health():
    # Simple health check
    return {"ok": True}


@app.post("/auth/register")
def register(payload: RegisterRequest):
    # Hash the password for storage
    password_hash = hash_password(payload.password)

    # Open DB connection
    with get_conn() as conn:
        # Create cursor for SQL commands
        with conn.cursor() as cur:
            try:
                # Insert new user
                cur.execute(
                    """
                    INSERT INTO users
                        (name, email, password_hash, weight_kg, height_cm, age, sex, region)
                    VALUES
                        (%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id, name, email, weight_kg, height_cm, age, sex, region
                    """,
                    (
                        # Name value
                        payload.name,
                        # Email value
                        payload.email,
                        # Hashed password value
                        password_hash,
                        # Weight value
                        payload.weight,
                        # Height value
                        payload.height,
                        # Age value
                        payload.age,
                        # Sex value
                        payload.sex,
                        # Region value
                        payload.region,
                    ),
                )
                # Read inserted row
                row = cur.fetchone()
                # Commit transaction
                conn.commit()
                # Return created user without password
                return {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "weight_kg": row[3],
                    "height_cm": row[4],
                    "age": row[5],
                    "sex": row[6],
                    "region": row[7],
                }
            except psycopg.errors.UniqueViolation:
                # Email already exists
                raise HTTPException(status_code=409, detail="Email already exists")


@app.post("/auth/login")
def login(payload: LoginRequest):
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Find user by email
            cur.execute(
                "SELECT id, password_hash FROM users WHERE email = %s",
                (payload.email,),
            )
            # Fetch one row
            row = cur.fetchone()
            if not row:
                # No such email
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Extract fields
            user_id, password_hash = row
            # Compare password and hash
            if not verify_password(payload.password, password_hash):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Create JWT token
            token = create_token(user_id)
            # Return token
            return {"token": token}


@app.get("/users/me")
def me(user_id: int = Depends(get_current_user_id)):
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Load profile by user id
            cur.execute(
                """
                SELECT id, name, email, weight_kg, height_cm, age, sex, region
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            # Read row
            row = cur.fetchone()
            if not row:
                # User not found
                raise HTTPException(status_code=404, detail="User not found")

            # Return profile data
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "weight_kg": row[3],
                "height_cm": row[4],
                "age": row[5],
                "sex": row[6],
                "region": row[7],
            }


@app.post("/ice-creams")
def add_ice_cream(
    payload: IceCreamCreate, user_id: int = Depends(get_current_user_id)
):
    # user_id is only to protect the route, not used inside
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            try:
                # Insert ice cream
                cur.execute(
                    """
                    INSERT INTO ice_creams
                        (name, calories, carbohydrates, proteins, fats, sugar, rysk)
                    VALUES
                        (%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id, name, calories, carbohydrates, proteins, fats, sugar, rysk
                    """,
                    (
                        # Name
                        payload.name,
                        # Calories per 100g
                        payload.calories,
                        # Carbs per 100g
                        payload.carbohydrates,
                        # Proteins per 100g
                        payload.proteins,
                        # Fats per 100g
                        payload.fats,
                        # Sugar per 100g
                        payload.sugar,
                        # Risk level
                        payload.rysk,
                    ),
                )
                # Read created row
                row = cur.fetchone()
                # Commit transaction
                conn.commit()
                # Return ice cream
                return {
                    "id": row[0],
                    "name": row[1],
                    "calories": row[2],
                    "carbohydrates": row[3],
                    "proteins": row[4],
                    "fats": row[5],
                    "sugar": row[6],
                    "rysk": row[7],
                }
            except psycopg.errors.UniqueViolation:
                # Duplicate name
                raise HTTPException(status_code=409, detail="Ice cream exists")


@app.get("/ice-creams")
def list_ice_creams():
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Select all ice creams
            cur.execute(
                "SELECT id, name, calories, carbohydrates, proteins, fats, sugar, rysk FROM ice_creams ORDER BY id"
            )
            # Fetch all rows
            rows = cur.fetchall()
            # Convert rows to list of dicts
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "calories": r[2],
                    "carbohydrates": r[3],
                    "proteins": r[4],
                    "fats": r[5],
                    "sugar": r[6],
                    "rysk": r[7],
                }
                for r in rows
            ]


@app.put("/ice-creams/{ice_id}")
def update_ice_cream(
    ice_id: int, payload: IceCreamCreate, user_id: int = Depends(get_current_user_id)
):
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Update ice cream by id
            cur.execute(
                """
                UPDATE ice_creams
                SET name = %s,
                    calories = %s,
                    carbohydrates = %s,
                    proteins = %s,
                    fats = %s,
                    sugar = %s,
                    rysk = %s
                WHERE id = %s
                RETURNING id, name, calories, carbohydrates, proteins, fats, sugar, rysk
                """,
                (
                    payload.name,
                    payload.calories,
                    payload.carbohydrates,
                    payload.proteins,
                    payload.fats,
                    payload.sugar,
                    payload.rysk,
                    ice_id,
                ),
            )
            # Read updated row
            row = cur.fetchone()
            if not row:
                # No such ice cream
                raise HTTPException(status_code=404, detail="Ice cream not found")
            # Commit transaction
            conn.commit()
            # Return updated record
            return {
                "id": row[0],
                "name": row[1],
                "calories": row[2],
                "carbohydrates": row[3],
                "proteins": row[4],
                "fats": row[5],
                "sugar": row[6],
                "rysk": row[7],
            }


@app.delete("/ice-creams/{ice_id}")
def delete_ice_cream(ice_id: int, user_id: int = Depends(get_current_user_id)):
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Delete and return id
            cur.execute(
                "DELETE FROM ice_creams WHERE id = %s RETURNING id",
                (ice_id,),
            )
            # Read deleted row
            row = cur.fetchone()
            if not row:
                # Not found
                raise HTTPException(status_code=404, detail="Ice cream not found")
            # Commit transaction
            conn.commit()
            # Return deletion status
            return {"deleted": True}


@app.post("/entries")
def add_entry(payload: EntryCreate, user_id: int = Depends(get_current_user_id)):
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Insert entry for user
            cur.execute(
                """
                INSERT INTO user_ice_creams
                    (user_id, ice_cream_id, eaten_date, amount_grams)
                VALUES
                    (%s,%s,%s,%s)
                RETURNING id, user_id, ice_cream_id, eaten_date, amount_grams
                """,
                (
                    user_id,
                    payload.ice_cream_id,
                    payload.eaten_date,
                    payload.amount_grams,
                ),
            )
            # Read created row
            row = cur.fetchone()
            # Commit transaction
            conn.commit()
            # Return entry
            return {
                "id": row[0],
                "user_id": row[1],
                "ice_cream_id": row[2],
                "eaten_date": row[3],
                "amount_grams": row[4],
            }


@app.get("/entries")
def list_entries(user_id: int = Depends(get_current_user_id)):
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Select entries and compute nutrition
            cur.execute(
                """
                SELECT
                    uic.id,
                    uic.eaten_date,
                    uic.amount_grams,
                    ic.name,
                    (ic.calories * uic.amount_grams / 100) AS calories,
                    (ic.carbohydrates * uic.amount_grams / 100) AS carbohydrates,
                    (ic.proteins * uic.amount_grams / 100) AS proteins,
                    (ic.fats * uic.amount_grams / 100) AS fats,
                    (ic.sugar * uic.amount_grams / 100) AS sugar,
                    ic.rysk
                FROM user_ice_creams uic
                JOIN ice_creams ic ON ic.id = uic.ice_cream_id
                WHERE uic.user_id = %s
                ORDER BY uic.eaten_date DESC, uic.id DESC
                """,
                (user_id,),
            )
            # Fetch all rows
            rows = cur.fetchall()
            # Map rows to dicts
            return [
                {
                    "id": r[0],
                    "eaten_date": r[1],
                    "amount_grams": r[2],
                    "ice_cream_name": r[3],
                    "calories": r[4],
                    "carbohydrates": r[5],
                    "proteins": r[6],
                    "fats": r[7],
                    "sugar": r[8],
                    "rysk": r[9],
                }
                for r in rows
            ]


@app.put("/entries/{entry_id}")
def update_entry(
    entry_id: int, payload: EntryCreate, user_id: int = Depends(get_current_user_id)
):
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Update entry only for current user
            cur.execute(
                """
                UPDATE user_ice_creams
                SET ice_cream_id = %s,
                    eaten_date = %s,
                    amount_grams = %s
                WHERE id = %s AND user_id = %s
                RETURNING id, user_id, ice_cream_id, eaten_date, amount_grams
                """,
                (
                    payload.ice_cream_id,
                    payload.eaten_date,
                    payload.amount_grams,
                    entry_id,
                    user_id,
                ),
            )
            # Read updated row
            row = cur.fetchone()
            if not row:
                # Not found
                raise HTTPException(status_code=404, detail="Entry not found")
            # Commit transaction
            conn.commit()
            # Return updated entry
            return {
                "id": row[0],
                "user_id": row[1],
                "ice_cream_id": row[2],
                "eaten_date": row[3],
                "amount_grams": row[4],
            }


@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, user_id: int = Depends(get_current_user_id)):
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Delete entry by id for current user
            cur.execute(
                "DELETE FROM user_ice_creams WHERE id = %s AND user_id = %s RETURNING id",
                (entry_id, user_id),
            )
            # Read deleted row
            row = cur.fetchone()
            if not row:
                # Not found
                raise HTTPException(status_code=404, detail="Entry not found")
            # Commit transaction
            conn.commit()
            # Return deletion status
            return {"deleted": True}


@app.get("/entries/summary")
def summary(date: date, user_id: int = Depends(get_current_user_id)):
    # Open DB connection
    with get_conn() as conn:
        # Create cursor
        with conn.cursor() as cur:
            # Sum nutrition for the given date
            cur.execute(
                """
                SELECT
                    SUM(ic.calories * uic.amount_grams / 100) AS calories,
                    SUM(ic.carbohydrates * uic.amount_grams / 100) AS carbohydrates,
                    SUM(ic.proteins * uic.amount_grams / 100) AS proteins,
                    SUM(ic.fats * uic.amount_grams / 100) AS fats,
                    SUM(ic.sugar * uic.amount_grams / 100) AS sugar
                FROM user_ice_creams uic
                JOIN ice_creams ic ON ic.id = uic.ice_cream_id
                WHERE uic.user_id = %s AND uic.eaten_date = %s
                """,
                (user_id, date),
            )
            # Read summary row
            row = cur.fetchone()
            # Return totals
            return {
                "date": str(date),
                "calories": row[0],
                "carbohydrates": row[1],
                "proteins": row[2],
                "fats": row[3],
                "sugar": row[4],
            }
