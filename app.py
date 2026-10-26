import base64
import random
import re
import time
import pandas as pd
import psycopg2  # Используем PostgreSQL вместо sqlite3
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Portal BeamNG RP", page_icon="🏎️", layout="wide")

# Авто-обновление страницы каждые 10 секунд
st_autorefresh(interval=10000, key="crypto_ticker_refresh")

ADMIN_PASSWORD = st.secrets.get("admin_password", "1234")
DATABASE_URL = st.secrets.get(
    "DATABASE_URL", ""
)  дл  # Строка подключения из Secrets
FIXED_SCRAP_PAYOUT = 800
FEE_PERCENT = 0.03  # 3% комиссия биржи


def get_db():
  """Подключение к облачной базе данных PostgreSQL"""
  return psycopg2.connect(DATABASE_URL, sslmode="require")


# Аудио-ссылки для казино
SOUND_SPIN = "https://assets.mixkit.co/active_storage/sfx/2004/2004-preview.mp3"
SOUND_WIN = "https://assets.mixkit.co/active_storage/sfx/1435/1435-preview.mp3"
SOUND_LOSE = "https://assets.mixkit.co/active_storage/sfx/2019/2019-preview.mp3"

MARKET_NEWS = [
    ("🚀 Илон Маск опубликовал твит про монету!", 0.30, 0.60),
    ("💀 ВНИМАНИЕ: Крупный кит слил все активы! ДАМП!", -0.70, -0.40),
    ("⚠️ Крупный крипто-фонд зафиксировал прибыль.", -0.25, -0.10),
    ("🔥 Прошло успешное сжигание монет! Дефицит на рынке!", 0.20, 0.45),
    ("📉 Правительство вводит жесткие налоги на крипту.", -0.35, -0.15),
    ("🏛️ Банк добавил валюту в инвест-портфель.", 0.15, 0.35),
    ("📊 Обычные торги, манипуляции мелких трейдеров.", -0.05, 0.05),
]


def play_audio(url):
  audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="{url}" type="audio/mp3">
        </audio>
    """
  st.markdown(audio_html, unsafe_allow_html=True)


# Стили
st.markdown(
    """
