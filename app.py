import streamlit as st
import pandas as pd
import requests
import json

# Sayfa Genişlik Ayarı
st.set_page_config(layout="wide", page_title="Lojistik Araç İş Takip Sistemi")

# Google Apps Script URL'niz
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwYVCD0lLeo1l21CTaYw5RyXlUJIN168zsxvQD2Fx1RAJ5qQXGiobTcGNnqhyTnhHCaCg/exec"

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

# Google Sheets'ten Veri Çekme Fonksiyonu
def veri_cek():
    try:
        response = requests.get(SCRIPT_URL + "?sheetName=Sayfa1", timeout=10)
        if response.status_code == 200:
            veri = response.json()
            if veri and len(veri) > 0:
                df = pd.DataFrame(veri)
                df.columns = [str(c).strip().upper() for c in df.columns]
                return df
    except:
        pass
    return pd.DataFrame(columns=["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"])

# Google Sheets'e Veri Gönderme Fonksiyonu
def veri_gonder(action, row_data, search_key=None, search_column=None):
    payload = {
        "sheetName": "Sayfa1",
        "action": action,
        "rowData": row_data,
        "searchKey": search_key,
        "searchColumn": search_column
    }
    try:
        response = requests.post(SCRIPT_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
        return response.status_code == 200
    except:
        return False

# Uygulama Başladığında Veriyi Hafızaya Al
if 'sevkiyatlar' not in st.session_state:
    st.session_state.sevkiyatlar = veri_cek()

# --- PANEL ARAYÜZÜ ---
st.title("🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU")

# Tabloyu Temizle ve Hazırla
if not st.session_state.sevkiyatlar.empty:
    # Sütun kontrolü ve zorunlu veri tipi dönüşümü (Metne Sabitleme)
    for col in ["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]:
        if col in st.session_state.sevkiyatlar.columns:
            st.session_state.sevkiyatlar[col] = st.session_state.sevkiyatlar[col].fillna("").astype(str).str.strip()
        else:
            st.session_state.sevkiyatlar[col] = ""

    # PLAKA_KONTROL sütununu hatasız oluşturma
    st.session_state.sevkiyatlar['PLAKA_KONTROL'] = st.session_state.sevkiyatlar['PLAKA'].apply(
        lambda x: 0 if str(x) == "" or str(x).lower() == "nan" or str(x).strip() == "" else 1
    )

    # Renklendirme Kuralları
    def satir_renklendir(row):
        try:
            if str(row.get('DURUM', '')).upper() == 'PLAKA ATANDI':
                return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
            else:
                return ['background-color: #fff3cd; color: #856404; font-weight: bold;'] * len(row)
        except:
            return [''] * len(row)

    gosterilecek_df = st.session_state.sevkiyatlar[["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]]
    st.dataframe(gosterilecek_df.style.apply(satir_renklendir, axis=1), use_container_width=True)
else:
    st.info("Şu anda aktif iş havuzu boş. Lütfen aşağıdan yeni iş emri ekleyin.")

st.markdown("---")

# ➕ BÖLÜM 1: YENİ İŞ EMRİ EKLE
st.subheader("➕ Günlük Yeni İş Emri Ekle")
col1, col2 = st.columns(2)

with col1:
    secilen_secenek = st.selectbox("Müşteri & Depo Seç:", MUSTERI_DEPO_LISTESI)
with col2:
    secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin:", URUN_LISTESI)

if st.button("🚀 Veriyi Havuza Gönder (Turuncu Yap)"):
    if not secilen_urunler:
        st.error("Lütfen en az bir ürün seçin!")
    else:
        parcalar = secilen_secenek.split(" - ")
        musteri = parcalar[0]
        depo = parcalar[1] if len(parcalar) > 1 else parcalar[0]
        urunler_str = ", ".join(secilen_urunler)
        
        yeni_satir = [musteri, depo, urunler_str, "", "BEKLİYOR (BOŞTA)"]
        
        with st.spinner("Veri e-tabloya yazılıyor..."):
            if veri_gonder("EKLE", yeni_satir):
                st.success("İş emri başarıyla havuza gönderildi!")
                st.session_state.sevkiyatlar = veri_cek()
                st.rerun()
            else:
                st.error("Google Sheets'e yazılamadı. Lütfen Apps Script izinlerini kontrol edin.")

st.markdown("---")

# 📝 BÖLÜM 2: PLAKA / ŞOFÖR ATA
st.subheader("✍️ Boştaki İşe Plaka / Şoför Ata")

if not st.session_state.sevkiyatlar.empty and 'PLAKA_KONTROL' in st.session_state.sevkiyatlar.columns:
    bosta_olanlar = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar['PLAKA_KONTROL'] == 0]
    
    if not bosta_olanlar.empty:
        is_secenekleri = []
        idx_haritasi = {}
        
        for idx, r in bosta_olanlar.iterrows():
            gosterim = f"Sıra {idx+1}: {r['MÜŞTERİ']} ({r['DEPO']}) -> {r['ÜRÜNLER']}"
            is_secenekleri.append(gosterim)
            idx_haritasi[gosterim] = idx
            
        col3, col4 = st.columns(2)
        with col3:
            secilen_is = st.selectbox("Plaka Atanacak İş Emrini Seçin:", is_secenekleri)
        with col4:
            secilen_arac = st.selectbox("Atanacak Şoför & Araç:", SOFOR_ARAC_LISTESI)
            
        if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)"):
            gercek_idx = idx_haritasi[secilen_is]
            plaka_ayikla = secilen_arac.split("(")[-1].replace(")", "").strip()
            
            # --- 202. SATIRDAKİ STR/OBJECT HATA KORUMASI ---
            # DataFrame'in ilgili sütununu seriye/object tipine tamamen güvenli şekilde zorluyoruz
            st.session_state.sevkiyatlar["PLAKA"] = st.session_state.sevkiyatlar["PLAKA"].astype(str)
            st.session_state.sevkiyatlar["DURUM"] = st.session_state.sevkiyatlar["DURUM"].astype(str)
            
            # Atama işlemini doğrudan python seviyesinde gerçekleştiriyoruz
            st.session_state.sevkiyatlar.loc[gercek_idx, "PLAKA"] = str(plaka_ayikla)
            st.session_state.sevkiyatlar.loc[gercek_idx, "DURUM"] = "PLAKA ATANDI"
            
            guncellenecek_satir = [
                str(st.session_state.sevkiyatlar.loc[gercek_idx, "MÜŞTERİ"]),
                str(st.session_state.sevkiyatlar.loc[gercek_idx, "DEPO"]),
                str(st.session_state.sevkiyatlar.loc[gercek_idx, "ÜRÜNLER"]),
                str(plaka_ayikla),
                "PLAKA ATANDI"
            ]
            
            with st.spinner("Plaka güncelleniyor..."):
                if veri_gonder("GUNCELLE", guncellenecek_satir, search_key=str(guncellenecek_satir[2]), search_column="ÜRÜNLER"):
                    st.success(f"{plaka_ayikla} plakası başarıyla atandı!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
                else:
                    st.error("E-tablo güncellemesi başarısız oldu.")
    else:
        st.info("Şu anda plaka atanmayı bekleyen boşta iş yok.")
else:
    st.info("Şu anda plaka atanmayı bekleyen boşta iş yok.")
