import streamlit as st
import sqlite3
import pandas as pd
import re
import random
import time

st.set_page_config(page_title="Portal BeamNG RP", page_icon="🏎️", layout="wide")

DB_NAME = "beamng_rp.db"
ADMIN_PASSWORD = st.secrets.get("admin_password", "1234")
FIXED_SCRAP_PAYOUT = 800

# Кислотные, безумные и психоделические CSS-эффекты для легендарных машин
st.markdown("""
<style>
@keyframes crazyPsychoGlow {
    0% { border-color: #ff0055; box-shadow: 0 0 25px #ff0055, inset 0 0 15px #ff0055; transform: scale(1); }
    25% { border-color: #00ffcc; box-shadow: 0 0 35px #00ffcc, inset 0 0 25px #00ffcc; transform: scale(1.01); }
    50% { border-color: #ffcc00; box-shadow: 0 0 30px #ffcc00, inset 0 0 20px #ffcc00; transform: scale(1); }
    75% { border-color: #9900ff; box-shadow: 0 0 40px #9900ff, inset 0 0 30px #9900ff; transform: scale(1.01); }
    100% { border-color: #ff0055; box-shadow: 0 0 25px #ff0055, inset 0 0 15px #ff0055; transform: scale(1); }
}

@keyframes rainbowTextFast {
    0% { filter: hue-rotate(0deg); }
    100% { filter: hue-rotate(360deg); }
}

.crazy-legendary-card {
    border: 4px dashed #ff0055;
    border-radius: 15px;
    padding: 18px;
    background: radial-gradient(circle, rgba(30,0,50,0.95) 0%, rgba(5,5,15,0.98) 100%);
    animation: crazyPsychoGlow 1.5s infinite alternate ease-in-out;
    margin-bottom: 25px;
}

.crazy-legendary-title {
    background: linear-gradient(45deg, #ff0000, #ff7700, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff, #ff0000);
    background-size: 400% 400%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: rainbowTextFast 2s linear infinite, goldText 3s ease infinite;
    font-weight: 900 !important;
    font-size: 26px !important;
    text-transform: uppercase;
    text-align: center;
    letter-spacing: 2px;
}

.rare-card {
    border: 2px solid #00bfff;
    border-radius: 10px;
    padding: 12px;
    box-shadow: 0 0 12px rgba(0, 191, 255, 0.6);
    background: rgba(10, 25, 40, 0.85);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

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
                  is_approved INTEGER DEFAULT 0,
                  rarity TEXT DEFAULT 'Обычная')''')
    
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
    try:
        c.execute("ALTER TABLE garage ADD COLUMN rarity TEXT DEFAULT 'Обычная'")
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
    "👤 Профиль",
    "🎰 Казино",
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
    c.execute("""SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price, is_for_sale, rarity 
                 FROM garage WHERE is_approved = 1""")
    cars = c.fetchall()
    conn.close()

    if not cars:
        st.info("В общем гараже пока нет одобренных машин.")
    else:
        cols = st.columns(3)
        for idx, car in enumerate(cars):
            car_id, name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price, is_for_sale, rarity = car
            col = cols[idx % 3]
            
            with col:
                if rarity == "🔥 Легендарная":
                    st.markdown(f'<div class="crazy-legendary-card"><div class="crazy-legendary-title">⚡ {name} ⚡</div><p style="color: #ff0055; text-align:center; font-weight:bold;">🔥 АБСОЛЮТНЫЙ ЛЕГЕНДАРНЫЙ ЭКСЛЮЗИВ 🔥</p>', unsafe_allow_html=True)
                elif rarity == "💎 Редкая":
                    st.markdown(f'<div class="rare-card"><h3>💎 {name}</h3><p style="color: #00bfff;">РЕДКИЙ АВТОМОБИЛЬ</p>', unsafe_allow_html=True)
                else:
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
                
                if rarity in ["🔥 Легендарная", "💎 Редкая"]:
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")

# --- 2. АВТОРЫНОК ---
elif page == "🏷️ Авторынок":
    st.title("🏷️ Авторынок")
    st.write("Машины, которые игроки выставили на продажу. Покупайте в один клик!")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price, rarity 
                 FROM garage WHERE is_approved = 1 AND is_for_sale = 1""")
    cars = c.fetchall()
    conn.close()

    if not cars:
        st.info("На авторынке сейчас нет машин на продажу.")
    else:
        cols = st.columns(3)
        for idx, car in enumerate(cars):
            car_id, name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price, rarity = car
            col = cols[idx % 3]
            
            with col:
                if rarity == "🔥 Легендарная":
                    st.markdown(f'<div class="crazy-legendary-card"><div class="crazy-legendary-title">⚡ {name} ⚡</div><p style="color: #ff0055; text-align:center; font-weight:bold;">🔥 ЛЕГЕНДАРНЫЙ ЛОТ 🔥</p>', unsafe_allow_html=True)
                elif rarity == "💎 Редкая":
                    st.markdown(f'<div class="rare-card"><h3>💎 {name}</h3><p style="color: #00bfff;">РЕДКИЙ ЛОТ</p>', unsafe_allow_html=True)
                else:
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
                
                if rarity in ["🔥 Легендарная", "💎 Редкая"]:
                    st.markdown('</div>', unsafe_allow_html=True)
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
        c.execute("""SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, price, is_for_sale, is_approved, rarity 
                     FROM garage WHERE owner = ?""", (current_user,))
        my_cars = c.fetchall()
        conn.close()

        if not my_cars:
            st.info("У вас пока нет добавленных машин в гараже.")
        else:
            for car in my_cars:
                car_id, name, mod_link, pc_filename, pc_data, photo_url, photo_data, price, is_for_sale, is_approved, rarity = car
                
                expander_label = f"🔥 {name} (ID: {car_id}) [ЛЕГЕНДАРНАЯ]" if rarity == "🔥 Легендарная" else f"🚘 {name} (ID: {car_id})"
                with st.expander(expander_label):
                    col_img, col_info = st.columns([1, 2])
                    with col_img:
                        if rarity == "🔥 Легендарная":
                            st.markdown('<div class="crazy-legendary-card" style="padding:5px;">', unsafe_allow_html=True)
                        render_car_image(photo_data, photo_url)
                        if rarity == "🔥 Легендарная":
                            st.markdown('</div>', unsafe_allow_html=True)
                    with col_info:
                        if rarity == "🔥 Легендарная":
                            st.markdown('<p style="color: #ff0055; font-weight:bold;">⚡ СТАТУС: ЛЕГЕНДАРНЫЙ ЭКСЛЮЗИВ ⚡</p>', unsafe_allow_html=True)
                        
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

