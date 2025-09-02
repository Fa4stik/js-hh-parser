#!/usr/bin/env python3
"""
Упрощенная версия API без модели Qwen
"""

import json
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


# Pydantic модели
class VacancyRequest(BaseModel):
    body: str
    skill: str = None  # 'hard', 'soft' или None для обоих


class SkillsResponse(BaseModel):
    soft: List[str]
    hard: List[str]


class SimpleSkillExtractor:
    def __init__(self):
        self.soft_skills = []
        self.hard_skills = []
        self._load_skills()
        
    def _load_skills(self):
        """Загружает навыки из файлов"""
        base_path = Path(__file__).parent.parent
        
        # Загружаем софт-скиллы
        soft_path = base_path / "disco" / "skils" / "soft.txt"
        if soft_path.exists():
            with open(soft_path, 'r', encoding='utf-8') as f:
                self.soft_skills = [line.strip() for line in f.readlines() if line.strip()]
        
        # Загружаем хард-скиллы
        hard_path = base_path / "disco" / "skils" / "hard.txt"
        if hard_path.exists():
            with open(hard_path, 'r', encoding='utf-8') as f:
                self.hard_skills = [line.strip() for line in f.readlines() if line.strip()]
    
    def extract_skills(self, description: str, skill_type: str = None) -> Dict[str, List[str]]:
        """Простое извлечение навыков на основе ключевых слов"""
        description_lower = description.lower()
        
        result = {"soft": [], "hard": []}
        
        # Ищем софт-навыки (если нужны или не указан тип)
        if skill_type is None or skill_type == "soft":
            found_soft = []
            for skill in self.soft_skills:
                if skill.lower() in description_lower:
                    found_soft.append(skill)
            result["soft"] = found_soft[:10]  # Ограничиваем количество
        
        # Ищем хард-навыки (если нужны или не указан тип)
        if skill_type is None or skill_type == "hard":
            found_hard = []
            for skill in self.hard_skills:
                if skill.lower() in description_lower:
                    found_hard.append(skill)
            result["hard"] = found_hard[:10]  # Ограничиваем количество
        
        return result


# Инициализируем экстрактор
skill_extractor = SimpleSkillExtractor()

# Создаем FastAPI приложение
app = FastAPI(
    title="Simple Vacancy Skills Extractor API",
    description="Упрощенное API для извлечения навыков без модели Qwen. Поддерживает селективный поиск hard/soft навыков.",
    version="1.1.0"
)


@app.get("/")
async def root():
    """Проверка работоспособности API"""
    return {"message": "Simple Vacancy Skills Extractor API работает"}


@app.post("/api/vacancy", response_model=SkillsResponse)
async def extract_vacancy_skills(request: VacancyRequest):
    """Извлекает навыки из описания вакансии"""
    try:
        if not request.body.strip():
            raise HTTPException(status_code=400, detail="Описание вакансии не может быть пустым")
        
        # Валидация параметра skill
        if request.skill and request.skill not in ["hard", "soft"]:
            raise HTTPException(status_code=400, detail="Параметр skill должен быть 'hard', 'soft' или не указан")
        
        skills = skill_extractor.extract_skills(request.body, request.skill)
        
        return SkillsResponse(
            soft=skills.get("soft", []),
            hard=skills.get("hard", [])
        )
        
    except Exception as e:
        print(f"Ошибка при обработке вакансии: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


@app.get("/health")
async def health_check():
    """Проверка состояния API"""
    return {
        "status": "healthy",
        "model_type": "simple_keyword_extraction",
        "soft_skills_count": len(skill_extractor.soft_skills),
        "hard_skills_count": len(skill_extractor.hard_skills)
    }


if __name__ == "__main__":
    uvicorn.run(
        "simple_api:app",
        host="0.0.0.0", 
        port=6381,
        reload=True
    ) 