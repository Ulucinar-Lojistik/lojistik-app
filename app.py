import streamlit as st
import pandas as pd
import requests
import json

# Sayfa Genişlik Ayarı
st.set_page_config(layout="wide", page_title="Lojistik Yönetici Kontrol Paneli")

# Çalışan Apps Script URL'niz
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzh13LuC19Y-4vzTldvQYnJc-Qs1P_y02Yk7wU_-d6sC7kMYp5poEzkpaDftEFJVx05ZQ/exec"

# --- DİNAMİK VERİ ÇEKME VE SIRALAMA FONKSİYONLARI ---
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
                
                # --- SIRALAMA MANTIĞI: BEKLİYOR OLANLAR ÜSTE ---
                # "BEKLİYOR" içeren satırlara 0, diğerlerine 1 değerini verir ve 0'ları üste dizer.
                df['DURUM_ORDER'] = df['DURUM'].apply(lambda x: 0 if "BEKLİYOR" in str(x).upper() else 1)
                df = df.sort_values('DURUM_ORDER')
                return df.drop(columns=['DURUM_ORDER'])
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

# Güncel veriyi çek ve sütun düzenini sağla
df_aktif = veri_cek()
for col in ["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]:
    if col not in df_aktif.columns:
        df_aktif[col] = ""
    df_aktif[col] = df_aktif[col].fillna("").astype(str).str.strip()

gercek_kayit_var = len(df_aktif) > 0 and df_aktif.iloc[0]["MÜŞTERİ"] != ""

# --- 📌 SOL MENÜ (SİSTEM GİRİŞİ) ---
st.sidebar.title("🗂️ SİSTEM GİRİŞİ")
rol_secimi = st.sidebar.radio(
    "Rolünüzü Seçin:",
    ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"],
    key="rol_secimi_key"
)

yonetici_izni = False
if "⚙️ Yönetici Paneli" in rol_secimi:
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password", key="yonetici_sifre_key")
    if sifre == "1234":
        st.sidebar.success("Yönetici Girişi Başarılı.")
        yonetici_izni = True
    elif sifre != "":
        st.sidebar.error("Hatalı Şifre!")
else:
    yonetici_izni = False

# --- 📊 ANA TABLO GÖSTERİMİ ---
st.title("🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU")

if gercek_kayit_var:
    def satir_renklendir(row):
        if str(row.get('DURUM', '')).upper() == 'PLAKA ATANDI':
            return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
        else:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold;'] * len(row)
    st.dataframe(df_aktif[["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]].style.apply(satir_renklendir, axis=1), use_container_width=True)
else:
    st.info("Şu anda aktif iş havuzunda gösterilecek kayıt yok.")

# --- 🔒 YÖNETİCİ PANELİ İÇERİĞİ ---
if "⚙️ Yönetici Paneli" in rol_secimi and yonetici_izni:
    st.markdown("---")
    st.header("⚙️ Lojistik Yönetici Kontrol Paneli")
    
    # ... (Buraya senin eski kodundaki Ekleme, Silme ve Güncelleme bloklarının tamamı gelecek) ...
    # Kodu buraya yapıştırırken diğer blokların değişmediğinden emin ol.
    
    st.info("Sıralama aktif: Boştaki işler otomatik olarak en üste taşındı!")
