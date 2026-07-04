import streamlit as st
import pandas as pd
import requests
import json

# Sayfa Genişlik Ayarı
st.set_page_config(layout="wide", page_title="Lojistik Çift Girişli İş Takip Sistemi")

# ⚠️ BURAYA KENDİ YENİ APPS SCRIPT URL'Nİ YAPIŞTIR
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzh13LuC19Y-4vzTldvQYnJc-Qs1P_y02Yk7wU_-d6sC7kMYp5poEzkpaDftEFJVx05ZQ/exec"

# Sabit Seçenek Verileri
MUSTERI_DEPO_LISTESI = [
    "ABANT FABRİKA - BURDUR - AĞLASUN",
    "Abant Burdur - Burdur",
    "Burdur Belediye - Burdur"
]

URUN_LISTESI = [
    "0.33 LT EURO", "0.33 LT PALEX", "0.5 LT EURO", "0.5 LT PALEX", 
    "1.5 LT EURO", "5 LT", "19 LT PC DAMACANA", "19 LT CAM DAMACANA", "SEPARATÖR KARTON - 5 LT"
]

SOFOR_ARAC_LISTESI = [
    "Abant (15abnt15)",
    "Hüseyin (15hsyn15)",
    "Selim (15slm15)"
]

# Veri Çekme Fonksiyonu
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

# Veri Gönderme Fonksiyonu
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

# Veriyi Hafızada Tut
if 'sevkiyatlar' not in st.session_state:
    st.session_state.sevkiyatlar = veri_cek()

st.title("🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU")

# Sütun Güvenliği
df_aktif = st.session_state.sevkiyatlar.copy()
for col in ["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]:
    if col not in df_aktif.columns:
        df_aktif[col] = ""
    df_aktif[col] = df_aktif[col].fillna("").astype(str).str.strip()

gercek_kayit_var = len(df_aktif) > 0 and df_aktif.iloc[0]["MÜŞTERİ"] != ""

# --- 📊 İZLEME PANELİ ---
if gercek_kayit_var:
    def satir_renklendir(row):
        if str(row.get('DURUM', '')).upper() == 'PLAKA ATANDI':
            return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
        else:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold;'] * len(row)
    st.dataframe(df_aktif[["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]].style.apply(satir_renklendir, axis=1), use_container_width=True)
else:
    st.info("Havuz şu anda boş.")

st.markdown("---")

# --- 👥 ÇİFT GİRİŞLİ SEKMELER ---
sekme1, sekme2 = st.tabs(["➕ YENİ SİPARİŞ GİRİŞİ", "🛠️ LOJİSTİK / ATAMA VE DÜZELTME"])

with sekme1:
    st.subheader("📝 Günlük Yeni Sipariş Emri Ekle")
    col1, col2 = st.columns(2)
    with col1:
        secilen_secenek = st.selectbox("Müşteri & Depo Seç:", MUSTERI_DEPO_LISTESI, key="s_musteri")
    with col2:
        secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin:", URUN_LISTESI, key="s_urun")
        
    if st.button("🚀 Siparişi Havuza Gönder (Turuncu Yap)", key="btn_siparis"):
        if not secilen_urunler:
            st.error("Lütfen ürün seçin!")
        else:
            parcalar = secilen_secenek.split(" - ")
            yeni_satir = [parcalar[0], parcalar[1] if len(parcalar)>1 else parcalar[0], ", ".join(secilen_urunler), "", "BEKLİYOR (BOŞTA)"]
            if veri_gonder("EKLE", yeni_satir):
                st.success("Sipariş başarıyla gönderildi!")
                st.session_state.sevkiyatlar = veri_cek()
                st.rerun()

with sekme2:
    st.subheader("✍️ Boştaki İşe Plaka / Şoför Ata")
    bosta_olanlar = df_aktif[df_aktif['PLAKA'] == ""] if gercek_kayit_var else pd.DataFrame()
    
    if not bosta_olanlar.empty:
        is_secenekleri = [f"Sıra {idx+1}: {r['MÜŞTERİ']} -> {r['ÜRÜNLER']}" for idx, r in bosta_olanlar.iterrows()]
        idx_haritasi = {f"Sıra {idx+1}: {r['MÜŞTERİ']} -> {r['ÜRÜNLER']}": idx for idx, r in bosta_olanlar.iterrows()}
        
        col3, col4 = st.columns(2)
        with col3:
            secilen_is = st.selectbox("İş Emrini Seçin:", is_secenekleri, key="l_is")
        with col4:
            secilen_arac = st.selectbox("Atanacak Şoför & Araç:", SOFOR_ARAC_LISTESI, key="l_arac")
            
        if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)", key="btn_plaka"):
            g_idx = idx_haritasi[secilen_is]
            plaka = secilen_arac.split("(")[-1].replace(")", "").strip()
            guncel_satir = [df_aktif.loc[g_idx, "MÜŞTERİ"], df_aktif.loc[g_idx, "DEPO"], df_aktif.loc[g_idx, "ÜRÜNLER"], plaka, "PLAKA ATANDI"]
            if veri_gonder("GUNCELLE", guncel_satir, search_key=df_aktif.loc[g_idx, "ÜRÜNLER"]):
                st.success("Plaka başarıyla atandı!")
                st.session_state.sevkiyatlar = veri_cek()
                st.rerun()
    else:
        st.info("Atama bekleyen iş yok.")
        
    st.markdown("---")
    st.subheader("📝 Aktif İş Emrini Düzenle / Düzelt")
    if gercek_kayit_var:
        duzenleme_secenekleri = [f"Sıra {idx+1}: {r['MÜŞTERİ']} ({r['DURUM']})" for idx, r in df_aktif.iterrows()]
        d_idx_haritasi = {f"Sıra {idx+1}: {r['MÜŞTERİ']} ({r['DURUM']})": idx for idx, r in df_aktif.iterrows()}
        secilen_duzenleme = st.selectbox("Düzenlenecek İşi Seçin:", duzenleme_secenekleri, key="d_is")
        g_d_idx = d_idx_haritasi[secilen_duzenleme]
        
        col5, col6, col7 = st.columns(3)
        with col5:
            yeni_m = st.text_input("Müşteri Adı:", value=df_aktif.loc[g_d_idx, "MÜŞTERİ"], key="d_m")
        with col6:
            yeni_d = st.text_input("Depo Adı:", value=df_aktif.loc[g_d_idx, "DEPO"], key="d_d")
        with col7:
            yeni_p = st.text_input("Plaka:", value=df_aktif.loc[g_d_idx, "PLAKA"], key="d_p")
            
        if st.button("💾 Değişiklikleri Kaydet", key="btn_kaydet"):
            y_durum = "PLAKA ATANDI" if yeni_p.strip() != "" else "BEKLİYOR (BOŞTA)"
            guncel_satir = [yeni_m, yeni_d, df_aktif.loc[g_d_idx, "ÜRÜNLER"], yeni_p, y_durum]
            if veri_gonder("GUNCELLE", guncel_satir, search_key=df_aktif.loc[g_d_idx, "ÜRÜNLER"]):
                st.success("Başarıyla güncellendi!")
                st.session_state.sevkiyatlar = veri_cek()
                st.rerun()
