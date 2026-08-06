import hashlib
import hmac
import json
import os
import secrets

import razorpay

from authlib.integrations.flask_client import OAuth

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from config import Config

from database import (
    complete_payment_and_add_credits,
    create_payment_record,
    create_user_if_not_exists,
    get_dashboard_stats,
    get_payment_by_order,
    get_public_report,
    get_report_by_id,
    get_scan_history,
    get_user_access_status,
    initialize_database,
    reserve_scan_entitlement,
    restore_scan_entitlement,
    save_scan_history,
)

from report_generator import generate_pdf

from services.gemini_service import GeminiService
from services.upload_service import UploadService


# =====================================================
# FLASK APPLICATION
# =====================================================

app = Flask(__name__)

app.config.from_object(Config)

app.secret_key = Config.SECRET_KEY


# Local HTTP OAuth is allowed only during local development.
if os.getenv("RENDER") != "true":

    os.environ.setdefault(
        "AUTHLIB_INSECURE_TRANSPORT",
        "1"
    )


# =====================================================
# GOOGLE OAUTH
# =====================================================

oauth = OAuth(app)


google = oauth.register(

    name="google",

    client_id=Config.GOOGLE_CLIENT_ID,

    client_secret=Config.GOOGLE_CLIENT_SECRET,

    server_metadata_url=(
        "https://accounts.google.com/"
        ".well-known/openid-configuration"
    ),

    client_kwargs={
        "scope": "openid email profile"
    }

)


# =====================================================
# GEMINI SERVICE
# =====================================================

gemini = GeminiService()


# =====================================================
# RAZORPAY CLIENT
# =====================================================

def get_razorpay_credentials():

    key_id = (
        os.getenv("RAZORPAY_KEY_ID")
        or Config.RAZORPAY_KEY_ID
        or ""
    ).strip()

    key_secret = (
        os.getenv("RAZORPAY_KEY_SECRET")
        or Config.RAZORPAY_KEY_SECRET
        or ""
    ).strip()

    return key_id, key_secret


def get_razorpay_client():

    key_id, key_secret = get_razorpay_credentials()

    if not key_id or not key_secret:

        app.logger.error(
            "Razorpay configuration missing. "
            "Key ID loaded: %s, Secret loaded: %s",
            bool(key_id),
            bool(key_secret)
        )

        return None

    return razorpay.Client(
        auth=(
            key_id,
            key_secret
        )
    )


# =====================================================
# DATABASE INITIALIZATION
# =====================================================

initialize_database()


# =====================================================
# SAFE PAYMENT CONFIGURATION STATUS
# =====================================================

@app.route("/payment-config-status")
def payment_config_status():

    key_id, key_secret = get_razorpay_credentials()

    return jsonify({

        "key_id_loaded": bool(key_id),

        "secret_loaded": bool(key_secret),

        "test_mode": key_id.startswith("rzp_test_"),

        "key_id_length": len(key_id),

        "secret_length": len(key_secret)

    })


# =====================================================
# HOME
# =====================================================

@app.route("/")
def index():

    return render_template(

        "index.html",

        user=session.get("user")

    )


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if not session.get("user"):

        return redirect(
            url_for("index")
        )

    email = session["user"]

    create_user_if_not_exists(email)

    return render_template(

        "dashboard.html",

        user=email,

        scans=get_scan_history(email),

        stats=get_dashboard_stats(email),

        account=get_user_access_status(email),

        scan_price_rupees=Config.SCAN_PRICE_RUPEES

    )


# =====================================================
# PRICING
# =====================================================

@app.route("/pricing")
def pricing():

    if not session.get("user"):

        return redirect(
            url_for("index")
        )

    email = session["user"]

    create_user_if_not_exists(email)

    account = get_user_access_status(email)

    key_id, _ = get_razorpay_credentials()

    return render_template(

        "pricing.html",

        user=email,

        account=account,

        razorpay_key_id=key_id,

        scan_price_rupees=Config.SCAN_PRICE_RUPEES

    )


# =====================================================
# RAZORPAY CREATE ORDER
# =====================================================

