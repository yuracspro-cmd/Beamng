import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="BeamNG RP Portal", page_icon="🏎️", layout="wide")

DB_NAME = "beamng_rp.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, balance INTEGER, job TEXT)''')
    
    # Obnovlennaya tablitsa garazha s podderzhkoy prodazhi i tseny
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
    conn.commit()
    conn.close()

init_db()

st.sidebar.title("🎮 BeamNG.mp RP")
page = st.sidebar.radio("Razdely", [
    "🏎️ Garazh i Avtorinok", 
    "♻️ Svalka (Utilizatsiya)",
    "💰 Igroki i Balansy", 
    "➕ Dobavit mashinu", 
    "👑 Panel Admina"
])

# --- 1. GARAZH I AVTORINOK ---
if page == "🏎️ Garazh i Avtorinok":
    st.title("🏎️ Garazh i Avtorinok")
    st.write("Smotrite mashiny, kachayte .pc konfiguratsii ili pokupayte avto u drugikh igrokov!")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, car_name, mod_link, pc_filename, pc_data, photo_url, owner, price, is_for_sale FROM garage")
    cars = c.fetchall()
    conn.close()

    if not cars:
        st.info("V garazhe poka net mashin.")
    else:
        cols = st.columns(3)
        for idx, car in enumerate(cars):
            car_id, name, mod_link, pc_filename, pc_data, photo_url, owner, price, is_for_sale = car
            col = cols[idx % 3]
            
            with col:
                st.subheader(name)
                if photo_url:
                    st.image(photo_url, use_container_width=True)
                
                st.caption(f"👤 Vladalets: **{owner}**")
                
                if is_for_sale:
                    st.warning(f"🏷️ PRODAETSYA: **${price}**")
                else:
                    st.info("🅿️ Licheniy garazh (Ne prodatsya)")

                st.markdown(f"🔗 [Skachat mod]({mod_link})")
                
                st.download_button(
                    label=f"📥 Skachat {pc_filename}",
                    data=pc_data,
                    file_name=pc_filename,
                    mime="text/plain",
                    key=f"dl_{car_id}"
                )

                # Pokupka mashiny na avtorinke
                if is_for_sale:
                    st.markdown("---")
                    buyer_name = st.text_input(f"Vash nik dlya pokupki", key=f"buyer_{car_id}")
                    if st.button(f"🛒 Kupit za ${price}", key=f"buy_{car_id}"):
                        if buyer_name:
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            # Proverka balansa pokupatelya
                            c.execute("SELECT balance FROM users WHERE username = ?", (buyer_name,))
                            row = c.fetchone()
                            if row and row[0] >= price:
                                new_balance = row[0] - price
                                c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, buyer_name))
                                # Nachislenie deneg prodavtsu
                                c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (price, owner))
                                # Smena vladeltsa i snyatie s prodazhi
                                c.execute("UPDATE garage SET owner = ?, is_for_sale = 0 WHERE id = ?", (buyer_name, car_id))
                                conn.commit()
                                conn.close()
                                st.success("Uspeshno! Vy kupili etu mashinu.")
                                st.rerun()
                            else:
                                st.error("Nedostatochno deneg na balanse ili igrok ne nayden!")
                                conn.close()
                        else:
                            st.warning("Vvedite vash nik!")
                st.markdown("---")

