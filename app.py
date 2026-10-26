import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Портал BeamNG RP", page_icon="🏎️", layout="wide")

DB_NAME = "beamng_rp.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, balance INTEGER, job TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS garage 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  car_name TEXT, 
                  mod_link TEXT, 
                  pc_filename TEXT, 
                  pc_data BLOB, 
                  photo_url TEXT, 
                  owner TEXT, 
                  price INTEGER DEFAULT 0, 
                  is_for_sale INTEGER DEFAULT 0)''')
    
    # Автоматическое добавление колонок, если таблица уже существовала ранее
    try:
        c.execute("ALTER TABLE garage ADD COLUMN price INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE garage ADD COLUMN is_for_sale INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

init_db()

st.sidebar.title("🎮 BeamNG.mp RP")
page = st.sidebar.radio("Разделы", [
    "🏎️ Гараж и Авторынок", 
    "♻️ Свалка (Утилизация)",
    "💰 Игроки и Балансы", 
    "➕ Добавить машину", 
    "👑 Панель Администратора"
])

# --- 1. ГАРАЖ И АВТОРЫНОК ---
if page == "🏎️ Гараж и Авторынок":
    st.title("🏎️ Гараж и Авторынок")
    st.write("Смотрите машины, скачивайте .pc конфигурации или покупайте авто у других игроков!")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, owner, price, is_for_sale FROM garage")
    cars = c.fetchall()
    conn.close()

    if not cars:
        st.info("В гараже пока нет машин.")
    else:
        cols = st.columns(3)
        for idx, car in enumerate(cars):
            car_id, name, mod_link, pc_filename, pc_data, photo_url, owner, price, is_for_sale = car
            col = cols[idx % 3]
            
            with col:
                st.subheader(name)
                if photo_url:
                    st.image(photo_url, use_container_width=True)
                
                st.caption(f"👤 Владелец: **{owner}**")
                
                if is_for_sale:
                    st.warning(f"🏷️ ПРОДАЕТСЯ: **${price}**")
                else:
                    st.info("🅿️ Личный гараж (Не продается)")

                st.markdown(f"🔗 [Скачать мод]({mod_link})")
                
                st.download_button(
                    label=f"📥 Скачать {pc_filename}",
                    data=pc_data,
                    file_name=pc_filename,
                    mime="text/plain",
                    key=f"dl_{car_id}"
                )

                # Покупка машины на авторынке
                if is_for_sale:
                    st.markdown("---")
                    buyer_name = st.text_input(f"Ваш ник для покупки", key=f"buyer_{car_id}")
                    if st.button(f"🛒 Купить за ${price}", key=f"buy_{car_id}"):
                        if buyer_name:
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("SELECT balance FROM users WHERE username = ?", (buyer_name,))
                            row = c.fetchone()
                            if row and row[0] >= price:
                                new_balance = row[0] - price
                                c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, buyer_name))
                                c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (price, owner))
                                c.execute("UPDATE garage SET owner = ?, is_for_sale = 0 WHERE id = ?", (buyer_name, car_id))
                                conn.commit()
                                conn.close()
                                st.success("Успешно! Вы купили эту машину.")
                                st.rerun()
                            else:
                                st.error("Недостаточно денег на балансе или игрок не найден!")
                                conn.close()
                        else:
                            st.warning("Введите ваш ник!")
                st.markdown("---")

# --- 2. СВАЛКА (УТИЛИЗАЦИЯ) ---
elif page == "♻️ Свалка (Утилизация)":
    st.title("♻️ Мгновенная утилизация авто")
    st.write("Сдайте машину на свалку! Вы получите **30% от её цены** мгновенно, без ожидания покупателя.")

    owner_search = st.text_input("Введите ваш ник, чтобы увидеть ваши машины:")
    
    if owner_search:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, car_name, price FROM garage WHERE owner = ?", (owner_search,))
        my_cars = c.fetchall()
        conn.close()

        if not my_cars:
            st.info("У вас нет машин в гараже.")
        else:
            for car_id, name, price in my_cars:
                scrap_value = int(price * 0.3) if price > 0 else 300
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"🚘 **{name}** (Оценка: ${price}) -> Выкуп свалки: **${scrap_value}**")
                with col2:
                    if st.button(f"♻️ Утилизировать", key=f"scrap_{car_id}"):
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (scrap_value, owner_search))
                        c.execute("DELETE FROM garage WHERE id = ?", (car_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Машина утилизирована! Вы получили ${scrap_value}.")
                        st.rerun()

# --- 3. ИГРОКИ И БАЛАНСЫ ---
elif page == "💰 Игроки и Балансы":
    st.title("💰 Экономика и Список Игроков")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT username AS 'Игрок', balance AS 'Баланс ($)', job AS 'Работа' FROM users", conn)
    conn.close()
    
    if df.empty:
        st.info("Игроков пока нет.")
    else:
        st.dataframe(df, use_container_width=True)

# --- 4. ДОБАВИТЬ МАШИНУ ---
elif page == "➕ Добавить машину":
    st.title("➕ Добавление автомобиля")
    
    with st.form("add_car_form"):
        car_name = st.text_input("Название машины")
        owner = st.text_input("Ваш никнейм в игре")
        mod_link = st.text_input("Ссылка на мод")
        photo_url = st.text_input("Ссылка на скриншот")
        price = st.number_input("Цена машины ($)", value=1000, step=500)
        is_for_sale = st.checkbox("Выставить сразу на Авторынок?")
        uploaded_pc = st.file_uploader("Загрузите .pc файл", type=["pc"])
        
        submit = st.form_submit_button("Добавить в гараж")
        
        if submit:
            if car_name and mod_link and uploaded_pc and owner:
                pc_bytes = uploaded_pc.read()
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("""INSERT INTO garage 
                             (car_name, mod_link, pc_filename, pc_data, photo_url, owner, price, is_for_sale) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                          (car_name, mod_link, uploaded_pc.name, pc_bytes, photo_url, owner, price, 1 if is_for_sale else 0))
                conn.commit()
                conn.close()
                st.success("Машина успешно добавлена!")
            else:
                st.error("Заполните все поля и загрузите .pc файл!")

# --- 5. ПАНЕЛЬ АДМИНИСТРАТОРА ---
elif page == "👑 Панель Администратора":
    st.title("👑 Управление Сервером (Админ)")
    
    admin_pass = st.text_input("Введите пароль администратора", type="password")
    if admin_pass == "1234":
        st.success("Доступ разрешен!")
        
        tab1, tab2 = st.tabs(["👥 Игроки", "🏎️ Редактирование Машин"])
        
        with tab1:
            st.subheader("Изменение баланса / работы")
            username = st.text_input("Никнейм игрока")
            balance = st.number_input("Баланс ($)", value=1000, step=100)
            job = st.selectbox("Работа", ["Курьер", "Дальнобойщик", "Механик", "Полицейский", "Безработный"])
            
            if st.button("Сохранить игрока"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO users (username, balance, job) VALUES (?, ?, ?)",
                          (username, balance, job))
                conn.commit()
                conn.close()
                st.success(f"Игрок {username} обновлен!")

        with tab2:
            st.subheader("Редактирование машин в базе")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, car_name, owner, price, is_for_sale FROM garage")
            all_cars = c.fetchall()
            conn.close()

            if all_cars:
                car_options = {f"ID {c[0]}: {c[1]} (Владелец: {c[2]})": c[0] for c in all_cars}
                selected_car_label = st.selectbox("Выберите машину для редактирования", list(car_options.keys()))
                selected_car_id = car_options[selected_car_label]

                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT car_name, mod_link, photo_url, owner, price, is_for_sale FROM garage WHERE id = ?", (selected_car_id,))
                edit_car = c.fetchone()
                conn.close()

                if edit_car:
                    with st.form("edit_car_form"):
                        new_name = st.text_input("Название", value=edit_car[0])
                        new_mod = st.text_input("Ссылка на мод", value=edit_car[1])
                        new_photo = st.text_input("Ссылка на фото", value=edit_car[2])
                        new_owner = st.text_input("Владелец", value=edit_car[3])
                        new_price = st.number_input("Цена ($)", value=edit_car[4], step=100)
                        new_sale = st.checkbox("На продаже (Авторынок)", value=bool(edit_car[5]))

                        col_save, col_del = st.columns(2)
                        with col_save:
                            btn_save = st.form_submit_button("💾 Сохранить изменения")
                        
                        if btn_save:
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("""UPDATE garage SET 
                                         car_name=?, mod_link=?, photo_url=?, owner=?, price=?, is_for_sale=? 
                                         WHERE id=?""",
                                      (new_name, new_mod, new_photo, new_owner, new_price, 1 if new_sale else 0, selected_car_id))
                            conn.commit()
                            conn.close()
                            st.success("Машина успешно отредактирована!")
                            st.rerun()

                    if st.button("❌ Удалить машину из базы", key="del_car_admin"):
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("DELETE FROM garage WHERE id = ?", (selected_car_id,))
                        conn.commit()
                        conn.close()
                        st.warning("Машина удалена!")
                        st.rerun()
