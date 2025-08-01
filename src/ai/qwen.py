import json
import os
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import uvicorn

# Константа для кеша модели
CACHE_DIR = "/mnt/kernai_storage02/s.v.sharifulin/model_cache"

# Pydantic модели для request/response
class VacancyRequest(BaseModel):
    body: str


class SkillsResponse(BaseModel):
    soft: List[str]
    hard: List[str]


class QwenSkillExtractor:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.soft_skills = []
        self.hard_skills = []
        self.prompt_template = ""
        self._load_skills_and_prompt()
        
    def _load_skills_and_prompt(self):
        """Загружает навыки и промт из файлов"""
        base_path = Path(__file__).parent.parent
        
        # Загружаем софт-скиллы
        soft_path = base_path / "disco" / "skils" / "soft.txt"
        with open(soft_path, 'r', encoding='utf-8') as f:
            self.soft_skills = [line.strip() for line in f.readlines() if line.strip()]
            
        # Загружаем хард-скиллы
        hard_path = base_path / "disco" / "skils" / "hard.txt"
        with open(hard_path, 'r', encoding='utf-8') as f:
            self.hard_skills = [line.strip() for line in f.readlines() if line.strip()]
            
        # Загружаем промт
        prompt_path = base_path / "ai" / "promt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read().strip()
    
    def _load_model(self):
        """Загружает модель Qwen3-8B"""
        if self.model is None:
            print("Загружаем модель Qwen3-8B...")
            model_name = "Qwen/Qwen3-8B"
            
            # Создаем директорию кеша, если не существует
            cache_dir = Path(CACHE_DIR)
            cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"Кеш модели будет сохранен в: {cache_dir}")
            
            try:
                # Загружаем токенайзер
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    cache_dir=CACHE_DIR
                )
                
                # Загружаем модель
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype="auto",
                    device_map="auto",
                    cache_dir=CACHE_DIR
                )
                
                print(f"Модель загружена успешно")
                
            except Exception as e:
                error_msg = str(e)
                if "Qwen2Tokenizer" in error_msg:
                    print("❌ Ошибка: Устаревшая версия transformers!")
                    print("📋 Решение: Обновите transformers до версии >= 4.51.0")
                    print("🔧 Команда: pip install transformers>=4.51.0 --upgrade")
                    print("🚀 Или запустите: python update_requirements.py")
                elif "Connection" in error_msg or "timeout" in error_msg.lower():
                    print("❌ Ошибка: Проблемы с интернет соединением")
                    print("📋 Проверьте подключение и повторите попытку")
                else:
                    print(f"❌ Ошибка при загрузке модели: {e}")
                raise
    
    def _format_skills_list(self, skills: List[str]) -> str:
        """Форматирует список навыков для промта"""
        return "\n".join(f"- {skill}" for skill in skills)
    
    def _prepare_prompt(self, description: str) -> str:
        """Подготавливает промт с заменой переменных"""
        soft_formatted = self._format_skills_list(self.soft_skills)
        hard_formatted = self._format_skills_list(self.hard_skills)
        
        prompt = self.prompt_template.replace("${description}", description)
        prompt = prompt.replace("${soft}", soft_formatted)
        prompt = prompt.replace("${hard}", hard_formatted)
        
        return prompt
    
    def _parse_model_response(self, response: str) -> Dict[str, List[str]]:
        """Парсит ответ модели и извлекает JSON"""
        try:
            # Ищем JSON в ответе
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("JSON не найден в ответе модели")
            
            json_str = response[start_idx:end_idx + 1]
            result = json.loads(json_str)
            
            # Поддерживаем оба варианта ключей: "soft"/"hard" и "soft_skills"/"hard_skills"
            soft_skills = []
            hard_skills = []
            
            if 'soft' in result and isinstance(result['soft'], list):
                soft_skills = result['soft']
            elif 'soft_skills' in result and isinstance(result['soft_skills'], list):
                soft_skills = result['soft_skills']
            
            if 'hard' in result and isinstance(result['hard'], list):
                hard_skills = result['hard']
            elif 'hard_skills' in result and isinstance(result['hard_skills'], list):
                hard_skills = result['hard_skills']
            
            # Проверяем, что хотя бы один тип навыков найден
            if not soft_skills and not hard_skills:
                raise ValueError("Не найдены навыки в ответе модели")
            
            return {"soft": soft_skills, "hard": hard_skills}
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Ошибка парсинга ответа модели: {e}")
            print(f"Ответ модели: {response}")
            
            # Возвращаем пустой результат в случае ошибки
            return {"soft": [], "hard": []}
    
    def extract_skills(self, description: str) -> Dict[str, List[str]]:
        """Извлекает навыки из описания вакансии"""
        self._load_model()
        
        # Подготавливаем промт
        prompt = self._prepare_prompt(description)
        
        # Формируем сообщения для чата
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Применяем шаблон чата
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False  # Отключаем thinking mode для простоты
        )
        
        # Токенизируем
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        # Генерируем ответ с параметрами для non-thinking mode
        with torch.no_grad():
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=1000,
                temperature=0.7,
                top_p=0.8,
                top_k=20,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Декодируем только новую часть
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        response = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        
        # Парсим результат
        return self._parse_model_response(response)


# Инициализируем экстрактор навыков
skill_extractor = QwenSkillExtractor()

# Создаем FastAPI приложение
app = FastAPI(
    title="Vacancy Skills Extractor API",
    description="API для извлечения навыков из описаний вакансий с помощью Qwen3-8B",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Проверка работоспособности API"""
    return {"message": "Vacancy Skills Extractor API работает"}


@app.post("/api/vacancy", response_model=SkillsResponse)
async def extract_vacancy_skills(request: VacancyRequest):
    """
    Извлекает навыки из описания вакансии
    
    Args:
        request: Объект с описанием вакансии
    
    Returns:
        SkillsResponse: Объект с списками софт и хард навыков
    """
    try:
        if not request.body.strip():
            raise HTTPException(status_code=400, detail="Описание вакансии не может быть пустым")
        
        # Извлекаем навыки
        skills = skill_extractor.extract_skills(request.body)
        
        return SkillsResponse(
            soft=skills.get("soft", []),
            hard=skills.get("hard", [])
        )
        
    except Exception as e:
        print(f"Ошибка при обработке вакансии: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


@app.get("/health")
async def health_check():
    """Проверка состояния модели"""
    try:
        model_loaded = skill_extractor.model is not None
        return {
            "status": "healthy",
            "model_loaded": model_loaded,
            "soft_skills_count": len(skill_extractor.soft_skills),
            "hard_skills_count": len(skill_extractor.hard_skills)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    # Запускаем сервер
    uvicorn.run(
        "qwen:app",
        host="0.0.0.0", 
        port=8000,
        reload=True
    )
