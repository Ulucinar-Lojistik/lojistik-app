import streamlit as st
import pandas as pd

st.set_page_config(page_title="Lojistik Sevkiyat Paneli", layout="wide")

# Sistem Hafızası (Session State) Kurulumları
if 'sevkiyatlar' not in st.session_state:
    st.session_state.sevkiyatlar = pd.DataFrame([
        {"MÜŞTERİ": "A101", "DEPO": "İZMİR", "ÜRÜNLER": "1.50 LT PET SU", "PLAKA": "15AB175", "DURUM": "YÜKLENDİ"},
        {"MÜŞTERİ": "BİM", "DEPO": "KONYA", "ÜRÜNLER": "0.50 LT PET SU, 5.00 LT PET SU", "PLAKA": "", "DURUM": "BEKLİYOR (BOŞTA)"},
    ])
if 'sofor_listesi' not in st.session_state:
    st.session_state.sofor_listesi = ["İbrahim Erdem (15AB175)", "Hasan Akın (15AL283)"]
if 'depo_listesi' not in st.session_state:
    st.session_state.depo_listesi = ["A101 - İZMİR", "BİM - KONYA", "ABANT SU - BURDUR"]
if 'urun_listesi' not in st.session_state:
    st.session_state.urun_listesi = ["0.50 LT PET SU", "1.50 LT PET SU", "5.00 LT PET SU"]

# Kaydedildi mesajlarını sayfa yenilense de gösterebilmek için geçici hafıza alanları
if 'mesaj_sofor' not in st.session_state: st.session_state.mesaj_sofor = ""
if 'mesaj_depo' not in st.session_state: st.session_state.mesaj_depo = ""
if 'mesaj_urun' not in st.session_state: st.session_state.mesaj_urun = ""

def satir_boya(row):
    if str(row["PLAKA"]).strip() == "":
        return ['background-color: #fef7e0; color: #b06000; font-weight: bold;'] * len(row)
    else:
        return ['background-color: #e6f4ea; color: #137333; font-weight: 600;'] * len(row)

st.sidebar.markdown("### 🚪 SİSTEM GİRİŞİ")
giris_turu = st.sidebar.radio("Rolünüzü Seçin:", ["🚚 Şoför Ekranı (Sadece İzleme)", "⚙️ Yönetici Paneli (Veri Giriş)"])