<style>
@keyframes psychoFlash {
    0% { border-color: #ff0055; box-shadow: 0 0 35px #ff0055, inset 0 0 25px #ff0055; filter: hue-rotate(0deg); }
    33% { border-color: #00ffcc; box-shadow: 0 0 45px #00ffcc, inset 0 0 35px #00ffcc; }
    66% { border-color: #ffff00; box-shadow: 0 0 40px #ffff00, inset 0 0 30px #ffff00; }
    100% { border-color: #ff00ff; box-shadow: 0 0 55px #ff00ff, inset 0 0 40px #ff00ff; filter: hue-rotate(360deg); }
}
.psycho-legendary-card, .rare-card, .normal-card {
    box-sizing: border-box; width: 100%; border-radius: 16px; padding: 15px; margin-bottom: 15px; border: 4px solid;
}
.psycho-legendary-card {
    background: linear-gradient(135deg, #1a002c 0%, #0a0a16 50%, #200010 100%);
    animation: psychoFlash 1.2s infinite alternate ease-in-out;
}
.rare-card { border-color: #00bfff; background: rgba(10, 25, 40, 0.9); box-shadow: 0 0 15px rgba(0, 191, 255, 0.4); }
.normal-card { border-color: #333333; background: rgba(20, 20, 20, 0.8); }
.car-title-legendary {
    font-size: 20px; font-weight: 900; text-align: center;
    background: linear-gradient(90deg, #ff0055, #00ffcc, #ffff00, #ff00ff, #ff0055);
    background-size: 300% 300%; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 5px; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.car-title-rare { font-size: 20px; font-weight: bold; text-align: center; color: #00bfff; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.car-title-normal { font-size: 20px; font-weight: bold; text-align: center; color: #fff; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.legendary-badge {
    background: linear-gradient(90deg, #ff0055, #9900ff); color: white; text-align: center; font-size: 10px;
    font-weight: bold; padding: 4px; border-radius: 6px; margin-bottom: 10px; letter-spacing: 1px; box-shadow: 0 0 15px #ff0055; text-transform: uppercase;
}
.badge-placeholder { height: 22px; margin-bottom: 10px; }
.car-img { width: 100%; height: 160px; object-fit: cover; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); margin-bottom: 10px; }
.car-info { text-align: center; color: #ccc; font-size: 14px; }
.news-box { background: rgba(30, 41, 59, 0.8); border-left: 4px solid #38bdf8; padding: 12px; border-radius: 6px; margin-bottom: 15px; }
</style>
""",
    unsafe_allow_html=True,
)


def init_db():
  if not DATABASE_URL:
    st.error(
        "❌ Не найдена переменная `DATABASE_URL` в Streamlit Secrets! Добавьте"
        " её."
    )
    return

  conn = get_db()
  c = conn.cursor()

  c.execute("""CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, balance INTEGER, job TEXT, password TEXT)""")

  c.execute("""CREATE TABLE IF NOT EXISTS garage 
                 (id SERIAL PRIMARY KEY, 
                  car_name TEXT, 
                  mod_link TEXT, 
                  pc_filename TEXT, 
                  pc_data BYTEA, 
                  photo_url TEXT, 
                  photo_data BYTEA,
                  owner TEXT, 
                  price INTEGER DEFAULT 0, 
                  is_for_sale INTEGER DEFAULT 0,
                  is_approved INTEGER DEFAULT 0,
                  rarity TEXT DEFAULT 'Обычная')""")

  c.execute("""CREATE TABLE IF NOT EXISTS crypto_coins 
                 (symbol TEXT PRIMARY KEY, name TEXT, price REAL, history TEXT, last_news TEXT)""")

  c.execute("""CREATE TABLE IF NOT EXISTS user_crypto 
                 (username TEXT, symbol TEXT, amount REAL, avg_buy_price REAL DEFAULT 0, PRIMARY KEY (username, symbol))""")

  c.execute("SELECT COUNT(*) FROM crypto_coins")
  if c.fetchone()[0] == 0:
    c.execute(
        "INSERT INTO crypto_coins (symbol, name, price, history, last_news)"
        " VALUES (%s, %s, %s, %s, %s)",
        ("VVEDI", "Введите Текст", 100.0, "90,95,98,100", "Обычный день."),
    )

  conn.commit()
  c.close()
  conn.close()


init_db()

fn_fix_image_url = lambda url: (
    f"https://drive.google.com/uc?export=view&id={re.search(r'/file/d/([a-zA-Z0-9_-]+)', url).group(1)}"
    if url and re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
    else (
        f"https://drive.google.com/uc?export=view&id={re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url).group(1)}"
        if url and re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
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
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = %s", (login_user,))
        row = c.fetchone()
        c.close()
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
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT username FROM users WHERE username = %s", (login_user,)
        )
        if c.fetchone():
          st.sidebar.error("Игрок с таким ником уже существует!")
        else:
          c.execute(
              "INSERT INTO users (username, balance, job, password) VALUES"
              " (%s, 1000, 'Безработный', %s)",
              (login_user, login_pass),
          )
          conn.commit()
          c.close()
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
page = st.sidebar.radio(
    "Разделы",
    [
        "🏎️ Общий Гараж",
        "🏷️ Авторынок",
        "🅿️ Мой Гараж",
        "📈 Биржа (Введите Текст)",
        "👤 Профиль",
        "🎰 Казино",
        "♻️ Свалка (Утилизация)",
        "💰 Игроки и Балансы",
        "➕ Добавить машину",
        "👑 Панель Администратора",
    ],
)


def render_car_card_html(name, photo_data, photo_url, owner, rarity):
  img_html = ""
  if photo_data:
    b64 = base64.b64encode(photo_data).decode()
    img_html = f'<img src="data:image/png;base64,{b64}" class="car-img">'
  elif photo_url:
    fixed_url = fn_fix_image_url(photo_url)
    img_html = f'<img src="{fixed_url}" class="car-img">'
  else:
    img_html = (
        '<div style="height:160px; display:flex; align-items:center;'
        ' justify-content:center; color:#777; background:#111;'
        ' border-radius:8px; margin-bottom:10px;">Нет изображения</div>'
    )

  if rarity == "🔥 Легендарная":
    st.markdown(
        f"""
        <div class="psycho-legendary-card">
            <div class="car-title-legendary">⚡ {name} ⚡</div>
            <div class="legendary-badge">🔥 Абсолютный психо-эксклюзив 🔥</div>
            {img_html}
            <div class="car-info">👤 Владелец: <b>{owner}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  elif rarity == "💎 Редкая":
    st.markdown(
        f"""
        <div class="rare-card">
            <div class="car-title-rare">💎 {name}</div>
            <div class="badge-placeholder"></div>
            {img_html}
            <div class="car-info">👤 Владелец: <b>{owner}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  else:
    st.markdown(
        f"""
        <div class="normal-card">
            <div class="car-title-normal">{name}</div>
            <div class="badge-placeholder"></div>
            {img_html}
            <div class="car-info">👤 Владелец: <b>{owner}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- 1. ОБЩИЙ ГАРАЖ ---
if page == "🏎️ Общий Гараж":
  st.title("🏎️ Общий Гараж сервера")
  conn = get_db()
  df_cars = pd.read_sql(
      "SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url,"
      " photo_data, owner, price, is_for_sale, rarity FROM garage WHERE"
      " is_approved = 1",
      conn,
  )
  conn.close()

  if df_cars.empty:
    st.info("В общем гараже пока нет одобренных машин.")
  else:
    cols = st.columns(3)
    for idx, row in df_cars.iterrows():
      col = cols[idx % 3]
      with col:
        render_car_card_html(
            row["car_name"],
            row["photo_data"],
            row["photo_url"],
            row["owner"],
            row["rarity"],
        )
        if row["is_for_sale"]:
          st.warning(f"🏷️ ПРОДАЕТСЯ НА РЫНКЕ: **${row['price']}**")
        else:
          st.info("🅿️ В личном пользовании")
        st.markdown(f"🔗 [Скачать мод]({row['mod_link']})")
        if row["pc_data"]:
          st.download_button(
              label=f"📥 Скачать {row['pc_filename']}",
              data=row["pc_data"],
              file_name=row["pc_filename"],
              mime="text/plain",
              key=f"dl_gen_{row['id']}",
          )
        st.markdown("---")

# --- 2. АВТОРЫНОК ---
elif page == "🏷️ Авторынок":
  st.title("🏷️ Авторынок")
  conn = get_db()
  df_market = pd.read_sql(
      "SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url,"
      " photo_data, owner, price, rarity FROM garage WHERE is_approved = 1 AND"
      " is_for_sale = 1",
      conn,
  )
  conn.close()

  if df_market.empty:
    st.info("На авторынке сейчас нет машин на продажу.")
  else:
    cols = st.columns(3)
    for idx, row in df_market.iterrows():
      col = cols[idx % 3]
      with col:
        render_car_card_html(
            row["car_name"],
            row["photo_data"],
            row["photo_url"],
            row["owner"],
            row["rarity"],
        )
        st.warning(f"💵 Цена: **${row['price']}**")
        st.markdown(f"🔗 [Скачать мод]({row['mod_link']})")
        if row["pc_data"]:
          st.download_button(
              label=f"📥 Скачать {row['pc_filename']}",
              data=row["pc_data"],
              file_name=row["pc_filename"],
              mime="text/plain",
              key=f"dl_market_{row['id']}",
          )

        if st.session_state.logged_user:
          if st.session_state.logged_user == row["owner"]:
            st.info("Это ваша машина.")
          else:
            if st.button(
                f"🛒 Купить за ${row['price']}", key=f"buy_market_{row['id']}"
            ):
              buyer = st.session_state.logged_user
              conn = get_db()
              c = conn.cursor()
              c.execute(
                  "SELECT balance FROM users WHERE username = %s", (buyer,)
              )
              bal_row = c.fetchone()
              if bal_row and bal_row[0] >= row["price"]:
                c.execute(
                    "UPDATE users SET balance = balance - %s WHERE username ="
                    " %s",
                    (row["price"], buyer),
                )
                c.execute(
                    "UPDATE users SET balance = balance + %s WHERE username ="
                    " %s",
                    (row["price"], row["owner"]),
                )
                c.execute(
                    "UPDATE garage SET owner = %s, is_for_sale = 0, price = 0"
                    " WHERE id = %s",
                    (buyer, row["id"]),
                )
                conn.commit()
                c.close()
                conn.close()
                st.success("Успешно! Вы купили эту машину.")
                st.rerun()
              else:
                st.error("Недостаточно денег на балансе!")
                c.close()
                conn.close()
        st.markdown("---")

# --- 3. МОЙ ГАРАЖ ---
elif page == "🅿️ Мой Гараж":
  st.title("🅿️ Мой Личный Гараж")
  if not st.session_state.logged_user:
    st.warning("⚠️ Войдите в аккаунт.")
  else:
    user = st.session_state.logged_user
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url,"
        " photo_data, price, is_for_sale, is_approved, rarity FROM garage WHERE"
        " owner = %s",
        (user,),
    )
    my_cars = c.fetchall()
    c.close()
    conn.close()

    if not my_cars:
      st.info("У вас нет машин.")
    else:
      for car in my_cars:
        car_id, name, mod_link, pc_filename, pc_data, photo_url, photo_data, price, is_for_sale, is_approved, rarity = (
            car
        )
        with st.expander(f"🚘 {name} (ID: {car_id})"):
          col1, col2 = st.columns([1, 2])
          with col1:
            render_car_card_html(name, photo_data, photo_url, user, rarity)
          with col2:
            if is_approved == 0:
              st.error("⏳ На модерации")
            else:
              st.success("✅ Одобрено")
            st.markdown(f"🔗 [Мод]({mod_link})")
            if pc_data:
              st.download_button(
                  "📥 Скачать .pc",
                  pc_data,
                  pc_filename,
                  key=f"dl_my_{car_id}",
              )
            with st.form(f"sale_form_{car_id}"):
              ns = st.checkbox("На продажу", value=bool(is_for_sale))
              np = st.number_input("Цена ($)", value=int(price), step=100)
              if st.form_submit_button("Сохранить"):
                conn = get_db()
                c = conn.cursor()
                c.execute(
                    "UPDATE garage SET is_for_sale = %s, price = %s WHERE id ="
                    " %s",
                    (1 if ns else 0, np, car_id),
                )
                conn.commit()
                c.close()
                conn.close()
                st.success("Сохранено!")
                st.rerun()

# --- 4. БИРЖА ---
elif page == "📈 Биржа (Введите Текст)":
  st.title("📈 Живая Криптобиржа")
  conn = get_db()
  c = conn.cursor()
  c.execute("SELECT symbol, name, price, history, last_news FROM crypto_coins")
  coins = c.fetchall()
  c.close()
  conn.close()

  if coins:
    symbol, coin_name, price, history_str, last_news = coins[0]
    history_list = [float(x) for x in history_str.split(",") if x]

    news_text, min_m, max_m = random.choice(MARKET_NEWS)
    new_price = max(1.0, round(price * (1 + random.uniform(min_m, max_m)), 2))
    history_list.append(new_price)
    if len(history_list) > 25:
      history_list.pop(0)

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE crypto_coins SET price = %s, history = %s, last_news = %s WHERE"
        " symbol = %s",
        (new_price, ",".join(map(str, history_list)), news_text, symbol),
    )
    conn.commit()
    c.close()
    conn.close()

    st.markdown(
        f'<div class="news-box"><b>📰 Новости:</b> {news_text}</div>',
        unsafe_allow_html=True,
    )
    st.metric(f"{coin_name} ({symbol})", f"${new_price:.2f}")
    st.line_chart(pd.DataFrame({"Курс": history_list}))

    if st.session_state.logged_user:
      user = st.session_state.logged_user
      conn = get_db()
      c = conn.cursor()
      c.execute("SELECT balance FROM users WHERE username = %s", (user,))
      bal = c.fetchone()[0]
      c.execute(
          "SELECT amount FROM user_crypto WHERE username = %s AND symbol = %s",
          (user, symbol),
      )
      cr_row = c.fetchone()
      cr_amt = cr_row[0] if cr_row else 0.0
      c.close()
      conn.close()

      col1, col2 = st.columns(2)
      with col1:
        buy_q = st.number_input("Кол-во для покупки", 1.0, step=1.0, key="bq")
        cost = buy_q * new_price * (1 + FEE_PERCENT)
        if st.button("Купить"):
          if bal >= cost:
            conn = get_db()
            c = conn.cursor()
            c.execute(
                "UPDATE users SET balance = balance - %s WHERE username = %s",
                (cost, user),
            )
            c.execute(
                "INSERT INTO user_crypto (username, symbol, amount) VALUES"
                " (%s, %s, %s) ON CONFLICT (username, symbol) DO UPDATE SET"
                " amount = user_crypto.amount + %s",
                (user, symbol, buy_q, buy_q),
            )
            conn.commit()
            c.close()
            conn.close()
            st.success("Куплено!")
            st.rerun()
          else:
            st.error("Не хватает денег")
      with col2:
        st.write(f"У вас: {cr_amt} {symbol}")
        sell_q = st.number_input(
            "Кол-во для продажи",
            0.1,
            max_value=max(0.1, cr_amt),
            step=1.0,
            key="sq",
        )
        payout = sell_q * new_price * (1 - FEE_PERCENT)
        if st.button("Продать"):
          if cr_amt >= sell_q:
            conn = get_db()
            c = conn.cursor()
            c.execute(
                "UPDATE users SET balance = balance + %s WHERE username = %s",
                (payout, user),
            )
            c.execute(
                "UPDATE user_crypto SET amount = amount - %s WHERE username ="
                " %s AND symbol = %s",
                (sell_q, user, symbol),
            )
            conn.commit()
            c.close()
            conn.close()
            st.success("Продано!")
            st.rerun()

# --- 5. ПРОФИЛЬ ---
elif page == "👤 Профиль":
  st.title("👤 Профиль")
  if st.session_state.logged_user:
    user = st.session_state.logged_user
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, job FROM users WHERE username = %s", (user,))
    u_info = c.fetchone()
    c.close()
    conn.close()
    st.write(
        f"Игрок: **{user}** | Баланс: **${u_info[0]}** | Работа: **{u_info[1]}**"
    )

# --- 6. КАЗИНО ---
elif page == "🎰 Казино":
  st.title("🎰 Казино")
  if st.session_state.logged_user:
    user = st.session_state.logged_user
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE username = %s", (user,))
    bal = c.fetchone()[0]
    c.close()
    conn.close()
    st.write(f"Баланс: ${bal}")
    bet = st.number_input("Ставка", 10, bal if bal >= 10 else 10, step=10)
    if st.button("Крутить"):
      play_audio(SOUND_SPIN)
      time.sleep(1)
      win = random.choice([True, False])
      conn = get_db()
      c = conn.cursor()
      if win:
        play_audio(SOUND_WIN)
        c.execute(
            "UPDATE users SET balance = balance + %s WHERE username = %s",
            (bet, user),
        )
        st.success(f"Выиграли ${bet}!")
      else:
        play_audio(SOUND_LOSE)
        c.execute(
            "UPDATE users SET balance = balance - %s WHERE username = %s",
            (bet, user),
        )
        st.error(f"Проиграли ${bet}")
      conn.commit()
      c.close()
      conn.close()
      st.rerun()

# --- 7. СВАЛКА ---
elif page == "♻️ Свалка (Утилизация)":
  st.title("♻️ Свалка")
  if st.session_state.logged_user:
    user = st.session_state.logged_user
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, car_name FROM garage WHERE owner = %s", (user,))
    cars = c.fetchall()
    c.close()
    conn.close()
    for cid, cname in cars:
      if st.button(f"Утилизировать {cname}", key=f"sc_{cid}"):
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "UPDATE users SET balance = balance + %s WHERE username = %s",
            (FIXED_SCRAP_PAYOUT, user),
        )
        c.execute("DELETE FROM garage WHERE id = %s", (cid,))
        conn.commit()
        c.close()
        conn.close()
        st.success("Утилизировано!")
        st.rerun()

# --- 8. ИГРОКИ И БАЛАНСЫ ---
elif page == "💰 Игроки и Балансы":
  st.title("💰 Игроки")
  conn = get_db()
  df = pd.read_sql(
      "SELECT username AS 'Игрок', balance AS 'Баланс ($)', job AS 'Работа' FROM"
      " users",
      conn,
  )
  conn.close()
  st.dataframe(df, use_container_width=True)

# --- 9. ДОБАВИТЬ МАШИНУ ---
elif page == "➕ Добавить машину":
  st.title("➕ Добавить авто")
  if st.session_state.logged_user:
    with st.form("add_car"):
      cname = st.text_input("Название")
      mlink = st.text_input("Ссылка на мод")
      photo = st.file_uploader("Фото", type=["png", "jpg"])
      pc = st.file_uploader("Конфиг .pc", type=["pc"])
      forsale = st.checkbox("На продажу")
      price = st.number_input("Цена", value=0)
      if st.form_submit_button("Отправить"):
        if cname and mlink and pc:
          pc_bytes = pc.read()
          photo_bytes = photo.read() if photo else None
          conn = get_db()
          c = conn.cursor()
          c.execute(
              """INSERT INTO garage (car_name, mod_link, pc_filename, pc_data, photo_url, photo_data, owner, price, is_for_sale, is_approved, rarity)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 'Обычная')""",
              (
                  cname,
                  mlink,
                  pc.name,
                  psycopg2.Binary(pc_bytes),
                  "",
                  psycopg2.Binary(photo_bytes) if photo_bytes else None,
                  st.session_state.logged_user,
                  price if forsale else 0,
                  1 if forsale else 0,
              ),
          )
          conn.commit()
          c.close()
          conn.close()
          st.success("Отправлено на модерацию!")

# --- 10. АДМИНКА ---
elif page == "👑 Панель Администратора":
  st.title("👑 Админка")
  apass = st.text_input("Пароль админа", type="password")
  if apass == ADMIN_PASSWORD and ADMIN_PASSWORD != "":
    st.success("Доступ разрешен")
    conn = get_db()
    df_pend = pd.read_sql(
        "SELECT id, car_name, owner FROM garage WHERE is_approved = 0", conn
    )
    conn.close()
    st.write("Машины на модерации:")
    for idx, row in df_pend.iterrows():
      st.write(f"ID: {row['id']} | {row['car_name']} (Владелец: {row['owner']})")
      if st.button(f"Одобрить #{row['id']}", key=f"app_{row['id']}"):
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE garage SET is_approved = 1 WHERE id = %s", (row["id"],))
        conn.commit()
        c.close()
        conn.close()
        st.success("Одобрено!")
        st.rerun()
