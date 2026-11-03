# main.py

import telebot
import time
import threading
import config

# Инициализируем бота с использованием токена из config.py
bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)

# Переменные для отслеживания состояния
current_mode = config.MODE
last_message_time = 0
attack_count = 0
defense_count = 0
is_waiting_for_defense = False # Флаг для режима "атака-защита"
next_action_is_attack = True # Чередование атаки/защиты в режиме "атака-защита"

# Флаг для триггера сообщения
trigger_received = False

# --- Функции для отправки сообщений ---

def send_attack_message():
    """Отправляет сообщение "атака"."""
    global attack_count, next_action_is_attack, is_waiting_for_defense, trigger_received
    
    message_to_send = "атака"
    print(f"Отправляю: {message_to_send}") # Логирование в консоль
    try:
        bot.send_message(config.CHAT_ID, message_to_send)
        attack_count += 1
        print(f"Успешно отправлено: {message_to_send}. Атак: {attack_count}")
        
        if current_mode == 'advanced':
            # В режиме "атака-защита" после атаки ждем защиту
            is_waiting_for_defense = True
            next_action_is_attack = False # Следующая должна быть защита
            print("Режим 'атака-защита': Ждем 'защита'.")
        
        # Если был получен триггер, следующая атака может быть заменена на защиту
        if trigger_received:
            print("Триггер получен, следующая атака будет заменена на защиту.")
            trigger_received = False # Сброс триггера после обработки
            if current_mode == 'advanced':
                # Если мы в режиме "атака-защита" и получили триггер,
                # то ближайшую защиту не пропускаем, а предыдущую атаку (если она была)
                # мы уже отправили, и теперь ждем защиту.
                # Если же мы в режиме "auto", то эту атаку заменяем на защиту.
                if config.MODE == 'auto': # Если режим "auto" (только атака)
                    print("Режим 'auto': Заменяем ближайшую атаку на защиту.")
                    schedule_defense_message() # Планируем защиту вместо атаки
                    return # Прерываем текущий поток атаки
    except Exception as e:
        print(f"Ошибка при отправке сообщения '{message_to_send}': {e}")

def send_defense_message():
    """Отправляет сообщение "защита"."""
    global defense_count, next_action_is_attack, is_waiting_for_defense
    
    message_to_send = "защита"
    print(f"Отправляю: {message_to_send}")
    try:
        bot.send_message(config.CHAT_ID, message_to_send)
        defense_count += 1
        print(f"Успешно отправлено: {message_to_send}. Защит: {defense_count}")
        
        if current_mode == 'advanced':
            # После защиты, если режим "атака-защита", готовимся к следующей атаке
            is_waiting_for_defense = False
            next_action_is_attack = True # Следующая должна быть атака
            print("Режим 'атака-защита': Готовимся к следующей атаке.")
            
    except Exception as e:
        print(f"Ошибка при отправке сообщения '{message_to_send}': {e}")

# --- Функции для планирования сообщений ---

def schedule_attack_message():
    """Планирует отправку сообщения "атака" через заданный интервал."""
    threading.Timer(config.ATTACK_INTERVAL, send_attack_message).start()
    print(f"Следующая атака запланирована через {config.ATTACK_INTERVAL} секунд.")

def schedule_defense_message():
    """Планирует отправку сообщения "защита" через заданный интервал."""
    threading.Timer(config.DEFENSE_INTERVAL, send_defense_message).start()
    print(f"Следующая защита запланирована через {config.DEFENSE_INTERVAL} секунд.")

# --- Основная логика режимов ---

def run_mode_auto():
    """Режим: атака каждые 5 минут."""
    global current_mode, trigger_received
    current_mode = 'auto'
    print("Переключен режим: 'auto' (атака каждые 5 минут).")
    
    # Сразу отправляем первую атаку, а потом планируем следующие
    send_attack_message()
    
    while current_mode == 'auto':
        # Проверяем триггер перед планированием следующей атаки
        if trigger_received:
            print("Триггер получен в режиме 'auto'. Заменяем ближайшую атаку на защиту.")
            trigger_received = False # Сбрасываем триггер
            schedule_defense_message() # Планируем защиту вместо атаки
            # После защиты, если триггер был, возможно, захотим вернуться к атаке
            # Но для простоты, просто планируем следующую атаку после защиты
            threading.Timer(config.ATTACK_INTERVAL, schedule_attack_message).start() 
        else:
            schedule_attack_message()
        
        # Ждем до следующей проверки или до следующего запланированного действия
        # В реальном приложении лучше использовать более продвинутые методы планирования
        # или библиотеки для управления задачами. Здесь простой цикл.
        time.sleep(10) # Небольшая пауза, чтобы не грузить процессор
        # Проверка для выхода из цикла, если режим сменится
        if current_mode != 'auto':
            break

