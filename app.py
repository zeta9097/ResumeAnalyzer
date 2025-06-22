from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import shutil
import os
import uuid
import traceback
from pathlib import Path
import threading

# Module imports (renamed as per your pipeline)
from M1_file_handling import ResumeParser
from M2_resume_exp_extractor import ExperienceExtractorAndParser
from M3_resume_skills_extractor import SkillExtractor
from M4_resume_educ_extractor import ResumeEducationExtractor
from M5_resume_projects import ProjectsExtractor
from M6_jd_processor import JDExtractorGroq
from M7_scoring import ResumeJDScorerAsync
from M8_ranking import ResumeRanker

# FastAPI setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Module initializations
resume_parser = ResumeParser()
experience_parser = ExperienceExtractorAndParser()
skill_extractor = SkillExtractor()
education_extractor = ResumeEducationExtractor()
projects_extractor = ProjectsExtractor()
jd_extractor = JDExtractorGroq()
scorer = ResumeJDScorerAsync()
ranker = ResumeRanker()

# Cache recent result
last_results = []


@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        html_path = Path("static/index.html")
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/analyze")
async def analyze_resumes(
    resume: List[UploadFile] = File(...),
    jd_text: str = Form(...),
    top_n: int = Form(5)
):
    global last_results
    try:
        if not resume:
            raise HTTPException(status_code=400, detail="No files uploaded")
        if not jd_text.strip():
            raise HTTPException(status_code=400, detail="Job description is empty")

        # Save uploaded files
        file_paths = []
        for file in resume:
            filename = f"{uuid.uuid4()}_{file.filename}"
            path = os.path.join(UPLOAD_DIR, filename)
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(path)

        # === JD Processing ===
        parsed_jd = jd_extractor.extract(jd_text)

        # === Resume Processing ===
        parsed = resume_parser.parse_resumes(file_paths)
        experience_data = experience_parser.extract_and_parse_batch(parsed)
        skills_data = skill_extractor.extract_and_clean_batch(parsed)
        education_data = education_extractor.extract_batch(parsed)
        projects_data = projects_extractor.extract_and_clean_batch(parsed)

        # Combine resume components
        parsed_resumes = []
        for i in range(len(parsed)):
            contact_info = experience_data[i].get("contact_info", {})
            parsed_resumes.append({
                "skills": skills_data[i],
                "education": education_data[i],
                "experience": experience_data[i].get("experience", []),
                "projects": projects_data[i],
                "contact_info": contact_info,
                "original_file_name": os.path.basename(file_paths[i])
            })


        # === Scoring ===
        results = await scorer.score_resumes_batch(parsed_resumes, parsed_jd, include_contact=True)

        # Attach name/email/phone for ranking output
        for i, res in enumerate(results):
            contact = parsed_resumes[i].get("contact_info", {})
            res.update({
                "name": contact.get("name", f"Resume {i+1}").title(),
                "email": contact.get("email", ""),
                "phone": contact.get("phone", ""),
                "original_file_url": f"/uploads/{os.path.basename(file_paths[i])}"
            })

        # === Ranking ===
        ranked = ResumeRanker(top_n=top_n).rank(results)
        last_results = ranked

        # Cleanup
        

        def delayed_cleanup(paths):
            for path in paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")

        # Schedule file deletion after 10 seconds
        threading.Timer(300.0, delayed_cleanup, args=[file_paths]).start()

        return JSONResponse(content=ranked)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
