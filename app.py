import os
import json
import secrets


from flask import (
    Flask,
    request,
    render_template,
    session,
    redirect,
    url_for,
    send_file
)


from authlib.integrations.flask_client import OAuth


from config import Config


from services.upload_service import UploadService
from services.gemini_service import GeminiService


from database import (
    initialize_database,
    save_scan_history,
    get_scan_history,
    get_report_by_id,
    get_dashboard_stats,
    get_public_report
)


from report_generator import generate_pdf




# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)

app.config.from_object(Config)


# Required for sessions
app.secret_key = Config.SECRET_KEY


os.environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"






# =====================================================
# GOOGLE OAUTH
# =====================================================

oauth = OAuth(app)


google = oauth.register(

    name="google",

    client_id=Config.GOOGLE_CLIENT_ID,

    client_secret=Config.GOOGLE_CLIENT_SECRET,

    server_metadata_url=
    "https://accounts.google.com/.well-known/openid-configuration",

    client_kwargs={
        "scope":"openid email profile"
    }

)






# =====================================================
# GEMINI
# =====================================================

gemini = GeminiService()






# =====================================================
# DATABASE
# =====================================================

initialize_database()







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

        return redirect(url_for("index"))



    email = session["user"]


    return render_template(

        "dashboard.html",

        user=email,

        scans=get_scan_history(email),

        stats=get_dashboard_stats(email)

    )







# =====================================================
# PRIVATE REPORT
# =====================================================

@app.route("/report/<int:scan_id>")
def view_report(scan_id):


    if not session.get("user"):

        return redirect(url_for("index"))



    scan = get_report_by_id(

        scan_id,

        session["user"]

    )


    if not scan:

        return "Report not found"




    report=json.loads(

        scan["report_data"]

    )



    share_url = None



    if scan["public_token"]:

        share_url = (

            request.host_url +

            "shared-report/" +

            scan["public_token"]

        )





    return render_template(

        "report.html",

        filename=scan["filename"],

        report=report,

        scan_id=scan_id,

        share_url=share_url,

        public=False,

        logs=[
            "Loaded from history"
        ]

    )








# =====================================================
# PUBLIC SHARED REPORT
# =====================================================

@app.route("/shared-report/<token>")
def shared_report(token):


    scan = get_public_report(token)



    if not scan:

        return "Shared report not found"




    report=json.loads(

        scan["report_data"]

    )




    return render_template(

        "report.html",

        filename=scan["filename"],

        report=report,

        scan_id=None,

        share_url=None,

        public=True,

        logs=[
            "Public shared report"
        ]

    )








# =====================================================
# DOWNLOAD PDF
# =====================================================

@app.route("/download-report/<int:scan_id>")
def download_report(scan_id):


    if not session.get("user"):

        return redirect(url_for("index"))



    scan=get_report_by_id(

        scan_id,

        session["user"]

    )


    if not scan:

        return "Report not found"




    report=json.loads(

        scan["report_data"]

    )



    pdf_path=generate_pdf(

        filename=scan["filename"],

        report=report,

        scan_id=scan_id

    )



    return send_file(

        pdf_path,

        as_attachment=True,

        download_name=f"AI_Video_Report_{scan_id}.pdf"

    )







# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))






# =====================================================
# GOOGLE LOGIN
# =====================================================

@app.route("/auth/google")
def auth_google():


    redirect_uri=url_for(

        "auth_google_callback",

        _external=True

    )


    return google.authorize_redirect(

        redirect_uri

    )






@app.route("/auth/google/callback")
def auth_google_callback():

    try:


        token=google.authorize_access_token()



        user_info = token.get(
            "userinfo"
        )



        if not user_info:


            response = google.get(

                "https://openidconnect.googleapis.com/v1/userinfo"

            )


            user_info=response.json()




        session["user"] = user_info["email"]



        return redirect(

            url_for("dashboard")

        )



    except Exception as e:


        print(
            "LOGIN ERROR:",
            e
        )


        return str(e)









# =====================================================
# VIDEO SCAN
# =====================================================

@app.route("/scan",methods=["POST"])
def scan():


    if not session.get("user"):

        return redirect(url_for("index"))



    try:


        if "video" not in request.files:

            raise Exception(
                "No video uploaded"
            )



        uploaded_file=request.files["video"]



        if uploaded_file.filename=="":

            raise Exception(
                "Select video"
            )




        filepath=UploadService.save(

            uploaded_file

        )




        report=gemini.analyze(

            filepath

        )




        if not isinstance(report,dict):

            raise Exception(
                "Invalid Gemini response"
            )





        copyright_score = (

            report
            .get("copyright",{})
            .get("risk","N/A")

        )



        seo_score = (

            report
            .get("seo",{})
            .get("score",0)

        )



        content_id = (

            report
            .get("audio",{})
            .get("content_id_risk","N/A")

        )





        public_token = secrets.token_urlsafe(24)





        scan_id = save_scan_history(

            user_email=session["user"],

            filename=uploaded_file.filename,

            copyright_score=str(copyright_score),

            seo_score=str(seo_score),

            content_id=str(content_id),

            report_data=json.dumps(report),

            public_token=public_token

        )





        share_url = (

            request.host_url +

            "shared-report/" +

            public_token

        )





        print(
            "SHARE URL:",
            share_url
        )





        return render_template(

            "report.html",

            filename=uploaded_file.filename,

            report=report,

            scan_id=scan_id,

            share_url=share_url,

            public=False,

            logs=[
                "Video analysed",
                "Report saved"
            ]

        )






    except Exception as e:


        print(
            "SCAN ERROR:",
            e
        )


        return render_template(

            "report.html",

            filename="Error",

            report={
                "error":str(e)
            },

            scan_id=None,

            share_url=None,

            logs=[
                str(e)
            ]

        )









# =====================================================
# SERVER START
# =====================================================

if __name__=="__main__":


    app.run(

        debug=True,

        use_reloader=False,

        host="0.0.0.0",

        port=5000

    )