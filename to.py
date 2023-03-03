import telebot
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from aiogram import types
import nest_asyncio
import logging
import random
import time
import urllib.request
nest_asyncio.apply()
import json
import numpy as np
from datetime import date
import datetime
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import aiogram.utils.markdown as md
import mysql.connector as mariadb
from mysql.connector import Error
bot = Bot(token="5788754560:AAGI-nyBFJmSxr8GfcaLIBJ3k8kTtBzHiDA")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)
connection = mariadb.connect(user = 'pyuser', password = '8i5eki', database = 'TO', host = 'localhost', port = '4727')
curs = connection.cursor(buffered=True)

class Name(StatesGroup):
    name = State()
    
class ID(StatesGroup):
    pr_id = State()

class exterminate(StatesGroup):
    ex = State()

class problem(StatesGroup):
    pr = State()
    
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message): 
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    query = f"SELECT ФИО FROM to.users WHERE UserID = {message.from_user.id}"
    curs.execute(query)
    tmp = curs.fetchall()
    if tmp == []:
        buttons = ["Пройти регистрацию"]
        keyboard.add(*buttons)
        await message.answer('Добро пожаловать, я — бот-менеджер проблем компании. Похоже, Вы тут впервые. Чтобы приступить к работе, пройдите процедуру регистрации.', reply_markup=keyboard)
    else:
        buttons = ["Начать работу"]
        keyboard.add(*buttons)
        await message.answer(f'Здравствуйте, {tmp[0][0]}', reply_markup=keyboard)
    
@dp.message_handler(lambda message: message.text == "Пройти регистрацию")
async def reg(message: types.Message):
    await Name.name.set()
    await message.answer(f"Введите свое ФИО:")
    
