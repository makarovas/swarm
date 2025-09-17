#!/usr/bin/env python3
"""
Скрипт для запуска примеров системы роевого программирования
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

def print_menu():
    """Вывод меню выбора примеров"""
    print("🤖 Система агентного роевого программирования")
    print("=" * 50)
    print("Выберите пример для запуска:")
    print()
    print("1. Базовое использование роя")
    print("2. Коллективное принятие решений")
    print("3. Продвинутый сценарий разработки")
    print("4. Запустить все примеры подряд")
    print("0. Выход")
    print()


async def run_basic_swarm():
    """Запуск базового примера"""
    print("🚀 Запуск базового примера...")
    try:
        from examples.basic_swarm import main
        await main()
    except Exception as e:
        print(f"❌ Ошибка при запуске базового примера: {e}")


async def run_collective_decisions():
    """Запуск примера коллективных решений"""
    print("🧠 Запуск примера коллективных решений...")
    try:
        from examples.collective_decision_making import main
        await main()
    except Exception as e:
        print(f"❌ Ошибка при запуске примера коллективных решений: {e}")


async def run_advanced_programming():
    """Запуск продвинутого примера"""
    print("🏗️ Запуск продвинутого примера...")
    try:
        from examples.advanced_swarm_programming import main
        await main()
    except Exception as e:
        print(f"❌ Ошибка при запуске продвинутого примера: {e}")


async def run_all_examples():
    """Запуск всех примеров подряд"""
    print("🔄 Запуск всех примеров подряд...")
    print()
    
    examples = [
        ("Базовый пример", run_basic_swarm),
        ("Коллективные решения", run_collective_decisions),
        ("Продвинутый сценарий", run_advanced_programming)
    ]
    
    for name, example_func in examples:
        print(f"\n{'='*60}")
        print(f"🎯 Запуск: {name}")
        print('='*60)
        
        try:
            await example_func()
            print(f"✅ {name} завершен успешно")
        except Exception as e:
            print(f"❌ Ошибка в {name}: {e}")
            
        print("\n" + "⏱️ " * 20)
        print("Пауза 3 секунды перед следующим примером...")
        await asyncio.sleep(3)
        
    print("\n🎉 Все примеры завершены!")


def check_dependencies():
    """Проверка зависимостей"""
    try:
        import swarm
        return True
    except ImportError:
        print("❌ Модуль swarm не найден!")
        print("Убедитесь, что вы находитесь в правильной директории")
        print("и установили все зависимости: pip install -r requirements.txt")
        return False


async def main():
    """Главная функция"""
    
    if not check_dependencies():
        return
        
    while True:
        print_menu()
        
        try:
            choice = input("Введите номер примера (0-4): ").strip()
            
            if choice == "0":
                print("👋 До свидания!")
                break
            elif choice == "1":
                await run_basic_swarm()
            elif choice == "2":
                await run_collective_decisions()
            elif choice == "3":
                await run_advanced_programming()
            elif choice == "4":
                await run_all_examples()
            else:
                print("❌ Неверный выбор. Попробуйте снова.")
                
        except KeyboardInterrupt:
            print("\n⏹️ Прервано пользователем")
            break
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            
        if choice in ["1", "2", "3", "4"]:
            input("\n📋 Нажмите Enter для возврата в меню...")
            print("\n" * 3)  # Очистка экрана


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа завершена")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
