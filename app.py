import streamlit as st
import sqlite3
import pandas as pd
import re

st.set_page_config(page_title="Портал BeamNG RP", page_icon="🏎️", layout="wide")

DB_NAME = "beamng_rp.db"
ADMIN_PASSWORD = st.secrets.get("admin_password", "1234")

# Фиксированная выплата свалки за любую утилизированную машину (не зависит от рынка!)
FIXED_SCRAP_PAYOUT = 800 

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, balance INTEGER, job TEXT, password TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS garage 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  car_name TEXT, 
                  mod_link TEXT, 
                  pc_filename TEXT, 
                  pc_data BLOB, 
                  photo_url TEXT, 
                  photo_data BLOB,
                  owner TEXT, 
                  price INTEGER DEFAULT 0, 
                  is_for_sale INTEGER DEFAULT 0,
                  is_approved INTEGER DEFAULT 0)''')
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN password TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE garage ADD COLUMN price INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE garage ADD COLUMN is_for_sale INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE garage ADD COLUMN is_approved INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE garage ADD COLUMN photo_data BLOB")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

init_db()

fn_fix_image_url = lambda url: (
    f"https://drive.google.com/uc?export=view&id={re.search(r'/file/d/([a-zA-Z0-9_-]+)', url).group(1)}"
    if url and re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    else (
        f"https://drive.google.com/uc?export=view&id={re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url).group(1)}"
        if url and re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
        else url
    )
)

if "logged_user" not in st.session_state:
    st.session_state.logged_user = None

# --- БОКОВАЯ ПАНЕЛЬ И АВТОРИЗАЦИЯ ---
st.sidebar.title("🎮 BeamNG.mp RP")
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Аккаунт игрока")

if st.session_state.logged_user is None:
    login_user = st.sidebar.text_input("Ваш никнейм")
    login_pass = st.sidebar.text_input("Пароль", type="password")
    
    col_l1, col_l2 = st.sidebar.columns(2)
    with col_l1:
        if st.sidebar.button("Войти"):
            if login_user and login_pass:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT password FROM users WHERE username = ?", (login_user,))
                row = c.fetchone()
                conn.close()
                if row and row[0] == login_pass:
                    st.session_state.logged_user = login_user
                    st.success(f"Вход выполнен, {login_user}!")
                    st.rerun()
                else:
                    st.sidebar.error("Неверный ник или пароль!")
            else:
                st.sidebar.warning("Введите ник и пароль.")
                
    with col_l2:
        if st.sidebar.button("Регистрация"):
            if login_user and login_pass:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT username FROM users WHERE username = ?", (login_user,))
                if c.fetchone():
                    st.sidebar.error("Игрок с таким ником уже существует!")
                else:
                    c.execute("INSERT INTO users (username, balance, job, password) VALUES (?, 1000, 'Безработный', ?)", 
                              (login_user, login_pass))
                    conn.commit()
                    conn.close()
                    st.session_state.logged_user = login_user
                    st.sidebar.success(f"Аккаунт создан! Добро пожаловать, {login_user}!")
                    st.rerun()
            else:
                st.sidebar.warning("Введите ник и пароль для регистрации.")
else:
    st.sidebar.success(f"Вы вошли как: **{st.session_state.logged_user}**")
    if st.sidebar.button("Выйти из аккаунта"):
        st.session_state.logged_user = None
        st.rerun()

st.sidebar.markdown("---")
page = st.sidebar.radio("Разделы", [
    "🏎️ Общий Гараж", 
    "🏷️ Авторынок",
    "🅿️ Мой Гараж",
    "♻️ Свалка (Утилизация)",
    "💰 Игроки и Балансы", 
    "➕ Добавить машину", 
    "👑 Панель Администратора"
])

def render_car_image(photo_data, photo_url):
    if photo_data:
        try:
            st.image(photo_data, use_container_width=True)
            return
        except Exception:
            pass
    if photo_url:
        fixed_photo = fn_fix_image_url(photo_url)
        try:
            st.image(fixed_photo, use_container_width=True)
        except Exception:
            st.warning("Не удалось загрузить фото.")

# --- 1. ОБЩИЙ ГАРАЖ ---
if page == "🏎️ Общий Гараж":
    st.title("🏎️ Общий Гараж сервера")
    st.write("Здесь хранятся все одобренные администратором автомобили игроков.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price, is_for_sale 
                 FROM garage WHERE is_approved = 1""")
    cars = c.fetchall()
    conn.close()

    if not cars:
        st.info("В общем гараже пока нет одобренных машин.")
    else:
        cols = st.columns(3)
        for idx, car in enumerate(cars):
            car_id, name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price, is_for_sale = car
            col = cols[idx % 3]
            
            with col:
                st.subheader(name)
                render_car_image(photo_data, photo_url)
                
                st.caption(f"👤 Владелец: **{owner}**")
                
                if is_for_sale:
                    st.warning(f"🏷️ ПРОДАЕТСЯ НА РЫНКЕ: **${price}**")
                else:
                    st.info("🅿️ В личном пользовании")

                st.markdown(f"🔗 [Скачать мод]({mod_link})")
                st.download_button(
                    label=f"📥 Скачать {pc_filename}",
                    data=pc_data,
                    file_name=pc_filename,
                    mime="text/plain",
                    key=f"dl_gen_{car_id}"
                )
                st.markdown("---")

# --- 2. АВТОРЫНОК ---
elif page == "🏷️ Авторынок":
    st.title("🏷️ Авторынок")
    st.write("Машины, которые игроки выставили на продажу. Покупайте в один клик!")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price 
                 FROM garage WHERE is_approved = 1 AND is_for_sale = 1""")
    cars = c.fetchall()
    conn.close()

    if not cars:
        st.info("На авторынке сейчас нет машин на продажу.")
    else:
        cols = st.columns(3)
        for idx, car in enumerate(cars):
            car_id, name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price = car
            col = cols[idx % 3]
            
            with col:
                st.subheader(name)
                render_car_image(photo_data, photo_url)
                
                st.caption(f"👤 Продавец: **{owner}**")
                st.warning(f"💵 Цена: **${price}**")

                st.markdown(f"🔗 [Скачать мод]({mod_link})")
                st.download_button(
                    label=f"📥 Скачать {pc_filename}",
                    data=pc_data,
                    file_name=pc_filename,
                    mime="text/plain",
                    key=f"dl_market_{car_id}"
                )

                st.markdown("---")
                if st.session_state.logged_user:
                    if st.session_state.logged_user == owner:
                        st.info("Это ваша машина.")
                    else:
                        if st.button(f"🛒 Купить за ${price}", key=f"buy_market_{car_id}"):
                            buyer_name = st.session_state.logged_user
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("SELECT balance FROM users WHERE username = ?", (buyer_name,))
                            row = c.fetchone()
                            if row and row[0] >= price:
                                new_balance = row[0] - price
                                c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, buyer_name))
                                c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (price, owner))
                                c.execute("UPDATE garage SET owner = ?, is_for_sale = 0, price = 0 WHERE id = ?", (buyer_name, car_id))
                                conn.commit()
                                conn.close()
                                st.success("Успешно! Вы купили эту машину.")
                                st.rerun()
                            else:
                                st.error("Недостаточно денег на вашем балансе!")
                                conn.close()
                else:
                    st.warning("⚠️ Войдите в аккаунт, чтобы купить машину.")
                st.markdown("---")

# --- 3. МОЙ ГАРАЖ ---
elif page == "🅿️ Мой Гараж":
    st.title("🅿️ Мой Личный Гараж")
    
    if not st.session_state.logged_user:
        st.warning("⚠️ Пожалуйста, войдите в аккаунт в боковой панели, чтобы управлять своими машинами.")
    else:
        current_user = st.session_state.logged_user
        st.write(f"Управление автомобилями игрока: **{current_user}**")

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, price, is_for_sale, is_approved 
                     FROM garage WHERE owner = ?""", (current_user,))
        my_cars = c.fetchall()
        conn.close()

        if not my_cars:
            st.info("У вас пока нет добавленных машин в гараже.")
        else:
            for car in my_cars:
                car_id, name, mod_link, pc_filename, pc_data, photo_url, photo_data, price, is_for_sale, is_approved = car
                
                with st.expander(f"🚘 {name} (ID: {car_id})"):
                    col_img, col_info = st.columns([1, 2])
                    with col_img:
                        render_car_image(photo_data, photo_url)
                    with col_info:
                        if is_approved == 0:
                            st.error("⏳ Статус: На модерации у администратора")
                        else:
                            st.success("✅ Статус: Одобрено")
                        
                        st.markdown(f"🔗 [Ссылка на мод]({mod_link})")
                        st.download_button(
                            label=f"📥 Скачать конфигурацию {pc_filename}",
                            data=pc_data,
                            file_name=pc_filename,
                            mime="text/plain",
                            key=f"dl_my_{car_id}"
                        )

                        st.markdown("---")
                        with st.form(f"sale_form_{car_id}"):
                            st.subheader("Настройки авторынка")
                            new_sale_status = st.checkbox("Выставить на Авторынок", value=bool(is_for_sale))
                            new_car_price = st.number_input("Цена продажи ($)", value=int(price), step=100)
                            
                            update_btn = st.form_submit_button("Сохранить настройки продажи")
                            if update_btn:
                                conn = sqlite3.connect(DB_NAME)
                                c = conn.cursor()
                                c.execute("UPDATE garage SET is_for_sale = ?, price = ? WHERE id = ?", 
                                          (1 if new_sale_status else 0, new_car_price, car_id))
                                conn.commit()
                                conn.close()
                                st.success("Настройки успешно обновлены!")
                                st.rerun()

# --- 4. СВАЛКА (УТИЛИЗАЦИЯ С ФИКСИРОВАННОЙ ВЫПЛАТОЙ) ---
elif page == "♻️ Свалка (Утилизация)":
    st.title("♻️ Мгновенная утилизация авто")
    st.write(f"Сдайте свою машину на свалку! Фиксированная государственная компенсация за утилизацию любого авто составляет **${FIXED_SCRAP_PAYOUT}**.")

    if not st.session_state.logged_user:
        st.warning("⚠️ Пожалуйста, войдите в аккаунт в боковой панели.")
    else:
        owner_search = st.session_state.logged_user
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, car_name FROM garage WHERE owner = ?", (owner_search,))
        my_cars = c.fetchall()
        conn.close()

        if not my_cars:
            st.info("У вас нет машин в личном гараже для утилизации.")
        else:
            for car_id, name in my_cars:
                scrap_value = FIXED_SCRAP_PAYOUT
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"🚘 **{name}** -> Выплата свалки: **${scrap_value}**")
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

# --- 5. ИГРОКИ И БАЛАНСЫ ---
elif page == "💰 Игроки и Балансы":
    st.title("💰 Экономика и Список Игроков")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT username AS 'Игрок', balance AS 'Баланс ($)', job AS 'Работа' FROM users", conn)
    conn.close()
    
    if df.empty:
        st.info("Игроков пока нет.")
    else:
        st.dataframe(df, use_container_width=True)

# --- 6. ДОБАВИТЬ МАШИНУ ---
elif page == "➕ Добавить машину":
    st.title("➕ Добавление автомобиля")
    
    if not st.session_state.logged_user:
        st.warning("⚠️ Пожалуйста, войдите в аккаунт в боковой панели, чтобы добавить машину в гараж.")
    else:
        with st.form("add_car_form"):
            st.write(f"Владелец: **{st.session_state.logged_user}** (автоматически)")
            car_name = st.text_input("Название машины")
            mod_link = st.text_input("Ссылка на мод")
            
            uploaded_photo = st.file_uploader("Загрузите фото машины (PNG, JPG)", type=["png", "jpg", "jpeg"])
            
            is_for_sale = st.checkbox("Выставить сразу на Авторынок?")
            price = st.number_input("Цена машины ($) [укажите, если продаете]", value=0, step=500)
            
            uploaded_pc = st.file_uploader("Загрузите конфигурационный файл (.pc)", type=["pc"])
            
            submit = st.form_submit_button("Отправить на модерацию")
            
            if submit:
                if car_name and mod_link and uploaded_pc:
                    pc_bytes = uploaded_pc.read()
                    photo_bytes = uploaded_photo.read() if uploaded_photo else None
                    
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("""INSERT INTO garage 
                                 (car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price, is_for_sale, is_approved) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                              (car_name, mod_link, uploaded_pc.name, pc_bytes, "", photo_bytes, st.session_state.logged_user, price if is_for_sale else 0, 1 if is_for_sale else 0))
                    conn.commit()
                    conn.close()
                    st.success("Машина отправлена на проверку администратору!")
                else:
                    st.error("Заполните название, ссылку на мод и загрузите .pc файл!")

# --- 7. ПАНЕЛЬ АДМИНИСТРАТОРА ---
elif page == "👑 Панель Администратора":
    st.title("👑 Управление Сервером (Админ)")
    
    admin_pass = st.text_input("Введите пароль администратора", type="password")
    
    if admin_pass == ADMIN_PASSWORD and ADMIN_PASSWORD != "":
        st.success("Доступ разрешен!")
        
        tab1, tab2, tab3 = st.tabs(["👥 Игроки", "🏎️ Редактирование Машин", "🛡️ Модерация машин"])
        
        with tab1:
            st.subheader("Управление игроками (Изменение / Удаление)")
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT username FROM users")
            all_users = [row[0] for row in c.fetchall()]
            conn.close()

            if not all_users:
                st.info("Зарегистрированных игроков пока нет.")
            else:
                selected_user = st.selectbox("Выберите игрока для управления", all_users)
                
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT balance, job FROM users WHERE username = ?", (selected_user,))
                user_data = c.fetchone()
                conn.close()
                
                if user_data:
                    with st.form("edit_user_form"):
                        new_balance = st.number_input("Баланс ($)", value=user_data[0], step=100)
                        jobs_list = ["Курьер", "Дальнобойщик", "Механик", "Полицейский", "Безработный"]
                        default_idx = jobs_list.index(user_data[1]) if user_data[1] in jobs_list else 0
                        new_job = st.selectbox("Работа", jobs_list, index=default_idx)
                        
                        submitted = st.form_submit_button("💾 Сохранить изменения игрока")
                        if submitted:
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("UPDATE users SET balance = ?, job = ? WHERE username = ?", (new_balance, new_job, selected_user))
                            conn.commit()
                            conn.close()
                            st.success(f"Данные игрока {selected_user} успешно обновлены!")
                            st.rerun()

                    st.markdown("---")
                    if st.button(f"❌ Полностью удалить игрока '{selected_user}' и все его машины"):
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("DELETE FROM users WHERE username = ?", (selected_user,))
                        c.execute("DELETE FROM garage WHERE owner = ?", (selected_user,))
                        conn.commit()
                        conn.close()
                        st.warning(f"Игрок {selected_user} и все его автомобили были удалены из базы!")
                        st.rerun()

        with tab2:
            st.subheader("Редактирование машин в базе")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, car_name, owner, price, is_for_sale FROM garage")
            all_cars = c.fetchall()
            conn.close()

            if not all_cars:
                st.info("Машин в базе нет.")
            else:
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
                        new_photo = st.text_input("Ссылка на фото (или оставьте как есть)", value=edit_car[2])
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

        with tab3:
            st.subheader("Машины, ожидающие проверки")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, car_name, mod_link, photo_url, photo_data, owner, price FROM garage WHERE is_approved = 0")
            pending_cars = c.fetchall()
            conn.close()

            if not pending_cars:
                st.info("Нет машин на модерации. Всё проверено!")
            else:
                for p_car in pending_cars:
                    p_id, p_name, p_link, p_photo, p_photo_data, p_owner, p_price = p_car
                    st.markdown(f"### 🚘 {p_name} (ID: {p_id})")
                    st.write(f"👤 **Владелец:** {p_owner} | 💵 **Цена:** ${p_price}")
                    st.markdown(f"🔗 [Ссылка на мод]({p_link})")
                    render_car_image(p_photo_data, p_photo)
                    
                    col_ap1, col_ap2 = st.columns(2)
                    with col_ap1:
                        if st.button(f"✅ Одобрить машину #{p_id}", key=f"app_{p_id}"):
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("UPDATE garage SET is_approved = 1 WHERE id = ?", (p_id,))
                            conn.commit()
                            conn.close()
                            st.success(f"Машина #{p_id} одобрена и опубликована!")
                            st.rerun()
                    with col_ap2:
                        if st.button(f"❌ Отклонить (удалить) #{p_id}", key=f"py_rej_{p_id}"):
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("DELETE FROM garage WHERE id = ?", (p_id,))
                            conn.commit()
                            conn.close()
                            st.warning(f"Машина #{p_id} отклонена и удалена.")
                            st.rerun()
                    st.markdown("---")