@app.route(
    "/api/create-order",
    methods=["POST"]
)
@app.route(
    "/create-order",
    methods=["POST"]
)
def create_order():

    if not session.get("user"):

        return jsonify({

            "ok": False,

            "error": "Login required"

        }), 401

    razorpay_client = get_razorpay_client()

    if razorpay_client is None:

        return jsonify({

            "ok": False,

            "error": (
                "Payment gateway is not configured. "
                "Check RAZORPAY_KEY_ID and "
                "RAZORPAY_KEY_SECRET in Render."
            )

        }), 503

    payload = request.get_json(
        silent=True
    ) or {}

    try:

        requested_amount = int(

            payload.get(
                "amount",
                Config.SCAN_PRICE_PAISE
            )

        )

    except (TypeError, ValueError):

        return jsonify({

            "ok": False,

            "error": (
                "Amount must be an integer in paise"
            )

        }), 400

    if requested_amount < 100:

        return jsonify({

            "ok": False,

            "error": (
                "Minimum payment amount is 100 paise"
            )

        }), 400

    # This endpoint sells exactly one scan
    # at the server-configured price.
    if requested_amount != Config.SCAN_PRICE_PAISE:

        return jsonify({

            "ok": False,

            "error": "Invalid product amount"

        }), 400

    email = session["user"]

    create_user_if_not_exists(email)

    receipt = (
        f"scan_{secrets.token_hex(8)}"
    )

    try:

        order = razorpay_client.order.create(

            data={

                "amount":
                    Config.SCAN_PRICE_PAISE,

                "currency":
                    "INR",

                "receipt":
                    receipt,

                "payment_capture":
                    1,

                "notes": {

                    "user_email":
                        email,

                    "product":
                        "1_video_scan"

                }

            }

        )

        create_payment_record(

            user_email=email,

            order_id=order["id"],

            amount_paise=(
                Config.SCAN_PRICE_PAISE
            ),

            credits=1

        )

        key_id, _ = get_razorpay_credentials()

        return jsonify({

            "ok":
                True,

            "order_id":
                order["id"],

            "amount":
                order["amount"],

            "currency":
                order["currency"],

            "key_id":
                key_id,

            "name":
                "AI Video Inspector",

            "description":
                "1 Video Scan Credit",

            "prefill": {

                "email":
                    email

            }

        })

    except razorpay.errors.BadRequestError as exc:

        app.logger.exception(
            "Razorpay rejected order creation"
        )

        message = str(exc)

        if "authentication" in message.lower():

            return jsonify({

                "ok": False,

                "error":
                    "Razorpay authentication failed"

            }), 401

        return jsonify({

            "ok": False,

            "error":
                "Razorpay rejected the payment order"

        }), 400

    except Exception as exc:

        app.logger.exception(
            "Razorpay order creation failed"
        )

        status_code = getattr(
            exc,
            "status_code",
            None
        )

        message = str(exc) or (
            "Unable to create payment order"
        )

        if (
            status_code in {401, 403}
            or "authentication" in message.lower()
        ):

            return jsonify({

                "ok": False,

                "error":
                    "Razorpay authentication failed"

            }), 401

        return jsonify({

            "ok": False,

            "error":
                "Unable to create payment order"

        }), 500


# =====================================================
# VERIFY RAZORPAY PAYMENT
# =====================================================