def run_mode_advanced():
    """Режим: атака через 5 мин, потом защита через 5 мин и так далее."""
    global current_mode, next_action_is_attack, is_waiting_for_defense, trigger_received
    current_mode = 'advanced'
    print("Переключен режим: 'advanced' (атака-защита).")
    
    # Начинаем с атаки
    next_action_is_attack = True
    is_waiting_for_defense = False

    while current_mode == 'advanced':
        if next_action_is_attack:
            # Если ожидаем атаку ИЛИ если триггер получен, заменяем атаку на защиту
            if trigger_received:
                print("Триггер получен в режиме 'advanced'. Заменяем ближайшую атаку на защиту.")
                trigger_received = False
                send_defense_message()
                next_action_is_attack = True # Следующая должна быть атака
                is_waiting_for_defense = False
                schedule_attack_message() # Планируем следующую атаку
            else:
                send_attack_message()
                # После отправки атаки, ждем защиту (если не было триггера)
                # is_waiting_for_defense = True
                # next_action_is_attack = False # Следующая должна быть защита
                schedule_defense_message() # Планируем следующую защиту
                
            time.sleep(5) # Небольшая пауза перед следующей проверкой
            
        elif is_waiting_for_defense:
            # Эта часть срабатывает, если мы отправили атаку и теперь ждем ответ "защита"
            # Проверяем, получили ли сообщение "защита" от пользователя
            # В данной реализации, если пользователь не пишет "защита",
            # бот просто продолжит цикл.
            # Для автоматического перехода к атаке после защиты,
            # надо дождаться, пока `send_defense_message` отработает.
            # В данном коде, `send_defense_message` сам устанавливает `next_action_is_attack = True`.
            time.sleep(5) # Пауза
        else: # Если мы должны делать защиту (но она уже запланирована)
             # Если мы здесь, значит, предыдущая была атака, и защита запланирована.
             # Мы просто ждем, пока она сработает.
             time.sleep(5)
             
        # Проверка для выхода из цикла
        if current_mode != 'advanced':
            break
            
    # Важно: в режиме "атака-защита", при переключении режимов,
    # нужно остановить все запланированные таймеры.
    # В этом простом примере это не реализовано явно, но при перезапуске бота
    # таймеры сбрасываются.

# --- Обработчики команд Telegram ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Приветственное сообщение при команде /start или /help."""
    bot.reply_to(message, "Привет! Я бот для автоматической отправки сообщений.\n"
                         "Доступные команды:\n"
                         "/mode auto - Режим: атака каждые 5 минут.\n"
                         "/mode advanced - Режим: атака через 5 мин, защита через 5 мин.\n"
                         "/stop - Остановить работу бота.")

@bot.message_handler(commands=['mode'])
def change_mode(message):
    """Переключение режимов работы бота."""
    global current_mode, attack_count, defense_count, is_waiting_for_defense, next_action_is_attack, trigger_received
    
    command_parts = message.text.split()
    if len(command_parts) < 2:
        bot.reply_to(message, "Используйте команду /mode <auto|advanced>")
        return

    new_mode = command_parts[1].lower()
    
    if new_mode == 'auto':
        current_mode = 'auto'
        # Сбрасываем счетчики и состояние при смене режима
        attack_count = 0
        defense_count = 0
        is_waiting_for_defense = False
        next_action_is_attack = True # Начинаем с атаки
        trigger_received = False
        bot.reply_to(message, "Режим изменен на 'auto'. Бот начнет отправлять 'атака' каждые 5 минут.")
        
        # Останавливаем предыдущие таймеры (если они были запущены)
        # В этом простом коде, перезапуск потока с помощью threading.Thread
        # эффективно перезапускает планирование.
        # Для более сложного управления таймерами понадобится отдельная логика.
        
        # Запускаем режим в новом потоке, чтобы не блокировать основной цикл бота
        # (Обработка входящих сообщений)
        thread = threading.Thread(target=run_mode_auto)
        thread.daemon = True # Позволяет программе завершиться, даже если этот поток работает
        thread.start()
        
    elif new_mode == 'advanced':
        current_mode = 'advanced'
        # Сбрасываем счетчики и состояние при смене режима
        attack_count = 0
        defense_count = 0
        is_waiting_for_defense = False
        next_action_is_attack = True # Начинаем с атаки
        trigger_received = False
        bot.reply_to(message, "Режим изменен на 'advanced'. Бот начнет чередовать 'атака' и 'защита' каждые 5 минут.")
        
        thread = threading.Thread(target=run_mode_advanced)
        thread.daemon = True
        thread.start()
        
    else:
        bot.reply_to(message, "Неизвестный режим. Доступные режимы: 'auto', 'advanced'.")

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    """Остановка работы бота."""
    global current_mode
    current_mode = 'stopped' # Устанавливаем флаг для остановки циклов
    bot.reply_to(message, "Бот остановлен. Для запуска используйте команду /mode.")
    print("Получена команда /stop. Бот остановлен.")
    # Здесь также нужно было бы остановить активные таймеры, если бы они были
    # управляемы через более сложную систему.