# --- 4. ПРОФИЛЬ ---
elif page == "👤 Профиль":
    st.title("👤 Профиль игрока")
    
    if not st.session_state.logged_user:
        st.warning("⚠️ Пожалуйста, войдите в аккаунт через боковую панель, чтобы просмотреть профиль.")
    else:
        current_user = st.session_state.logged_user
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT balance, job FROM users WHERE username = ?", (current_user,))
        user_info = c.fetchone()
        
        c.execute("SELECT COUNT(*), SUM(CASE WHEN is_approved=1 THEN 1 ELSE 0 END) FROM garage WHERE owner = ?", (current_user,))
        car_stats = c.fetchone()
        conn.close()
        
        balance = user_info[0] if user_info else 0
        job = user_info[1] if user_info else "Безработный"
        total_cars = car_stats[0] if car_stats else 0
        approved_cars = car_stats[1] if car_stats else 0

        # Карточка профиля
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2f, #111118); padding: 25px; border-radius: 15px; border: 2px solid #4f46e5; box-shadow: 0 0 15px rgba(79, 70, 229, 0.4); margin-bottom: 25px;">
            <h2 style="margin-top: 0; color: #818cf8;">👤 Игрок: {current_user}</h2>
            <hr style="border-color: #374151;">
            <p style="font-size: 18px;">💰 <b>Баланс:</b> <span style="color: #34d399;">${balance}</span></p>
            <p style="font-size: 18px;">💼 <b>Работа:</b> <span style="color: #fbbf24;">{job}</span></p>
            <p style="font-size: 18px;">🚘 <b>Всего машин в гараже:</b> {total_cars} (Одобрено: {approved_cars})</p>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("🚗 Ваши автомобили")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, car_name, price, is_for_sale, is_approved, rarity FROM garage WHERE owner = ?", (current_user,))
        my_profile_cars = c.fetchall()
        conn.close()

        if not my_profile_cars:
            st.info("У вас пока нет добавленных автомобилей.")
        else:
            df_profile = pd.DataFrame(my_profile_cars, columns=["ID", "Название", "Цена ($)", "На рынке", "Одобрено", "Редкость"])
            st.dataframe(df_profile, use_container_width=True)

