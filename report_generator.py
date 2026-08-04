from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

import os



REPORT_FOLDER = "reports"



def generate_pdf(filename, report, scan_id):


    if not os.path.exists(REPORT_FOLDER):

        os.makedirs(REPORT_FOLDER)



    pdf_path = os.path.join(

        REPORT_FOLDER,

        f"AI_Report_{scan_id}.pdf"

    )



    doc = SimpleDocTemplate(
        pdf_path
    )



    styles = getSampleStyleSheet()


    content = []



    content.append(

        Paragraph(

            "AI Video Inspector Report",

            styles["Title"]

        )

    )


    content.append(Spacer(1,20))



    content.append(

        Paragraph(

            f"Video Name: {filename}",

            styles["Normal"]

        )

    )


    content.append(Spacer(1,15))





    content.append(

        Paragraph(

            "Overall Score",

            styles["Heading2"]

        )

    )



    content.append(

        Paragraph(

            str(
                report.get(
                    "overall_score",
                    "N/A"
                )
            ),

            styles["Normal"]

        )

    )



    content.append(Spacer(1,15))





    copyright_data = report.get(
        "copyright",
        {}
    )


    content.append(

        Paragraph(

            "Copyright Analysis",

            styles["Heading2"]

        )

    )


    content.append(

        Paragraph(

            f"""
            Risk:
            {copyright_data.get('risk','N/A')}
            <br/>
            Confidence:
            {copyright_data.get('confidence','N/A')}%
            <br/>
            Claim Probability:
            {copyright_data.get('claim_probability','N/A')}%
            """,

            styles["Normal"]

        )

    )





    content.append(Spacer(1,15))





    seo = report.get(
        "seo",
        {}
    )


    content.append(

        Paragraph(

            "YouTube SEO",

            styles["Heading2"]

        )

    )


    content.append(

        Paragraph(

            f"""
            SEO Score:
            {seo.get('score','N/A')}

            <br/><br/>

            Suggested Title:

            {seo.get('title','N/A')}

            <br/><br/>

            Description:

            {seo.get('description','N/A')}

            """,

            styles["Normal"]

        )

    )





    content.append(Spacer(1,15))





    content.append(

        Paragraph(

            "AI Recommendations",

            styles["Heading2"]

        )

    )



    recommendations = report.get(
        "recommendations",
        []
    )


    for item in recommendations:


        content.append(

            Paragraph(

                "• " + str(item),

                styles["Normal"]

            )

        )




    doc.build(content)



    return pdf_path