@dp.message_handler(state=Name.name)
async def wr(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
        user_message = data['text']
        query = f"SELECT COUNT(*) FROM to.users"
        curs.execute(query)
        ident = curs.fetchone()[0]
        query = f"INSERT INTO to.users (UserID, ID, ФИО) VALUES ('{message.from_user.id}', '{ident}', '{user_message}')"
        curs.execute(query)
        connection.commit()
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Директор", "Заместитель директора", "Подчиненный директора", "Сотрудник"]
    keyboard.add(*buttons)
    await message.answer("Теперь выберите свою роль:", reply_markup=keyboard)   
    
@dp.message_handler(lambda message: message.text in ["Директор", "Заместитель директора", "Подчиненный директора", "Сотрудник"])
async def wr(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Начать работу"]
    keyboard.add(*buttons)
    query = f"UPDATE to.users SET Роль = '{message.text}' WHERE (UserID) = ({message.from_user.id})"
    curs.execute(query)
    connection.commit()
    await message.answer("Вы зарегистрированы!", reply_markup=keyboard)  
  
@dp.message_handler(lambda message: message.text in ["Начать работу", "Назад"])
async def wr(message: types.Message, state: FSMContext):
    query = f"SELECT Роль FROM to.users WHERE UserID = ({message.from_user.id})"
    curs.execute(query)
    tmp = curs.fetchone()[0]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Список проблем", "Сообщить о проблеме", "Проверить статус проблемы"] if tmp != "Сотрудник" else ["Сообщить о проблеме", "Проверить статус проблемы"]
    keyboard.add(*buttons)
    await message.answer("Выберите действие: ", reply_markup=keyboard)
    
@dp.message_handler(lambda message: message.text == "Список проблем")
async def wr(message: types.Message, state: FSMContext):
    query = f"SELECT Роль FROM to.users WHERE UserID = ({message.from_user.id})"
    curs.execute(query)
    role = curs.fetchone()[0]
    query = f"SELECT Проблема, Статус FROM to.problems_list"
    curs.execute(query)
    tmp = curs.fetchall()
    fulf = str("Выполнены:\n" + "".join([i[0]+"\n" for i in tmp if i[1] == 1]))
    proc = str("В процессе:\n" + "".join([i[0]+"\n" for i in tmp if i[1] == 2]))
    nfulf = str("Не выполнены:\n" + "".join([i[0]+"\n" for i in tmp if i[1] == 0]))
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Изменить статус проблемы", "Удалить проблему", "Назад"] if role in ["Директор", "Заместитель директора"] else ["Изменить статус проблемы", "Назад"]
    keyboard.add(*buttons)
    await message.answer(f"{fulf}\n{proc}\n{nfulf}", reply_markup=keyboard)
    
@dp.message_handler(lambda message: message.text == "Изменить статус проблемы")
async def wr(message: types.Message, state: FSMContext):
    query = f"SELECT ID, Проблема, Статус FROM to.problems_list"
    curs.execute(query)
    tmp = curs.fetchall()
    fulf = str("Выполнены:\n" + "".join([str(i[0]) + ". " + i[1]+"\n" for i in tmp if i[2] == 1]))
    proc = str("В процессе:\n" + "".join([str(i[0]) + ". " + i[1]+"\n" for i in tmp if i[2] == 2]))
    nfulf = str("Не выполнены:\n" + "".join([str(i[0]) + ". " + i[1]+"\n" for i in tmp if i[2] == 0]))
    await ID.pr_id.set()
    await message.answer(f"{fulf}\n{proc}\n{nfulf}\n\nВыберите номер проблемы, статус которой хотите изменить:")

@dp.message_handler(state=ID.pr_id)
async def wr(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
        global pr_ident  
        pr_ident = data['text']
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Выполнена", "В процессе", "Не выполнена"]
    keyboard.add(*buttons)
    await message.answer("Теперь выберите статус проблемы:", reply_markup=keyboard)  

@dp.message_handler(lambda message: message.text in ["Не выполнена","Выполнена", "В процессе"])
async def wr(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Назад"]
    keyboard.add(*buttons)
    st = ["Не выполнена","Выполнена", "В процессе"]
    query = f"UPDATE to.problems_list SET Статус = '{st.index(message.text)}' WHERE (ID) = ({pr_ident})"
    curs.execute(query)
    connection.commit()
    await message.answer("Выполнено!", reply_markup=keyboard) 
   
@dp.message_handler(lambda message: message.text == "Удалить проблему")
async def wr(message: types.Message, state: FSMContext):
    query = f"SELECT ID, Проблема, Статус FROM to.problems_list"
    curs.execute(query)
    tmp = curs.fetchall()
    fulf = str("Выполнены:\n" + "".join([str(i[0]) + ". " + i[1]+"\n" for i in tmp if i[2] == 1]))
    proc = str("В процессе:\n" + "".join([str(i[0]) + ". " + i[1]+"\n" for i in tmp if i[2] == 2]))
    nfulf = str("Не выполнены:\n" + "".join([str(i[0]) + ". " + i[1]+"\n" for i in tmp if i[2] == 0]))
    await exterminate.ex.set()
    await message.answer(f"{fulf}\n{proc}\n{nfulf}\n\nВыберите номер проблемы, которую хотите удалить:") 

@dp.message_handler(state=exterminate.ex)
async def wr(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
        message_text = data['text']
    await state.finish()
    query = f"DELETE FROM to.problems_list WHERE (ID) = ({message_text})"
    curs.execute(query)
    connection.commit()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Назад"]
    keyboard.add(*buttons)
    await message.answer("Выполнено!", reply_markup=keyboard)  
    
@dp.message_handler(lambda message: message.text == "Сообщить о проблеме")
async def wr(message: types.Message, state: FSMContext):
    await problem.pr.set()
    await message.answer(f"Опишите свою проблему:") 
    
@dp.message_handler(state=problem.pr)
async def wr(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
        message_text = data['text']
        query = f"SELECT COUNT(*) FROM to.problems_list"
        curs.execute(query)
        ident = curs.fetchone()[0]
        query = f"INSERT INTO to.problems_list (ID, Проблема, ID_автора, Статус) VALUES ('{ident}', '{message_text}', '{message.from_user.id}',  '{0}')"
        curs.execute(query)
        connection.commit()
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Назад"]
    keyboard.add(*buttons)
    await message.answer("Проблема принята!", reply_markup=keyboard)   
    
    
@dp.message_handler(lambda message: message.text == "Проверить статус проблемы")
async def wr(message: types.Message, state: FSMContext):
    query = f"SELECT Проблема, ID_автора, Статус FROM to.problems_list"
    curs.execute(query)
    tmp = curs.fetchall()
    tmp = [i for i in tmp if i[1] == message.from_user.id]
    fulf = str("Выполнены:\n" + "".join([i[0]+"\n" for i in tmp if i[2] == 1]))
    proc = str("В процессе:\n" + "".join([i[0]+"\n" for i in tmp if i[2] == 2]))
    nfulf = str("Не выполнены:\n" + "".join([i[0]+"\n" for i in tmp if i[2] == 0]))
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Назад"]
    keyboard.add(*buttons)
    await message.answer(f"{fulf}\n{proc}\n{nfulf}\n\n", reply_markup=keyboard)   
    
    
if __name__ == "__main__":
    executor.start_polling(dp)