# --- 5. КАЗИНО ---
elif page == "🎰 Казино":
    st.title("🎰 Городское Казино (Рулетка)")
    
    if not st.session_state.logged_user:
        st.warning("⚠️ Пожалуйста, войдите в аккаунт в боковой панели, чтобы играть в казино.")
    else:
        current_user = st.session_state.logged_user
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE username = ?", (current_user,))
        user_row = c.fetchone()
        user_balance = user_row[0] if user_row else 0
        conn.close()

        st.subheader(f"Ваш баланс: **${user_balance}**")

        col1, col2 = st.columns([1, 1])
        with col1:
            bet_amount = st.number_input("Размер ставки ($)", min_value=10, max_value=max(10, user_balance), value=100, step=50)
            choice_type = st.radio("Тип ставки:", ["На Цвет (x2)", "На Число (x35)"])
            
            if choice_type == "На Цвет (x2)":
                target_choice = st.selectbox("Выберите цвет:", ["Красное", "Черное"])
            else:
                target_choice = st.number_input("Выберите число (0 - 36):", min_value=0, max_value=36, value=7)

            spin_clicked = st.button("🎲 ВРАЩАТЬ РУЛЕТКУ", use_container_width=True)

        with col2:
            if spin_clicked:
                if user_balance < bet_amount:
                    st.error("Недостаточно денег на балансе!")
                else:
                    with st.spinner("🎲 Рулетка вращается, шарик прыгает по лункам..."):
                        time.sleep(2.5)
                    
                    winning_num = random.randint(0, 36)
                    
                    if winning_num == 0:
                        winning_color = "Зеленое"
                    elif winning_num in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
                        winning_color = "Красное"
                    else:
                        winning_color = "Черное"

                    is_win = False
                    payout = 0
                    
                    if choice_type == "На Цвет (x2)":
                        if target_choice == winning_color:
                            is_win = True
                            payout = bet_amount
                    else:
                        if int(target_choice) == winning_num:
                            is_win = True
                            payout = bet_amount * 35

                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    if is_win:
                        new_bal = user_balance + payout
                        st.balloons()
                        st.success(f"🎉 ПОБЕДА! Выпало число **{winning_num} ({winning_color})**.\n\nВы выиграли **${payout}**! Баланс обновлен.")
                    else:
                        new_bal = user_balance - bet_amount
                        st.error(f"❌ ПРОИГРЫШ! Выпало число **{winning_num} ({winning_color})**.\n\nВы потеряли **${bet_amount}**.")
                        
                    c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_bal, current_user))
                    conn.commit()
                    conn.close()
            else:
                st.info("👈 Настройте ставку слева и нажмите **«Вращать рулетку»**.")

# --- 6. СВАЛКА (УТИЛИЗАЦИЯ) ---
elif page == "♻️ Свалка (Утилизация)":
    st.title("♻️ Мгновенная утилизация авто")
    st.write(f"Сдайте свою машину на свалку! Фиксированная компенсация за утилизацию составляет **${FIXED_SCRAP_PAYOUT}**.")

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

# --- 7. ИГРОКИ И БАЛАНСЫ ---
elif page == "💰 Игроки и Балансы":
    st.title("💰 Экономика и Список Игроков")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT username AS 'Игрок', balance AS 'Баланс ($)', job AS 'Работа' FROM users", conn)
    conn.close()
    
    if df.empty:
        st.info("Игроков пока нет.")
    else:
        st.dataframe(df, use_container_width=True)

# --- 8. ДОБАВИТЬ МАШИНУ ---
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
                                 (car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price, is_for_sale, is_approved, rarity) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'Обычная')""",
                              (car_name, mod_link, uploaded_pc.name, pc_bytes, "", photo_bytes, st.session_state.logged_user, price if is_for_sale else 0, 1 if is_for_sale else 0))
                    conn.commit()
                    conn.close()
                    st.success("Машина отправлена на проверку администратору!")
                else:
                    st.error("Заполните название, ссылку на мод и загрузите .pc файл!")

# --- 9. ПАНЕЛЬ АДМИНИСТРАТОРА ---
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
            st.subheader("Редактирование машин в базе (включая редкость)")
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
                c.execute("SELECT car_name, mod_link, photo_url, owner, price, is_for_sale, rarity FROM garage WHERE id = ?", (selected_car_id,))
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
                        
                        rarity_options = ["Обычная", "💎 Редкая", "🔥 Легендарная"]
                        current_rarity = edit_car[6] if edit_car[6] in rarity_options else "Обычная"
                        new_rarity = st.selectbox("Редкость / Эффект авто", rarity_options, index=rarity_options.index(current_rarity))

                        col_save, col_del = st.columns(2)
                        with col_save:
                            btn_save = st.form_submit_button("💾 Сохранить изменения")
                        
                        if btn_save:
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("""UPDATE garage SET 
                                         car_name=?, mod_link=?, photo_url=?, owner=?, price=?, is_for_sale=?, rarity=? 
                                         WHERE id=?""",
                                      (new_name, new_mod, new_photo, new_owner, new_price, 1 if new_sale else 0, new_rarity, selected_car_id))
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
            c.execute("SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price FROM garage WHERE is_approved = 0")
            pending_cars = c.fetchall()
            conn.close()

            if not pending_cars:
                st.info("Нет машин на модерации. Всё проверено!")
            else:
                for p_car in pending_cars:
                    p_id, p_name, p_link, p_pc_filename, p_pc_data, p_photo, p_photo_data, p_owner, p_price = p_car
                    st.markdown(f"### 🚘 {p_name} (ID: {p_id})")
                    st.write(f"👤 **Владелец:** {p_owner} | 💵 **Цена:** ${p_price}")
                    st.markdown(f"🔗 [Ссылка на мод]({p_link})")
                    
                    if p_pc_data and p_pc_filename:
                        st.download_button(
                            label=f"📥 Скачать конфигурацию {p_pc_filename}",
                            data=p_pc_data,
                            file_name=p_pc_filename,
                            mime="text/plain",
                            key=f"dl_pending_{p_id}"
                        )
                    
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
