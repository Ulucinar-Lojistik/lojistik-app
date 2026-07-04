import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(layout="wide", page_title="Lojistik Yönetici Kontrol Paneli")

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzh13LuC19Y-4vzTldvQYnJc-Qs1P_y02Yk7wU_-d6sC7kMYp5poEzkpaDftEFJVx05ZQ/exec"

# --- VERİ İŞLEMLERİ ---
def veri_cek():
    try:
        response = requests.get(SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            veri = response.json()
            if veri and isinstance(veri, list) and len(veri) > 0:
                df = pd.DataFrame(veri)
                df.columns = [str(c).strip().upper() for c in df.columns]
                if "MÜŞTERI" in df.columns: df.rename(columns={"MÜŞTERI": "MÜŞTERİ"}, inplace=True)
                return df
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
if 'urunler' not in st.session_state: st.session_state.urunler = ["0.33 LT EURO", "0.33 LT PALEX", "0.5 LT EURO", "0.5 LT PALEX", "1.5 LT EURO", "5 LT", "19 LT PC DAMACANA", "19 LT CAM DAMACANA"]

# --- ARAYÜZ ---
st.sidebar.title("🗂️ SİSTEM GİRİŞİ")
rol_secimi = st.sidebar.radio("Rolünüzü Seçin:", ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"])
yonetici_izni = (rol_secimi == "⚙️ Yönetici Paneli (Veri Giriş)" and st.sidebar.text_input("Yönetici Şifresi:", type="password") == "1234")

st.title("🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU")
df_aktif = st.session_state.sevkiyatlar.copy()
if not df_aktif.empty:
    df_aktif['SIRALAMA'] = df_aktif['DURUM'].apply(lambda x: 0 if "BEKLİYOR" in str(x).upper() else 1)
    df_sirali = df_aktif.sort_values(by='SIRALAMA').drop(columns=['SIRALAMA'])
    def renk(row):
        return ['background-color: #d4edda;' if 'PLAKA ATANDI' in str(row['DURUM']) else 'background-color: #fff3cd;'] * len(row)
    st.dataframe(df_sirali.style.apply(renk, axis=1), use_container_width=True)
else: st.info("Havuz boş.")

if yonetici_izni:
    st.header("⚙️ Lojistik Yönetici Kontrol Paneli")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        yeni_sof = st.text_input("Şoför Adı-Plaka:")
        if st.button("➕ Şoför Ekle"): st.session_state.soforler.append(yeni_sof); st.rerun()
    with col2:
        yeni_mus = st.text_input("Müşteri-Depo:")
        if st.button("➕ Müşteri Ekle"): st.session_state.musteriler.append(yeni_mus); st.rerun()
    with col3:
        yeni_urn = st.text_input("Ürün Adı:")
        if st.button("➕ Ürün Ekle"): st.session_state.urunler.append(yeni_urn); st.rerun()

    st.subheader("➕ Yeni İş Emri")
    c1, c2 = st.columns(2)
    with c1: mus_sec = st.selectbox("Müşteri:", st.session_state.musteriler)
    with c2: urn_sec = st.multiselect("Ürünler:", st.session_state.urunler)
    if st.button("🚀 Havuza Gönder"):
        p = mus_sec.split(" - ")
        if veri_gonder("EKLE", [p[0], p[1] if len(p)>1 else p[0], ", ".join(urn_sec), "", "BEKLİYOR (BOŞTA)"]):
            st.session_state.sevkiyatlar = veri_cek(); st.rerun()

    st.subheader("✍️ Plaka Atama")
    bosta = df_aktif[df_aktif['DURUM'].str.contains("BEKLİYOR", na=False)]
    if not bosta.empty:
        is_sec = st.selectbox("İş Seç:", [f"{r['MÜŞTERİ']} -> {r['ÜRÜNLER']}" for _, r in bosta.iterrows()])
        sof_sec = st.selectbox("Şoför:", st.session_state.soforler)
        if st.button("✅ Atamayı Yap"):
            plaka = sof_sec.split("(")[-1].replace(")", "")
            # Güncelleme mantığı buraya...
            st.session_state.sevkiyatlar = veri_cek(); st.rerun()

    st.subheader("📝 Düzenleme")
    duz_sec = st.selectbox("Düzenlenecek İş:", [f"{r['MÜŞTERİ']} ({r['ÜRÜNLER']})" for _, r in df_aktif.iterrows()])
    if st.button("🗑️ Sil / Güncelle"): st.session_state.sevkiyatlar = veri_cek(); st.rerun()
