import sqlite3

from contextlib import closing


DATABASE = "video_inspector.db"


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    conn.execute(
        "PRAGMA journal_mode = WAL"
    )

    return conn


# =====================================================
# DATABASE INITIALIZATION
# =====================================================

def initialize_database():

    with closing(
        get_connection()
    ) as conn:

        try:

            cursor = conn.cursor()

            # ---------------------------------
            # Scan history table
            # ---------------------------------

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_history
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_email TEXT NOT NULL,

                    filename TEXT NOT NULL,

                    copyright_score TEXT,

                    seo_score TEXT,

                    content_id TEXT,

                    report_data TEXT NOT NULL,

                    public_token TEXT,

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # ---------------------------------
            # Existing database migration
            # ---------------------------------

            cursor.execute(
                "PRAGMA table_info(scan_history)"
            )

            history_columns = {

                row["name"]

                for row in cursor.fetchall()

            }

            if "public_token" not in history_columns:

                cursor.execute(
                    """
                    ALTER TABLE scan_history
                    ADD COLUMN public_token TEXT
                    """
                )

            # ---------------------------------
            # Users and scan credits
            # ---------------------------------

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    email TEXT NOT NULL
                        UNIQUE COLLATE NOCASE,

                    free_scan_used INTEGER
                        NOT NULL
                        DEFAULT 0
                        CHECK (
                            free_scan_used IN (0, 1)
                        ),

                    scan_credits INTEGER
                        NOT NULL
                        DEFAULT 0
                        CHECK (
                            scan_credits >= 0
                        ),

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # ---------------------------------
            # Razorpay payment records
            # ---------------------------------

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS payments
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_email TEXT NOT NULL,

                    razorpay_order_id TEXT
                        NOT NULL
                        UNIQUE,

                    razorpay_payment_id TEXT
                        UNIQUE,

                    amount_paise INTEGER
                        NOT NULL,

                    credits INTEGER
                        NOT NULL
                        DEFAULT 1,

                    status TEXT
                        NOT NULL
                        DEFAULT 'created',

                    created_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,

                    paid_at TIMESTAMP,

                    FOREIGN KEY (
                        user_email
                    )
                    REFERENCES users(email)
                )
                """
            )

            # ---------------------------------
            # Indexes
            # ---------------------------------

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_public_token

                ON scan_history(public_token)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_scan_user

                ON scan_history(
                    user_email,
                    id DESC
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_payment_user

                ON payments(
                    user_email,
                    id DESC
                )
                """
            )

            conn.commit()

            print(
                "Database initialized successfully"
            )

        except Exception:

            conn.rollback()

            raise


# =====================================================
# CREATE USER
# =====================================================

def create_user_if_not_exists(email):

    if not email:

        raise ValueError(
            "Email is required"
        )

    normalized_email = (
        email
        .strip()
        .lower()
    )

    with closing(
        get_connection()
    ) as conn:

        conn.execute(
            """
            INSERT INTO users
            (
                email
            )

            VALUES
            (
                ?
            )

            ON CONFLICT(email)
            DO NOTHING
            """,
            (
                normalized_email,
            )
        )

        conn.commit()


# =====================================================
# GET USER
# =====================================================

def get_user(email):

    create_user_if_not_exists(
        email
    )

    normalized_email = (
        email
        .strip()
        .lower()
    )

    with closing(
        get_connection()
    ) as conn:

        return conn.execute(
            """
            SELECT

                id,

                email,

                free_scan_used,

                scan_credits,

                created_at,

                updated_at

            FROM users

            WHERE email = ?
            COLLATE NOCASE
            """,
            (
                normalized_email,
            )
        ).fetchone()


# =====================================================
# GET USER ACCESS STATUS
# =====================================================

def get_user_access_status(email):

    user = get_user(
        email
    )

    free_available = (
        user["free_scan_used"] == 0
    )

    credits = int(
        user["scan_credits"] or 0
    )

    return {

        "email":
            user["email"],

        "free_scan_used":
            bool(
                user["free_scan_used"]
            ),

        "free_scan_available":
            free_available,

        "scan_credits":
            credits,

        "can_scan":
            free_available
            or credits > 0

    }


# =====================================================
# RESERVE SCAN ACCESS
# =====================================================

