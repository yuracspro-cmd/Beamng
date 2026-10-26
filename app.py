import streamlit as st
import sqlite3
import pandas as pd
import re
import random
import time
import base64

st.set_page_config(page_title="Portal BeamNG RP", page_icon="🏎️", layout="wide")

DB_NAME = "beamng_rp.db"
ADMIN_PASSWORD = st.secrets.get("admin_password", "1234")
FIXED_SCRAP_PAYOUT = 800
FEE_PERCENT = 0.03 # 3% комиссия биржи

# Аудио-ссылки для казино
SOUND_SPIN = "https://assets.mixkit.co/active_storage/sfx/2004/2004-preview.mp3"
SOUND_WIN = "https://assets.mixkit.co/active_storage/sfx/1435/1435-preview.mp3"
SOUND_LOSE = "https://assets.mixkit.co/active_storage/sfx/2019/2019-preview.mp3"

# Новостной фон для биржи
MARKET_NEWS = [
    ("🚀 Илон Маск опубликовал мем с названием валюты!", 0.25, 0.45),
    ("⚠️ Крупный крипто-фонд зафиксировал прибыль и продал активы.", -0.30, -0.15),
    ("🔥 Прошло успешное обновление сети и сжигание монет!", 0.10, 0.20),
    ("📉 Правительство объявило о возможном запрете анонимных транзакций.", -0.25, -0.10),
    ("🏛️ Крупный банк добавил монету в список инвестиционных активов.", 0.15, 0.30),
    ("💀 Хакеры попытались атаковать сеть, но защита выдержала.", -0.10, 0.05),
    ("📊 Обычный торговый день на бирже, киты манипулируют курсом.", -0.08, 0.08),
]

def play_audio(url):
    audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="{url}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# Стили
