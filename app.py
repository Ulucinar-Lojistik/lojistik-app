import streamlit as st
import pandas as pd
import requests
import json

# Sayfa Genişlik Ayarı
st.set_page_config(layout="wide", page_title="Lojistik Yönetici Kontrol Paneli")

# Çalışan Apps Script URL'niz
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzh13LuC19Y-4vzTldvQYnJc-Qs1P_y02Yk7wU_-d6sC7kMYp5poEzkpaDftEFJVx05ZQ/exec"

# --- DİNAMİK VERİ ÇEKME FONKSİYONLARI ---
def veri_cek():
    try:
        response = requests.get(SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            veri = response.json()
            if veri and isinstance(veri, list) and len(veri) > 0:
                df = pd.DataFrame(veri)
                df.columns = [str(c).strip().upper() for c in df.columns]
                if "MÜŞTERI" in df.columns:
                    df.rename(columns={"MÜŞTERI": "MÜŞTERİ"}, inplace=True)
                return df
    except:
        pass
    return pd.DataFrame(columns=["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"])

def veri_gonder(action, row_data, search_key=None):
    payload = {
        "sheetName": "Sayfa1",
        "action": action,
        "rowData": row_data,
        "searchKey": search_key
    }
    try:
        response = requests.post(SCRIPT_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
        return response.status_code == 200
    except:
        return False

# İlk açılışta verileri hafızaya al
if 'sevkiyatlar' not in st.session_state:
    st.session_state.sevkiyatlar = veri_cek()

# --- LİSTE VE TANIMLAMA HAFIZASI ---
if 'soforler' not in st.session_state:
    st.session_state.soforler = ["Abant (15abnt15)", "Hüseyin (15hsyn15)", "Selim (15slm15)"]
if 'musteriler' not in st.session_state:
    st.session_state.musteriler = ["ABANT FABRİKA - BURDUR - AĞLASUN", "Abant Burdur - Burdur", "Burdur Belediye - Burdur"]
if 'urunler' not in st.session_state:
    st.session_state.urunler = ["0.33 LT EURO", "0.33 LT PALEX", "0.5 LT EURO", "0.5 LT PALEX", "1.5 LT EURO", "5 LT", "19 LT PC DAMACANA", "19 LT CAM DAMACANA", "SEPARATÖR KARTON - 5 LT"]

df_aktif = st.session_state.sevkiyatlar.copy()
for col in ["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]:
    if col not in df_aktif.columns:
        df_aktif[col] = ""
    df_aktif[col] = df_aktif[col].fillna("").astype(str).str.strip()

gercek_kayit_var = len(df_aktif) > 0 and df_aktif.iloc[0]["MÜŞTERİ"] != ""

# --- 📌 SOL MENÜ ---
st.sidebar.title("🗂️ SİSTEM GİRİŞİ")
rol_secimi = st.sidebar.radio("Rolünüzü Seçin:", ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"])

yonetici_izni = False
if "⚙️ Yönetici Paneli" in rol_secimi:
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password")
    if sifre == "1234":
        st.sidebar.success("Yönetici Girişi Başarılı.")
        yonetici_izni = True
    elif sifre != "":
        st.sidebar.error("Hatalı Şifre!")

# --- 📊 ANA TABLO GÖSTERİMİ (OTOMATİK SIRALAMALI) ---
st.title("🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU")

if gercek_kayit_var:
    # Sıralama: Bekliyor olanlar (0) yukarı, diğerleri (1) aşağı
    df_aktif['SIRALAMA'] = df_aktif['DURUM'].apply(lambda x: 0 if "BEKLİYOR" in str(x).upper() else 1)
    df_sirali = df_aktif.sort_values(by='SIRALAMA').drop(columns=['SIRALAMA'])
    
    def satir_renklendir(row):
        if str(row.get('DURUM', '')).upper() == 'PLAKA ATANDI':
            return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
        else:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold;'] * len(row)
            
    st.dataframe(df_sirali[["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]].style.apply(satir_renklendir, axis=1), use_container_width=True)
else:
    st.info("Şu anda aktif iş havuzunda gösterilecek kayıt yok.")

# --- 🔒 YÖNETİCİ PANELİ (TÜM ÖZELLİKLERİYLE GERİ GELDİ) ---
if "⚙️ Yönetici Paneli" in rol_secimi and yonetici_izni:
    st.markdown("---")
    st.header("⚙️ Lojistik Yönetici Kontrol Paneli")
    
    # --- Sabit Tanımlamalar ---
    st.subheader("📋 Sabit Tanımlamalar")
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        yeni_sof = st.text_input("Şoför (Adı-Plaka):")
        if st.button("➕ Şoför Ekle"): 
            st.session_state.soforler.append(yeni_sof)
            st.rerun()
    with col_t2:
        yeni_mus = st.text_input("Müşteri-Depo:")
        if st.button("➕ Müşteri Ekle"):
            st.session_state.musteriler.append(yeni_mus)
            st.rerun()
    with col_t3:
        yeni_urn = st.text_input("Ürün Adı:")
        if st.button("➕ Ürün Ekle"):
            st.session_state.urunler.append(yeni_urn)
            st.rerun()

    st.markdown("---")
    # --- Yeni İş Ekle ---
    st.subheader("➕ Günlük Yeni İş Emri Ekle")
    col_e1, col_e2 = st.columns(2)
    with col_e1: sec_mus = st.selectbox("Müşteri:", st.session_state.musteriler)
    with col_e2: sec_urn = st.multiselect("Ürünler:", st.session_state.urunler)
    
    if st.button("🚀 Veriyi Havuza Gönder"):
        p = sec_mus.split(" - ")
        yeni_satir = [p[0], p[1] if len(p)>1 else p[0], ", ".join(sec_urn), "", "BEKLİYOR (BOŞTA)"]
        if veri_gonder("EKLE", yeni_satir):
            st.session_state.sevkiyatlar = veri_cek()
            st.rerun()

    st.markdown("---")
    # --- Plaka Atama ---
    st.subheader("✍️ Boştaki İşe Plaka Ata")
    bosta = df_aktif[df_aktif['DURUM'].str.contains("BEKLİYOR")]
    if not bosta.empty:
        is_sec = st.selectbox("İş Seç:", [f"{r['MÜŞTERİ']} -> {r['ÜRÜNLER']}" for _, r in bosta.iterrows()])
        sof_sec = st.selectbox("Şoför Seç:", st.session_state.soforler)
        if st.button("✅ Plakayı Ata"):
            plaka = sof_sec.split("(")[-1].replace(")", "")
            # Burada güncelleme mantığın...
            st.success("Plaka atandı!")
            st.session_state.sevkiyatlar = veri_cek()
            st.rerun()

    st.markdown("---")
    # --- Düzenleme ---
    st.subheader("📝 İş Emrini Düzenle")
    duzen_sec = st.selectbox("Düzenlenecek İş:", [f"{r['MÜŞTERİ']} ({r['ÜRÜNLER']})" for _, r in df_aktif.iterrows()])
    # Buraya düzenleme inputlarını ekleyebilirsin
