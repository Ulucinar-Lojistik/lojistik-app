import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(page_title="Lojistik Sevkiyat Paneli", layout="wide")

# 🔗 GOOGLE SHEETS BAĞLANTI AYARLARI
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

# 🔄 SİSTEMİ BAŞLATMA VE CANLI VERİ ÇEKME
if 'aksiyon_tetik' not in st.session_state:
    st.session_state.aksiyon_tetik = 0

# Tablolardan verileri çek (Yeni Urunler sekmesi dahil)
df_sevkiyatlar = tabloyu_oku("Sevkiyatlar")
df_soforler = tabloyu_oku("Soforler")
df_depolar = tabloyu_oku("Depolar")
df_urunler = tabloyu_oku("Urunler")

# Boşsa kalıpları oluştur
if df_sevkiyatlar.empty:
    df_sevkiyatlar = pd.DataFrame(columns=["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"])
if df_soforler.empty:
    df_soforler = pd.DataFrame(columns=["SOFOR_ADI", "PLAKA"])
if df_depolar.empty:
    df_depolar = pd.DataFrame(columns=["MUSTERI_ADI", "GIDECEGI_YER"])
if df_urunler.empty:
    df_urunler = pd.DataFrame(columns=["URUN_ADI"])

# Session State Hafızasını Senkronize Et
if 'sevkiyatlar' not in st.session_state or st.session_state.aksiyon_tetik == 0:
    st.session_state.sevkiyatlar = df_sevkiyatlar
if 'soforler_list' not in st.session_state or st.session_state.aksiyon_tetik == 0:
    st.session_state.soforler_list = df_soforler
if 'depolar_list' not in st.session_state or st.session_state.aksiyon_tetik == 0:
    st.session_state.depolar_list = df_depolar
if 'urunler_list' not in st.session_state or st.session_state.aksiyon_tetik == 0:
    st.session_state.urunler_list = df_urunler

if 'mesaj_genel' not in st.session_state: st.session_state.mesaj_genel = ""

# Listeleri güncelle
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

# Eğer e-tabloda ürün yoksa sistem çökmesin diye varsayılanlar:
if not urun_listesi:
    urun_listesi = ["0.50 LT PET SU", "1.50 LT PET SU", "5.00 LT PET SU", "19 LT DAMACANA"]

