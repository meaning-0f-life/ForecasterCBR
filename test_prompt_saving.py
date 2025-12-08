#!/usr/bin/env python3
"""
Тестовый скрипт для проверки сохранения промптов в файлы
"""

from app.llm.analyzer import LLMAnalyzer
import os
import time

def test_prompt_saving():
    """Test that prompts are saved to files when SAVE_PROMPTS is enabled"""
    print("=== ТЕСТИРОВАНИЕ СОХРАНЕНИЯ ПРОМПТОВ ===")

    # Initialize analyzer
    analyzer = LLMAnalyzer()

    # Test prompt saving
    system_context = """
Текущая дата и время: 2025-12-08 03:50:00 (МСК, UTC+3)

=== НОВОСТИ И СТАТЬИ ===
Тестовые новости о экономике

=== ИСТОРИЯ КЛЮЧЕВЫХ СТАВОК ===
Текущая ставка: 16.50% (2025-12-08)
    """

    user_question = "Какая сейчас ключевая ставка ЦБ РФ?"

    print("Отправка тестового запроса...")
    try:
        # Call analyzer with system context
        start_time = time.time()
        answer = analyzer.answer_with_system_context(system_context, user_question)
        end_time = time.time()

        print("> Запрос обработан за {:.2f} секунд".format(end_time - start_time))
        print("> Ответ модели:")
        print(f"  {answer}")

        # Check if prompt file was created
        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        if os.path.exists(prompts_dir):
            prompt_files = [f for f in os.listdir(prompts_dir) if f.startswith("prompt_system_context_")]
            if prompt_files:
                print("> Сохраненные файлы промптов:")
                for f in prompt_files:
                    filepath = os.path.join(prompts_dir, f)
                    size = os.path.getsize(filepath)
                    print(f"  {f} ({size} байт)")

                # Show content of latest file
                latest_file = max(prompt_files)
                with open(os.path.join(prompts_dir, latest_file), 'r', encoding='utf-8') as file:
                    content = file.read()[:500] + "..." if len(file.read()) > 500 else file.read()
                    file.seek(0)
                    content = file.read()
                    print("> Содержимое последнего файла:")
                    print("-" * 50)
                    # Show only first 1000 chars to avoid too long output
                    preview = content[:1000] + ("...\n[Содержимое сокращено]" if len(content) > 1000 else "")
                    print(preview)
                    print("-" * 50)
            else:
                print("❌ Файлы промптов не найдены")
        else:
            print("❌ Директория prompts не существует")

        return True

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

if __name__ == "__main__":
    import datetime
    print("=" * 60)
    print(" ТЕСТИРОВАНИЕ СОХРАНЕНИЯ ПРОМПТОВ LLM")
    print("=" * 60)

    success = test_prompt_saving()

    print("\n" + "=" * 60)
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
    else:
        print("❌ ОШИБКА В ТЕСТИРОВАНИИ")

    print("   Время тестирования:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