@app.route(
    "/api/verify-payment",
    methods=["POST"]
)
@app.route(
    "/verify-payment",
    methods=["POST"]
)
def verify_payment():

    if not session.get("user"):

        return jsonify({

            "ok": False,

            "error": "Login required"

        }), 401

    _, razorpay_key_secret = (
        get_razorpay_credentials()
    )

    if not razorpay_key_secret:

        return jsonify({

            "ok": False,

            "error": (
                "Payment verification secret "
                "is not configured"
            )

        }), 503

    payload = (
        request.get_json(silent=True)
        or request.form
    )

    order_id = payload.get(
        "razorpay_order_id"
    )

    payment_id = payload.get(
        "razorpay_payment_id"
    )

    received_signature = payload.get(
        "razorpay_signature"
    )

    if not all([

        order_id,

        payment_id,

        received_signature

    ]):

        return jsonify({

            "ok": False,

            "error": (
                "Missing payment verification fields"
            )

        }), 400

    payment = get_payment_by_order(
        order_id
    )

    if not payment:

        return jsonify({

            "ok": False,

            "error":
                "Payment order was not found"

        }), 404

    if (
        payment["user_email"].lower()
        != session["user"].lower()
    ):

        return jsonify({

            "ok": False,

            "error": (
                "Payment order does not "
                "belong to this user"
            )

        }), 403

    if (
        int(payment["amount_paise"])
        != Config.SCAN_PRICE_PAISE
    ):

        return jsonify({

            "ok": False,

            "error": "Payment amount mismatch"

        }), 400

    # Razorpay Standard Checkout signature:
    # HMAC-SHA256(order_id + "|" + payment_id, secret)

    signed_payload = (
        f"{order_id}|{payment_id}"
    ).encode("utf-8")

    generated_signature = hmac.new(

        razorpay_key_secret.encode(
            "utf-8"
        ),

        signed_payload,

        hashlib.sha256

    ).hexdigest()

    if not hmac.compare_digest(

        generated_signature,

        received_signature

    ):

        app.logger.warning(

            "Rejected invalid Razorpay "
            "signature for order %s",

            order_id

        )

        return jsonify({

            "ok": False,

            "error": (
                "Payment signature "
                "verification failed"
            )

        }), 400

    try:

        # Database transaction makes credit
        # fulfilment idempotent.
        complete_payment_and_add_credits(

            order_id=order_id,

            payment_id=payment_id,

            user_email=session["user"]

        )

        account = get_user_access_status(
            session["user"]
        )

        return jsonify({

            "ok":
                True,

            "message":
                (
                    "Payment verified. "
                    "One scan credit was added."
                ),

            "credits":
                account["scan_credits"],

            "redirect_url":
                url_for("dashboard")

        })

    except Exception:

        app.logger.exception(
            "Payment fulfilment failed"
        )

        return jsonify({

            "ok": False,

            "error": (
                "Payment was verified but "
                "credit fulfilment failed"
            )

        }), 500


# =====================================================
# PRIVATE REPORT
# =====================================================

@app.route("/report/<int:scan_id>")
def view_report(scan_id):

    if not session.get("user"):

        return redirect(
            url_for("index")
        )

    scan = get_report_by_id(

        scan_id,

        session["user"]

    )

    if not scan:

        return "Report not found", 404

    report = json.loads(
        scan["report_data"]
    )

    share_url = None

    if scan["public_token"]:

        share_url = url_for(

            "shared_report",

            token=scan["public_token"],

            _external=True,

            _scheme=(
                "https"
                if os.getenv("RENDER") == "true"
                else None
            )

        )

    return render_template(

        "report.html",

        filename=scan["filename"],

        report=report,

        scan_id=scan_id,

        share_url=share_url,

        public=False,

        account=get_user_access_status(
            session["user"]
        ),

        logs=[
            "Loaded from history"
        ]

    )


# =====================================================
# PUBLIC REPORT
# =====================================================

@app.route("/shared-report/<token>")
def shared_report(token):

    scan = get_public_report(
        token
    )

    if not scan:

        return (
            "Shared report not found",
            404
        )

    return render_template(

        "report.html",

        filename=scan["filename"],

        report=json.loads(
            scan["report_data"]
        ),

        scan_id=None,

        share_url=None,

        public=True,

        account=None,

        logs=[
            "Public shared report"
        ]

    )


# =====================================================
# DOWNLOAD PDF
# =====================================================