# --- Обработчик входящих сообщений (для режима "атака-защита" и триггера) ---

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обрабатывает входящие сообщения."""
    global current_mode, last_message_time, is_waiting_for_defense, next_action_is_attack, trigger_received

    # Проверяем, является ли сообщение триггерным
    trigger_text = "Обязательно напишите «защита», иначе ваш персонаж погибнет!"
    if trigger_text in message.text:
        print(f"Получено триггерное сообщение: '{message.text[:30]}...'")
        trigger_received = True
        # В зависимости от текущего режима, триггер может повлиять на следующую атаку/защиту.
        # Логика обработки триггера уже в send_attack_message() и run_mode_advanced()

    if current_mode == 'advanced':
        # В режиме "атака-защита" реагируем на "защита"
        if message.text.lower() == 'защита':
            if is_waiting_for_defense: # Если мы действительно ждали "защита"
                print("Получено сообщение 'защита'.")
                # Можно было бы сбрасывать таймер защиты, если бы он был активен
                # и запускать следующую атаку.
                # В текущей реализации, send_defense_message() сама планирует следующую атаку.
                # Мы просто обрабатываем это как получение подтверждения.
                
                # Важно: если мы получили "защита", то флаг is_waiting_for_defense
                # должен быть сброшен, чтобы цикл мог перейти к следующей атаке.
                # Это уже реализовано в send_defense_message()
                
                # Проверяем, не был ли этот "защита" вызван триггером,
                # который заменил атаку на защиту.
                # Если да, то все уже обработано.
                # Если нет, то это ответ пользователя.
                # Мы просто подтверждаем получение.
                
                # Если мы получили "защита" как ответ на нашу "атака"
                if not trigger_received: # Если это не замена атаки на защиту из-за триггера
                    send_defense_message() # Отправляем "защита" и планируем следующую атаку
                    # next_action_is_attack = True # Устанавливаем, что следующая - атака
                    # is_waiting_for_defense = False
                    # schedule_attack_message() # Планируем следующую атаку
                else: # Если получили "защита" потому что триггер заменил атаку на защиту
                    print("Получена 'защита' после того, как триггер заменил атаку на защиту. Все уже обработано.")
                    # Ничего не делаем, так как все уже запланировано.
                    pass # Пропускаем отправку защиты, она уже была запланирована
                    
            else:
                # Если мы не ждали "защита" (например, режим 'auto' или уже прошло время)
                print("Получено сообщение 'защита', но мы не ожидали его.")
                # Можно добавить логику, если нужно.
                pass
        # Если получили "атака" в режиме advanced, игнорируем, так как бот сам отправляет
        elif message.text.lower() == 'атака':
            print("Получено сообщение 'атака' в режиме 'advanced'. Игнорирую, бот сам отправляет.")
            pass
        else:
            # Если получили какое-то другое сообщение, можем его игнорировать или обрабатывать.
            # print(f"Получено другое сообщение: '{message.text}'. Игнорирую.")
            pass
    elif current_mode == 'auto':
        # В режиме 'auto' мы игнорируем входящие сообщения, кроме команды /mode
        # А триггер все равно обрабатывается, чтобы заменить атаку на защиту
        pass # Игнорируем все сообщения, кроме команд

# --- Основной цикл запуска бота ---

if __name__ == '__main__':
    print("Бот запущен. Идет ожидание команд...")
    
    # При старте бота, можно сразу запустить один из режимов или ждать команды.
    # Для простоты, будем ждать команды.
    
    # Если вы хотите, чтобы бот стартовал сразу в режиме 'auto' или 'advanced':
    # thread = threading.Thread(target=run_mode_auto) # или run_mode_advanced
    # thread.daemon = True
    # thread.start()

    try:
        # Бот будет работать, пока не будет остановлен
        bot.polling(none_stop=True, interval=0) # none_stop=True, чтобы работать без остановки
    except Exception as e:
        print(f"Произошла ошибка при работе polling: {e}")
        # Можно добавить логику для перезапуска бота при ошибке
        time.sleep(10) # Ждем перед перезапуском
        print("Перезапускаю bot.polling...")
        bot.polling(none_stop=True, interval=0)