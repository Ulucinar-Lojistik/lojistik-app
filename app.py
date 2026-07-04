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

# --- VERİ YÜKLE VE SIRALA ---
df_aktif = st.session_state.sevkiyatlar.copy()

for col in ["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]:
    if col not in df_aktif.columns:
        df_aktif[col] = ""
    df_aktif[col] = df_aktif[col].fillna("").astype(str).str.strip()

# 🔥 YENİ SIRALAMA: Boştaki işler üstte, plaka atananlar altta
if not df_aktif.empty:
    # Durum önceliği: BEKLİYOR önce gelsin
    df_aktif["SIRALAMA"] = df_aktif["DURUM"].apply(lambda x: 0 if "BEKLİYOR" in str(x).upper() else 1)
    df_aktif = df_aktif.sort_values(by=["SIRALAMA", "MÜŞTERİ"]).drop(columns=["SIRALAMA"]).reset_index(drop=True)

gercek_kayit_var = len(df_aktif) > 0 and df_aktif.iloc[0]["MÜŞTERİ"] != ""

# --- SOL MENÜ ---
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

# --- ANA TABLO (SIRALI) ---
st.title("🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU")

if gercek_kayit_var:
    def satir_renklendir(row):
        if str(row.get('DURUM', '')).upper() == 'PLAKA ATANDI':
            return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
        else:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold;'] * len(row)
    
    st.dataframe(
        df_aktif[["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"]].style.apply(satir_renklendir, axis=1),
        use_container_width=True
    )
else:
    st.info("Şu anda aktif iş havuzunda gösterilecek kayıt yok.")

# --- YÖNETİCİ PANELİ ---
if "⚙️ Yönetici Paneli" in rol_secimi and yonetici_izni:
    st.markdown("---")
    st.header("⚙️ Lojistik Yönetici Kontrol Paneli")
    
    # Sabit Tanımlamalar (mevcut kod aynı kaldı...)
    st.subheader("📋 Sabit Tanımlamalar Ekle (Mükerrer Kontrollü)")
    col_t1, col_t2, col_t3 = st.columns(3)
    
    with col_t1:
        st.markdown("**🚚 Yeni Şoför & Plaka Ekle**")
        yeni_sofor_ad = st.text_input("Şoför Adı Soyadı:", key="y_sof_ad")
        yeni_sofor_plk = st.text_input("Araç Plakası:", key="y_sof_plk")
        if st.button("➕ Şoförü Kaydet", key="btn_sof_kaydet"):
            if yeni_sofor_ad and yeni_sofor_plk:
                formatli = f"{yeni_sofor_ad} ({yeni_sofor_plk})"
                if formatli not in st.session_state.soforler:
                    st.session_state.soforler.append(formatli)
                    st.success("Şoför listeye eklendi!")
                    st.rerun()
                else: 
                    st.warning("Bu şoför zaten mevcut.")
                    
    with col_t2:
        st.markdown("**🗺️ Yeni Müşteri & Depo Ekle**")
        yeni_mus_ad = st.text_input("Müşteri/Bayi Adı:", key="y_mus_ad")
        yeni_depo_ad = st.text_input("Depo / Gideceği Yer:", key="y_dep_ad")
        if st.button("➕ Depoyu Kaydet", key="btn_dep_kaydet"):
            if yeni_mus_ad and yeni_depo_ad:
                formatli = f"{yeni_mus_ad} - {yeni_depo_ad}"
                if formatli not in st.session_state.musteriler:
                    st.session_state.musteriler.append(formatli)
                    st.success("Müşteri/Depo eklendi!")
                    st.rerun()
                else: 
                    st.warning("Bu lokasyon zaten mevcut.")

    with col_t3:
        st.markdown("**📦 Yeni Ürün Çeşidi Ekle**")
        yeni_urn_ad = st.text_input("Ürün Adı:", key="y_urn_ad")
        if st.button("➕ Ürünü Kaydet", key="btn_urn_kaydet"):
            if yeni_urn_ad:
                if yeni_urn_ad not in st.session_state.urunler:
                    st.session_state.urunler.append(yeni_urn_ad)
                    st.success("Ürün çeşidi eklendi!")
                    st.rerun()
                else: 
                    st.warning("Bu ürün zaten mevcut.")

    st.markdown("---")

    # ❌ Silme işlemleri (mevcut)
    st.subheader("❌ Kayıtlı Tanımlamaları Sil")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        sil_sof = st.selectbox("Silinecek Şoförü Seçin:", st.session_state.soforler, key="s_sof_sel")
        if st.button("🗑️ Şoförü Listeden Kaldır", key="btn_sof_sil"):
            st.session_state.soforler.remove(sil_sof)
            st.success("Şoför kaldırıldı.")
            st.rerun()
    with col_s2:
        sil_mus = st.selectbox("Silinecek Depo/Bayi Seçin:", st.session_state.musteriler, key="s_mus_sel")
        if st.button("🗑️ Depoyu Listeden Kaldır", key="btn_mus_sil"):
            st.session_state.musteriler.remove(sil_mus)
            st.success("Müşteri/Depo kaldırıldı.")
            st.rerun()
    with col_s3:
        sil_urn = st.selectbox("Silinecek Ürünü Seçin:", st.session_state.urunler, key="s_urn_sel")
        if st.button("🗑️ Ürünü Listeden Kaldır", key="btn_urn_sil"):
            st.session_state.urunler.remove(sil_urn)
            st.success("Ürün kaldırıldı.")
            st.rerun()

    st.markdown("---")

    # --- 🧼 TEMİZLİK BÖLÜMÜ (YENİ ÖZELLİK BURADA) ---
    st.subheader("🧹 Gün Sonu Temizliği & İş Silme")
    
    col_temiz1, col_temiz2 = st.columns(2)
    
    with col_temiz1:
        if st.button("🧼 Sadece 'PLAKA ATANDI' Olanları Temizle", key="btn_gun_sonu"):
            if gercek_kayit_var:
                atananlar = df_aktif[df_aktif['DURUM'].str.upper() == 'PLAKA ATANDI']
                if not atananlar.empty:
                    silinen_sayisi = 0
                    with st.spinner("Tamamlanan işler temizleniyor..."):
                        for _, r in atananlar.iterrows():
                            silinecek_satir = ["", "", str(r['ÜRÜNLER']), "", ""]
                            if veri_gonder("SIL", silinecek_satir, search_key=str(r['ÜRÜNLER'])):
                                silinen_sayisi += 1
                    st.success(f"Tamamlanmış {silinen_sayisi} adet sevkiyat temizlendi!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
                else:
                    st.info("Temizlenecek 'PLAKA ATANDI' işi bulunamadı.")

    with col_temiz2:
        if st.button("🗑️ Boştaki İşleri (BEKLİYOR) Sil", key="btn_bosta_sil", type="secondary"):
            if gercek_kayit_var:
                bostakiler = df_aktif[df_aktif['DURUM'].str.contains("BEKLİYOR", na=False)]
                if not bostakiler.empty:
                    silinen_sayisi = 0
                    with st.spinner("Boştaki işler siliniyor..."):
                        for _, r in bostakiler.iterrows():
                            silinecek_satir = ["", "", str(r['ÜRÜNLER']), "", ""]
                            if veri_gonder("SIL", silinecek_satir, search_key=str(r['ÜRÜNLER'])):
                                silinen_sayisi += 1
                    st.success(f"{silinen_sayisi} adet boştaki iş havuzdan silindi!")
                    st.session_state.sevkiyatlar = veri_cek()
                    st.rerun()
                else:
                    st.info("Silinecek boştaki iş bulunamadı.")
            else:
                st.info("Havuzda kayıt yok.")

    st.markdown("---")

    # Diğer yönetici işlemleri (iş ekleme, plaka atama, düzenleme) aynı kalıyor...
    # (Kod uzun olmasın diye buraya koymadım ama istersen tamamını da verebilirim)

    # ... (mevcut iş ekleme, plaka atama ve düzenleme kodlarını buraya yapıştırabilirsiniz)

else:
    st.info("💡 Şu anda Şoför modundasınız. Yukarıdaki tablodan anlık atamaları izleyebilirsiniz.")
