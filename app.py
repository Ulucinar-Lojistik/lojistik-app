import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(page_title="Lojistik Sevkiyat Paneli", layout="wide")

# 🔗 GOOGLE SHEETS BAĞLANTI AYARLARI
SHEET_ID = "1dxRbPvjXBwlozdEzlwqsQ-HSjf_nKU5hIvTLa_W4TaI"

# Google Sheets'ten Canlı Veri Okuma Fonksiyonu
def tabloyu_oku(sekme_adi):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sekme_adi}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            # Sütun isimlerindeki boşlukları temizle
            df.columns = df.columns.str.strip()
            return df
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# Google Sheets'e Veri Gönderme (Form Üzerinden Web App ile veya Alternatif Güncelleme)
# Not: Streamlit üzerinde doğrudan düzenleme için session_state senkronizasyonu kullanıyoruz.
# Eğer Google tablosuna anlık yazma hatası oluşursa altyapıyı streamlit secrets ile güçlendireceğiz.

# 🔄 CANLI VERİ ENTEGRASYONU (Her yenilemede tablodan güncel çekilir)
df_sevkiyatlar = tabloyu_oku("Sevkiyatlar")
df_soforler = tabloyu_oku("Soforler")
df_depolar = tabloyu_oku("Depolar")

# Eğer sekmeler boşsa veya hata alındıysa sistem çökmesin diye boş kalıplar:
if df_sevkiyatlar.empty:
    df_sevkiyatlar = pd.DataFrame(columns=["MÜŞTERİ", "DEPO", "ÜRÜNLER", "PLAKA", "DURUM"])
if df_soforler.empty:
    df_soforler = pd.DataFrame(columns=["SOFOR_ADI", "PLAKA"])
if df_depolar.empty:
    df_depolar = pd.DataFrame(columns=["MUSTERI_ADI", "GIDECEGI_YER"])

# Hafızayı ilk açılışta canlı tablodan besle
if 'sevkiyatlar' not in st.session_state:
    st.session_state.sevkiyatlar = df_sevkiyatlar

# Sabit listeleri E-Tablodan dinamik oluştur
sofor_listesi = []
for _, r in df_soforler.iterrows():
    if pd.notna(r["SOFOR_ADI"]) and pd.notna(r["PLAKA"]):
        sofor_listesi.append(f"{r['SOFOR_ADI']} ({r['PLAKA']})")
if not sofor_listesi:
    sofor_listesi = ["Sistemde Şoför Bulunamadı (E-Tabloyu kontrol edin)"]

depo_listesi = []
for _, r in df_depolar.iterrows():
    if pd.notna(r["MUSTERI_ADI"]) and pd.notna(r["GIDECEGI_YER"]):
        depo_listesi.append(f"{r['MUSTERI_ADI']} - {r['GIDECEGI_YER']}")
if not depo_listesi:
    depo_listesi = ["Sistemde Depo Bulunamadı (E-Tabloyu kontrol edin)"]

# Ürün listesi şimdilik sabit veya yönetici panelinden genişletilebilir
if 'urun_listesi' not in st.session_state:
    st.session_state.urun_listesi = ["0.50 LT PET SU", "1.50 LT PET SU", "5.00 LT PET SU", "19 LT DAMACANA"]

# Mesaj hafızaları
if 'mesaj_genel' not in st.session_state: st.session_state.mesaj_genel = ""

def satir_boya(row):
    if str(row["PLAKA"]).strip() == "" or pd.isna(row["PLAKA"]):
        return ['background-color: #fef7e0; color: #b06000; font-weight: bold;'] * len(row)
    else:
        return ['background-color: #e6f4ea; color: #137333; font-weight: 600;'] * len(row)

