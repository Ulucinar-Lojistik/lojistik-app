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
def tabloya_yaz(sekme_adi, veri_listesi, aksiyon="EKLE", aranan_deger=None, aranan_sutun=None):
    try:
        payload = {
            "sheetName": sekme_adi,
            "action": aksiyon,
            "rowData": [str(x) for x in veri_listesi],
            "searchKey": str(aranan_deger) if aranan_deger else None,
            "searchColumn": str(aranan_sutun) if aranan_sutun else None
        }
        res = requests.post(SCRIPT_URL, json=payload)
        if res.status_code == 200:
            return True
    except:
        pass
    return False

# 🔄 VERİLERİ ANLIK OLARAK E-TABLODAN ÇEK
df_sevkiyatlar = tabloyu_oku("Sevkiyatlar")
df_soforler = tabloyu_oku("Soforler")
df_depolar = tabloyu_oku("Depolar")
df_urunler = tabloyu_oku("Urunler")

# Boş Tablo Korumaları ve Veri Tipi Sabitleme
if df_sevkiyatlar.empty: 
    df_sevkiyatlar = pd.DataFrame(columns=["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"])
else:
    for col in df_sevkiyatlar.columns:
        df_sevkiyatlar[col] = df_sevkiyatlar[col].fillna("").astype(str)

if df_soforler.empty: df_soforler = pd.DataFrame(columns=["SOFOR_ADI", "PLAKA"])
if df_depolar.empty: df_depolar = pd.DataFrame(columns=["MUSTERI_ADI", "GIDECEGI_YER"])
if df_urunler.empty: df_urunler = pd.DataFrame(columns=["URUN_ADI"])

# Seçim Kutusu Listelerini Oluşturma
sofor_listesi = []
for _, r in df_soforler.iterrows():
    if pd.notna(r["SOFOR_ADI"]) and pd.notna(r["PLAKA"]):
        sofor_listesi.append(f"{str(r['SOFOR_ADI']).strip()} ({str(r['PLAKA']).strip()})")

depo_listesi = []
for _, r in df_depolar.iterrows():
    if pd.notna(r["MUSTERI_ADI"]) and pd.notna(r["GIDECEGI_YER"]):
        depo_listesi.append(f"{str(r['MUSTERI_ADI']).strip()} - {str(r['GIDECEGI_YER']).strip()}")

urun_listesi = []
for _, r in df_urunler.iterrows():
    if pd.notna(r["URUN_ADI"]):
        urun_listesi.append(str(r["URUN_ADI"]).strip().upper())

if not urun_listesi:
    urun_listesi = ["0.50 LT PET SU", "1.50 LT PET SU", "5.00 LT PET SU", "19 LT DAMACANA"]

# Akıllı Sıralama Mantığı (Boştakiler Üste, Atananlar Alta)
if not df_sevkiyatlar.empty:
    df_sevkiyatlar['PLAKA_KONTROL'] = df_sevkiyatlar['PLAKA'].apply(lambda x: 0 if str(x).strip() == "" or str(x).lower() == "nan" else 1)
    df_sevkiyatlar = df_sevkiyatlar.sort_values(by=['PLAKA_KONTROL']).reset_index(drop=True)
    df_sevkiyatlar = df_sevkiyatlar.drop(columns=['PLAKA_KONTROL'])

def satir_boya(row):
    if str(row["PLAKA"]).strip() == "" or str(row["PLAKA"]).lower() == "nan":
        return ['background-color: #fef7e0; color: #b06000; font-weight: bold;'] * len(row)
    else:
        return ['background-color: #e6f4ea; color: #137333; font-weight: 600;'] * len(row)