def reserve_scan_entitlement(email):

    """
    Reserve one scan before analysis starts.

    Returns:
        "free"
        "credit"
        None

    If the scan fails, call
    restore_scan_entitlement().
    """

    normalized_email = (
        email
        .strip()
        .lower()
    )

    create_user_if_not_exists(
        normalized_email
    )

    with closing(
        get_connection()
    ) as conn:

        try:

            conn.execute(
                "BEGIN IMMEDIATE"
            )

            user = conn.execute(
                """
                SELECT

                    free_scan_used,

                    scan_credits

                FROM users

                WHERE email = ?
                COLLATE NOCASE
                """,
                (
                    normalized_email,
                )
            ).fetchone()

            # ---------------------------------
            # Use lifetime free scan first
            # ---------------------------------

            if user["free_scan_used"] == 0:

                conn.execute(
                    """
                    UPDATE users

                    SET
                        free_scan_used = 1,

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE email = ?
                    COLLATE NOCASE
                    """,
                    (
                        normalized_email,
                    )
                )

                conn.commit()

                return "free"

            # ---------------------------------
            # Use paid scan credit
            # ---------------------------------

            if int(
                user["scan_credits"] or 0
            ) > 0:

                cursor = conn.execute(
                    """
                    UPDATE users

                    SET
                        scan_credits =
                            scan_credits - 1,

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE email = ?
                    COLLATE NOCASE

                    AND scan_credits > 0
                    """,
                    (
                        normalized_email,
                    )
                )

                if cursor.rowcount == 1:

                    conn.commit()

                    return "credit"

            conn.rollback()

            return None

        except Exception:

            conn.rollback()

            raise


# =====================================================
# RESTORE FAILED SCAN ACCESS
# =====================================================

def restore_scan_entitlement(
        email,
        entitlement_type
):

    if entitlement_type not in {
        "free",
        "credit"
    }:

        return

    normalized_email = (
        email
        .strip()
        .lower()
    )

    with closing(
        get_connection()
    ) as conn:

        if entitlement_type == "free":

            conn.execute(
                """
                UPDATE users

                SET
                    free_scan_used = 0,

                    updated_at =
                        CURRENT_TIMESTAMP

                WHERE email = ?
                COLLATE NOCASE
                """,
                (
                    normalized_email,
                )
            )

        else:

            conn.execute(
                """
                UPDATE users

                SET
                    scan_credits =
                        scan_credits + 1,

                    updated_at =
                        CURRENT_TIMESTAMP

                WHERE email = ?
                COLLATE NOCASE
                """,
                (
                    normalized_email,
                )
            )

        conn.commit()


# =====================================================
# ADD SCAN CREDITS
# =====================================================

def add_credits(
        email,
        credits
):

    credits = int(
        credits
    )

    if credits <= 0:

        raise ValueError(
            "Credits must be greater than zero"
        )

    normalized_email = (
        email
        .strip()
        .lower()
    )

    create_user_if_not_exists(
        normalized_email
    )

    with closing(
        get_connection()
    ) as conn:

        conn.execute(
            """
            UPDATE users

            SET
                scan_credits =
                    scan_credits + ?,

                updated_at =
                    CURRENT_TIMESTAMP

            WHERE email = ?
            COLLATE NOCASE
            """,
            (
                credits,
                normalized_email
            )
        )

        conn.commit()


# =====================================================
# CREATE PAYMENT RECORD
# =====================================================

def create_payment_record(
        user_email,
        order_id,
        amount_paise,
        credits=1
):

    create_user_if_not_exists(
        user_email
    )

    normalized_email = (
        user_email
        .strip()
        .lower()
    )

    with closing(
        get_connection()
    ) as conn:

        conn.execute(
            """
            INSERT INTO payments
            (
                user_email,

                razorpay_order_id,

                amount_paise,

                credits,

                status
            )

            VALUES
            (
                ?, ?, ?, ?, 'created'
            )
            """,
            (
                normalized_email,

                order_id,

                int(
                    amount_paise
                ),

                int(
                    credits
                )
            )
        )

        conn.commit()


# =====================================================
# GET PAYMENT BY ORDER ID
# =====================================================

def get_payment_by_order(order_id):

    with closing(
        get_connection()
    ) as conn:

        return conn.execute(
            """
            SELECT *

            FROM payments

            WHERE razorpay_order_id = ?
            """,
            (
                order_id,
            )
        ).fetchone()


# =====================================================
# VERIFY PAYMENT AND ADD CREDIT
# =====================================================

