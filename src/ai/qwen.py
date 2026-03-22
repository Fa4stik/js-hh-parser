import json
import os
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import uvicorn

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


class VacancyRequest(BaseModel):
    body: str
    skill: str = None  # 'hard', 'soft' or None for both


class SkillsResponse(BaseModel):
    soft: List[str]
    hard: List[str]


class QwenSkillExtractor:
    def __init__(self):
        self.soft_skills = []
        self.hard_skills = []
        self.prompt_template = ""
        self._load_skills_and_prompt()

    def _load_skills_and_prompt(self):
        base_path = Path(__file__).parent.parent

        soft_path = base_path / "disco" / "skils" / "soft.txt"
        with open(soft_path, 'r', encoding='utf-8') as f:
            self.soft_skills = [line.strip() for line in f.readlines() if line.strip()]

        hard_path = base_path / "disco" / "skils" / "hard.txt"
        with open(hard_path, 'r', encoding='utf-8') as f:
            self.hard_skills = [line.strip() for line in f.readlines() if line.strip()]

        prompt_path = base_path / "ai" / "promt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read().strip()

    def _format_skills_list(self, skills: List[str]) -> str:
        return "\n".join(f"- {skill}" for skill in skills)

    def _prepare_prompt(self, description: str, skill_type: str = None) -> str:
        soft_formatted = self._format_skills_list(self.soft_skills)
        hard_formatted = self._format_skills_list(self.hard_skills)

        prompt = self.prompt_template.replace("${description}", description)

        if skill_type == "hard":
            prompt = prompt.replace("${soft}", "")
            prompt = prompt.replace("${hard}", hard_formatted)
            prompt += "\n\nВАЖНО: Найди только технические (hard) навыки. Игнорируй мягкие навыки."
        elif skill_type == "soft":
            prompt = prompt.replace("${soft}", soft_formatted)
            prompt = prompt.replace("${hard}", "")
            prompt += "\n\nВАЖНО: Найди только мягкие (soft) навыки. Игнорируй технические навыки."
        else:
            prompt = prompt.replace("${soft}", soft_formatted)
            prompt = prompt.replace("${hard}", hard_formatted)

        return prompt

    def _parse_model_response(self, response: str) -> Dict[str, List[str]]:
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx == -1 or end_idx == -1:
                raise ValueError("JSON not found in model response")

            json_str = response[start_idx:end_idx + 1]
            result = json.loads(json_str)

            if 'soft' not in result:
                result['soft'] = []
            if 'hard' not in result:
                result['hard'] = []

            if not isinstance(result['soft'], list) or not isinstance(result['hard'], list):
                raise ValueError("Invalid JSON structure in response")

            return self._validate_and_filter_skills(result)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing model response: {e}")
            print(f"Model response: {response}")
            return {"soft": [], "hard": []}

    def _validate_and_filter_skills(self, result: Dict[str, List[str]]) -> Dict[str, List[str]]:
        def normalize_skill(skill: str) -> str:
            return skill.strip().lower()

        def find_exact_skill(skill_to_find: str, skills_list: List[str]) -> str:
            normalized_to_find = normalize_skill(skill_to_find)
            for original_skill in skills_list:
                if normalize_skill(original_skill) == normalized_to_find:
                    return original_skill
            return None

        def remove_duplicates(skills_list: List[str]) -> List[str]:
            seen = set()
            unique_skills = []
            for skill in skills_list:
                normalized = normalize_skill(skill)
                if normalized not in seen:
                    seen.add(normalized)
                    unique_skills.append(skill)
            return unique_skills

        filtered_soft = []
        for skill in result.get('soft', []):
            exact_skill = find_exact_skill(skill, self.soft_skills)
            if exact_skill:
                filtered_soft.append(exact_skill)

        filtered_hard = []
        for skill in result.get('hard', []):
            exact_skill = find_exact_skill(skill, self.hard_skills)
            if exact_skill:
                filtered_hard.append(exact_skill)

        unique_soft = remove_duplicates(filtered_soft)
        unique_hard = remove_duplicates(filtered_hard)

        print(f"Validation done. Soft: {len(unique_soft)}/{len(result.get('soft', []))}, Hard: {len(unique_hard)}/{len(result.get('hard', []))}")

        return {
            "soft": unique_soft,
            "hard": unique_hard
        }

    async def extract_skills(self, description: str, skill_type: str = None) -> Dict[str, List[str]]:
        prompt = self._prepare_prompt(description, skill_type)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.8,
                        "top_k": 20,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            model_response = data["message"]["content"]

        result = self._parse_model_response(model_response)

        if skill_type == "hard":
            return {"soft": [], "hard": result.get("hard", [])}
        elif skill_type == "soft":
            return {"soft": result.get("soft", []), "hard": []}
        else:
            return result


skill_extractor = QwenSkillExtractor()

app = FastAPI(
    title="Vacancy Skills Extractor API",
    description="API for extracting skills from vacancy descriptions using Qwen2.5-7B via Ollama.",
    version="2.0.0"
)


@app.get("/")
async def root():
    return {"message": "Vacancy Skills Extractor API is running"}


@app.post("/api/vacancy", response_model=SkillsResponse)
async def extract_vacancy_skills(request: VacancyRequest):
    try:
        if not request.body.strip():
            raise HTTPException(status_code=400, detail="Vacancy description cannot be empty")

        if request.skill and request.skill not in ["hard", "soft"]:
            raise HTTPException(status_code=400, detail="skill must be 'hard', 'soft' or omitted")

        skills = await skill_extractor.extract_skills(request.body, request.skill)

        return SkillsResponse(
            soft=skills.get("soft", []),
            hard=skills.get("hard", [])
        )

    except httpx.HTTPError as e:
        print(f"Ollama request error: {e}")
        raise HTTPException(status_code=502, detail=f"Ollama error: {str(e)}")
    except Exception as e:
        print(f"Error processing vacancy: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/health")
async def health_check():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            ollama_ok = resp.status_code == 200
    except Exception:
        ollama_ok = False

    return {
        "status": "healthy" if ollama_ok else "degraded",
        "ollama_connected": ollama_ok,
        "model": OLLAMA_MODEL,
        "soft_skills_count": len(skill_extractor.soft_skills),
        "hard_skills_count": len(skill_extractor.hard_skills)
    }


if __name__ == "__main__":
    uvicorn.run(
        "qwen:app",
        host="0.0.0.0",
        port=6380,
    )