st.sidebar.markdown("### 🚪 SİSTEM GİRİŞİ")
giris_turu = st.sidebar.radio("Rolünüzü Seçin:", ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"])

# 📌 AKILLI SIRALAMA MANTIĞI: Plakası boş olanlar (bekleyenler) hep en üstte, atananlar en altta kalır.
if not st.session_state.sevkiyatlar.empty:
    st.session_state.sevkiyatlar['PLAKA_KONTROL'] = st.session_state.sevkiyatlar['PLAKA'].apply(lambda x: 0 if str(x).strip() == "" or pd.isna(x) else 1)
    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.sort_values(by=['PLAKA_KONTROL']).reset_index(drop=True)
    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.drop(columns=['PLAKA_KONTROL'])

if giris_turu == "🚚 Şoför Ekranı (Sadece İzleme)":
    st.markdown("<h2 style='text-align: center; color: #1e3d59;'>🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU</h2>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center; color: #17b978;'>• CANLI ŞOFÖR BİLGİLENDİRME PANOSU •</h5>", unsafe_allow_html=True)
    st.divider()
    
    # Boş verileri şık göster
    gosterilecek_df = st.session_state.sevkiyatlar.fillna("")
    styled_df = gosterilecek_df.style.apply(satir_boya, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-top: 30px;'>🔄 Liste her dakika otomatik yenilenir. Boştaki (Turuncu) işler için sevkiyat amirliği ile görüşün.</p>", unsafe_allow_html=True)

else:
    st.title("⚙️ Lojistik Yönetici Kontrol Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password")
    
    if sifre == "1234":
        st.success("Giriş Başarılı. Veri ekleme ve güncelleme yapabilirsiniz.")
        if st.session_state.mesaj_genel: st.success(st.session_state.mesaj_genel); st.session_state.mesaj_genel = ""

        # GÜN SONU VE İŞ TEMİZLEME PANELİ
        st.divider()
        st.subheader("🧹 3. Gün Sonu Temizliği & İptal İşlemleri")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("**🔄 Gün Sonu Sıfırlama**")
            st.caption("Plakası atanan (Yeşil) tüm işleri ekrandan temizler. Bekleyen (Turuncu) işler kalır.")
            if st.button("🗑️ Sadece 'PLAKA ATANDI' Olanları Listeden Temizle", type="secondary"):
                st.session_state.sevkiyatlar = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["DURUM"] == "BEKLİYOR (BOŞTA)"].reset_index(drop=True)
                st.session_state.mesaj_genel = "🧹 Plakası atanan tüm işler ekrandan temizlendi!"
                st.rerun()
                
        with col_g2:
            st.markdown("**❌ Özel İş İptal Et / Sil**")
            st.caption("İptal olan iş emrini listeden tamamen kaldırır.")
            
            if not st.session_state.sevkiyatlar.empty:
                silme_secenekleri = []
                silme_haritasi = {}
                for list_idx, (real_idx, row) in enumerate(st.session_state.sevkiyatlar.iterrows()):
                    durum_notu = "✅" if row['DURUM'] == "PLAKA ATANDI" else "⏳"
                    opt_text = f"Sıra {list_idx+1}: {durum_notu} {row['MÜŞTERİ']} ({row['DEPO']}) -> {row['ÜRÜNLER']}"
                    silme_secenekleri.append(opt_text)
                    silme_haritasi[opt_text] = real_idx
                    
                secilen_silinecek = st.selectbox("Sistemden Tamamen Silinecek İşi Seçin:", silme_secenekleri, key="silme_box")
                if st.button("🚨 Seçilen İş Emrini Listeden Sil", type="primary"):
                    gercek_sil_idx = silme_haritasi[secilen_silinecek]
                    st.session_state.sevkiyatlar = st.session_state.sevkiyatlar.drop(gercek_sil_idx).reset_index(drop=True)
                    st.session_state.mesaj_genel = "❌ Seçilen iş emri başarıyla sistemden kaldırıldı!"
                    st.rerun()

        # ARAÇ ARIZA / PLAKA REVİZE PANELİ
        st.divider()
        st.subheader("🔄 4. Atanan Plakayı İptal Et (Arıza / Revize)")
        st.caption("Araç arıza yaptığında, plaka atanmış (Yeşil) bir işi tekrar 'Boşta/Bekliyor' (Turuncu) durumuna getirir ve en üste taşır.")
        
        atanmis_isler_df = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["PLAKA"].get("", pd.Series()) != ""]
        if not st.session_state.sevkiyatlar.empty:
            atanmis_isler_df = st.session_state.sevkiyatlar[(st.session_state.sevkiyatlar["PLAKA"].str.strip() != "") & (st.session_state.sevkiyatlar["PLAKA"].notna())]
        
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
                    st.session_state.mesaj_genel = "🔄 Araç plakası iptal edildi, iş emri yeniden üst sıraya gönderildi!"
                    st.rerun()
        else:
            st.info("Şu anda plakası atanmış aktif bir iş bulunmuyor.")

        # GÜNLÜK YENİ İŞ EMRİ EKLE
        st.divider()
        st.subheader("➕ 1. Günlük Yeni İş Emri Ekle")
        st.caption("Müşteri ve Depolar doğrudan Google E-Tablonuzdaki canlı listeden çekilmektedir.")
        with st.form("is_formu", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: 
                secilen_yer = st.selectbox("Müşteri & Depo Seç (Canlı Tablodan):", depo_listesi)
            with c2: 
                secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin (Çoklu Seçim):", st.session_state.urun_listesi)
            
            if st.form_submit_button("🚀 Veriyi Havuza Gönder (Turuncu Yap)"):
                if secilen_yer and secilen_urunler and "Sistemde" not in secilen_yer:
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
                    st.success("İş emri başarıyla havuza eklendi!")
                    st.rerun()
                else:
                    st.error("Lütfen geçerli bir Depo ve en az bir Ürün seçin.")

        # BOŞTAKİ İŞE PLAKA / ŞOFÖR ATA
        st.divider()
        st.subheader("✍️ 2. Boştaki İşe Plaka / Şoför Ata")
        st.caption("Şoförler ve araç plakaları doğrudan Google E-Tablonuzdaki canlı listeden çekilmektedir.")
        
        bostaki_isler_df = st.session_state.sevkiyatlar[(st.session_state.sevkiyatlar["PLAKA"].isna()) | (st.session_state.sevkiyatlar["PLAKA"].get("", pd.Series()).str.strip() == "")]
        
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
                secilen_sofor = st.selectbox("Atanacak Şoför & Araç (Canlı Tablodan):", sofor_listesi)
            
            if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)"):
                if secilen_is_metni and secilen_sofor and "Sistemde" not in secilen_sofor:
                    gercek_satir_no = indeks_haritasi[secilen_is_metni]
                    
                    if "(" in secilen_sofor:
                        plaka_ayikla = secilen_sofor.split("(")[1].replace(")", "")
                    else:
                        plaka_ayikla = secilen_sofor
                    
                    st.session_state.sevkiyatlar.loc[gercek_satir_no, "PLAKA"] = plaka_ayikla
                    st.session_state.sevkiyatlar.loc[gercek_satir_no, "DURUM"] = "PLAKA ATANDI"
                    st.success("Plaka başarıyla atandı!")
                    st.rerun()
        else:
            st.info("Havuzda plaka atanmayı bekleyen boşta iş yok.")