st.markdown("""
<style>
@keyframes psychoFlash {
    0% { border-color: #ff0055; box-shadow: 0 0 35px #ff0055, inset 0 0 25px #ff0055; filter: hue-rotate(0deg); }
    33% { border-color: #00ffcc; box-shadow: 0 0 45px #00ffcc, inset 0 0 35px #00ffcc; }
    66% { border-color: #ffff00; box-shadow: 0 0 40px #ffff00, inset 0 0 30px #ffff00; }
    100% { border-color: #ff00ff; box-shadow: 0 0 55px #ff00ff, inset 0 0 40px #ff00ff; filter: hue-rotate(360deg); }
}

@keyframes textGlitch {
    0% { text-shadow: 3px 3px #ff0055, -3px -3px #00ffcc; }
    50% { text-shadow: -4px 3px #ffff00, 4px -3px #9900ff; }
    100% { text-shadow: 3px -3px #ff0055, -3px 3px #00ffcc; }
}

.psycho-legendary-card, .rare-card, .normal-card {
    box-sizing: border-box;
    width: 100%;
    border-radius: 16px;
    padding: 15px;
    margin-bottom: 15px;
    border: 4px solid;
}

.psycho-legendary-card {
    background: linear-gradient(135deg, #1a002c 0%, #0a0a16 50%, #200010 100%);
    animation: psychoFlash 1.2s infinite alternate ease-in-out;
}

.rare-card {
    border-color: #00bfff;
    background: rgba(10, 25, 40, 0.9);
    box-shadow: 0 0 15px rgba(0, 191, 255, 0.4);
}

.normal-card {
    border-color: #333333;
    background: rgba(20, 20, 20, 0.8);
}

.car-title-legendary {
    font-size: 20px;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #ff0055, #00ffcc, #ffff00, #ff00ff, #ff0055);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: textGlitch 0.4s infinite, goldText 2s linear infinite;
    margin-bottom: 5px;
    text-transform: uppercase;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.car-title-rare {
    font-size: 20px;
    font-weight: bold;
    text-align: center;
    color: #00bfff;
    margin-bottom: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.car-title-normal {
    font-size: 20px;
    font-weight: bold;
    text-align: center;
    color: #fff;
    margin-bottom: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.legendary-badge {
    background: linear-gradient(90deg, #ff0055, #9900ff);
    color: white;
    text-align: center;
    font-size: 10px;
    font-weight: bold;
    padding: 4px;
    border-radius: 6px;
    margin-bottom: 10px;
    letter-spacing: 1px;
    box-shadow: 0 0 15px #ff0055;
    text-transform: uppercase;
}

.badge-placeholder {
    height: 22px;
    margin-bottom: 10px;
}

.car-img {
    width: 100%;
    height: 160px;
    object-fit: cover;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.2);
    margin-bottom: 10px;
}

.car-info {
    text-align: center;
    color: #ccc;
    font-size: 14px;
}

.news-box {
    background: rgba(30, 41, 59, 0.8);
    border-left: 4px solid #38bdf8;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 15px;
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
    
    # Таблицы для биржи
    c.execute('''CREATE TABLE IF NOT EXISTS crypto_coins 
                 (symbol TEXT PRIMARY KEY, name TEXT, price REAL, history TEXT, last_news TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_crypto 
                 (username TEXT, symbol TEXT, amount REAL, avg_buy_price REAL DEFAULT 0, PRIMARY KEY (username, symbol))''')

    try:
        c.execute("ALTER TABLE crypto_coins ADD COLUMN last_news TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE user_crypto ADD COLUMN avg_buy_price REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Создаем валюту "Введите Текст" по умолчанию
    c.execute("SELECT COUNT(*) FROM crypto_coins")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO crypto_coins (symbol, name, price, history, last_news) VALUES (?, ?, ?, ?, ?)", 
                  ('VVEDI', 'Введите Текст', 100.0, "90,95,98,100", "Обычный торговый день на бирже."))

    for col, definition in [('password', 'TEXT'), ('price', 'INTEGER DEFAULT 0'), 
                            ('is_for_sale', 'INTEGER DEFAULT 0'), ('is_approved', 'INTEGER DEFAULT 0'), 
                            ('photo_data', 'BLOB'), ('rarity', "TEXT DEFAULT 'Обычная'")]:
        try:
            c.execute(f"ALTER TABLE garage ADD COLUMN {col} {definition}")
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
    "📈 Биржа (Введите Текст)",
    "👤 Профиль",
    "🎰 Казино",
    "♻️ Свалка (Утилизация)",
    "💰 Игроки и Балансы", 
    "➕ Добавить машину", 
    "👑 Панель Администратора"
])

def render_car_card_html(name, photo_data, photo_url, owner, rarity):
    img_html = ""
    if photo_data:
        b64 = base64.b64encode(photo_data).decode()
        img_html = f'<img src="data:image/png;base64,{b64}" class="car-img">'
    elif photo_url:
        fixed_url = fn_fix_image_url(photo_url)
        img_html = f'<img src="{fixed_url}" class="car-img">'
    else:
        img_html = '<div style="height:160px; display:flex; align-items:center; justify-content:center; color:#777; background:#111; border-radius:8px; margin-bottom:10px;">Нет изображения</div>'

    if rarity == "🔥 Легендарная":
        card_html = f"""
        <div class="psycho-legendary-card">
            <div class="car-title-legendary">⚡ {name} ⚡</div>
            <div class="legendary-badge">🔥 Абсолютный психо-эксклюзив 🔥</div>
            {img_html}
            <div class="car-info">👤 Владелец: <b>{owner}</b></div>
        </div>
        """
    elif rarity == "💎 Редкая":
        card_html = f"""
        <div class="rare-card">
            <div class="car-title-rare">💎 {name}</div>
            <div class="badge-placeholder"></div>
            {img_html}
            <div class="car-info">👤 Владелец: <b>{owner}</b></div>
        </div>
        """
    else:
        card_html = f"""
        <div class="normal-card">
            <div class="car-title-normal">{name}</div>
            <div class="badge-placeholder"></div>
            {img_html}
            <div class="car-info">👤 Владелец: <b>{owner}</b></div>
        </div>
        """
    st.markdown(card_html, unsafe_allow_html=True)

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
                render_car_card_html(name, photo_data, photo_url, owner, rarity)
                
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
                render_car_card_html(name, photo_data, photo_url, owner, rarity)
                st.warning(f"💵 Цена: **${price}**")

                st.markdown(f"🔗 [Скачать мод]({mod_link})")
                st.download_button(
                    label=f"📥 Скачать {pc_filename}",
                    data=pc_data,
                    file_name=pc_filename,
                    mime="text/plain",
                    key=f"dl_market_{car_id}"
                )

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
        c.execute("""SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, price, is_for_sale, is_approved, rarity 
                     FROM garage WHERE owner = ?""", (current_user,))
        my_cars = c.fetchall()
        conn.close()

        if not my_cars:
            st.info("У вас пока нет добавленных машин в гараже.")
        else:
            for car in my_cars:
                car_id, name, mod_link, pc_filename, pc_data, photo_url, photo_data, price, is_for_sale, is_approved, rarity = car
                
                exp_label = f"🔥 {name} (ID: {car_id}) [ЛЕГЕНДАРНАЯ]" if rarity == "🔥 Легендарная" else f"🚘 {name} (ID: {car_id})"
                with st.expander(exp_label):
                    col_img, col_info = st.columns([1, 2])
                    with col_img:
                        render_car_card_html(name, photo_data, photo_url, current_user, rarity)
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

# --- 4. БИРЖА (ВВЕДИТЕ ТЕКСТ) ---
elif page == "📈 Биржа (Введите Текст)":
    st.title("📈 Биржа Валют и Скачков Рынка")
    st.write("Зарабатывайте на пампе и дампе! Учитывайте комиссии 3% и новостной фон.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT symbol, name, price, history, last_news FROM crypto_coins")
    coins = c.fetchall()
    conn.close()

    if not coins:
        st.info("Биржа временно закрыта.")
    else:
        coin_dict = {f"{c[1]} ({c[0]})": c for c in coins}
        selected_coin_label = st.selectbox("Выберите актив для торговли:", list(coin_dict.keys()))
        selected_coin = coin_dict[selected_coin_label]
        
        symbol, coin_name, price, history_str, last_news = selected_coin
        history_list = [float(x) for x in history_str.split(",") if x]
        
        if not last_news:
            last_news = "На рынке затишье."

        # Показываем блок новостей
        st.markdown(f"""
        <div class="news-box">
            <b>📰 Лента Новостей:</b> {last_news}
        </div>
        """, unsafe_allow_html=True)

        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            prev_price = history_list[-2] if len(history_list) > 1 else price
            diff = price - prev_price
            percent_change = (diff / prev_price) * 100 if prev_price else 0
            
            st.metric(label=f"Текущий курс {coin_name} ({symbol})", value=f"${price:.2f}", delta=f"{percent_change:+.2f}%")
            
            # График
            df_chart = pd.DataFrame({"Курс ($)": history_list})
            st.line_chart(df_chart)

        with col_m2:
            st.subheader("⚡ Симуляция скачка")
            st.caption("Каждый клик имитирует новые события на рынке!")
            if st.button("📊 Спровоцировать скачок цен"):
                # Выбираем случайную новость
                news_text, min_mult, max_mult = random.choice(MARKET_NEWS)
                multiplier = 1 + random.uniform(min_mult, max_mult)
                
                new_price = max(1.0, round(price * multiplier, 2))
                
                history_list.append(new_price)
                if len(history_list) > 25:
                    history_list.pop(0)
                
                new_history_str = ",".join(map(str, history_list))
                
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("UPDATE crypto_coins SET price = ?, history = ?, last_news = ? WHERE symbol = ?", 
                          (new_price, new_history_str, news_text, symbol))
                conn.commit()
                conn.close()
                st.rerun()

        st.markdown("---")
        st.subheader("🛒 Торговый Терминал")

        if not st.session_state.logged_user:
            st.warning("⚠️ Войдите в аккаунт, чтобы торговать на бирже.")
        else:
            user = st.session_state.logged_user
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE username = ?", (user,))
            user_balance = c.fetchone()[0]
            
            c.execute("SELECT amount, avg_buy_price FROM user_crypto WHERE username = ? AND symbol = ?", (user, symbol))
            crypto_row = c.fetchone()
            user_crypto_amount = crypto_row[0] if crypto_row else 0.0
            avg_buy_price = crypto_row[1] if crypto_row else 0.0
            conn.close()

            # Считаем прибыльность портфеля
            current_val = user_crypto_amount * price
            invested_val = user_crypto_amount * avg_buy_price
            pnl_dollars = current_val - invested_val
            pnl_percent = (pnl_dollars / invested_val * 100) if invested_val > 0 else 0.0

            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                st.markdown(f"### 🟢 Купить {symbol}")
                st.write(f"Ваш баланс: **${user_balance}**")
                
                buy_amount = st.number_input(f"Количество {symbol}", min_value=0.1, step=1.0, value=1.0, key="buy_amt")
                gross_cost = buy_amount * price
                fee = gross_cost * FEE_PERCENT
                total_cost = gross_cost + fee
                
                st.write(f"Сумма: **${gross_cost:.2f}** + Комиссия 3%: **${fee:.2f}**")
                st.write(f"**Итого спишется:** <span style='color:#ff4b4b;'>${total_cost:.2f}</span>", unsafe_allow_html=True)
                
                if st.button(f"🟢 Купить {symbol}"):
                    if user_balance >= total_cost:
                        new_bal = user_balance - total_cost
                        new_amount = user_crypto_amount + buy_amount
                        
                        # Перерасчет средней цены входа
                        new_avg_price = ((user_crypto_amount * avg_buy_price) + total_cost) / new_amount
                        
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_bal, user))
                        c.execute("""INSERT INTO user_crypto (username, symbol, amount, avg_buy_price) 
                                     VALUES (?, ?, ?, ?) 
                                     ON CONFLICT(username, symbol) DO UPDATE SET amount = ?, avg_buy_price = ?""",
                                  (user, symbol, new_amount, new_avg_price, new_amount, new_avg_price))
                        conn.commit()
                        conn.close()
                        st.success(f"Успешно куплено {buy_amount} {symbol}!")
                        st.rerun()
                    else:
                        st.error("Недостаточно денег на балансе с учетом комиссии!")

            with col_b2:
                st.markdown(f"### 🔴 Продать {symbol}")
                st.write(f"В наличии: **{user_crypto_amount:.2f} {symbol}**")
                if user_crypto_amount > 0:
                    st.write(f"Средняя покупка: **${avg_buy_price:.2f}** | PnL: **{pnl_dollars:+.2f}$ ({pnl_percent:+.2f}%)**")
                
                sell_amount = st.number_input(f"Количество на продажу", min_value=0.1, max_value=max(0.1, user_crypto_amount), step=1.0, value=min(1.0, max(0.1, user_crypto_amount)), key="sell_amt")
                gross_payout = sell_amount * price
                sell_fee = gross_payout * FEE_PERCENT
                net_payout = gross_payout - sell_fee
                
                st.write(f"Сумма: **${gross_payout:.2f}** - Комиссия 3%: **${sell_fee:.2f}**")
                st.write(f"**Итого зачислится:** <span style='color:#00f5d4;'>${net_payout:.2f}</span>", unsafe_allow_html=True)
                
                if st.button(f"🔴 Продать {symbol}"):
                    if user_crypto_amount >= sell_amount:
                        new_bal = user_balance + net_payout
                        new_amount = user_crypto_amount - sell_amount
                        
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_bal, user))
                        c.execute("UPDATE user_crypto SET amount = ? WHERE username = ? AND symbol = ?", (new_amount, user, symbol))
                        conn.commit()
                        conn.close()
                        st.success(f"Успешно продано {sell_amount} {symbol}!")
                        st.rerun()
                    else:
                        st.error("У вас нет столько монет!")

# --- 5. ПРОФИЛЬ ---
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
        
        c.execute("SELECT symbol, amount, avg_buy_price FROM user_crypto WHERE username = ? AND amount > 0", (current_user,))
        user_cryptos = c.fetchall()
        conn.close()
        
        balance = user_info[0] if user_info else 0
        job = user_info[1] if user_info else "Безработный"
        total_cars = car_stats[0] if car_stats else 0
        approved_cars = car_stats[1] if car_stats else 0

        crypto_str = ", ".join([f"{amt:.2f} {sym}" for sym, amt, _ in user_cryptos]) if user_cryptos else "Нет активов"

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2f, #111118); padding: 25px; border-radius: 15px; border: 2px solid #4f46e5; box-shadow: 0 0 15px rgba(79, 70, 229, 0.4); margin-bottom: 25px;">
            <h2 style="margin-top: 0; color: #818cf8;">👤 Игрок: {current_user}</h2>
            <hr style="border-color: #374151;">
            <p style="font-size: 18px;">💰 <b>Баланс:</b> <span style="color: #34d399;">${balance}</span></p>
            <p style="font-size: 18px;">💼 <b>Работа:</b> <span style="color: #fbbf24;">{job}</span></p>
            <p style="font-size: 18px;">📈 <b>Криптоактивы:</b> <span style="color: #38bdf8;">{crypto_str}</span></p>
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

# --- 6. КАЗИНО ---
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

        if user_balance < 10:
            st.error("❌ У вас недостаточно средств для игры в казино (минимальная ставка: $10). Пополните баланс на работе или продажей авто.")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                max_bet = user_balance
                default_bet = min(100, user_balance)
                
                bet_amount = st.number_input("Размер ставки ($)", min_value=10, max_value=max_bet, value=default_bet, step=10)
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
                        play_audio(SOUND_SPIN)
                        
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
                            play_audio(SOUND_WIN)
                            st.balloons()
                            st.success(f"🎉 ПОБЕДА! Выпало число **{winning_num} ({winning_color})**.\n\nВы выиграли **${payout}**! Баланс обновлен.")
                        else:
                            new_bal = user_balance - bet_amount
                            play_audio(SOUND_LOSE)
                            st.error(f"❌ ПРОИГРЫШ! Выпало число **{winning_num} ({winning_color})**.\n\nВы потеряли **${bet_amount}**.")
                            
                        c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_bal, current_user))
                        conn.commit()
                        conn.close()
                else:
                    st.info("👈 Настройте ставку слева и нажмите **«Вращать рулетку»**.")

# --- 7. СВАЛКА (УТИЛИЗАЦИЯ) ---
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

# --- 8. ИГРОКИ И БАЛАНСЫ ---
elif page == "💰 Игроки и Балансы":
    st.title("💰 Экономика и Список Игроков")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT username AS 'Игрок', balance AS 'Баланс ($)', job AS 'Работа' FROM users", conn)
    conn.close()
    
    if df.empty:
        st.info("Игроков пока нет.")
    else:
        st.dataframe(df, use_container_width=True)

# --- 9. ДОБАВИТЬ МАШИНУ ---
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

# --- 10. ПАНЕЛЬ АДМИНИСТРАТОРА ---
elif page == "👑 Панель Администратора":
    st.title("👑 Управление Сервером (Админ)")
    
    admin_pass = st.text_input("Введите пароль администратора", type="password")
    
    if admin_pass == ADMIN_PASSWORD and ADMIN_PASSWORD != "":
        st.success("Доступ разрешен!")
        
        tab1, tab2, tab3, tab4 = st.tabs(["👥 Игроки", "🏎️ Редактирование Машин", "🛡️ Модерация машин", "🪙 Создание монет"])
        
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
                    
                    render_car_card_html(p_name, p_photo_data, p_photo, p_owner, "Обычная")
                    
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

        with tab4:
            st.subheader("🪙 Создание новой валюты на бирже")
            with st.form("add_coin_form"):
                new_symbol = st.text_input("Тикер / Символ монеты (например: BTC, DOGE)").upper()
                new_coin_name = st.text_input("Полное название (например: Bitcoin)")
                start_price = st.number_input("Стартовая цена ($)", min_value=1.0, value=100.0, step=10.0)
                
                coin_submit = st.form_submit_button("➕ Создать новую валюту")
                if coin_submit:
                    if new_symbol and new_coin_name:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        init_hist = f"{start_price*0.9:.1f},{start_price*0.95:.1f},{start_price:.1f}"
                        try:
                            c.execute("INSERT INTO crypto_coins (symbol, name, price, history, last_news) VALUES (?, ?, ?, ?, ?)",
                                      (new_symbol, new_coin_name, start_price, init_hist, "Валюта впервые вышла на биржу!"))
                            conn.commit()
                            st.success(f"Монета {new_coin_name} ({new_symbol}) успешно добавлена на биржу!")
                        except sqlite3.IntegrityError:
                            st.error("Монета с таким тикером уже существует!")
                        conn.close()
                        st.rerun()
                    else:
                        st.error("Заполните все поля!")
