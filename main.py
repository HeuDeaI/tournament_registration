import telebot
import os
import sqlite3
import json
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(API_TOKEN)

def get_teams():
    connection = sqlite3.connect('teams.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM teams')
    rows = cursor.fetchall()
    connection.close()
    teams = []
    for row in rows:
        teams.append({
            "id": row[0],
            "number": row[1],
            "captain": row[2],
            "members": json.loads(row[3])
        })
    return teams

teams = get_teams()
current_team_number = 0

def redirect_message(message, redirect_text):
    sent_message = bot.send_message(message.chat.id, redirect_text, reply_markup=ReplyKeyboardRemove())  
    bot.delete_message(message.chat.id, sent_message.id)

@bot.message_handler(commands=['start'])
def choose_action(message):
    redirect_message(message, "Перемещение в главное меню...")
    reply_markup = ReplyKeyboardMarkup(row_width=1)
    join_team = KeyboardButton("👥 Присоедениться к команде")
    view_teams = KeyboardButton("👀 Посмотреть список всех команд")
    my_team = KeyboardButton("🧑‍💻 Моя команда")
    reply_markup.add(join_team, view_teams, my_team)
    bot.send_message(message.chat.id, "📍 Главное меню: ", reply_markup=reply_markup)

@bot.message_handler(func=lambda message: message.text.strip() in ["👥 Присоедениться к команде", "👀 Посмотреть список всех команд", "⛔ Нет, вернуться назад"])
def handle_action(message):
    redirect_message(message, "Формируем список команд...")
    if message.text == "👥 Присоедениться к команде" or message.text == "⛔ Нет, вернуться назад":
        markup = InlineKeyboardMarkup()
        for i, team in enumerate(teams):
            team_name = f"{team['number']} Команда: {team['captain']}" if team['captain'] else f"{team['number']} Пустая команда"
            markup.add(InlineKeyboardButton(team_name, callback_data=f"team{i+1}"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
        bot.send_message(message.chat.id, "👇 Выберите команду: ", reply_markup=markup)
    elif message.text == "👀 Посмотреть список всех команд":
        team_list = "Список всех команд: \n\n"
        for team in teams:
            if team['members']:
                members_list = "\n".join([f"{i+1}. {member}" for i, member in enumerate(team['members'])])
            else:
                members_list = "Пусто 🤷‍♂️"   
            team_list += f"{team['number']} Команда:\n{members_list} \n\n"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
        bot.send_message(message.chat.id, team_list, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def choose_action_callback(call):
    choose_action(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('team'))
def handle_team_selection(call):
    redirect_message(call.message, "Формируем список участников команды...")
    global current_team_number
    current_team_number = int(call.data.replace('team', '')) - 1
    team = teams[current_team_number]
    if team['members']:
        members_list = "\n".join([f"{i+1}. {member}" for i, member in enumerate(team['members'])])
    else:
        members_list = "Пусто 🤷‍♂️"
    team_members_message = f"{team['number']} Команда:\n{members_list} \n\nВы действительно хотите присоедниться к команде?"
    reply_markup = ReplyKeyboardMarkup(row_width=1)
    join_team = KeyboardButton("👌 Да, присоедениться!")
    view_teams = KeyboardButton("⛔ Нет, вернуться назад")
    reply_markup.add(join_team, view_teams)
    bot.answer_callback_query(call.id, team_members_message)
    bot.send_message(call.message.chat.id, team_members_message, reply_markup=reply_markup)

def user_exists_in_any_team(user):
    teams = get_teams()
    for team in teams:
        if user in team['members']:
            return True
    return False

@bot.message_handler(func=lambda message: message.text == "👌 Да, присоедениться!")
def join_team(message):
    redirect_message(message, "Добавляем вас в команду...")
    if message.from_user.username:
        user = "@" + message.from_user.username
    else: 
        user = message.from_user.first_name + message.from_user.last_name

    user_in_team = user_exists_in_any_team(user)
    
    if user_in_team:
        bot.send_message(message.chat.id, "Вы уже в одной из команд!")
    else:
        team = teams[current_team_number]
        print(current_team_number)
        if user not in team['members']:
            team['members'].append(user)
            connection = sqlite3.connect('teams.db')
            cursor = connection.cursor()
            cursor.execute('UPDATE teams SET members = ? WHERE id = ?', (json.dumps(team['members']), team['id']))
            connection.commit()
            connection.close()
            bot.send_message(message.chat.id, "Вы успешно присоединились к команде!")
        else:
            bot.send_message(message.chat.id, "Вы уже в этой команде!")



bot.infinity_polling()
