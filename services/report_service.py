import markdown


class ReportService:

    @staticmethod
    def normalize_score(value):

        if value is None:
            return 0

        if value <= 1:
            return round(value * 100)

        if value <= 10:
            return round(value * 10)

        return round(value)


    @staticmethod
    def risk_icon(risk):

        risk = str(risk).lower()

        if risk == "low":
            return "🟢 LOW RISK"

        if risk == "moderate" or risk == "medium":
            return "🟡 MODERATE RISK"

        if risk == "high":
            return "🔴 HIGH RISK"

        return "⚪ UNKNOWN"


    @staticmethod
    def build_markdown(report: dict):

        md = "# 🎥 AI Video Inspector Report\n\n"

        md += "---\n\n"


        # Summary

        score = ReportService.normalize_score(
            report.get("overall_score", 0)
        )

        md += "## 📊 Creator Summary\n\n"

        md += f"**Overall Score:** {score}/100\n\n"


        if score >= 80:
            status = "READY TO UPLOAD ✅"
        elif score >= 50:
            status = "READY WITH REVIEW ⚠️"
        else:
            status = "NEEDS IMPROVEMENT ❌"


        md += f"**Upload Status:** {status}\n\n"



        # Copyright

        cp = report.get("copyright", {})

        md += "## 🛡️ Copyright Safety\n\n"

        md += f"**Risk:** {ReportService.risk_icon(cp.get('risk'))}\n\n"


        confidence = ReportService.normalize_score(
            cp.get("confidence",0)
        )

        claim = ReportService.normalize_score(
            cp.get("claim_probability",0)
        )

        strike = ReportService.normalize_score(
            cp.get("strike_probability",0)
        )


        md += f"- Confidence: **{confidence}%**\n"
        md += f"- Claim Probability: **{claim}%**\n"
        md += f"- Strike Probability: **{strike}%**\n\n"



        if cp.get("issues"):

            md += "### ⚠️ Copyright Notes\n\n"

            for issue in cp["issues"]:
                md += f"- {issue}\n"

            md += "\n"



        # Reused Content

        visual = report.get("visual", {})

        md += "## ♻️ Reused Content Check\n\n"


        logos = visual.get("logos", [])

        if logos:

            md += "⚠️ **Social Media Watermark Detected**\n\n"

            for logo in logos:
                md += f"- {logo}\n"

            md += "\nRecommendation:\n"
            md += "Remove external platform watermarks before uploading.\n\n"

        else:

            md += "✅ No obvious watermark detected.\n\n"



        # Audio

        audio = report.get("audio", {})

        md += "## 🎵 Audio Check\n\n"

        md += f"- Music: {audio.get('music_detected','None')}\n"
        md += f"- Voice: {audio.get('voice_type','None')}\n"
        md += f"- Content ID Risk: {audio.get('content_id_risk','Unknown')}\n\n"



        # Visual

        md += "## 👁️ Visual Analysis\n\n"

        md += f"- Faces: {visual.get('faces_detected',False)}\n"
        md += f"- Brands: {', '.join(visual.get('brands',[])) or 'None'}\n"
        md += f"- Celebrities: {', '.join(visual.get('celebrities',[])) or 'None'}\n\n"



        # Community

        community = report.get("community_guidelines", {})

        md += "## 📋 Community Guidelines\n\n"

        if community.get("safe"):
            md += "✅ No issues detected.\n\n"
        else:
            for issue in community.get("issues",[]):
                md += f"- {issue}\n"



        # SEO

        seo = report.get("seo",{})

        seo_score = ReportService.normalize_score(
            seo.get("score",0)
        )


        md += "## 🚀 YouTube SEO Optimization\n\n"

        md += f"SEO Score: **{seo_score}/100**\n\n"

        md += "### 🎯 Suggested Title\n\n"
        md += f"{seo.get('title','')}\n\n"

        md += "### 📝 Description\n\n"
        md += f"{seo.get('description','')}\n\n"


        md += "### 🏷️ Tags\n\n"

        for tag in seo.get("tags",[]):
            md += f"- {tag}\n"

        md += "\n"


        md += "### #️⃣ Hashtags\n\n"

        md += " ".join(
            seo.get("hashtags",[])
        )

        md += "\n\n"



        # Thumbnail

        thumbnail = report.get("thumbnail",{})

        md += "## 🖼️ Thumbnail Advice\n\n"

        md += thumbnail.get(
            "suggestion",
            "No suggestion available."
        )

        md += "\n\n"



        # Checklist

        md += "## ✅ Before Publishing Checklist\n\n"

        md += "- ☐ Verify music license\n"
        md += "- ☐ Remove third-party watermark\n"
        md += "- ☐ Improve thumbnail quality\n"
        md += "- ☐ Add engagement hooks\n\n"



        # Recommendations

        md += "## 💡 AI Recommendations\n\n"

        for rec in report.get("recommendations",[]):
            md += f"- {rec}\n"


        return md



    @staticmethod
    def markdown_to_html(md):

        return markdown.markdown(
            md,
            extensions=["tables","fenced_code"]
        )