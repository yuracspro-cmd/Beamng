import streamlit as st
import sqlite3
import pandas as pd
import os

# Настройка страницы
st.set_page_config(page_title="BeamNG RP Portal", page_icon="🚗", layout="wide")

DB_NAME = "beamng_rp.db"

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, balance INTEGER, job TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS garage 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, car_name TEXT, mod_link TEXT, pc_filename TEXT, pc_data BLOB, photo_url TEXT, owner TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Боковая панель навигации
st.sidebar.title("🎮 BeamNG.mp RP")
page = st.sidebar.radio("Разделы", ["🚗 Виртуальный Гараж", "💰 Игроки и Балансы", "➕ Добавить машину", "👑 Панель Админа"])

# --- СТРАНИЦА 1: ВИРТУАЛЬНЫЙ ГАРАЖ ---
if page == "🚗 Виртуальный Гараж":
    st.title("🚗 Виртуальный Гараж")
    st.write("Качайте моды и конфигурации (.pc) для игры на сервере!")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, owner FROM garage")
    cars = c.fetchall()
    conn.close()

    if not cars:
        st.info("В гараже пока нет машин. Добавьте первую во вкладке 'Добавить машину'!")
    else:
        # Отображаем машины сеткой по 3 в ряд
        cols = st.columns(3)
        for idx, car in enumerate(cars):
            car_id, name, mod_link, pc_filename, pc_data, photo_url, owner = car
            col = cols[idx % 3]
            
            with col:
                st.subheader(name)
                if photo_url:
                    st.image(photo_url, use_column_width=True)
                st.caption(f"Владелец: {owner}")
                
                st.markdown(f"🔗 [Скачать мод]({mod_link})")
                
                # Кнопка скачивания .pc файла
                st.download_button(
                    label=f"📥 Скачать {pc_filename}",
                    data=pc_data,
                    file_name=pc_filename,
                    mime="text/plain",
                    key=f"dl_{car_id}"
                )
                st.markdown("---")

# --- СТРАНИЦА 2: БАЛАНСЫ И ИГРОКИ ---
elif page == "💰 Игроки и Балансы":
    st.title("💰 Экономика и Список Игроков")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT username AS 'Имя игрока', balance AS 'Баланс ($)', job AS 'Работа' FROM users", conn)
    conn.close()
    
    if df.empty:
        st.info("Игроков пока нет.")
    else:
        st.dataframe(df, use_container_width=True)

# --- СТРАНИЦА 3: ДОБАВЛЕНИЕ МАШИНЫ ---
elif page == "➕ Добавить машину":
    st.title("➕ Добавление авто в общий гараж")
    
    with st.form("add_car_form"):
        car_name = st.text_input("Название машины (например, Gavril D-Series Stance)")
        owner = st.text_input("Ваш никнейм в игре")
        mod_link = st.text_input("Ссылка на мод (ModLand, Drive и т.д.)")
        photo_url = st.text_input("Ссылка на скриншот машины (Прямая ссылка на картинку)")
        uploaded_pc = st.file_uploader("Загрузите файл конфигурации (.pc)", type=["pc"])
        
        submit = st.form_submit_button("Добавить в гараж")
        
        if submit:
            if car_name and mod_link and uploaded_pc:
                pc_bytes = uploaded_pc.read()
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO garage (car_name, mod_link, pc_filename, pc_data, photo_url, owner) VALUES (?, ?, ?, ?, ?, ?)",
                          (car_name, mod_link, uploaded_pc.name, pc_bytes, photo_url, owner or "Аноним"))
                conn.commit()
                conn.close()
                st.success("Машина успешно добавлена в гараж!")
            else:
                st.error("Заполните название, ссылку на мод и загрузите .pc файл!")

# --- СТРАНИЦА 4: АДМИН-ПАНЕЛЬ ---
elif page == "👑 Панель Админа":
    st.title("👑 Управление игроками")
    
    admin_pass = st.text_input("Введите пароль админа", type="password")
    if admin_pass == "1234": # Поменяйте пароль на свой!
        st.success("Доступ разрешен!")
        
        st.subheader("Регистрация / Изменение игрока")
        username = st.text_input("Никнейм игрока")
        balance = st.number_input("Баланс ($)", value=1000, step=100)
        job = st.selectbox("Работа", ["Курьер", "Дальнобойщик", "Механик", "Полицейский", "Безработный"])
        
        if st.button("Сохранить данные игрока"):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO users (username, balance, job) VALUES (?, ?, ?)",
                      (username, balance, job))
            conn.commit()
            conn.close()
            st.success(f"Данные для {username} обновлены!")