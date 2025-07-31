import requests
import json


def test_api():
    """Тестирует работу API для извлечения навыков"""
    
    base_url = "http://localhost:8000"
    
    # Тестовые описания вакансий
    test_vacancies = [
        "Ищем Python разработчика с опытом работы с FastAPI, Django. Требуется умение работать в команде, аналитическое мышление и знание SQL.",
        "Нужен frontend разработчик со знанием React, JavaScript, HTML/CSS. Важны коммуникативные навыки и креативность.",
        "Требуется DevOps инженер с опытом работы с Docker, Kubernetes, Linux. Необходимы навыки решения проблем и самоорганизации."
    ]
    
    print("🚀 Тестирование API для извлечения навыков\n")
    
    # Проверяем доступность API
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ API доступно: {response.json()['message']}")
    except requests.exceptions.ConnectionError:
        print("❌ API недоступно. Убедитесь, что сервер запущен на порту 8000")
        return
    
    # Проверяем health endpoint
    try:
        health_response = requests.get(f"{base_url}/health")
        health_data = health_response.json()
        print(f"📊 Состояние: {health_data['status']}")
        print(f"📈 Загружено софт-навыков: {health_data['soft_skills_count']}")
        print(f"📈 Загружено хард-навыков: {health_data['hard_skills_count']}\n")
    except Exception as e:
        print(f"⚠️ Ошибка при проверке health: {e}\n")
    
    # Тестируем основной endpoint
    for i, vacancy_text in enumerate(test_vacancies, 1):
        print(f"🔍 Тест {i}: Анализ вакансии")
        print(f"📝 Описание: {vacancy_text[:100]}...")
        
        try:
            response = requests.post(
                f"{base_url}/api/vacancy",
                json={"body": vacancy_text},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Софт-навыки ({len(result['soft'])}): {', '.join(result['soft'][:5])}{'...' if len(result['soft']) > 5 else ''}")
                print(f"✅ Хард-навыки ({len(result['hard'])}): {', '.join(result['hard'][:5])}{'...' if len(result['hard']) > 5 else ''}")
            else:
                print(f"❌ Ошибка {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка при запросе: {e}")
        
        print("-" * 80)
    
    # Тест с пустым описанием
    print("🧪 Тест с пустым описанием")
    try:
        response = requests.post(
            f"{base_url}/api/vacancy",
            json={"body": ""},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            print("✅ Правильно обработана ошибка валидации")
        else:
            print(f"❌ Неожиданный ответ: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при тесте валидации: {e}")


if __name__ == "__main__":
    test_api() 