if giris_turu == "🚚 Şoför Ekranı (Sadece İzleme)":
    st.markdown("<h2 style='text-align: center; color: #1e3d59;'>🚚 SEVKİYAT TAKİP VE AKTİF İŞ HAVUZU</h2>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center; color: #17b978;'>• CANLI ŞOFÖR BİLGİLENDİRME PANOSU •</h5>", unsafe_allow_html=True)
    st.divider()
    
    styled_df = st.session_state.sevkiyatlar.style.apply(satir_boya, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-top: 30px;'>🔄 Liste her dakika otomatik yenilenir. Boştaki (Turuncu) işler için sevkiyat amirliği ile görüşün.</p>", unsafe_allow_html=True)

else:
    st.title("⚙️ Lojistik Yönetici Kontrol Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi:", type="password")
    
    if sifre == "1234":
        st.success("Giriş Başarılı. Veri ekleme ve güncelleme yapabilirsiniz.")
        
        # Üstte biriken yeşil uyarı mesajlarını göster ve temizle
        if st.session_state.mesaj_sofor:
            st.success(st.session_state.mesaj_sofor)
            st.session_state.mesaj_sofor = ""
        if st.session_state.mesaj_depo:
            st.success(st.session_state.mesaj_depo)
            st.session_state.mesaj_depo = ""
        if st.session_state.mesaj_urun:
            st.success(st.session_state.mesaj_urun)
            st.session_state.mesaj_urun = ""

        st.subheader("📦 1. Hızlı Tanımlamalar (Hafızaya Alınacak Sabitler)")
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            with st.form("sofor_ekleme_formu", clear_on_submit=True):
                st.markdown("**👤 Yeni Şoför & Plaka Kaydet**")
                s_ad = st.text_input("Şoför Adı Soyadı:")
                s_plaka = st.text_input("Araç Plakası:")
                if st.form_submit_button("💾 Şoförü Hafızaya Ekle"):
                    if s_ad and s_plaka:
                        st.session_state.sofor_listesi.append(f"{s_ad} ({s_plaka})")
                        st.session_state.mesaj_sofor = f"✅ Şoför {s_ad} ({s_plaka}) başarıyla hafızaya kaydedildi!"
                        st.rerun()
                        
        with col_s2:
            with st.form("depo_ekleme_formu", clear_on_submit=True):
                st.markdown("**🏢 Yeni Müşteri & Depo Kaydet**")
                m_ad = st.text_input("Müşteri / Firma Adı:")
                d_yer = st.text_input("Gideceği Yer/Şehir:")
                if st.form_submit_button("💾 Depoyu Hafızaya Ekle"):
                    if m_ad and d_yer:
                        st.session_state.depo_listesi.append(f"{m_ad} - {d_yer}")
                        st.session_state.mesaj_depo = f"✅ Depo {m_ad} - {d_yer} başarıyla hafızaya kaydedildi!"
                        st.rerun()

        with col_s3:
            with st.form("urun_ekleme_formu", clear_on_submit=True):
                st.markdown("**💧 Yeni Ürün Çeşidi Kaydet**")
                yeni_urun = st.text_input("Ürün Hacmi/Türü (Örn: 19 LT Damacana):")
                if st.form_submit_button("💾 Ürünü Hafızaya Ekle"):
                    if yeni_urun:
                        if yeni_urun not in st.session_state.urun_listesi:
                            st.session_state.urun_listesi.append(yeni_urun)
                            st.session_state.mesaj_urun = f"✅ Ürün {yeni_urun} başarıyla ürün listesine eklendi!"
                            st.rerun()
        
        st.divider()
        st.subheader("➕ 2. Günlük Yeni İş Emri Ekle")
        with st.form("is_formu", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: 
                secilen_yer = st.selectbox("Müşteri & Depo Seç (Hafızadan):", st.session_state.depo_listesi)
            with c2: 
                secilen_urunler = st.multiselect("Yüklenecek Ürünleri Seçin (Çoklu Seçilebilir):", st.session_state.urun_listesi)
            
            if st.form_submit_button("🚀 Veriyi Havuza Gönder (Turuncu Yap)"):
                if secilen_yer and secilen_urunler:
                    m_parca, d_parca = secilen_yer.split(" - ")
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
                    st.error("Lütfen Depo ve en az bir Ürün seçtiğinizden emin olun.")

        st.divider()
        st.subheader("✍️ 3. Boştaki İşe Plaka / Şoför Ata")
        
        # Plakası boş olan satırları bulup indeks numarası ve müşteri bilgisiyle listeliyoruz
        bostaki_isler_df = st.session_state.sevkiyatlar[st.session_state.sevkiyatlar["PLAKA"] == ""]
        
        if not bostaki_isler_df.empty:
            # Seçim kutusunda göstermek için benzersiz seçenekler hazırlıyoruz
            bostaki_secenekler = []
            for idx, row in bostaki_isler_df.iterrows():
                bostaki_secenekler.append(f"Sıra {idx+1}: {row['MÜŞTERİ']} ({row['DEPO']}) -> {row['ÜRÜNLER']}")
                
            cc1, cc2 = st.columns(2)
            with cc1: 
                secilen_is_metni = st.selectbox("Plaka Atanacak İş Emrini Seçin:", bostaki_secenekler)
            with cc2: 
                secilen_sofor = st.selectbox("Atanacak Şoför & Araç (Hafızadan):", st.session_state.sofor_listesi)
            
            if st.button("✅ Plakayı Güncelle (Satırı Yeşile Döndür)"):
                # Seçilen metinden tablodaki gerçek indeks numarasını geri ayıklıyoruz
                secilen_sira_no = int(secilen_is_metni.split(":")[0].replace("Sıra ", "")) - 1
                plaka_ayikla = secilen_sofor.split("(")[1].replace(")", "")
                
                st.session_state.sevkiyatlar.loc[secilen_sira_no, "PLAKA"] = plaka_ayikla
                st.session_state.sevkiyatlar.loc[secilen_sira_no, "DURUM"] = "YÜKLENDİ"
                st.success("Plaka başarıyla atandı!")
                st.rerun()
        else:
            st.info("Havuzda plaka atanmayı bekleyen boşta iş yok.")