def complete_payment_and_add_credits(
        order_id,
        payment_id,
        user_email
):

    """
    Mark a payment as paid and add credits
    exactly once.

    Returns:
        True  -> credit added now
        False -> already processed earlier
    """

    normalized_email = (
        user_email
        .strip()
        .lower()
    )

    with closing(
        get_connection()
    ) as conn:

        try:

            conn.execute(
                "BEGIN IMMEDIATE"
            )

            payment = conn.execute(
                """
                SELECT *

                FROM payments

                WHERE razorpay_order_id = ?

                AND user_email = ?
                COLLATE NOCASE
                """,
                (
                    order_id,
                    normalized_email
                )
            ).fetchone()

            if not payment:

                raise ValueError(
                    "Payment order not found"
                )

            # Prevent duplicate credits
            if payment["status"] == "paid":

                conn.commit()

                return False

            conn.execute(
                """
                UPDATE payments

                SET
                    razorpay_payment_id = ?,

                    status = 'paid',

                    paid_at =
                        CURRENT_TIMESTAMP

                WHERE razorpay_order_id = ?
                """,
                (
                    payment_id,
                    order_id
                )
            )

            conn.execute(
                """
                UPDATE users

                SET
                    scan_credits =
                        scan_credits + ?,

                    updated_at =
                        CURRENT_TIMESTAMP

                WHERE email = ?
                COLLATE NOCASE
                """,
                (
                    int(
                        payment["credits"]
                    ),

                    normalized_email
                )
            )

            conn.commit()

            return True

        except Exception:

            conn.rollback()

            raise


# =====================================================
# SAVE SCAN HISTORY
# =====================================================

def save_scan_history(
        user_email,
        filename,
        copyright_score,
        seo_score,
        content_id,
        report_data,
        public_token=None
):

    with closing(
        get_connection()
    ) as conn:

        cursor = conn.execute(
            """
            INSERT INTO scan_history
            (
                user_email,

                filename,

                copyright_score,

                seo_score,

                content_id,

                report_data,

                public_token
            )

            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                user_email,

                filename,

                copyright_score,

                seo_score,

                content_id,

                report_data,

                public_token
            )
        )

        conn.commit()

        return cursor.lastrowid


# =====================================================
# GET SCAN HISTORY
# =====================================================

def get_scan_history(user_email):

    with closing(
        get_connection()
    ) as conn:

        return conn.execute(
            """
            SELECT

                id,

                filename,

                copyright_score,

                seo_score,

                content_id,

                created_at

            FROM scan_history

            WHERE user_email = ?

            ORDER BY id DESC
            """,
            (
                user_email,
            )
        ).fetchall()


# =====================================================
# GET PRIVATE REPORT
# =====================================================

def get_report_by_id(
        scan_id,
        user_email
):

    with closing(
        get_connection()
    ) as conn:

        return conn.execute(
            """
            SELECT *

            FROM scan_history

            WHERE id = ?

            AND user_email = ?
            """,
            (
                scan_id,
                user_email
            )
        ).fetchone()


# =====================================================
# GET PUBLIC REPORT
# =====================================================

def get_public_report(token):

    with closing(
        get_connection()
    ) as conn:

        return conn.execute(
            """
            SELECT *

            FROM scan_history

            WHERE public_token = ?
            """,
            (
                token,
            )
        ).fetchone()


# =====================================================
# DASHBOARD STATISTICS
# =====================================================

def get_dashboard_stats(user_email):

    with closing(
        get_connection()
    ) as conn:

        # ---------------------------------
        # Total scans
        # ---------------------------------

        total_scans = conn.execute(
            """
            SELECT COUNT(*)

            FROM scan_history

            WHERE user_email = ?
            """,
            (
                user_email,
            )
        ).fetchone()[0]

        # ---------------------------------
        # Average SEO score
        # ---------------------------------

        rows = conn.execute(
            """
            SELECT seo_score

            FROM scan_history

            WHERE user_email = ?
            """,
            (
                user_email,
            )
        ).fetchall()

        seo_values = []

        for row in rows:

            try:

                value = str(
                    row["seo_score"]
                )

                value = value.replace(
                    "/100",
                    ""
                )

                value = value.split(
                    "/"
                )[0]

                seo_values.append(
                    int(
                        float(
                            value
                        )
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                continue

        avg_seo = (

            round(
                sum(
                    seo_values
                )
                /
                len(
                    seo_values
                )
            )

            if seo_values

            else 0

        )

        # ---------------------------------
        # Copyright alerts
        # ---------------------------------

        risk_count = conn.execute(
            """
            SELECT COUNT(*)

            FROM scan_history

            WHERE user_email = ?

            AND
            (
                copyright_score
                    LIKE '%High%'

                OR copyright_score
                    LIKE '%Moderate%'

                OR copyright_score
                    LIKE '%Medium%'
            )
            """,
            (
                user_email,
            )
        ).fetchone()[0]

        # ---------------------------------
        # Latest scan
        # ---------------------------------

        latest = conn.execute(
            """
            SELECT created_at

            FROM scan_history

            WHERE user_email = ?

            ORDER BY id DESC

            LIMIT 1
            """,
            (
                user_email,
            )
        ).fetchone()

        return {

            "total_scans":
                total_scans,

            "avg_seo":
                avg_seo,

            "risk_count":
                risk_count,

            "latest_scan":
                (
                    latest["created_at"]
                    if latest
                    else "No scans"
                )

        }