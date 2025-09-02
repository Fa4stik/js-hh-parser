#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API с новым параметром skill
"""

import requests
import json

API_URL = "http://10.230.206.201:6381/api/vacancy"

def test_api_requests():
    """Тестирует API с разными параметрами skill"""
    
    test_description = """
    Требуется разработчик Python с опытом работы с Django, PostgreSQL, Docker.
    Необходимы навыки коммуникации, работы в команде, аналитического мышления.
    Знание JavaScript, React будет плюсом.
    """
    
    print("=== Тестирование API с параметром skill ===\n")
    
    # Тест 1: Запрос всех навыков (без параметра skill)
    print("1. Запрос всех навыков (без параметра skill):")
    payload1 = {"body": test_description}
    try:
        response1 = requests.post(API_URL, json=payload1, headers={"Content-Type": "application/json"})
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"   Hard skills: {result1.get('hard', [])}")
            print(f"   Soft skills: {result1.get('soft', [])}")
        else:
            print(f"   Ошибка: {response1.status_code} - {response1.text}")
    except Exception as e:
        print(f"   Ошибка запроса: {e}")
    
    print()
    
    # Тест 2: Запрос только hard skills
    print("2. Запрос только hard skills:")
    payload2 = {"body": test_description, "skill": "hard"}
    try:
        response2 = requests.post(API_URL, json=payload2, headers={"Content-Type": "application/json"})
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"   Hard skills: {result2.get('hard', [])}")
            print(f"   Soft skills: {result2.get('soft', [])} (должны быть пустые)")
        else:
            print(f"   Ошибка: {response2.status_code} - {response2.text}")
    except Exception as e:
        print(f"   Ошибка запроса: {e}")
    
    print()
    
    # Тест 3: Запрос только soft skills
    print("3. Запрос только soft skills:")
    payload3 = {"body": test_description, "skill": "soft"}
    try:
        response3 = requests.post(API_URL, json=payload3, headers={"Content-Type": "application/json"})
        if response3.status_code == 200:
            result3 = response3.json()
            print(f"   Hard skills: {result3.get('hard', [])} (должны быть пустые)")
            print(f"   Soft skills: {result3.get('soft', [])}")
        else:
            print(f"   Ошибка: {response3.status_code} - {response3.text}")
    except Exception as e:
        print(f"   Ошибка запроса: {e}")
    
    print()
    
    # Тест 4: Неверный параметр skill
    print("4. Тест с неверным параметром skill:")
    payload4 = {"body": test_description, "skill": "invalid"}
    try:
        response4 = requests.post(API_URL, json=payload4, headers={"Content-Type": "application/json"})
        if response4.status_code == 400:
            print(f"   Ожидаемая ошибка 400: {response4.json()}")
        else:
            print(f"   Неожиданный ответ: {response4.status_code} - {response4.text}")
    except Exception as e:
        print(f"   Ошибка запроса: {e}")
    
    print("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    test_api_requests() 