import json
import time


from google import genai
from google.genai import types


from config import Config





class GeminiService:



    def __init__(self):


        self.client = genai.Client(

            api_key=Config.GEMINI_API_KEY

        )


        self.model = Config.MODEL_NAME






    # =====================================================
    # UPLOAD VIDEO TO GEMINI
    # =====================================================

    def upload_video(self, filepath):


        uploaded_file = self.client.files.upload(

            file=filepath

        )



        start_time = time.time()



        while uploaded_file.state.name == "PROCESSING":



            if time.time() - start_time > 300:

                raise Exception(

                    "Gemini video processing timeout"

                )



            time.sleep(3)



            uploaded_file = self.client.files.get(

                name=uploaded_file.name

            )






        if uploaded_file.state.name == "FAILED":


            raise Exception(

                "Gemini failed to process video"

            )



        return uploaded_file







    # =====================================================
    # VIDEO ANALYSIS
    # =====================================================

    def analyze(self, filepath):


        video_file = self.upload_video(filepath)





        prompt = """

You are an expert YouTube Copyright,
Content ID and SEO auditor.

Analyze this video deeply.

Your job:

1. Detect possible copyright risks.

2. Identify:
- movies
- TV clips
- anime
- famous characters
- logos
- brands
- celebrity appearances
- reused content

3. Analyze audio:
- background music
- songs
- AI voice
- human voice
- possible Content ID match risk


4. Analyze YouTube SEO quality.

5. Suggest improvements.


IMPORTANT:

Return ONLY valid JSON.

Do not use markdown.

Do not add explanations outside JSON.



Return exactly this format:


{

"overall_score":0,


"copyright":{

"risk":"Low",

"confidence":0,

"claim_probability":0,

"strike_probability":0,

"issues":[],

"timestamps":[],

"explanation":""

},



"audio":{

"music_detected":"",

"music_type":"",

"voice_type":"",

"content_id_risk":"Low",

"audio_issues":[]

},




"visual":{

"faces_detected":false,

"logos":[],

"brands":[],

"celebrities":[],

"objects":[],

"reused_content_probability":0

},




"community_guidelines":{

"safe":true,

"issues":[]

},




"seo":{

"score":0,

"title":"",

"description":"",

"tags":[],

"hashtags":[],

"keywords":[]

},




"thumbnail":{

"suggestion":""

},




"monetization":{

"youtube_partner_program_ready":true,

"concerns":[]

},




"recommendations":[

""

]

}



SCORING RULES:


overall_score:

90-100:
Very safe original content.


70-89:
Low risk.


40-69:
Needs review.


0-39:
High copyright concern.



Copyright risk:

Low:
No obvious copyrighted material.


Moderate:
Possible reused material.


High:
Clear copyrighted content detected.



Probability values must be numbers only.

Example:

"claim_probability":25


Analyze the actual uploaded video.

Do not assume AI generated videos are copyrighted.

"""







        response = self.client.models.generate_content(


            model=self.model,


            contents=[


                video_file,


                prompt


            ],


            config=types.GenerateContentConfig(


                temperature=0.1,


                response_mime_type="application/json"


            )


        )






        return self.parse_response(response.text)









    # =====================================================
    # SAFE JSON PARSER
    # =====================================================

    def parse_response(self, text):


        try:


            data=json.loads(text)



        except Exception:



            print(
                "Gemini RAW RESPONSE:"
            )


            print(text)



            text=text.replace(
                "```json",
                ""
            )


            text=text.replace(
                "```",
                ""
            )


            data=json.loads(text)







        # Safety defaults


        data.setdefault(
            "overall_score",
            0
        )


        data.setdefault(
            "copyright",
            {}
        )


        data.setdefault(
            "audio",
            {}
        )


        data.setdefault(
            "visual",
            {}
        )


        data.setdefault(
            "seo",
            {}
        )


        data.setdefault(
            "recommendations",
            []
        )



        return data