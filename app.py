import streamlit as st
import pandas as pd
import requests
import json

# Sayfa Genişlik Ayarı
st.set_page_config(layout="wide", page_title="Lojistik Yönetici Kontrol Paneli")

# Çalışan Apps Script URL'niz
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzh13LuC19Y-4vzTldvQYnJc-Qs1P_y02Yk7wU_-d6sC7kMYp5poEzkpaDftEFJVx05ZQ/exec"

# --- DİNAMİK VERİ ÇEKME VE SIRALAMA FONKSİYONU ---
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
                
                # SIRALAMA MANTIĞI: BEKLİYOR OLANLAR ÜSTE (DURUM_ORDER 0 olur, diğerleri 1)
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

# Veriyi çek ve sıralamayı uygula
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
    
    # --- SABİT TANIMLAMALAR ---
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.markdown("**🚚 Yeni Şoför & Plaka Ekle**")
        yeni_sofor_ad = st.text_input("Şoför Adı Soyadı:", key="y_sof_ad")
        yeni_sofor_plk = st.text_input("Araç Plakası:", key="y_sof_plk")
        if st.button("➕ Şoförü Kaydet", key="btn_sof_kaydet"):
            st.session_state.soforler.append(f"{yeni_sofor_ad} ({yeni_sofor_plk})")
            st.success("Eklendi!")
            st.rerun()
                
    with col_t2:
        st.markdown("**🗺️ Yeni Müşteri & Depo Ekle**")
        yeni_mus_ad = st.text_input("Müşteri/Bayi Adı:", key="y_mus_ad")
        yeni_depo_ad = st.text_input("Depo / Gideceği Yer:", key="y_dep_ad")
        if st.button("➕ Depoyu Kaydet", key="btn_dep_kaydet"):
            st.session_state.musteriler.append(f"{yeni_mus_ad} - {yeni_depo_ad}")
            st.success("Eklendi!")
            st.rerun()

    with col_t3:
        st.markdown("**📦 Yeni Ürün Çeşidi Ekle**")
        yeni_urn_ad = st.text_input("Ürün Adı:", key="y_urn_ad")
        if st.button("➕ Ürünü Kaydet", key="btn_urn_kaydet"):
            st.session_state.urunler.append(yeni_urn_ad)
            st.success("Eklendi!")
            st.rerun()

    st.markdown("---")
    
    # --- İŞ EMRİ EKLE ---
    st.subheader("➕ Günlük Yeni İş Emri Ekle")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        secilen_secenek = st.selectbox("Müşteri & Depo Seç:", st.session_state.musteriler, key="y_isl_mus")
    with col_e2:
        secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin:", st.session_state.urunler, key="y_isl_urn")
        
    if st.button("🚀 Veriyi Havuza Gönder", key="btn_isl_ekle"):
        parcalar = secilen_secenek.split(" - ")
        musteri = parcalar[0]
        depo = parcalar[1] if len(parcalar) > 1 else parcalar[0]
        if veri_gonder("EKLE", [musteri, depo, ", ".join(secilen_urunler), "", "BEKLİYOR (BOŞTA)"]):
            st.success("Eklendi!")
            st.rerun()

    st.markdown("---")
    
    # --- PLAKA ATA ---
    st.subheader("✍️ Boştaki İşe Plaka / Şoför Ata")
    bosta_olanlar = df_aktif[df_aktif['PLAKA'] == ""] if gercek_kayit_var else pd.DataFrame()
    if not bosta_olanlar.empty:
        is_secenekleri = [f"Sıra {idx+1}: {r['MÜŞTERİ']} -> {r['ÜRÜNLER']}" for idx, r in bosta_olanlar.iterrows()]
        idx_haritasi = {f"Sıra {idx+1}: {r['MÜŞTERİ']} -> {r['ÜRÜNLER']}": idx for idx, r in bosta_olanlar.iterrows()}
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            secilen_is = st.selectbox("İş Emrini Seçin:", is_secenekleri, key="ata_is_sel")
        with col_a2:
            secilen_arac = st.selectbox("Şoför & Araç:", st.session_state.soforler, key="ata_sof_sel")
        if st.button("✅ Plakayı Güncelle", key="btn_ata_kaydet"):
            g_idx = idx_haritasi[secilen_is]
            plaka = secilen_arac.split("(")[-1].replace(")", "").strip()
            if veri_gonder("GUNCELLE", [str(df_aktif.loc[g_idx, "MÜŞTERİ"]), str(df_aktif.loc[g_idx, "DEPO"]), str(df_aktif.loc[g_idx, "ÜRÜNLER"]), str(plaka), "PLAKA ATANDI"], search_key=df_aktif.loc[g_idx, "ÜRÜNLER"]):
                st.success("Atandı!")
                st.rerun()
