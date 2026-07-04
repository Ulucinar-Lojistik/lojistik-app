import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(layout="wide", page_title="Lojistik Yönetici Kontrol Paneli")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzh13LuC19Y-4vzTldvQYnJc-Qs1P_y02Yk7wU_-d6sC7kMYp5poEzkpaDftEFJVx05ZQ/exec"

# --- VERİ ÇEKME VE SIRALAMA ---
def veri_cek():
    try:
        response = requests.get(SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            veri = response.json()
            if veri and isinstance(veri, list) and len(veri) > 0:
                df = pd.DataFrame(veri)
                df.columns = [str(c).strip().upper() for c in df.columns]
                if "MÜŞTERI" in df.columns: df.rename(columns={"MÜŞTERI": "MÜŞTERİ"}, inplace=True)
                
                # Boştakileri üste taşıyan sıralama
                df['DURUM_ORDER'] = df['DURUM'].apply(lambda x: 0 if "BEKLİYOR" in str(x).upper() else 1)
                df = df.sort_values('DURUM_ORDER')
                return df.drop(columns=['DURUM_ORDER'])
    except: pass
    return pd.DataFrame(columns=["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"])

def veri_gonder(action, row_data, search_key=None):
    payload = {"sheetName": "Sayfa1", "action": action, "rowData": row_data, "searchKey": search_key}
    try:
        response = requests.post(SCRIPT_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
        return response.status_code == 200
    except: return False

if 'sevkiyatlar' not in st.session_state: st.session_state.sevkiyatlar = veri_cek()
if 'soforler' not in st.session_state: st.session_state.soforler = ["Abant (15abnt15)", "Hüseyin (15hsyn15)", "Selim (15slm15)"]
if 'musteriler' not in st.session_state: st.session_state.musteriler = ["ABANT FABRİKA - BURDUR - AĞLASUN", "Abant Burdur - Burdur", "Burdur Belediye - Burdur"]
if 'urunler' not in st.session_state: st.session_state.urunler = ["0.33 LT EURO", "0.33 LT PALEX", "0.5 LT EURO", "0.5 LT PALEX", "1.5 LT EURO", "5 LT", "19 LT PC DAMACANA", "19 LT CAM DAMACANA", "SEPARATÖR KARTON - 5 LT"]

# --- ARAYÜZ ---
st.title("🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU")
df_aktif = veri_cek()

if not df_aktif.empty:
    st.dataframe(df_aktif[["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]], use_container_width=True)
else: st.info("Havuz şu anda boş.")

st.sidebar.title("🗂️ SİSTEM GİRİŞİ")
rol = st.sidebar.radio("Rolünüzü Seçin:", ["🚚 Şoför Ekranı", "⚙️ Yönetici Paneli"])

if "Yönetici" in rol:
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password")
    if sifre == "1234":
        st.markdown("---")
        st.header("⚙️ Lojistik Yönetici Kontrol Paneli")
        
        # --- SABİT TANIMLAMALAR ---
        col1, col2, col3 = st.columns(3)
        with col1:
            sof = st.text_input("Şoför Adı:", key="s_ad")
            plk = st.text_input("Plaka:", key="s_plk")
            if st.button("➕ Şoförü Kaydet"):
                st.session_state.soforler.append(f"{sof} ({plk})")
                st.success(f"{sof} sisteme eklendi!")
                st.rerun()
        with col2:
            mus = st.text_input("Müşteri:", key="m_ad")
            dep = st.text_input("Depo:", key="d_ad")
            if st.button("➕ Depoyu Kaydet"):
                st.session_state.musteriler.append(f"{mus} - {dep}")
                st.success(f"{mus} eklendi!")
                st.rerun()
        with col3:
            urn = st.text_input("Ürün Adı:", key="u_ad")
            if st.button("➕ Ürünü Kaydet"):
                st.session_state.urunler.append(urn)
                st.success(f"{urn} eklendi!")
                st.rerun()

        st.markdown("---")
        st.subheader("➕ Günlük Yeni İş Emri Ekle")
        c1, c2 = st.columns(2)
        with c1: mus_sec = st.selectbox("Müşteri & Depo:", st.session_state.musteriler)
        with c2: urn_sec = st.multiselect("Ürünler:", st.session_state.urunler)
        if st.button("🚀 Havuza Gönder"):
            parcalar = mus_sec.split(" - ")
            if veri_gonder("EKLE", [parcalar[0], parcalar[1] if len(parcalar)>1 else parcalar[0], ", ".join(urn_sec), "", "BEKLİYOR (BOŞTA)"]):
                st.success("İş başarıyla eklendi!")
                st.rerun()
    else: st.warning("Şifre giriniz (1234).")
else: st.info("Şoför modundasınız, sadece izleyebilirsiniz.")