# 📊 EKRAN GÖSTERİMİ
st.sidebar.markdown("### 🚪 SİSTEM GİRİŞİ")
giris_turu = st.sidebar.radio("Rolünüzü Seçin:", ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"])

if giris_turu == "🚚 Şoför Ekranı (Sadece İzleme)":
    st.markdown("<h2 style='text-align: center; color: #1e3d59;'>🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU</h2>", unsafe_allow_html=True)
    st.divider()
    gosterilecek_df = df_sevkiyatlar.fillna("")
    styled_df = gosterilecek_df.style.apply(satir_boya, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.title("⚙️ Lojistik Yönetici Kontrol Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password")
    
    if sifre == "1234":
        st.success("Yönetici Girişi Başarılı.")

        # 📋 YENİ TANIMLAMALAR EKLEME ALANI
        st.divider()
        st.subheader("📋 Sabit Tanımlamalar Ekle (E-Tabloya Kaydeder)")
        col_tanim1, col_tanim2, col_tanim3 = st.columns(3)
        
        with col_tanim1:
            st.markdown("**🚚 Yeni Şoför & Plaka Ekle**")
            with st.form("sh_form", clear_on_submit=True):
                y_sh_adi = st.text_input("Şoför Adı Soyadı:")
                y_sh_plaka = st.text_input("Araç Plakası:")
                if st.form_submit_button("➕ Şoförü Kaydet"):
                    if y_sh_adi and y_sh_plaka:
                        if tabloya_yaz("Soforler", [y_sh_adi.strip(), y_sh_plaka.strip().upper()]):
                            st.success(f"{y_sh_adi} kaydedildi!")
                            st.rerun()
                        
        with col_tanim2:
            st.markdown("**🏢 Yeni Müşteri & Depo Ekle**")
            with st.form("dp_form", clear_on_submit=True):
                y_m_adi = st.text_input("Müşteri/Bayi Adı:")
                y_g_yer = st.text_input("Depo / Gideceği Yer:")
                if st.form_submit_button("➕ Depoyu Kaydet"):
                    if y_m_adi and y_g_yer:
                        if tabloya_yaz("Depolar", [y_m_adi.strip(), y_g_yer.strip()]):
                            st.success(f"{y_m_adi} kaydedildi!")
                            st.rerun()

        with col_tanim3:
            st.markdown("**📦 Yeni Ürün Çeşidi Ekle**")
            with st.form("ur_form", clear_on_submit=True):
                y_ur_adi = st.text_input("Ürün Adı:")
                if st.form_submit_button("➕ Ürünü Kaydet"):
                    if y_ur_adi:
                        if tabloya_yaz("Urunler", [y_ur_adi.strip().upper()]):
                            st.success(f"{y_ur_adi.upper()} kaydedildi!")
                            st.rerun()

        # ❌ SİSTEMDEN ŞOFÖR/BAYİ/ÜRÜN SİLME PANELİ
        st.divider()
        st.subheader("❌ Kayıtlı Tanımlamaları Sil (Şoför, Depo, Ürün)")
        st.caption("Çalışmayı bıraktığınız veya artık listede görünmesini istemediğiniz kayıtları buradan silebilirsiniz.")
        col_sil1, col_sil2, col_sil3 = st.columns(3)
        
        with col_sil1:
            if sofor_listesi:
                silinecek_sh = st.selectbox("Silinecek Şoförü Seçin:", sofor_listesi)
                if st.button("🗑️ Şoförü Listeden Kaldır"):
                    sh_adi_ham = silinecek_sh.split(" (")[0]
                    if tabloya_yaz("Soforler", [], aksiyon="SIL", aranan_deger=sh_adi_ham, aranan_sutun="SOFOR_ADI"):
                        st.success(f"{sh_adi_ham} sistemden silindi.")
                        st.rerun()
            else:
                st.info("Kayıtlı şoför bulunamadı.")
                
        with col_sil2:
            if depo_listesi:
                silinecek_dp = st.selectbox("Silinecek Depo/Bayi Seçin:", depo_listesi)
                if st.button("🗑️ Depoyu Listeden Kaldır"):
                    dp_adi_ham = silinecek_dp.split(" - ")[0]
                    if tabloya_yaz("Depolar", [], aksiyon="SIL", aranan_deger=dp_adi_ham, aranan_sutun="MUSTERI_ADI"):
                        st.success(f"{dp_adi_ham} sistemden silindi.")
                        st.rerun()
            else:
                st.info("Kayıtlı depo bulunamadı.")
                
        with col_sil3:
            if urun_listesi:
                silinecek_ur = st.selectbox("Silinecek Ürünü Seçin:", urun_listesi)
                if st.button("🗑️ Ürünü Listeden Kaldır"):
                    if tabloya_yaz("Urunler", [], aksiyon="SIL", aranan_deger=silinecek_ur, aranan_sutun="URUN_ADI"):
                        st.success(f"{silinecek_ur} sistemden silindi.")
                        st.rerun()
            else:
                st.info("Kayıtlı ürün bulunamadı.")

        # 🧹 GÜN SONU VE İŞ TEMİZLEME PANELİ
        st.divider()
        st.subheader("🧹 Gün Sonu Temizliği & İptal İşlemleri")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if st.button("🗑️ Sadece 'PLAKA ATANDI' Olanları Listeden Temizle"):
                for i, r in df_sevkiyatlar.iterrows():
                    if str(r["DURUM"]) == "PLAKA ATANDI":
                        tabloya_yaz("Sevkiyatlar", [], aksiyon="SIL", aranan_deger=str(r["ÜRÜNLER"]), aranan_sutun="ÜRÜNLER")
                st.success("Atanan tüm işler temizlendi!")
                st.rerun()
        with col_g2:
            if not df_sevkiyatlar.empty:
                silme_secenekleri = [f"Sıra {i+1}: {r['MÜŞTERİ']} ({r['DEPO']}) -> {r['ÜRÜNLER']}" for i, r in df_sevkiyatlar.iterrows()]
                secilen_silinecek = st.selectbox("Silinecek Aktif İş Emrini Seçin:", silme_secenekleri)
                if st.button("🚨 Seçilen İş Emrini Sil"):
                    idx = silme_secenekleri.index(secilen_silinecek)
                    hedef_satir = df_sevkiyatlar.iloc[idx]
                    if tabloya_yaz("Sevkiyatlar", [], aksiyon="SIL", aranan_deger=str(hedef_satir["ÜRÜNLER"]), aranan_sutun="ÜRÜNLER"):
                        st.success("İş emri silindi.")
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
                    if tabloya_yaz("Sevkiyatlar", [m_parca.strip(), d_parca.strip(), ", ".join(secilen_urunler), "", "BEKLİYOR (BOŞTA)"]):
                        st.success("İş başarıyla havuzda oluşturuldu!")
                        st.rerun()

        # ✍️ BOŞTAKİ İŞE PLAKA / ŞOFÖR ATA
        st.divider()
        st.subheader("✍️ Boştaki İşe Plaka / Şoför Ata")
        bostaki_isler_df = df_sevkiyatlar[df_sevkiyatlar["DURUM"] == "BEKLİYOR (BOŞTA)"]
        
        if not bostaki_isler_df.empty:
            bostaki_secenekler = [f"Sıra {i+1}: {r['MÜŞTERİ']} ({r['DEPO']}) -> {r['ÜRÜNLER']}" for i, r in bostaki_isler_df.iterrows()]
            cc1, cc2 = st.columns(2)
            with cc1: secilen_is_metni = st.selectbox("Plaka Atanacak İş Emrini Seçin:", bostaki_secenekler)
            with cc2: secilen_sofor = st.selectbox("Atanacak Şoför & Araç:", sofor_listesi if sofor_listesi else ["Önce yukarıdan şoför ekleyin"])
            if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)"):
                if secilen_is_metni and secilen_sofor and "Önce" not in secilen_sofor:
                    is_idx = bostaki_secenekler.index(secilen_is_metni)
                    hedef_satir = bostaki_isler_df.iloc[is_idx]
                    plaka_ayikla = secilen_sofor.split("(")[1].replace(")", "") if "(" in secilen_sofor else secilen_sofor
                    
                    if tabloya_yaz("Sevkiyatlar", [str(hedef_satir["MÜŞTERİ"]), str(hedef_satir["DEPO"]), str(hedef_satir["ÜRÜNLER"]), str(plaka_ayikla), "PLAKA ATANDI"], aksiyon="GUNCELLE", aranan_deger=str(hedef_satir["ÜRÜNLER"]), aranan_sutun="ÜRÜNLER"):
                        st.success(f"{plaka_ayikla} plakası e-tabloya başarıyla işlendi!")
                        st.rerun()
        else:
            st.info("Şu anda plaka atanmayı bekleyen boşta iş yok.")

        # 🛠️ AKTİF İŞ EMİRLERİNİ DÜZENLEME PANELİ
        st.divider()
        st.subheader("📝 Aktif İş Emrini Düzenle / Düzelt")
        
        if not df_sevkiyatlar.empty:
            tum_isler_secenekler = []
            for i, r in df_sevkiyatlar.iterrows():
                durum_emoji = "✅" if str(r['DURUM']) == "PLAKA ATANDI" else "⏳"
                plaka_notu = f" [{r['PLAKA']}]" if r['PLAKA'] and str(r['PLAKA']).lower() != 'nan' else " [BOŞTA]"
                tum_isler_secenekler.append(f"Sıra {i+1}: {durum_emoji} {r['MÜŞTERİ']} ({r['DEPO']}){plaka_notu}")
                
            secilen_duzenlenecek = st.selectbox("Düzeltme Yapılacak İş Emrini Seçin:", tum_isler_secenekler)
            duzenle_idx = tum_isler_secenekler.index(secilen_duzenlenecek)
            mevcut_satir = df_sevkiyatlar.iloc[duzenle_idx]
            
            with st.form(f"duzenleme_formu_{duzenle_idx}"):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    yeni_musteri = st.text_input("Müşteri Adı:", value=str(mevcut_satir["MÜŞTERİ"]))
                    yeni_depo = st.text_input("Depo / Gideceği Yer:", value=str(mevcut_satir["DEPO"]))
                with col_d2:
                    yeni_urunler_metni = st.text_input("Yüklü Ürünler:", value=str(mevcut_satir["ÜRÜNLER"]))
                    yeni_plaka = st.text_input("Atanan Plaka (Boş bırakırsanız boşa çıkar):", value="" if str(mevcut_satir["PLAKA"]).lower() == "nan" else str(mevcut_satir["PLAKA"]))
                
                if st.form_submit_button("💾 Değişiklikleri Kaydet ve Listeyi Güncelle"):
                    y_durum = "BEKLİYOR (BOŞTA)" if yeni_plaka.strip() == "" else "PLAKA ATANDI"
                    if tabloya_yaz("Sevkiyatlar", [yeni_musteri, yeni_depo, yeni_urunler_metni, yeni_plaka, y_durum], aksiyon="GUNCELLE", aranan_deger=str(mevcut_satir["ÜRÜNLER"]), aranan_sutun="ÜRÜNLER"):
                        st.success("İş emri başarıyla güncellendi!")
                        st.rerun()
        else:
            st.info("Düzenlenecek herhangi bir aktif iş emri bulunmuyor.")
