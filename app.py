import streamlit as st
import pandas as pd
import requests
import json

# Sayfa Genişlik Ayarı
st.set_page_config(layout="wide", page_title="Lojistik Çift Girişli İş Takip Sistemi")

# Güncel ve Çalışan Google Apps Script URL'niz
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

# Sütun Güvenliği (KeyError çökmelerini tamamen önler)
df_aktif = st.session_state.sevkiyatlar.copy()
for col in ["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]:
    if col not in df_aktif.columns:
        df_aktif[col] = ""
    df_aktif[col] = df_aktif[col].fillna("").astype(str).str.strip()

gercek_kayit_var = len(df_aktif) > 0 and df_aktif.iloc[0]["MÜŞTERİ"] != ""

# --- 📊 1. ANLIK DURUM TABLOSU PANELİ ---
if gercek_kayit_var:
    def satir_renklendir(row):
        if str(row.get('DURUM', '')).upper() == 'PLAKA ATANDI':
            return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
        else:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold;'] * len(row)
    st.dataframe(df_aktif[["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]].style.apply(satir_renklendir, axis=1), use_container_width=True)
else:
    st.info("Aktif iş havuzu şu anda boş. Aşağıdaki sekmelerden işlem yapabilirsiniz.")

st.markdown("---")

# --- 👥 2. ÇİFT GİRİŞLİ SEKMELER ---
sekme1, sekme2 = st.tabs(["➕ YENİ SİPARİŞ GİRİŞİ", "🛠️ LOJİSTİK / ATAMA VE DÜZELTME"])

# 🏢 SEKME 1: YENİ SİPARİŞ GİRİŞİ PANELİ
with sekme1:
    st.subheader("📝 Günlük Yeni Sipariş Emri Ekle")
    col1, col2 = st.columns(2)
    with col1:
        secilen_secenek = st.selectbox("Müşteri & Depo Seç:", MUSTERI_DEPO_LISTESI, key="s_musteri")
    with col2:
        secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin:", URUN_LISTESI, key="s_urun")
        
    if st.button("🚀 Siparişi Havuza Gönder (Turuncu Yap)", key="btn_siparis"):
        if not secilen_urunler:
            st.error("Lütfen en az bir ürün seçin!")
        else:
            parcalar = secilen_secenek.split(" - ")
            musteri = parcalar[0]
            depo = parcalar[1] if len(parcalar) > 1 else parcalar[0]
            urunler_str = ", ".join(secilen_urunler)
            
            yeni_satir = [musteri, depo, urunler_str, "", "BEKLİYOR (BOŞTA)"]
            
            with st.spinner("Sipariş sisteme kaydediliyor..."):
                if veri_gonder("EKLE", yeni_satir):
                    st.success("Sipariş başarıyla havuza gönderildi!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
                else:
                    st.error("Kayıt başarısız. Bağlantıyı kontrol edin.")

# 🔧 SEKME 2: LOJİSTİK / ATAMA, DÜZELTME VE SİLME PANELİ
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
            
            guncel_satir = [
                str(df_aktif.loc[g_idx, "MÜŞTERİ"]), 
                str(df_aktif.loc[g_idx, "DEPO"]), 
                str(df_aktif.loc[g_idx, "ÜRÜNLER"]), 
                str(plaka), 
                "PLAKA ATANDI"
            ]
            
            with st.spinner("Plaka atanıyor..."):
                if veri_gonder("GUNCELLE", guncel_satir, search_key=df_aktif.loc[g_idx, "ÜRÜNLER"]):
                    st.success("Plaka başarıyla atandı!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
                else:
                    st.error("Plaka güncellenirken bir hata oluştu.")
    else:
        st.info("Atama bekleyen boşta iş emri bulunmuyor.")
        
    st.markdown("---")
    
    # 📝 AKTİF İŞ EMRİNİ DÜZENLE / DÜZELT PANELİ
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
            
            with st.spinner("Düzenlemeler kaydediliyor..."):
                if veri_gonder("GUNCELLE", guncel_satir, search_key=df_aktif.loc[g_d_idx, "ÜRÜNLER"]):
                    st.success("İş emri başarıyla güncellendi!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
                else:
                    st.error("Güncelleme başarısız oldu.")
    else:
        st.info("Düzenlenecek herhangi bir aktif kayıt bulunmuyor.")

    st.markdown("---")

    # 🗑️ İŞ EMRİNİ TAMAMEN SİL PANELİ (Geri Getirilen Kısım)
    st.subheader("🗑️ İş Emrini Sistemden Tamamen Sil")
    if gercek_kayit_var:
        silme_secenekleri = [f"Sıra {idx+1}: {r['MÜŞTERİ']} -> {r['ÜRÜNLER']}" for idx, r in df_aktif.iterrows()]
        s_idx_haritasi = {f"Sıra {idx+1}: {r['MÜŞTERİ']} -> {r['ÜRÜNLER']}": idx for idx, r in df_aktif.iterrows()}
        secilen_silme = st.selectbox("Silinecek İş Emrini Seçin:", silme_secenekleri, key="s_silme_box")
        
        if st.button("🚨 Seçili İş Emrini Kalıcı Olarak Sil", key="btn_sil_is"):
            g_s_idx = s_idx_haritasi[secilen_silme]
            silinecek_urun = str(df_aktif.loc[g_s_idx, "ÜRÜNLER"])
            silinecek_satir = ["", "", silinecek_urun, "", ""]
            
            with st.spinner("İş emri siliniyor..."):
                if veri_gonder("SIL", silinecek_satir, search_key=silinecek_urun):
                    st.success("İş emri e-tablodan ve sistemden tamamen silindi!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
                else:
                    st.error("Silme işlemi gerçekleştirilemedi.")
    else:
        st.info("Sistemde silinecek herhangi bir iş emri bulunmuyor.")
