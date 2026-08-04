import sqlite3


DATABASE = "video_inspector.db"





# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn






# =====================================================
# INITIALIZE DATABASE
# =====================================================

def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()


    try:


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

                report_data TEXT,

                public_token TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            )
            """
        )



        # ---------------------------------
        # Migration support
        # ---------------------------------

        cursor.execute(
            "PRAGMA table_info(scan_history)"
        )


        columns = [

            row["name"]

            for row in cursor.fetchall()

        ]



        if "public_token" not in columns:


            cursor.execute(
                """
                ALTER TABLE scan_history
                ADD COLUMN public_token TEXT
                """
            )



        # Index for public sharing

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_public_token

            ON scan_history(public_token)

            """
        )



        conn.commit()


        print(
            "Database initialized successfully"
        )


    except Exception as e:


        conn.rollback()

        print(
            "DATABASE INIT ERROR:",
            e
        )


        raise e


    finally:


        conn.close()








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


    conn = get_connection()

    cursor = conn.cursor()



    try:


        cursor.execute(

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

            (?, ?, ?, ?, ?, ?, ?)

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



        scan_id = cursor.lastrowid



        print(
            "Scan saved ID:",
            scan_id
        )


        return scan_id



    except Exception as e:


        conn.rollback()


        print(
            "SAVE ERROR:",
            e
        )


        raise e



    finally:


        conn.close()








# =====================================================
# GET USER HISTORY
# =====================================================

def get_scan_history(user_email):


    conn = get_connection()

    cursor = conn.cursor()



    cursor.execute(

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

    )



    scans = cursor.fetchall()


    conn.close()



    return scans







# =====================================================
# GET PRIVATE REPORT
# =====================================================

def get_report_by_id(

        scan_id,

        user_email

):


    conn = get_connection()

    cursor = conn.cursor()



    cursor.execute(

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

    )



    report = cursor.fetchone()



    conn.close()



    return report








# =====================================================
# GET PUBLIC REPORT
# =====================================================

def get_public_report(token):


    conn = get_connection()

    cursor = conn.cursor()



    cursor.execute(

        """
        SELECT *

        FROM scan_history


        WHERE public_token = ?

        """,

        (

            token,

        )

    )



    report = cursor.fetchone()



    conn.close()



    return report








# =====================================================
# DASHBOARD STATISTICS
# =====================================================

def get_dashboard_stats(user_email):


    conn = get_connection()

    cursor = conn.cursor()



    # Total scans

    cursor.execute(

        """
        SELECT COUNT(*)

        FROM scan_history


        WHERE user_email = ?

        """,

        (
            user_email,
        )

    )


    total_scans = cursor.fetchone()[0]





    # Average SEO

    cursor.execute(

        """
        SELECT seo_score

        FROM scan_history


        WHERE user_email = ?

        """,

        (
            user_email,
        )

    )


    rows = cursor.fetchall()



    seo_values=[]



    for row in rows:


        try:


            value = str(
                row["seo_score"]
            )


            value=value.replace(
                "/100",
                ""
            )


            value=value.split("/")[0]


            seo_values.append(
                int(value)
            )


        except:


            continue





    avg_seo = (

        round(
            sum(seo_values)
            /
            len(seo_values)
        )

        if seo_values

        else 0

    )








    # Copyright risk count

    cursor.execute(

        """
        SELECT COUNT(*)

        FROM scan_history


        WHERE user_email = ?


        AND

        (

            copyright_score LIKE '%High%'

            OR copyright_score LIKE '%Moderate%'

            OR copyright_score LIKE '%Medium%'

        )

        """,

        (
            user_email,
        )

    )


    risk_count = cursor.fetchone()[0]







    # Latest scan

    cursor.execute(

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

    )


    latest = cursor.fetchone()



    conn.close()





    return {


        "total_scans":

            total_scans,


        "avg_seo":

            avg_seo,


        "risk_count":

            risk_count,


        "latest_scan":

            latest["created_at"]

            if latest

            else "No scans"

    }