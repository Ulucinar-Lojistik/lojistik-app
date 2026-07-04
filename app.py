import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(page_title="Lojistik Sevkiyat Paneli", layout="wide")

# 🔗 GOOGLE SHEETS VE APPS SCRIPT BAĞLANTI AYARLARI
SHEET_ID = "1dxRbPvjXBwlozdEzlwqsQ-HSjf_nKU5hIvTLa_W4TaI"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyO7A0Yix4tlG5q7AqHupjJRkxnWNPl-rC5SJdqvSoXtCd_LVmN4_WpBeVQYo8PGCMoEA/exec"

# Google Sheets'ten Canlı Veri Okuma Fonksiyonu
def tabloyu_oku(sekme_adi):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sekme_adi}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            df.columns = df.columns.str.strip()
            return df
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# Google Sheets'e Canlı Veri Yazma Fonksiyonu
def tabloya_yaz(sekme_adi, veri_listesi):
    try:
        payload = {
            "sheetName": sekme_adi,
            "rowData": veri_listesi
        }
        res = requests.post(SCRIPT_URL, json=payload)
        if res.status_code == 200:
            return True
    except:
        pass
    return False

# 🔄 SİSTEMİ BAŞLATMA VE CANLI VERİ ÇEKME
if 'aksiyon_tetik' not in st.session_state:
    st.session_state.aksiyon_tetik = 0

df_sevkiyatlar = tabloyu_oku("Sevkiyatlar")
df_soforler = tabloyu_oku("Soforler")
df_depolar = tabloyu_oku("Depolar")
df_urunler = tabloyu_oku("Urunler")

if df_sevkiyatlar.empty: df_sevkiyatlar = pd.DataFrame(columns=["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"])
if df_soforler.empty: df_soforler = pd.DataFrame(columns=["SOFOR_ADI", "PLAKA"])
if df_depolar.empty: df_depolar = pd.DataFrame(columns=["MUSTERI_ADI", "GIDECEGI_YER"])
if df_urunler.empty: df_urunler = pd.DataFrame(columns=["URUN_ADI"])

if 'sevkiyatlar' not in st.session_state or st.session_state.aksiyon_tetik == 0:
    st.session_state.sevkiyatlar = df_sevkiyatlar
if 'soforler_list' not in st.session_state or st.session_state.aksiyon_tetik == 0:
    st.session_state.soforler_list = df_soforler
if 'depolar_list' not in st.session_state or st.session_state.aksiyon_tetik == 0:
    st.session_state.depolar_list = df_depolar
if 'urunler_list' not in st.session_state or st.session_state.aksiyon_tetik == 0:
    st.session_state.urunler_list = df_urunler

if 'mesaj_genel' not in st.session_state: st.session_state.mesaj_genel = ""

sofor_listesi = []
for _, r in st.session_state.soforler_list.iterrows():
    if pd.notna(r["SOFOR_ADI"]) and pd.notna(r["PLAKA"]):
        sofor_listesi.append(f"{r['SOFOR_ADI']} ({r['PLAKA']})")

depo_listesi = []
for _, r in st.session_state.depolar_list.iterrows():
    if pd.notna(r["MUSTERI_ADI"]) and pd.notna(r["GIDECEGI_YER"]):
        depo_listesi.append(f"{r['MUSTERI_ADI']} - {r['GIDECEGI_YER']}")

urun_listesi = []
for _, r in st.session_state.urunler_list.iterrows():
    if pd.notna(r["URUN_ADI"]):
        urun_listesi.append(str(r["URUN_ADI"]).strip().upper())

if not urun_listesi:
    urun_listesi = ["0.50 LT PET SU", "1.50 LT PET SU", "5.00 LT PET SU", "19 LT DAMACANA"]

# Akıllı Sıralama Mantığı (Hata Düzeltildi)
if not st.session_state.sevkiyatlar.empty:
    st.session_state.sevkiyatlar['PLAKA_KONTROL'] = st.session_state.sevkiyatlar['PLAKA'].apply(lambda x: 0 if str(x).strip() == "" or pd.isna(x) or x == "" else 1)
    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.sort_values(by=['PLAKA_KONTROL']).reset_index(drop=True)
    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.drop(columns=['PLAKA_KONTROL'])

def satir_boya(row):
    if str(row["PLAKA"]).strip() == "" or pd.isna(row["PLAKA"]) or row["PLAKA"] == "":
        return ['background-color: #fef7e0; color: #b06000; font-weight: bold;'] * len(row)
    else:
        return ['background-color: #e6f4ea; color: #137333; font-weight: 600;'] * len(row)