@app.route(
    "/download-report/<int:scan_id>"
)
def download_report(scan_id):

    if not session.get("user"):

        return redirect(
            url_for("index")
        )

    scan = get_report_by_id(

        scan_id,

        session["user"]

    )

    if not scan:

        return "Report not found", 404

    pdf_path = generate_pdf(

        filename=scan["filename"],

        report=json.loads(
            scan["report_data"]
        ),

        scan_id=scan_id

    )

    return send_file(

        pdf_path,

        as_attachment=True,

        download_name=(
            f"AI_Video_Report_{scan_id}.pdf"
        )

    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# =====================================================
# GOOGLE LOGIN
# =====================================================

@app.route("/auth/google")
def auth_google():

    return google.authorize_redirect(

        url_for(

            "auth_google_callback",

            _external=True,

            _scheme=(
                "https"
                if os.getenv("RENDER") == "true"
                else None
            )

        )

    )


@app.route("/auth/google/callback")
def auth_google_callback():

    try:

        token = (
            google.authorize_access_token()
        )

        user_info = token.get(
            "userinfo"
        )

        if not user_info:

            user_info = google.get(

                "https://openidconnect."
                "googleapis.com/v1/userinfo"

            ).json()

        email = user_info.get(
            "email"
        )

        if not email:

            raise ValueError(
                "Google did not return "
                "an email address"
            )

        session["user"] = (
            email.strip().lower()
        )

        create_user_if_not_exists(
            session["user"]
        )

        return redirect(
            url_for("dashboard")
        )

    except Exception as exc:

        app.logger.exception(
            "Google login failed"
        )

        return (
            f"Login failed: {exc}",
            400
        )


# =====================================================
# VIDEO SCAN
# =====================================================

@app.route(
    "/scan",
    methods=["POST"]
)
def scan():

    if not session.get("user"):

        return redirect(
            url_for("index")
        )

    email = session["user"]

    entitlement = None

    filepath = None

    try:

        if "video" not in request.files:

            raise ValueError(
                "No video uploaded"
            )

        uploaded_file = (
            request.files["video"]
        )

        if uploaded_file.filename == "":

            raise ValueError(
                "Please select a video"
            )

        entitlement = (
            reserve_scan_entitlement(
                email
            )
        )

        if entitlement is None:

            return redirect(
                url_for("pricing")
            )

        filepath = UploadService.save(
            uploaded_file
        )

        report = gemini.analyze(
            filepath
        )

        if not isinstance(
            report,
            dict
        ):

            raise ValueError(
                "Gemini returned an "
                "invalid response"
            )

        copyright_score = (

            report
            .get("copyright", {})
            .get("risk", "N/A")

        )

        seo_score = (

            report
            .get("seo", {})
            .get("score", 0)

        )

        content_id = (

            report
            .get("audio", {})
            .get("content_id_risk", "N/A")

        )

        public_token = (
            secrets.token_urlsafe(24)
        )

        scan_id = save_scan_history(

            user_email=email,

            filename=(
                uploaded_file.filename
            ),

            copyright_score=str(
                copyright_score
            ),

            seo_score=str(
                seo_score
            ),

            content_id=str(
                content_id
            ),

            report_data=json.dumps(
                report
            ),

            public_token=public_token

        )

        share_url = url_for(

            "shared_report",

            token=public_token,

            _external=True,

            _scheme=(
                "https"
                if os.getenv("RENDER") == "true"
                else None
            )

        )

        return render_template(

            "report.html",

            filename=(
                uploaded_file.filename
            ),

            report=report,

            scan_id=scan_id,

            share_url=share_url,

            public=False,

            account=(
                get_user_access_status(
                    email
                )
            ),

            logs=[

                "Video analysed",

                f"Used {entitlement} scan",

                "Report saved"

            ]

        )

    except Exception as exc:

        # A failed scan must not consume
        # the user's free scan or paid credit.
        if entitlement:

            try:

                restore_scan_entitlement(

                    email,

                    entitlement

                )

            except Exception:

                app.logger.exception(
                    "Failed to restore "
                    "scan entitlement"
                )

        app.logger.exception(
            "Scan failed"
        )

        return render_template(

            "report.html",

            filename="Error",

            report={
                "error": str(exc)
            },

            scan_id=None,

            share_url=None,

            public=False,

            account=(
                get_user_access_status(
                    email
                )
            ),

            logs=[
                str(exc)
            ]

        ), 500

    finally:

        if (
            filepath
            and os.path.exists(filepath)
        ):

            try:

                os.remove(
                    filepath
                )

            except OSError:

                app.logger.warning(

                    "Could not delete "
                    "temporary upload: %s",

                    filepath

                )


# =====================================================
# SERVER START
# =====================================================

if __name__ == "__main__":

    app.run(

        debug=(
            os.getenv(
                "FLASK_DEBUG",
                "false"
            ).lower()
            == "true"
        ),

        use_reloader=False,

        host="0.0.0.0",

        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        )

    )