# --- 2. SVALKA (UTILIZATSIYA) ---
elif page == "♻️ Svalka (Utilizatsiya)":
    st.title("♻️ Msnnovennaya utilizatsiya avto")
    st.write("Sdytie mashinu na svalku! Vy poluchite **30% ot ee tseny** mgnovenno, bez ozhidaniya pokupatelya.")

    owner_search = st.text_input("Vvedite vash nik, chtoby uvidet vashi mashiny:")
    
    if owner_search:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, car_name, price FROM garage WHERE owner = ?", (owner_search,))
        my_cars = c.fetchall()
        conn.close()

        if not my_cars:
            st.info("U vas net mashin v garazhe.")
        else:
            for car_id, name, price in my_cars:
                scrap_value = int(price * 0.3) if price > 0 else 300 # minimum $300 za lyubuyu
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"🚘 **{name}** (Otsenka: ${price}) -> Vykup svalki: **${scrap_value}**")
                with col2:
                    if st.button(f"♻️ Utylizirovat", key=f"scrap_{car_id}"):
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        # Dobavlyaem deneg igroku
                        c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (scrap_value, owner_search))
                        # Udalaem mashinu
                        c.execute("DELETE FROM garage WHERE id = ?", (car_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"Mashina utylizirovana! Vy poluchili ${scrap_value}.")
                        st.rerun()

# --- 3. IGROKI I BALANSY ---
elif page == "💰 Igroki i Balansy":
    st.title("💰 Ekonomika i Spisok Igrokov")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT username AS 'Igrok', balance AS 'Balans ($)', job AS 'Rabota' FROM users", conn)
    conn.close()
    
    if df.empty:
        st.info("Igrokov poka net.")
    else:
        st.dataframe(df, use_container_width=True)

# --- 4. DOBAVIT MASHINU ---
elif page == "➕ Dobavit mashinu":
    st.title("➕ Dobavlenie avto")
    
    with st.form("add_car_form"):
        car_name = st.text_input("Nazvanie mashiny")
        owner = st.text_input("Vash nikneym v igre")
        mod_link = st.text_input("Ssylka na mod")
        photo_url = st.text_input("Ssylka na skrinshot")
        price = st.number_input("Tsena mashiny ($)", value=1000, step=500)
        is_for_sale = st.checkbox("Vystavit srazu na Avtorinok?")
        uploaded_pc = st.file_uploader("Zagruzite .pc fayl", type=["pc"])
        
        submit = st.form_submit_button("Dobavit v garazh")
        
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
                st.success("Mashina uspeshno dobavlena!")
            else:
                st.error("Zapolnite vse polya i zagruzite .pc fayl!")

# --- 5. PANEL ADMINA (REDAKTIROVANIE I MASHIN I IGROKOV) ---
elif page == "👑 Panel Admina":
    st.title("👑 Upravlenie Serverom (Admin)")
    
    admin_pass = st.text_input("Vvedite parol admina", type="password")
    if admin_pass == "1234": # Pomenyay parol!
        st.success("Dostup razreshen!")
        
        tab1, tab2 = st.tabs(["👥 Igroki", "🏎️ Redaktirovanie Mashin"])
        
        with tab1:
            st.subheader("Izmenenie balansa / raboty")
            username = st.text_input("Nikneym igroka")
            balance = st.number_input("Balans ($)", value=1000, step=100)
            job = st.selectbox("Rabota", ["Kuryer", "Dalnoboyshchik", "Mekhanik", "Politseyskiy", "Bezrabotnyy"])
            
            if st.button("Sokhranit igroka"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO users (username, balance, job) VALUES (?, ?, ?)",
                          (username, balance, job))
                conn.commit()
                conn.close()
                st.success(f"Igrok {username} obnovlen!")

        with tab2:
            st.subheader("Redaktirovanie mashin v baze")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, car_name, owner, price, is_for_sale FROM garage")
            all_cars = c.fetchall()
            conn.close()

            if all_cars:
                car_options = {f"ID {c[0]}: {c[1]} (Vladalets: {c[2]})": c[0] for c in all_cars}
                selected_car_label = st.selectbox("Vyberite mashinu dlya redaktirovaniya", list(car_options.keys()))
                selected_car_id = car_options[selected_car_label]

                # Poluchaem tekushchie dannye mashiny
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT car_name, mod_link, photo_url, owner, price, is_for_sale FROM garage WHERE id = ?", (selected_car_id,))
                edit_car = c.fetchone()
                conn.close()

                if edit_car:
                    with st.form("edit_car_form"):
                        new_name = st.text_input("Nazvanie", value=edit_car[0])
                        new_mod = st.text_input("Ssylka na mod", value=edit_car[1])
                        new_photo = st.text_input("Ssylka na foto", value=edit_car[2])
                        new_owner = st.text_input("Vladelets", value=edit_car[3])
                        new_price = st.number_input("Tsena ($)", value=edit_car[4], step=100)
                        new_sale = st.checkbox("Na prodazhe (Avtorinok)", value=bool(edit_car[5]))

                        col_save, col_del = st.columns(2)
                        with col_save:
                            btn_save = st.form_submit_button("💾 Sokhranit izmeneniya")
                        
                        if btn_save:
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("""UPDATE garage SET 
                                         car_name=?, mod_link=?, photo_url=?, owner=?, price=?, is_for_sale=? 
                                         WHERE id=?""",
                                      (new_name, new_mod, new_photo, new_owner, new_price, 1 if new_sale else 0, selected_car_id))
                            conn.commit()
                            conn.close()
                            st.success("Mashina uspeshno otredaktirovana!")
                            st.rerun()

                    # Knopka udaleniya otndelno
                    if st.button("❌ Udalit mashinu iz bazy", key="del_car_admin"):
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("DELETE FROM garage WHERE id = ?", (selected_car_id,))
                        conn.commit()
                        conn.close()
                        st.warning("Mashina udalena!")
                        st.rerun()