# 📊 EKRAN GÖSTERİMİ
st.sidebar.markdown("### 🚪 SİSTEM GİRİŞİ")
giris_turu = st.sidebar.radio("Rolünüzü Seçin:", ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"])

if giris_turu == "🚚 Şoför Ekranı (Sadece İzleme)":
    st.markdown("<h2 style='text-align: center; color: #1e3d59;'>🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU</h2>", unsafe_allow_html=True)
    st.divider()
    gosterilecek_df = st.session_state.sevkiyatlar.fillna("")
    styled_df = gosterilecek_df.style.apply(satir_boya, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.title("⚙️ Lojistik Yönetici Kontrol Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password")
    
    if sifre == "1234":
        st.success("Giriş Başarılı.")
        if st.session_state.mesaj_genel: st.success(st.session_state.mesaj_genel); st.session_state.mesaj_genel = ""

        # 📋 TEK SAYFADA CANLI VE KALICI EKLEME ALANLARI
        st.divider()
        st.subheader("📋 Sabit Tanımlamalar (E-Tabloya Anında Kaydeder)")
        col_tanim1, col_tanim2, col_tanim3 = st.columns(3)
        
        with col_tanim1:
            st.markdown("**🚚 Yeni Şoför & Plaka Ekle**")
            with st.form("sh_form", clear_on_submit=True):
                y_sh_adi = st.text_input("Şoför Adı Soyadı:")
                y_sh_plaka = st.text_input("Araç Plakası:")
                if st.form_submit_button("➕ Şoförü Kaydet"):
                    if y_sh_adi and y_sh_plaka:
                        if tabloya_yaz("Soforler", [y_sh_adi, y_sh_plaka]):
                            st.success(f"{y_sh_adi} E-Tabloya kaydedildi!")
                            st.session_state.aksiyon_tetik += 1
                            st.rerun()
                        
        with col_tanim2:
            st.markdown("**🏢 Yeni Müşteri & Depo Ekle**")
            with st.form("dp_form", clear_on_submit=True):
                y_m_adi = st.text_input("Müşteri Adı:")
                y_g_yer = st.text_input("Depo / Gideceği Yer:")
                if st.form_submit_button("➕ Depoyu Kaydet"):
                    if y_m_adi and y_g_yer:
                        if tabloya_yaz("Depolar", [y_m_adi, y_g_yer]):
                            st.success(f"{y_m_adi} E-Tabloya kaydedildi!")
                            st.session_state.aksiyon_tetik += 1
                            st.rerun()

        with col_tanim3:
            st.markdown("**📦 Yeni Ürün Çeşidi Ekle**")
            with st.form("ur_form", clear_on_submit=True):
                y_ur_adi = st.text_input("Ürün Adı:")
                if st.form_submit_button("➕ Ürünü Kaydet"):
                    if y_ur_adi:
                        if tabloya_yaz("Urunler", [y_ur_adi.upper()]):
                            st.success(f"{y_ur_adi.upper()} E-Tabloya kaydedildi!")
                            st.session_state.aksiyon_tetik += 1
                            st.rerun()

        # 🧹 GÜN SONU VE İŞ TEMİZLEME PANELİ
        st.divider()
        st.subheader("🧹 Gün Sonu Temizliği & İptal İşlemleri")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if st.button("🗑️ Sadece 'PLAKA ATANDI' Olanları Listeden Temizle"):
                st.session_state.sevkiyatlar = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["DURUM"] == "BEKLİYOR (BOŞTA)"].reset_index(drop=True)
                st.session_state.aksiyon_tetik += 1
                st.rerun()
        with col_g2:
            if not st.session_state.sevkiyatlar.empty:
                silme_secenekleri = [f"Sıra {i+1}: {r['MÜŞTERİ']} ({r['DEPO']}) -> {r['ÜRÜNLER']}" for i, r in st.session_state.sevkiyatlar.iterrows()]
                secilen_silinecek = st.selectbox("Silinecek İşi Seçin:", silme_secenekleri)
                if st.button("🚨 Seçilen İş Emrini Sil"):
                    idx = silme_secenekleri.index(secilen_silinecek)
                    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.drop(idx).reset_index(drop=True)
                    st.session_state.aksiyon_tetik += 1
                    st.rerun()

        # ➕ GÜNLÜK YENİ İŞ EMRİ EKLE
        st.divider()
        st.subheader("➕ Günlük Yeni İş Emri Ekle")
        with st.form("is_formu", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: secilen_yer = st.selectbox("Müşteri & Depo Seç:", depo_listesi if depo_listesi else ["Önce yukarıdan depo ekleyin"])
            with c2: secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin:", urun_listesi)
            if st.form_submit_button("🚀 Veriyi Havuza Gönder (Turuncu Yap)"):
                if secilen_yer and secilen_urunler and "Önce" not in secilen_yer:
                    m_parca, d_parca = secilen_yer.split(" - ", 1) if " - " in secilen_yer else (secilen_yer, "Belirtilmedi")
                    tabloya_yaz("Sevkiyatlar", [m_parca, d_parca, ", ".join(secilen_urunler), "", "BEKLİYOR (BOŞTA)"])
                    st.session_state.aksiyon_tetik += 1
                    st.rerun()

        # ✍️ BOŞTAKİ İŞE PLAKA / ŞOFÖR ATA
        st.divider()
        st.subheader("✍️ Boştaki İşe Plaka / Şoför Ata")
        bostaki_isler_df = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["DURUM"] == "BEKLİYOR (BOŞTA)"]
        
        if not bostaki_isler_df.empty:
            bostaki_secenekler = [f"Sıra {i+1}: {r['MÜŞTERİ']} ({r['DEPO']}) -> {r['ÜRÜNLER']}" for i, r in bostaki_isler_df.iterrows()]
            cc1, cc2 = st.columns(2)
            with cc1: secilen_is_metni = st.selectbox("Plaka Atanacak İş Emrini Seçin:", bostaki_secenekler)
            with cc2: secilen_sofor = st.selectbox("Atanacak Şoför & Araç:", sofor_listesi if sofor_listesi else ["Önce yukarıdan şoför ekleyin"])
            if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)"):
                if secilen_is_metni and secilen_sofor and "Önce" not in secilen_sofor:
                    # Gerçek indexi bulma
                    is_idx = bostaki_secenekler.index(secilen_is_metni)
                    gercek_idx = bostaki_isler_df.index[is_idx]
                    plaka_ayikla = secilen_sofor.split("(")[1].replace(")", "") if "(" in secilen_sofor else secilen_sofor
                    st.session_state.sevkiyatlar.loc[gercek_idx, "PLAKA"] = plaka_ayikla
                    st.session_state.sevkiyatlar.loc[gercek_idx, "DURUM"] = "PLAKA ATANDI"
                    st.session_state.aksiyon_tetik += 1
                    st.success("Plaka başarıyla atandı!")
                    st.rerun()
        else:
            st.info("Şu anda plaka atanmayı bekleyen boşta iş yok.")

        # 🛠️ YENİ PANEL: AKTİF İŞ EMİRLERİNİ DÜZENLEME PANELİ (BÜTÜN ALANLAR DÜZELTİLEBİLİR)
        st.divider()
        st.subheader("📝 Aktif İş Emrini Düzenle / Düzelt")
        st.caption("İster plaka atanmış (Yeşil) ister boşta (Turuncu) olsun, listedeki herhangi bir işin müşteri, depo, ürün veya plaka bilgisini buradan anında revize edebilirsin.")
        
        if not st.session_state.sevkiyatlar.empty:
            tum_isler_secenekler = []
            for i, r in st.session_state.sevkiyatlar.iterrows():
                durum_emoji = "✅" if r['DURUM'] == "PLAKA ATANDI" else "⏳"
                plaka_notu = f" [{r['PLAKA']}]" if r['PLAKA'] else " [BOŞTA]"
                tum_isler_secenekler.append(f"Sıra {i+1}: {durum_emoji} {r['MÜŞTERİ']} ({r['DEPO']}){plaka_notu}")
                
            secilen_duzenlenecek = st.selectbox("Düzeltme Yapılacak İş Emrini Seçin:", tum_isler_secenekler)
            duzenle_idx = tum_isler_secenekler.index(secilen_duzenlenecek)
            mevcut_satir = st.session_state.sevkiyatlar.iloc[duzenle_idx]
            
            with st.form(f"duzenleme_formu_{duzenle_idx}"):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    yeni_musteri = st.text_input("Müşteri Adı:", value=str(mevcut_satir["MÜŞTERİ"]))
                    yeni_depo = st.text_input("Depo / Gideceği Yer:", value=str(mevcut_satir["DEPO"]))
                with col_d2:
                    yeni_urunler_metni = st.text_input("Yüklü Ürünler (Virgülle ayırın):", value=str(mevcut_satir["ÜRÜNLER"]))
                    # Mevcut plakayı şoför listesinden eşleştir veya elle yaz
                    varsayilan_plaka = str(mevcut_satir["PLAKA"])
                    yeni_plaka = st.text_input("Atanan Plaka (Boş bırakırsanız iş boşa çıkar):", value=varsayilan_plaka)
                
                if st.form_submit_button("💾 Değişiklikleri Kaydet ve Listeyi Güncelle"):
                    st.session_state.sevkiyatlar.loc[duzenle_idx, "MÜŞTERİ"] = yeni_musteri
                    st.session_state.sevkiyatlar.loc[duzenle_idx, "DEPO"] = yeni_depo
                    st.session_state.sevkiyatlar.loc[duzenle_idx, "ÜRÜNLER"] = yeni_urunler_metni
                    st.session_state.sevkiyatlar.loc[duzenle_idx, "PLAKA"] = yeni_plaka
                    
                    if yeni_plaka.strip() == "":
                        st.session_state.sevkiyatlar.loc[duzenle_idx, "DURUM"] = "BEKLİYOR (BOŞTA)"
                    else:
                        st.session_state.sevkiyatlar.loc[duzenle_idx, "DURUM"] = "PLAKA ATANDI"
                        
                    st.session_state.aksiyon_tetik += 1
                    st.success("İş emri başarıyla güncellendi!")
                    st.rerun()
        else:
            st.info("Düzenlenecek herhangi bir aktif iş emri bulunmuyor.")