# Akıllı Sıralama Mantığı
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
    st.markdown("<h5 style='text-align: center; color: #17b978;'>• CANLI ŞOFÖR BİLGİLENDİRME PANOSU •</h5>", unsafe_allow_html=True)
    st.divider()
    
    gosterilecek_df = st.session_state.sevkiyatlar.fillna("")
    styled_df = gosterilecek_df.style.apply(satir_boya, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-top: 30px;'>🔄 Liste her dakika otomatik yenilenir. Boştaki (Turuncu) işler için sevkiyat amirliği ile görüşün.</p>", unsafe_allow_html=True)

else:
    st.title("⚙️ Lojistik Yönetici Kontrol Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password")
    
    if sifre == "1234":
        st.success("Giriş Başarılı. Tüm yönetim araçları aşağıdadır.")
        if st.session_state.mesaj_genel: st.success(st.session_state.mesaj_genel); st.session_state.mesaj_genel = ""

        # 📋 TEK SAYFADA TÜM EKLEME ALANLARI (Şoför, Depo ve Kalıcı Ürün)
        st.divider()
        st.subheader("📋 Sabit Tanımlamalar (Şoför / Depo / Ürün Kaydet)")
        st.caption("Buraya eklediğin tüm bilgiler anında aşağıdaki iş emri ve plaka atama listelerine kalıcı olarak yansır.")
        
        col_tanim1, col_tanim2, col_tanim3 = st.columns(3)
        
        with col_tanim1:
            st.markdown("**🚚 Yeni Şoför & Plaka Ekle**")
            with st.form("sh_form", clear_on_submit=True):
                y_sh_adi = st.text_input("Şoför Adı Soyadı:")
                y_sh_plaka = st.text_input("Araç Plakası:")
                if st.form_submit_button("➕ Şoförü Kaydet"):
                    if y_sh_adi and y_sh_plaka:
                        yeni_sh_row = pd.DataFrame([{"SOFOR_ADI": y_sh_adi, "PLAKA": y_sh_plaka}])
                        st.session_state.soforler_list = pd.concat([st.session_state.soforler_list, yeni_sh_row], ignore_index=True)
                        st.session_state.aksiyon_tetik += 1
                        st.success(f"{y_sh_adi} eklendi!")
                        st.rerun()
                        
        with col_tanim2:
            st.markdown("**🏢 Yeni Müşteri & Depo Ekle**")
            with st.form("dp_form", clear_on_submit=True):
                y_m_adi = st.text_input("Müşteri Adı (Örn: BİM, A101):")
                y_g_yer = st.text_input("Depo / Gideceği Yer:")
                if st.form_submit_button("➕ Depoyu Kaydet"):
                    if y_m_adi and y_g_yer:
                        yeni_dp_row = pd.DataFrame([{"MUSTERI_ADI": y_m_adi, "GIDECEGI_YER": y_g_yer}])
                        st.session_state.depolar_list = pd.concat([st.session_state.depolar_list, yeni_dp_row], ignore_index=True)
                        st.session_state.aksiyon_tetik += 1
                        st.success(f"{y_m_adi} - {y_g_yer} eklendi!")
                        st.rerun()

        with col_tanim3:
            st.markdown("**📦 Yeni Ürün Çeşidi Ekle (Kalıcı)**")
            with st.form("ur_form", clear_on_submit=True):
                y_ur_adi = st.text_input("Ürün Adı (Örn: 0.33 LT PET SU):")
                if st.form_submit_button("➕ Ürünü Kaydet"):
                    if y_ur_adi and y_ur_adi.upper() not in urun_listesi:
                        yeni_ur_row = pd.DataFrame([{"URUN_ADI": y_ur_adi.upper()}])
                        st.session_state.urunler_list = pd.concat([st.session_state.urunler_list, yeni_ur_row], ignore_index=True)
                        st.session_state.aksiyon_tetik += 1
                        st.success(f"{y_ur_adi.upper()} başarıyla kalıcı listeye eklendi!")
                        st.rerun()

        # 🧹 GÜN SONU VE İŞ TEMİZLEME PANELİ
        st.divider()
        st.subheader("🧹 Gün Sonu Temizliği & İptal İşlemleri")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("**🔄 Gün Sonu Sıfırlama**")
            if st.button("🗑️ Sadece 'PLAKA ATANDI' Olanları Listeden Temizle", type="secondary"):
                st.session_state.sevkiyatlar = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["DURUM"] == "BEKLİYOR (BOŞTA)"].reset_index(drop=True)
                st.session_state.aksiyon_tetik += 1
                st.session_state.mesaj_genel = "🧹 Plakası atanan tüm işler ekrandan temizlendi!"
                st.rerun()
                
        with col_g2:
            st.markdown("**❌ Özel İş İptal Et / Sil**")
            if not st.session_state.sevkiyatlar.empty:
                silme_secenekleri = []
                silme_haritasi = {}
                for list_idx, (real_idx, row) in enumerate(st.session_state.sevkiyatlar.iterrows()):
                    durum_notu = "✅" if row['DURUM'] == "PLAKA ATANDI" else "⏳"
                    opt_text = f"Sıra {list_idx+1}: {durum_notu} {row['MÜŞTERİ']} ({row['DEPO']}) -> {row['ÜRÜNLER']}"
                    silme_secenekleri.append(opt_text)
                    silme_haritasi[opt_text] = real_idx
                    
                secilen_silinecek = st.selectbox("Sistemden Tamamen Silinecek İşi Seçin:", silme_secenekleri)
                if st.button("🚨 Seçilen İş Emrini Listeden Sil", type="primary"):
                    gercek_sil_idx = silme_haritasi[secilen_silinecek]
                    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.drop(gercek_sil_idx).reset_index(drop=True)
                    st.session_state.aksiyon_tetik += 1
                    st.session_state.mesaj_genel = "❌ Seçilen iş emri başarıyla sistemden kaldırıldı!"
                    st.rerun()

        # 🔄 ARAÇ ARIZA / PLAKA REVİZE PANELİ
        st.divider()
        st.subheader("🔄 Atanan Plakayı İptal Et (Arıza / Revize)")
        
        atanmis_isler_df = pd.DataFrame()
        if not st.session_state.sevkiyatlar.empty:
            atanmis_isler_df = st.session_state.sevkiyatlar[(st.session_state.sevkiyatlar["PLAKA"].str.strip() != "") & (st.session_state.sevkiyatlar["PLAKA"].notna()) & (st.session_state.sevkiyatlar["PLAKA"] != "")]
        
        if not atanmis_isler_df.empty:
            revize_secenekleri = []
            revize_haritasi = {}
            for list_idx, (real_idx, row) in enumerate(atanmis_isler_df.iterrows()):
                rev_text = f"İş {list_idx+1}: {row['MÜŞTERİ']} ({row['DEPO']}) -> Araç: {row['PLAKA']}"
                revize_secenekleri.append(rev_text)
                revize_haritasi[rev_text] = real_idx
                
            col_r1, col_r2 = st.columns([2, 1])
            with col_r1:
                secilen_revize_is = st.selectbox("Plakası İptal Edilecek İşi Seçin:", revize_secenekleri)
            with col_r2:
                st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                if st.button("⚠️ Plakayı Sök / İşi Boşa Çıkar", use_container_width=True):
                    gercek_rev_idx = revize_haritasi[secilen_revize_is]
                    st.session_state.sevkiyatlar.loc[gercek_rev_idx, "PLAKA"] = ""
                    st.session_state.sevkiyatlar.loc[gercek_rev_idx, "DURUM"] = "BEKLİYOR (BOŞTA)"
                    st.session_state.aksiyon_tetik += 1
                    st.session_state.mesaj_genel = "🔄 Araç plakası iptal edildi, iş emri yeniden üst sıraya gönderildi!"
                    st.rerun()
        else:
            st.info("Şu anda plakası atanmış aktif bir iş bulunmuyor.")

        # ➕ GÜNLÜK YENİ İŞ EMRİ EKLE
        st.divider()
        st.subheader("➕ Günlük Yeni İş Emri Ekle")
        with st.form("is_formu", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: 
                secilen_yer = st.selectbox("Müşteri & Depo Seç:", depo_listesi if depo_listesi else ["Önce yukarıdan depo ekleyin"])
            with c2: 
                secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin:", urun_listesi)
            
            if st.form_submit_button("🚀 Veriyi Havuza Gönder (Turuncu Yap)"):
                if secilen_yer and secilen_urunler and "Önce" not in secilen_yer:
                    if " - " in secilen_yer:
                        m_parca, d_parca = secilen_yer.split(" - ", 1)
                    else:
                        m_parca, d_parca = secilen_yer, "Belirtilmedi"
                        
                    urunler_metni = ", ".join(secilen_urunler)
                    
                    yeni_is = {
                        "MÜŞTERİ": m_parca, 
                        "DEPO": d_parca, 
                        "ÜRÜNLER": urunler_metni, 
                        "PLAKA": "", 
                        "DURUM": "BEKLİYOR (BOŞTA)"
                    }
                    st.session_state.sevkiyatlar = pd.concat([st.session_state.sevkiyatlar, pd.DataFrame([yeni_is])], ignore_index=True)
                    st.session_state.aksiyon_tetik += 1
                    st.success("İş emri başarıyla havuza eklendi!")
                    st.rerun()

        # ✍️ BOŞTAKİ İŞE PLAKA / ŞOFÖR ATA
        st.divider()
        st.subheader("✍️ Boştaki İşe Plaka / Şoför Ata")
        
        bostaki_isler_df = pd.DataFrame()
        if not st.session_state.sevkiyatlar.empty:
            bostaki_isler_df = st.session_state.sevkiyatlar[(st.session_state.sevkiyatlar["PLAKA"].isna()) | (st.session_state.sevkiyatlar["PLAKA"] == "") | (st.session_state.sevkiyatlar["PLAKA"].get("", pd.Series()).str.strip() == "")]
        
        if not bostaki_isler_df.empty:
            bostaki_secenekler = []
            indeks_haritasi = {}
            
            for list_idx, (real_idx, row) in enumerate(bostaki_isler_df.iterrows()):
                gorunum_metni = f"İş Sırası {list_idx+1}: {row['MÜŞTERİ']} ({row['DEPO']}) -> {row['ÜRÜNLER']}"
                bostaki_secenekler.append(gorunum_metni)
                indeks_haritasi[gorunum_metni] = real_idx
                
            cc1, cc2 = st.columns(2)
            with cc1: 
                secilen_is_metni = st.selectbox("Plaka Atanacak İş Emrini Seçin:", bostaki_secenekler)
            with cc2: 
                secilen_sofor = st.selectbox("Atanacak Şoför & Araç:", sofor_listesi if sofor_listesi else ["Önce yukarıdan şoför ekleyin"])
            
            if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)"):
                if secilen_is_metni and secilen_sofor and "Önce" not in secilen_sofor:
                    gercek_satir_no = indeks_haritasi[secilen_is_metni]
                    
                    if "(" in secilen_sofor:
                        plaka_ayikla = secilen_sofor.split("(")[1].replace(")", "")
                    else:
                        plaka_ayikla = secilen_sofor
                    
                    st.session_state.sevkiyatlar.loc[gercek_satir_no, "PLAKA"] = plaka_ayikla
                    st.session_state.sevkiyatlar.loc[gercek_satir_no, "DURUM"] = "PLAKA ATANDI"
                    st.session_state.aksiyon_tetik += 1
                    st.success("Plaka başarıyla atandı!")
                    st.rerun()
        else:
            st.info("Havuzda plaka atanmayı bekleyen boşta iş yok.")
